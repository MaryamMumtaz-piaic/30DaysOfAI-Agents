"""Autonomous AI project manager.

Given a one-sentence project goal, the agent:
  1. Clarifies scope, objectives, and team roles.
  2. Breaks the project into phases and detailed tasks.
  3. Estimates effort (story points + days) and assigns a role to each task.
  4. Identifies task dependencies and schedules a start-day offset.
  5. Performs a risk assessment with mitigations.

The scheduled offsets let the frontend render a Gantt chart, and the task
statuses seed a Kanban board.

Progress is reported through an async callback so the FastAPI layer can stream
it to the browser over a WebSocket.
"""

from __future__ import annotations

import json
import os
from typing import Awaitable, Callable

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


class ProjectManagerAgent:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.openai = AsyncOpenAI(api_key=key)

    async def plan(
        self,
        goal: str,
        team_size: int = 3,
        deadline_weeks: int = 0,
        progress: ProgressFn = _noop,
    ) -> dict:
        goal = (goal or "").strip()
        if len(goal) < 8:
            raise ValueError("Please describe the project goal in a sentence")

        team_size = max(1, min(20, int(team_size or 3)))
        deadline_weeks = max(0, min(104, int(deadline_weeks or 0)))

        await progress("start", f"Planning project: {goal}")
        await progress("decompose", "Breaking the goal into phases, tasks, and estimates")

        plan = await self._generate(goal, team_size, deadline_weeks)
        plan = self._post_process(plan, goal)

        stats = plan["stats"]
        await progress(
            "decompose",
            f"{stats['phases']} phases · {stats['tasks']} tasks · "
            f"{stats['total_points']} story points · ~{stats['duration_days']} days",
        )
        await progress("risk", f"Identified {len(plan.get('risks', []))} project risks")
        await progress("done", "Project plan ready")
        return plan

    async def _generate(self, goal: str, team_size: int, deadline_weeks: int) -> dict:
        deadline = (
            f"The target deadline is about {deadline_weeks} weeks."
            if deadline_weeks else "No hard deadline was given; propose a realistic timeline."
        )
        prompt = (
            "You are an experienced technical project manager. Turn the project goal into a "
            "complete, realistic project plan. Return ONLY JSON in this exact shape:\n"
            "{\n"
            '  "title": "concise project title",\n'
            '  "objective": "2-3 sentence project objective and scope",\n'
            '  "roles": ["team role needed, e.g. Backend Engineer"],\n'
            '  "phases": [\n'
            '    {"name": "phase name", "goal": "what this phase delivers"}\n'
            "  ],\n"
            '  "tasks": [\n'
            "    {\n"
            '      "id": "T1",\n'
            '      "name": "task name",\n'
            '      "description": "one-sentence description",\n'
            '      "phase": "phase name it belongs to",\n'
            '      "role": "assigned role",\n'
            '      "story_points": 1,\n'
            '      "estimate_days": 2,\n'
            '      "start_offset_days": 0,\n'
            '      "priority": "high|medium|low",\n'
            '      "status": "todo",\n'
            '      "depends_on": ["T0"]\n'
            "    }\n"
            "  ],\n"
            '  "milestones": [{"name": "milestone", "day": 0}],\n'
            '  "risks": [\n'
            '    {"risk": "description", "likelihood": "low|medium|high", "impact": "low|medium|high",\n'
            '     "mitigation": "how to reduce or handle it"}\n'
            "  ],\n"
            '  "critical_path": ["T1", "T3"]\n'
            "}\n"
            "Rules: give each task a unique id (T1, T2, ...). depends_on must reference existing "
            "ids (use [] if none). Set start_offset_days consistently with dependencies and a team "
            f"of {team_size} working in parallel where possible. Story points use a Fibonacci-like "
            "scale (1,2,3,5,8,13). Keep tasks actionable (aim for 8-20 tasks). All new tasks start "
            'with status "todo". ' + deadline + "\n\n"
            f"PROJECT GOAL: {goal}"
        )
        resp = await self.openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        return json.loads(resp.choices[0].message.content)

    def _post_process(self, plan: dict, goal: str) -> dict:
        plan.setdefault("title", goal[:60])
        plan.setdefault("objective", "")
        plan.setdefault("roles", [])
        plan.setdefault("phases", [])
        plan.setdefault("tasks", [])
        plan.setdefault("milestones", [])
        plan.setdefault("risks", [])
        plan.setdefault("critical_path", [])

        valid_ids: set[str] = set()
        clean_tasks: list[dict] = []
        for i, t in enumerate(plan["tasks"], 1):
            if not isinstance(t, dict) or not t.get("name"):
                continue
            tid = str(t.get("id") or f"T{i}").strip()
            t["id"] = tid
            valid_ids.add(tid)
            t["story_points"] = _int(t.get("story_points"), 1)
            t["estimate_days"] = max(1, _int(t.get("estimate_days"), 1))
            t["start_offset_days"] = max(0, _int(t.get("start_offset_days"), 0))
            t.setdefault("description", "")
            t.setdefault("phase", plan["phases"][0]["name"] if plan["phases"] else "General")
            t.setdefault("role", "")
            pr = str(t.get("priority", "medium")).lower()
            t["priority"] = pr if pr in ("high", "medium", "low") else "medium"
            st = str(t.get("status", "todo")).lower()
            t["status"] = st if st in ("todo", "in_progress", "done") else "todo"
            t["depends_on"] = [d for d in (t.get("depends_on") or []) if isinstance(d, str)]
            clean_tasks.append(t)

        # Drop dangling dependencies.
        for t in clean_tasks:
            t["depends_on"] = [d for d in t["depends_on"] if d in valid_ids and d != t["id"]]

        plan["tasks"] = clean_tasks
        plan["critical_path"] = [c for c in plan["critical_path"] if c in valid_ids]

        total_points = sum(t["story_points"] for t in clean_tasks)
        duration_days = max(
            (t["start_offset_days"] + t["estimate_days"] for t in clean_tasks), default=0
        )
        plan["stats"] = {
            "phases": len(plan["phases"]),
            "tasks": len(clean_tasks),
            "total_points": total_points,
            "duration_days": duration_days,
            "duration_weeks": round(duration_days / 5, 1) if duration_days else 0,  # working days
            "by_status": {
                "todo": sum(1 for t in clean_tasks if t["status"] == "todo"),
                "in_progress": sum(1 for t in clean_tasks if t["status"] == "in_progress"),
                "done": sum(1 for t in clean_tasks if t["status"] == "done"),
            },
        }
        return plan


def _int(v, default: int) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default
