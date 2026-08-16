"""EOS seat runtime — NO Google Antigravity.

Two backends:
  dry   — deterministic tool-using seats (always works; protocol + scorecard truth)
  grok  — OpenAI-compatible chat+tools against xAI (XAI_API_KEY / GROK_API_KEY)

The antigravity SDK is intentionally not imported anywhere in this module.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

from scorecard_tool import read_scorecard
from eos_knowledge_tool import query_eos_knowledge
from issues_tool import list_open_issues, close_issue

# --- tool registry (local, no SDK) -------------------------------------------

TOOL_IMPL: dict[str, Callable[..., str]] = {
    "read_scorecard": lambda metric_key, **_: read_scorecard(metric_key),
    "query_eos_knowledge": lambda query, **_: query_eos_knowledge(query),
    "list_open_issues": lambda **_: list_open_issues(),
    "close_issue": lambda issue_id, resolution, **_: close_issue(issue_id, resolution),
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_scorecard",
            "description": "Read one external scorecard metric. Never invent values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_key": {"type": "string", "description": "Registry metric_key"},
                },
                "required": ["metric_key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_eos_knowledge",
            "description": "Look up EOS doctrine from the local knowledge index.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_open_issues",
            "description": "List open IDS issues.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_issue",
            "description": "Persist-close an issue that is genuinely resolved.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string"},
                    "resolution": {"type": "string"},
                },
                "required": ["issue_id", "resolution"],
            },
        },
    },
]


def run_tool(name: str, arguments: dict[str, Any] | str | None) -> str:
    if name not in TOOL_IMPL:
        return f"ERROR: unknown tool {name}"
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            arguments = {}
    arguments = arguments or {}
    try:
        return str(TOOL_IMPL[name](**arguments))
    except TypeError as e:
        return f"ERROR: bad args for {name}: {e}"
    except Exception as e:
        return f"ERROR: {name} failed: {e}"


# --- seat -------------------------------------------------------------------

@dataclass
class Seat:
    name: str
    system: str
    metric_key: str | None = None
    backend: str = "dry"  # dry | grok
    model: str | None = None
    history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.history = [{"role": "system", "content": self.system}]

    async def chat(self, user_text: str) -> "SeatReply":
        self.history.append({"role": "user", "content": user_text})
        if self.backend == "grok":
            text = await self._chat_grok()
        else:
            text = self._chat_dry(user_text)
        self.history.append({"role": "assistant", "content": text})
        return SeatReply(text)

    def _chat_dry(self, user_text: str) -> str:
        """Deterministic seat: call tools the prompt asks for; emit EOS terminator."""
        ut = user_text.lower()
        chunks: list[str] = []

        # IDS first (prompt often contains the word "report" / "scorecard" as narrative)
        if "list_open_issues" in ut or ("ids" in ut and "issue" in ut):
            issues = run_tool("list_open_issues", {})
            chunks.append(issues)
            if issues.startswith("No open"):
                chunks.append("⟦EOS_HOLD: no open issues — clean IDS exit⟧⟦END⟧")
            else:
                chunks.append("⟦EOS_ESCALATE: open issues present — need Visionary priority?⟧⟦END⟧")
            return "\n".join(chunks)

        # Explicit own metric for Integrator
        if "your own" in ut and "scorecard" in ut:
            metric = "integrator_seats_reporting_pct"
            val = run_tool("read_scorecard", {"metric_key": metric})
            if val.startswith("NO DATA"):
                val2 = run_tool("read_scorecard", {"metric_key": "seat_health"})
                if not val2.startswith("NO DATA"):
                    val = val2
                    metric = "seat_health"
            chunks.append(val)
            chunks.append(f"⟦EOS_REPORT: integrator metric {metric}⟧⟦END⟧")
            return "\n".join(chunks)

        # Departmental scorecard report — only when tool is clearly requested
        m = re.search(r"read_scorecard.*?['\"]([a-z0-9_]+)['\"]", user_text, re.I)
        if not m:
            m = re.search(r"read_scorecard tool for ['\"]([a-z0-9_]+)['\"]", user_text, re.I)
        if not m:
            m = re.search(r"for ['\"]([a-z0-9_]+)['\"]\.?\s*Report exactly", user_text, re.I)
        metric = m.group(1) if m else None
        if not metric and self.metric_key and "read_scorecard" in ut:
            metric = self.metric_key

        if metric:
            val = run_tool("read_scorecard", {"metric_key": metric})
            chunks.append(val)
            chunks.append(f"⟦EOS_REPORT: {metric} -> {val.split('|')[0].strip() if '|' in val else val[:80]}⟧⟦END⟧")
            return "\n".join(chunks)

        if "adjourn" in ut or "end the meeting" in ut:
            return "Scorecard segment complete.\n⟦EOS_ADJOURN⟧⟦END⟧"

        # Integrator facilitation turns — no tool, still must terminate
        if "ask" in ut and ("sales" in ut or "operations" in ut or "report" in ut):
            return (
                "Acknowledged prior report. Proceeding to next seat report request.\n"
                "⟦EOS_HOLD: facilitation turn — awaiting departmental report⟧⟦END⟧"
            )

        return (
            "Acknowledged. No scorecard tool call required this turn.\n"
            "⟦EOS_HOLD: no tool action this turn⟧⟦END⟧"
        )

    async def _chat_grok(self) -> str:
        key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
        if not key:
            raise RuntimeError("grok backend requires XAI_API_KEY or GROK_API_KEY")
        model = self.model or os.environ.get("EOS_GROK_MODEL", "grok-4.5-latest")
        base = os.environ.get("EOS_GROK_UPSTREAM", "https://api.x.ai").rstrip("/")
        url = f"{base}/v1/chat/completions"

        messages = list(self.history)
        # tool loop max 6
        for _ in range(6):
            body = {
                "model": model,
                "messages": messages,
                "tools": TOOL_SCHEMAS,
                "tool_choice": "auto",
                "temperature": 0.2,
            }
            data = _http_json(url, body, key)
            choice = (data.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = msg.get("content") or ""
            if tool_calls:
                messages.append({"role": "assistant", "content": content or "", "tool_calls": tool_calls})
                for tc in tool_calls:
                    fn = tc.get("function") or {}
                    name = fn.get("name") or ""
                    args = fn.get("arguments") or "{}"
                    result = run_tool(name, args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id") or name,
                            "content": result,
                        }
                    )
                continue
            # final
            if not content.strip().endswith("⟦END⟧") and "⟦EOS_" not in content:
                content = content.rstrip() + "\n⟦EOS_HOLD: model omitted terminator — forced⟧⟦END⟧"
            # sync history without tool scaffolding noise for next user turn
            self.history = [messages[0]] + [m for m in messages[1:] if m.get("role") in ("user", "assistant") and "tool_calls" not in m]
            # last assistant already will be appended by chat()
            self.history = self.history[:-0] if False else [messages[0]] + [
                m for m in messages[1:] if m.get("role") == "user" or (m.get("role") == "assistant" and not m.get("tool_calls"))
            ]
            # simpler: just return content; chat() appends assistant
            # Fix history properly:
            self.history = [{"role": "system", "content": self.system}]
            for m in messages:
                if m.get("role") == "system":
                    continue
                if m.get("role") in ("user", "assistant") and not m.get("tool_calls"):
                    self.history.append({"role": m["role"], "content": m.get("content") or ""})
            # pop last assistant — chat() will re-append
            if self.history and self.history[-1]["role"] == "assistant":
                self.history.pop()
            return content
        return "⟦EOS_HOLD: tool loop exhausted⟧⟦END⟧"


@dataclass
class SeatReply:
    _text: str

    async def text(self) -> str:
        return self._text


def _http_json(url: str, body: dict, key: str) -> dict:
    raw = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=raw,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")[:500]
        raise RuntimeError(f"xAI HTTP {e.code}: {err}") from e
