"""Site-wide assistant (floating chatbot on every page).

Order of answering - safest first:
  1. Safety intents (emergency, medicine/dose advice, diagnosis) -> fixed replies from config/assistant_faq.yaml.
  2. A question that names a lab test -> knowledge library (RAG) + the person's verified value if a report is open.
  3. App how-to intents -> curated answers with navigation buttons.
  4. Anything else -> knowledge library if it has a source, else a friendly "here's what I can help with".
LLM text (when a key is configured) always passes safety_validator (BR-04/10/11); replies are AI_GENERATED.
Stateless: the client sends the last few turns; nothing is stored.
"""
from __future__ import annotations

import re
from functools import lru_cache

import yaml
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import SourceTag
from app.db.models import Document
from app.rag import prompts
from app.rag.llm_client import get_assistant_llm
from app.rag.retriever import Source, retrieve
from app.rag.safety_validator import generate_safely
from app.services.analysis_service import _name, _status_sentence, report_payload
from app.utils import dictionaries

SAFETY_INTENTS = ("emergency", "medicine_advice", "diagnosis")
OFF_TOPIC_SCORE = 0.15
# Panel names people use that aren't single parameters -> words that match the library's article titles.
PANEL_ALIASES = [(re.compile(p, re.IGNORECASE), e) for p, e in [
    (r"\bcbc\b|blood count|hemogram|haemogram", "Complete blood count (CBC) red cells white cells platelets"),
    (r"\blft\b|liver (function|test|panel)", "Liver function tests"),
    (r"\b(kft|rft)\b|kidney (function|test|panel)|renal", "kidney creatinine urea"),
    (r"lipid (profile|panel)", "Cholesterol levels lipid profile"),
    (r"thyroid (profile|panel|test)", "TSH thyroid stimulating hormone"),
    (r"sugar test|diabetes test", "Blood glucose test"),
    (r"electrolyte", "Electrolyte panel"),
]]

# "How do I lower / control / improve my X?" - answered with general, doctor-first guidance (no doses, no targets).
MANAGE_RE = re.compile(r"\b(control|lower|reduce|decrease|increase|raise|improve|manage|bring (it )?down|fix|normali[sz]e|"
                       r"keep .* (normal|in range))\b", re.IGNORECASE)
MANAGE_TEXT = ("Doctors generally recommend regular physical activity, a balanced diet, a healthy weight, good sleep, not "
               "smoking and limiting alcohol, along with taking any prescribed medicine exactly as directed - never start, "
               "stop or change a medicine on your own. The right plan depends on your health and other results, so make it "
               "with your doctor; a repeat test later shows whether the changes are working.")

FALLBACK = ("I'm not sure about that one. I can help you upload and understand a lab report, explain what a test "
            "measures, compare reports, or find a diagnostic centre. Try asking, for example, \"What does HbA1c measure?\"")

DEFAULT_SUGGESTIONS = ["How do I upload a report?", "What does a reference range mean?", "Find a lab near me"]
PAGE_SUGGESTIONS = {
    "/dashboard": ["What do these charts show?", "How do I compare reports?", "What does out of range mean?"],
    "/analysis": ["How do I upload a report?", "Why must I confirm the values?", "When does the AI analysis unlock?"],
    "/tests": ["How do I find a centre near me?", "Do I need to fast before a blood test?", "What does a CBC test measure?"],
    "/history": ["How do I compare reports?", "Can I delete a report?", "How long are guest reports kept?"],
    "/profile": ["Who can see my data?", "How do I delete my account?", "What happens to guest uploads?"],
}


class Action(BaseModel):
    label: str
    href: str


class Turn(BaseModel):
    role: str
    content: str


class AssistantReply(BaseModel):
    answer: str
    intent: str
    actions: list[Action] = []
    sources: list[dict] = []
    suggestions: list[str] = []
    source_tag: str = SourceTag.AI_GENERATED


@lru_cache
def _faq() -> list[dict]:
    data = yaml.safe_load((get_settings().config_dir / "assistant_faq.yaml").read_text(encoding="utf-8"))
    return [{**i, "_re": [re.compile(p, re.IGNORECASE) for p in i["patterns"]]} for i in data["intents"]]


def match_intent(question: str, only: tuple[str, ...] | None = None) -> dict | None:
    for intent in _faq():
        if only and intent["id"] not in only:
            continue
        if any(r.search(question) for r in intent["_re"]):
            return intent
    return None


