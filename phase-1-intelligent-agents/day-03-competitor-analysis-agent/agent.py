"""Real-time competitor intelligence agent.

Given your business niche and a list of competitor websites, the agent:
  1. Scrapes each competitor site (homepage + likely pricing page) in parallel.
  2. Extracts positioning, features, and pricing signals from the raw text.
  3. Runs an OpenAI analysis to produce:
       - a per-competitor SWOT matrix
       - a pricing & feature comparison table
       - review/market sentiment
       - strategic recommendations and feature gaps for YOU

Progress is reported through an async callback so the FastAPI layer can
stream it to the browser over a WebSocket.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Awaitable, Callable
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


@dataclass
class Competitor:
    name: str
    url: str
    content: str = ""
    scraped: bool = False


def _normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def _name_from_url(url: str) -> str:
    host = urlparse(url).netloc.replace("www.", "")
    return host.split(".")[0].capitalize() if host else url


class CompetitorAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def analyze(
        self, niche: str, urls: list[str], progress: ProgressFn = _noop
    ) -> dict:
        await progress("start", f"Analyzing {len(urls)} competitors in: {niche}")

        competitors = [
            Competitor(name=_name_from_url(u), url=u)
            for u in (_normalize_url(x) for x in urls)
            if u
        ]
        if not competitors:
            raise ValueError("No valid competitor URLs provided")

        competitors = await self._scrape_all(competitors, progress)
        result = await self._synthesize(niche, competitors, progress)

        await progress("done", "Competitive analysis complete")
        result["competitors_meta"] = [
            {"name": c.name, "url": c.url, "scraped": c.scraped} for c in competitors
        ]
        return result

    async def _scrape_all(
        self, competitors: list[Competitor], progress: ProgressFn
    ) -> list[Competitor]:
        await progress("scrape", f"Scraping {len(competitors)} competitor sites")
        headers = {"User-Agent": "Mozilla/5.0 (CompetitorAgent/1.0)"}

        async with httpx.AsyncClient(
            timeout=15, follow_redirects=True, headers=headers
        ) as client:

            async def _one(c: Competitor) -> None:
                texts: list[str] = []
                # Homepage
                home = await self._fetch_text(client, c.url)
                if home:
                    texts.append(home)
                    # Try to find a pricing page link from the homepage.
                    pricing_url = self._guess_pricing_url(c.url, home_html=home[1])
                    if pricing_url:
                        pg = await self._fetch_text(client, pricing_url)
                        if pg:
                            texts.append(pg)
                if texts:
                    c.content = " ".join(t[0] for t in texts)[:7000]
                    c.scraped = True
                await progress("scrape", f"✓ {c.name}" if c.scraped else f"✗ {c.name}")

            await asyncio.gather(*[_one(c) for c in competitors])

        ok = sum(1 for c in competitors if c.scraped)
        await progress("scrape", f"Scraped {ok}/{len(competitors)} sites")
        return competitors

    async def _fetch_text(
        self, client: httpx.AsyncClient, url: str
    ) -> tuple[str, str] | None:
        """Return (clean_text, raw_html) or None on failure."""
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = " ".join(soup.get_text(" ").split())
            return (text, html)
        except Exception:
            return None

    def _guess_pricing_url(self, base: str, home_html: str) -> str | None:
        try:
            soup = BeautifulSoup(home_html, "html.parser")
            for a in soup.find_all("a", href=True):
                label = (a.get_text() or "").lower()
                href = a["href"].lower()
                if "pricing" in label or "pricing" in href or "/plans" in href:
                    return urljoin(base, a["href"])
        except Exception:
            pass
        return None

    async def _synthesize(
        self, niche: str, competitors: list[Competitor], progress: ProgressFn
    ) -> dict:
        await progress("analyze", "Generating SWOT, pricing matrix, and strategy")

        corpus = "\n\n".join(
            f"### {c.name} ({c.url})\n{c.content[:3000]}"
            for c in competitors
            if c.content
        ) or "No site content could be scraped; analyze based on the names/URLs."

        names = ", ".join(c.name for c in competitors)
        prompt = (
            "You are a competitive intelligence analyst. Based ONLY on the scraped "
            f"content below for competitors in the '{niche}' niche, produce a "
            "structured analysis. Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "overview": "2-3 sentence market overview",\n'
            '  "competitors": [\n'
            "    {\n"
            '      "name": "competitor name",\n'
            '      "positioning": "one-line positioning",\n'
            '      "swot": {"strengths": ["..."], "weaknesses": ["..."],\n'
            '               "opportunities": ["..."], "threats": ["..."]},\n'
            '      "pricing": "summary of pricing tiers or Unknown",\n'
            '      "price_score": 0-100,\n'
            '      "feature_score": 0-100,\n'
            '      "sentiment": "positive|mixed|negative|unknown",\n'
            '      "key_features": ["feature", "..."]\n'
            "    }\n"
            "  ],\n"
            '  "feature_matrix": {"features": ["Feature A", "Feature B"],\n'
            '                     "rows": [{"name": "competitor", "has": [true,false]}]},\n'
            '  "gaps": ["feature gap / opportunity YOU could exploit"],\n'
            '  "recommendations": ["actionable strategic recommendation"]\n'
            "}\n"
            f"Competitors: {names}\n\nScraped content:\n{corpus}"
        )
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(resp.choices[0].message.content)
        data.setdefault("overview", "")
        data.setdefault("competitors", [])
        data.setdefault("feature_matrix", {"features": [], "rows": []})
        data.setdefault("gaps", [])
        data.setdefault("recommendations", [])
        await progress(
            "analyze",
            f"Analyzed {len(data['competitors'])} competitors, "
            f"{len(data['recommendations'])} recommendations",
        )
        return data
