"""Output guardrails (FR-AI-5, BR-04, P3-08). Regex rules from config/safety_rules.yaml, plus an
optional LLM judge. Callers use `generate_safely()` which regenerates once, then falls back."""
from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field

from app.core.config import get_settings


class Violation(BaseModel):
    category: str
    message: str
    match: str


class SafetyResult(BaseModel):
    ok: bool
    violations: list[Violation] = Field(default_factory=list)

    @property
    def messages(self) -> list[str]:
        return sorted({f"{v.message} (\"{v.match}\")" for v in self.violations})


@lru_cache
def _rules() -> dict:
    return yaml.safe_load((get_settings().config_dir / "safety_rules.yaml").read_text(encoding="utf-8"))


@lru_cache
def _compiled() -> list[tuple[str, str, set[str], re.Pattern]]:
    out = []
    for cat, spec in _rules()["categories"].items():
        for p in spec["patterns"]:
            out.append((cat, spec["message"], set(spec.get("contexts", [])), re.compile(p, re.I)))
    return out


def validate(text: str, context: str = "analysis") -> SafetyResult:
    violations = []
    for cat, message, contexts, pattern in _compiled():
        if contexts and context not in contexts:
            continue
        for m in pattern.finditer(text or ""):
            violations.append(Violation(category=cat, message=message, match=m.group(0)[:80]))
    if not violations and _rules().get("llm_judge", {}).get("enabled"):
        violations += _llm_judge(text)
    return SafetyResult(ok=not violations, violations=violations)


def _llm_judge(text: str) -> list[Violation]:
    from app.rag.llm_client import get_llm

    llm = get_llm()
    if not llm.available:
        return []
    out = []
    for q in _rules()["llm_judge"]["questions"]:
        try:
            ans = llm.complete("Answer only YES or NO.", [{"role": "user", "content": f"{q}\n\nTEXT:\n{text}"}], max_tokens=200)
        except Exception:
            continue
        if ans.strip().upper().startswith("YES"):
            out.append(Violation(category="llm_judge", message=q, match=""))
    return out


def generate_safely(generate: Callable[[list[str] | None], str], fallback: Callable[[], str], context: str,
                    extract: Callable[[str], str] = lambda s: s) -> tuple[str, bool]:
    """Run `generate(feedback)`; validate; regenerate once with feedback; else `fallback()`.
    Returns (text, used_llm). `extract` maps raw output to the text that must be validated."""
    feedback = None
    for _ in range(2):
        try:
            raw = generate(feedback)
        except Exception:
            break
        result = validate(extract(raw), context)
        if result.ok:
            return raw, True
        feedback = result.messages
    return fallback(), False