def mentioned_parameter_ids(question: str) -> list[str]:
    q = question.lower()
    # Short codes typed with stray spaces or dashes ("hb1 ac", "vit b 12", "hba 1c"): compare without separators.
    # Only names that contain a digit, so ordinary words can't merge into a false match.
    squashed = re.sub(r"[\s\-_.]+", "", q)
    found = []
    for pid, meta in dictionaries.parameters().items():
        names = [meta["canonical_name"].lower()] + [s.lower() for s in meta["synonyms"] if len(s) > 2]
        if any(re.search(rf"(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", q) for n in names) or any(
                re.search(r"\d", n) and len(n.replace(" ", "")) >= 4 and n.replace(" ", "") in squashed for n in names):
            found.append(pid)
    return found


def _suggestions(page: str | None) -> list[str]:
    return PAGE_SUGGESTIONS.get((page or "").split("?")[0], DEFAULT_SUGGESTIONS)


def _reply(intent: dict, page: str | None) -> AssistantReply:
    return AssistantReply(answer=" ".join(intent["answer"].split()), intent=intent["id"],
                          actions=[Action(**a) for a in intent.get("actions", [])], suggestions=_suggestions(page))


def _knowledge_template(question: str, doc: Document | None, pids: list[str], sources: list[Source]) -> str:
    parts = []
    if doc is not None:
        for p in doc.parameters:
            if p.verified and p.parameter_id in pids[:3]:
                parts.append(f"On your report, {_name(p)}: {_status_sentence(p)}")
    if sources:
        sentences = re.split(r"(?<=[.!?])\s+", sources[0].text)
        parts.append(" ".join(sentences[:2]) + " [S1]")
    if pids and MANAGE_RE.search(question):
        parts.append(MANAGE_TEXT)
    elif sources:
        parts.append("Please talk your results through with your doctor.")
    return " ".join(parts).strip()


class TermSuggestion(BaseModel):
    parameter_id: str
    canonical_name: str
    score: float


class TermExplanation(BaseModel):
    term: str
    kind: str  # test | not_a_test | unknown
    explanation: str
    suggestions: list[TermSuggestion] = []
    sources: list[dict] = []
    source_tag: str = SourceTag.AI_GENERATED


NOT_A_TEST_TEXT = ("This looks like part of the report's header or footer (for example the lab's address, a booking "
                   "note or a verification line), not a test result. You can remove it.")


_SHORTHAND = {"abs": "absolute", "cnt": "count", "ct": "count", "tot": "total", "conc": "concentration",
              "vit": "vitamin", "chol": "cholesterol", "trig": "triglycerides", "gluc": "glucose"}


def suggest_parameters(term: str, limit: int = 3, min_score: float = 72) -> list[TermSuggestion]:
    """Closest dictionary tests for an unrecognised name - shown as choices, never applied automatically (BR-03)."""
    from rapidfuzz import fuzz, process

    choices: dict[str, str] = {}
    for pid, meta in dictionaries.parameters().items():
        for name in [meta["canonical_name"], *meta["synonyms"]]:
            choices.setdefault(name.lower(), pid)
    q = re.sub(r"[^a-z0-9 ]+", " ", term.lower()).split()
    q = " ".join(_SHORTHAND.get(w, w) for w in q)
    best: dict[str, float] = {}
    # token_sort_ratio penalises extra words, so "absolute lymphocyte count" prefers the absolute test over "lymphocytes".
    for name, score, _ in process.extract(q, list(choices), scorer=fuzz.token_sort_ratio, limit=25):
        pid = choices[name]
        if score >= min_score and score > best.get(pid, 0):
            best[pid] = score
    ranked = sorted(best.items(), key=lambda kv: -kv[1])[:limit]
    params = dictionaries.parameters()
    return [TermSuggestion(parameter_id=pid, canonical_name=params[pid]["canonical_name"], score=round(s / 100, 2))
            for pid, s in ranked]


