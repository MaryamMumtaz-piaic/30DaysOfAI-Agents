"""AI job application automation agent.

Given a resume and a job description, the agent:
  1. Reverse-engineers the job into required skills, keywords, and priorities.
  2. Scores how well the resume matches, with a gap analysis.
  3. Rewrites the resume to surface ATS keywords honestly.
  4. Drafts a tailored cover letter.
  5. Prepares likely interview questions with strong sample answers.

Progress is reported through an async callback so the FastAPI layer can
stream it to the browser over a WebSocket.
"""

from __future__ import annotations

import json
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAX_CHARS = 16000

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


class JobApplicationAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def analyze(
        self,
        resume: str,
        job: str,
        num_questions: int = 20,
        progress: ProgressFn = _noop,
    ) -> dict:
        resume = (resume or "").strip()[:MAX_CHARS]
        job = (job or "").strip()[:MAX_CHARS]
        if len(resume) < 40:
            raise ValueError("Resume text is too short to analyze")
        if len(job) < 40:
            raise ValueError("Job description is too short to analyze")

        num_questions = max(5, min(25, int(num_questions or 20)))

        await progress("start", "Reverse-engineering the job requirements")
        jd = await self._parse_job(job)
        await progress(
            "job",
            f"Extracted {len(jd.get('must_have_keywords', []))} must-have keywords for "
            f"{jd.get('title', 'the role')}",
        )

        await progress("match", "Scoring resume against the job and finding gaps")
        match = await self._match(resume, job, jd)
        await progress("match", f"Match score: {match.get('match_score', 0)}%")

        await progress("resume", "Rewriting the resume for ATS keyword coverage")
        rewrite = await self._rewrite_resume(resume, job, jd)

        await progress("cover", "Drafting a tailored cover letter")
        cover = await self._cover_letter(resume, job, jd)

        await progress("interview", f"Preparing {num_questions} interview questions with answers")
        interview = await self._interview(resume, job, jd, num_questions)

        await progress("done", "Application package ready")
        return {
            "job": jd,
            "match": match,
            "resume_rewrite": rewrite,
            "cover_letter": cover,
            "interview": interview,
        }

    async def _json(self, prompt: str, temperature: float = 0.4) -> dict:
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(resp.choices[0].message.content)

    async def _parse_job(self, job: str) -> dict:
        prompt = (
            "You are a technical recruiter. Reverse-engineer this job description. "
            "Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "title": "job title",\n'
            '  "company": "company name if stated, else empty",\n'
            '  "seniority": "e.g. Junior/Mid/Senior",\n'
            '  "summary": "2-sentence summary of what they want",\n'
            '  "must_have_keywords": ["ATS keyword / hard skill", "..."],\n'
            '  "nice_to_have_keywords": ["..."],\n'
            '  "responsibilities": ["core responsibility", "..."],\n'
            '  "soft_skills": ["..."]\n'
            "}\n"
            "Keywords must be concrete terms an ATS would scan for (tools, languages, "
            "certifications, methodologies). Keep lists focused (max ~12 each).\n\n"
            f"--- JOB DESCRIPTION ---\n{job}"
        )
        d = await self._json(prompt, 0.3)
        d.setdefault("title", "the role")
        for k in ("must_have_keywords", "nice_to_have_keywords", "responsibilities", "soft_skills"):
            d.setdefault(k, [])
        d.setdefault("company", "")
        d.setdefault("seniority", "")
        d.setdefault("summary", "")
        return d

    async def _match(self, resume: str, job: str, jd: dict) -> dict:
        prompt = (
            "You are an ATS and hiring analyst. Compare the RESUME against the JOB. "
            "Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "match_score": 0-100,\n'
            '  "verdict": "one-line hiring-readiness verdict",\n'
            '  "matched_keywords": ["keyword present in resume"],\n'
            '  "missing_keywords": ["important keyword absent from resume"],\n'
            '  "strengths": ["what makes this candidate a strong fit"],\n'
            '  "gaps": [{"gap": "what is missing/weak", "fix": "concrete action to close it"}],\n'
            '  "ats_tips": ["formatting/keyword tip to improve ATS parsing"]\n'
            "}\n"
            "match_score reflects genuine fit AND keyword coverage. Only list missing_keywords "
            "that actually matter for this job.\n\n"
            f"Must-have keywords: {json.dumps(jd.get('must_have_keywords', []))}\n\n"
            f"--- RESUME ---\n{resume}\n\n--- JOB ---\n{job}"
        )
        d = await self._json(prompt, 0.3)
        d["match_score"] = max(0, min(100, int(d.get("match_score") or 0)))
        for k in ("matched_keywords", "missing_keywords", "strengths", "gaps", "ats_tips"):
            d.setdefault(k, [])
        d.setdefault("verdict", "")
        return d

    async def _rewrite_resume(self, resume: str, job: str, jd: dict) -> dict:
        prompt = (
            "You are an expert resume writer. Rewrite the candidate's resume to align "
            "with the target job and maximize ATS keyword coverage — WITHOUT inventing "
            "experience the candidate does not have. Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "professional_summary": "3-4 sentence tailored summary using target keywords",\n'
            '  "skills": ["prioritized skill for this role", "..."],\n'
            '  "experience_bullets": ["rewritten, achievement-focused bullet with metrics where possible"],\n'
            '  "keywords_added": ["ATS keyword newly surfaced honestly from existing experience"],\n'
            '  "notes": ["short note on what changed and why"]\n'
            "}\n"
            "Rewrite bullets in strong action-verb + impact form. Do not fabricate employers, "
            "titles, dates, or metrics that aren't supported by the original resume.\n\n"
            f"Target keywords: {json.dumps(jd.get('must_have_keywords', []) + jd.get('nice_to_have_keywords', []))}\n\n"
            f"--- ORIGINAL RESUME ---\n{resume}\n\n--- JOB ---\n{job}"
        )
        d = await self._json(prompt, 0.5)
        for k in ("skills", "experience_bullets", "keywords_added", "notes"):
            d.setdefault(k, [])
        d.setdefault("professional_summary", "")
        return d

    async def _cover_letter(self, resume: str, job: str, jd: dict) -> dict:
        prompt = (
            "You are a career coach. Write a tailored, professional cover letter for this "
            "candidate and job. Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "greeting": "e.g. Dear Hiring Manager,",\n'
            '  "body": "the full cover letter body as 3-4 paragraphs separated by \\n\\n",\n'
            '  "closing": "e.g. Sincerely,\\n[Your Name]"\n'
            "}\n"
            "Keep it concise (approx 250-350 words), specific to the role, confident but not "
            "arrogant, and grounded in the candidate's real experience.\n\n"
            f"Role: {jd.get('title','')} at {jd.get('company','the company')}\n\n"
            f"--- RESUME ---\n{resume}\n\n--- JOB ---\n{job}"
        )
        d = await self._json(prompt, 0.6)
        d.setdefault("greeting", "Dear Hiring Manager,")
        d.setdefault("body", "")
        d.setdefault("closing", "Sincerely,")
        return d

    async def _interview(self, resume: str, job: str, jd: dict, n: int) -> list[dict]:
        prompt = (
            f"You are an interview coach. Prepare {n} likely interview questions for this "
            "candidate and role, each with a strong sample answer tailored to the resume. "
            "Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "questions": [\n'
            '    {"question": "the interview question",\n'
            '     "category": "behavioral|technical|role-specific|culture",\n'
            '     "ideal_answer": "a strong, specific sample answer (3-5 sentences)",\n'
            '     "tip": "one-line tip on what the interviewer is really assessing"}\n'
            "  ]\n"
            "}\n"
            "Mix behavioral, technical, and role-specific questions. Ground sample answers in "
            "the candidate's actual background where possible.\n\n"
            f"Role: {jd.get('title','')}\n"
            f"Key skills: {json.dumps(jd.get('must_have_keywords', []))}\n\n"
            f"--- RESUME ---\n{resume}\n\n--- JOB ---\n{job}"
        )
        d = await self._json(prompt, 0.5)
        questions = d.get("questions", []) if isinstance(d, dict) else []
        cleaned = []
        for q in questions:
            if not isinstance(q, dict) or not q.get("question"):
                continue
            q.setdefault("category", "general")
            q.setdefault("ideal_answer", "")
            q.setdefault("tip", "")
            cleaned.append(q)
        return cleaned
