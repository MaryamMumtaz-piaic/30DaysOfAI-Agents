"""Autonomous deep research agent.

Pipeline:
  1. Decompose a research topic into focused sub-queries (OpenAI).
  2. Search the web for each sub-query (Tavily).
  3. Scrape the top sources in parallel (httpx + BeautifulSoup).
  4. Extract claims and synthesize findings (OpenAI).
  5. Cross-validate claims across sources, detect contradictions,
     and assign a confidence score per claim.

Every stage reports progress through an async callback so the FastAPI
layer can stream it to the browser over a WebSocket.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Awaitable, Callable

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from tavily import TavilyClient

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_SOURCES = int(os.getenv("MAX_SOURCES", "10"))

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:  # default progress sink
    return None


@dataclass
class Source:
    title: str
    url: str
    content: str = ""
    scraped: bool = False


@dataclass
class Claim:
    text: str
    confidence: float
    supporting_sources: list[str] = field(default_factory=list)
    contradicting_sources: list[str] = field(default_factory=list)


@dataclass
class ResearchResult:
    topic: str
    summary: str
    sub_queries: list[str]
    key_insights: list[str]
    claims: list[Claim]
    contradictions: list[str]
    sources: list[Source]

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "summary": self.summary,
            "sub_queries": self.sub_queries,
            "key_insights": self.key_insights,
            "claims": [
                {
                    "text": c.text,
                    "confidence": c.confidence,
                    "supporting_sources": c.supporting_sources,
                    "contradicting_sources": c.contradicting_sources,
                }
                for c in self.claims
            ],
            "contradictions": self.contradictions,
            "sources": [
                {"title": s.title, "url": s.url, "scraped": s.scraped}
                for s in self.sources
            ],
        }


class ResearchAgent:
    def __init__(self) -> None:
        openai_key = os.getenv("OPENAI_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not openai_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        if not tavily_key:
            raise RuntimeError("TAVILY_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=openai_key)
        self.tavily = TavilyClient(api_key=tavily_key)

    async def research(
        self, topic: str, progress: ProgressFn = _noop
    ) -> ResearchResult:
        await progress("start", f"Starting research on: {topic}")

        sub_queries = await self._decompose(topic, progress)
        sources = await self._search(sub_queries, progress)
        sources = await self._scrape(sources, progress)
        synthesis = await self._synthesize(topic, sources, progress)
        claims = await self._score_claims(synthesis["claims"], sources, progress)

        await progress("done", "Research complete")
        return ResearchResult(
            topic=topic,
            summary=synthesis["summary"],
            sub_queries=sub_queries,
            key_insights=synthesis["key_insights"],
            claims=claims,
            contradictions=synthesis["contradictions"],
            sources=sources,
        )

    async def _decompose(self, topic: str, progress: ProgressFn) -> list[str]:
        await progress("decompose", "Breaking the topic into sub-queries")
        prompt = (
            "You are a research planner. Break the topic below into 4-6 focused, "
            "diverse web-search sub-queries that together give comprehensive coverage. "
            'Return JSON: {"sub_queries": ["...", "..."]}\n\n'
            f"Topic: {topic}"
        )
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        data = json.loads(resp.choices[0].message.content)
        queries = data.get("sub_queries", [])[:6] or [topic]
        await progress("decompose", f"Generated {len(queries)} sub-queries")
        return queries

    async def _search(
        self, sub_queries: list[str], progress: ProgressFn
    ) -> list[Source]:
        await progress("search", "Searching the web across all sub-queries")
        per_query = max(2, MAX_SOURCES // max(1, len(sub_queries)))

        def _one(q: str) -> list[dict]:
            try:
                res = self.tavily.search(
                    query=q, max_results=per_query, search_depth="advanced"
                )
                return res.get("results", [])
            except Exception:
                return []

        batches = await asyncio.gather(
            *[asyncio.to_thread(_one, q) for q in sub_queries]
        )

        seen: set[str] = set()
        sources: list[Source] = []
        for batch in batches:
            for r in batch:
                url = r.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    sources.append(
                        Source(
                            title=r.get("title", url),
                            url=url,
                            content=r.get("content", ""),
                        )
                    )
        sources = sources[:MAX_SOURCES]
        await progress("search", f"Found {len(sources)} unique sources")
        return sources

    async def _scrape(
        self, sources: list[Source], progress: ProgressFn
    ) -> list[Source]:
        await progress("scrape", f"Scraping {len(sources)} sources in parallel")
        headers = {"User-Agent": "Mozilla/5.0 (ResearchAgent/1.0)"}

        async with httpx.AsyncClient(
            timeout=15, follow_redirects=True, headers=headers
        ) as client:

            async def _fetch(src: Source) -> None:
                try:
                    resp = await client.get(src.url)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    text = " ".join(soup.get_text(" ").split())
                    if len(text) > 200:  # prefer full page over Tavily snippet
                        src.content = text[:6000]
                    src.scraped = True
                except Exception:
                    src.scraped = False  # keep the Tavily snippet as fallback

            await asyncio.gather(*[_fetch(s) for s in sources])

        scraped = sum(1 for s in sources if s.scraped)
        await progress("scrape", f"Scraped {scraped}/{len(sources)} sources")
        return sources

    async def _synthesize(
        self, topic: str, sources: list[Source], progress: ProgressFn
    ) -> dict:
        await progress("synthesize", "Synthesizing findings and extracting claims")
        corpus = "\n\n".join(
            f"[Source {i + 1}] {s.title} ({s.url})\n{s.content[:2500]}"
            for i, s in enumerate(sources)
            if s.content
        )
        prompt = (
            "You are a rigorous research analyst. Using ONLY the sources below, "
            "produce a structured analysis of the topic. Cite sources by their "
            "[Source N] label inside claims where relevant.\n\n"
            "Return JSON with this exact shape:\n"
            "{\n"
            '  "summary": "3-4 paragraph executive summary",\n'
            '  "key_insights": ["insight", "..."],\n'
            '  "claims": [{"text": "factual claim", "source_indices": [1,2]}],\n'
            '  "contradictions": ["describe any conflicts between sources"]\n'
            "}\n\n"
            f"Topic: {topic}\n\nSources:\n{corpus}"
        )
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(resp.choices[0].message.content)
        data.setdefault("summary", "")
        data.setdefault("key_insights", [])
        data.setdefault("claims", [])
        data.setdefault("contradictions", [])
        await progress(
            "synthesize",
            f"Extracted {len(data['claims'])} claims and "
            f"{len(data['key_insights'])} insights",
        )
        return data

    async def _score_claims(
        self, raw_claims: list[dict], sources: list[Source], progress: ProgressFn
    ) -> list[Claim]:
        await progress("validate", "Cross-validating claims and scoring confidence")
        claims: list[Claim] = []
        for rc in raw_claims:
            idxs = rc.get("source_indices", []) or []
            supporting = [
                sources[i - 1].url
                for i in idxs
                if isinstance(i, int) and 1 <= i <= len(sources)
            ]
            # Confidence = how many independent sources back the claim.
            n = len(set(supporting))
            confidence = min(0.98, 0.4 + 0.18 * n) if n else 0.35
            claims.append(
                Claim(
                    text=rc.get("text", ""),
                    confidence=round(confidence, 2),
                    supporting_sources=list(set(supporting)),
                )
            )
        await progress("validate", f"Scored {len(claims)} claims")
        return claims