def explain_term(term: str) -> TermExplanation:
    from app.pipelines.lab_report.pipeline import is_boilerplate
    from app.services.analysis_service import about_text

    term = " ".join(term.split())[:200]
    if is_boilerplate(term) or len(term.split()) >= 10:
        return TermExplanation(term=term, kind="not_a_test", explanation=NOT_A_TEST_TEXT)
    suggestions = suggest_parameters(term)
    top = suggestions[0] if suggestions else None
    strong = top and top.score >= 0.85
    query = " ".join([e for p, e in PANEL_ALIASES if p.search(term)] + [term])
    sources = retrieve(query, k=3, parameter_id=top.parameter_id if strong else None)
    src = [s.model_dump() for s in sources]

    parts = []
    if strong and about_text(top.parameter_id):
        same = term.lower().strip(" .") == top.canonical_name.lower()
        lead = top.canonical_name if same else f'"{term}" most likely means {top.canonical_name}'
        parts.append(f"{lead} - this measures {about_text(top.parameter_id)}.")
    if sources:
        first = re.split(r"(?<=[.!?])\s+", sources[0].text)
        parts.append(" ".join(first[:2]) + " [S1]")
    template = " ".join(parts) or (f'FITSCAN\'s library has no source that explains "{term}". '
                                   "The lab that produced the report, or your doctor, can tell you what it means.")
    llm = get_assistant_llm()
    if llm.available:
        def gen(feedback):
            msgs = [{"role": "user", "content": prompts.term_prompt(term, top.canonical_name if top else None, src)}]
            if feedback:
                msgs.append({"role": "user", "content": prompts.regenerate_feedback(feedback)})
            return llm.complete(prompts.SYSTEM_RULES, msgs, max_tokens=800)

        text, _ = generate_safely(gen, lambda: template, "chat")
    else:
        text = template
    cited = [{**s, "n": i + 1} for i, s in enumerate(src) if f"[S{i + 1}]" in text]
    return TermExplanation(term=term, kind="test" if (strong or sources) else "unknown", explanation=text,
                           suggestions=suggestions, sources=cited)


def answer(db: Session, question: str, page: str | None = None, history: list[Turn] | None = None,
           doc: Document | None = None) -> AssistantReply:
    question = question.strip()
    safety = match_intent(question, SAFETY_INTENTS)
    if safety:
        return _reply(safety, page)

    pids = mentioned_parameter_ids(question)
    if not pids:
        intent = match_intent(question)
        if intent and intent["id"] not in SAFETY_INTENTS:
            return _reply(intent, page)

    query = question
    panels = [e for p, e in PANEL_ALIASES if p.search(question)]
    if panels:
        query = " ".join(panels) + " " + question
    sources = retrieve(query, k=4, parameter_id=pids[0] if pids else None)
    if not pids and not panels and sources and sources[0].score < OFF_TOPIC_SCORE:
        sources = []  # weak lexical overlap only - don't answer a non-medical question from the library
    llm = get_assistant_llm()
    if not sources and not pids and not llm.available:  # with an AI model connected, it answers everything else
        return AssistantReply(answer=FALLBACK, intent="fallback", suggestions=_suggestions(page),
                              actions=[Action(label="Upload a lab report", href="/analysis")])

    report = report_payload(doc) if doc is not None and any(p.verified for p in doc.parameters) else None
    src = [s.model_dump() for s in sources]
    template = _knowledge_template(question, doc if report else None, pids, sources) or FALLBACK
    if llm.available:
        turns = [{"role": t.role, "content": t.content[:2000]} for t in (history or [])[-6:] if t.role in ("user", "assistant")]
        while turns and turns[0]["role"] != "user":
            turns.pop(0)
        if turns and turns[-1]["role"] == "user":
            turns.pop()

        def gen(feedback):
            msgs = turns + [{"role": "user", "content": prompts.assistant_prompt(question, page, report, src)}]
            if feedback:
                msgs.append({"role": "user", "content": prompts.regenerate_feedback(feedback)})
            return llm.complete(prompts.SYSTEM_RULES, msgs, max_tokens=1500, effort="low")  # chat: fast replies

        text, _ = generate_safely(gen, lambda: template, "chat")
    else:
        text = template
    if not text:
        text = ("I couldn't find a source in FITSCAN's library that covers this, so I'd rather not guess. "
                "Your doctor is the best person to ask.")
    cited = [{**s, "n": i + 1} for i, s in enumerate(src) if f"[S{i + 1}]" in text]
    actions = [Action(label="Open my analysis", href=f"/analysis?doc={doc.id}")] if report else []
    return AssistantReply(answer=text, intent="knowledge", sources=cited, actions=actions, suggestions=_suggestions(page))
