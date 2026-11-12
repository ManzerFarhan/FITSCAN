"""AI analysis (FR-AI-1..9, BR-02/04/05/10/11; P3-10, P3-13).

* Uses VERIFIED parameters only (BR-02); unverified ones are listed as excluded.
* URGENT comes only from escalation rules (BR-05) with the fixed UI text.
* Every AI statement carries source_tag AI_GENERATED (BR-10) and cites sources or says none (BR-11).
* LLM output passes safety_validator; otherwise deterministic templates are used.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import DISCLAIMER_TEXT, URGENT_UI_TEXT, DocumentStatus, FindingClass, SourceTag
from app.core.errors import AppError
from app.db.models import Analysis, ChatMessage, Document, Parameter
from app.rag import prompts
from app.rag.llm_client import get_llm, parse_json
from app.rag.retriever import Source, retrieve
from app.rag.safety_validator import generate_safely
from app.services import audit
from app.utils import dictionaries

ABOUT = {
    "hemoglobin": "the oxygen-carrying protein in red blood cells",
    "rbc_count": "the number of red blood cells",
    "hematocrit": "the share of your blood volume made up of red blood cells",
    "mcv": "the average size of your red blood cells",
    "mch": "the average amount of hemoglobin in each red blood cell",
    "mchc": "the concentration of hemoglobin inside red blood cells",
    "rdw_cv": "how much your red blood cells vary in size",
    "wbc_count": "the number of white blood cells, which are part of the immune system",
    "neutrophils_pct": "the share of white blood cells that are neutrophils",
    "lymphocytes_pct": "the share of white blood cells that are lymphocytes",
    "monocytes_pct": "the share of white blood cells that are monocytes",
    "eosinophils_pct": "the share of white blood cells that are eosinophils",
    "basophils_pct": "the share of white blood cells that are basophils",
    "neutrophils_abs": "the number of neutrophils (a type of white blood cell) in a volume of blood",
    "lymphocytes_abs": "the number of lymphocytes (a type of white blood cell) in a volume of blood",
    "monocytes_abs": "the number of monocytes (a type of white blood cell) in a volume of blood",
    "eosinophils_abs": "the number of eosinophils (a type of white blood cell) in a volume of blood",
    "basophils_abs": "the number of basophils (a type of white blood cell) in a volume of blood",
    "nrbc": "immature red blood cells that still have a nucleus, counted per 100 white blood cells",
    "platelet_count": "the number of platelets, which help blood clot",
    "mpv": "the average size of your platelets",
    "esr": "how quickly red blood cells settle in a tube - a general marker",
    "bilirubin_total": "bilirubin, a substance made when red blood cells break down",
    "bilirubin_direct": "the part of bilirubin the liver has already processed",
    "bilirubin_indirect": "the part of bilirubin not yet processed by the liver",
    "ast_sgot": "AST, an enzyme found mainly in the liver and muscles",
    "alt_sgpt": "ALT, an enzyme found mainly in the liver",
    "alp": "alkaline phosphatase, an enzyme from the liver, bile ducts and bone",
    "ggt": "GGT, an enzyme linked to the liver and bile ducts",
    "total_protein": "the total amount of protein in your blood",
    "albumin": "albumin, the main protein made by the liver",
    "globulin": "globulins, a group of blood proteins",
    "ag_ratio": "the ratio of albumin to globulin",
    "urea": "urea, a waste product from protein breakdown removed by the kidneys",
    "bun": "the nitrogen part of urea, a waste product removed by the kidneys",
    "creatinine": "creatinine, a muscle waste product filtered by the kidneys",
    "uric_acid": "uric acid, made when the body breaks down purines",
    "egfr": "an estimate of how well the kidneys filter blood",
    "sodium": "sodium, an electrolyte that helps control fluid balance",
    "potassium": "potassium, an electrolyte important for nerves and muscles",
    "chloride": "chloride, an electrolyte that works with sodium",
    "calcium": "calcium, a mineral important for bones, nerves and muscles",
    "phosphorus": "phosphorus, a mineral that works with calcium",
    "cholesterol_total": "the total amount of cholesterol in your blood",
    "triglycerides": "triglycerides, a type of fat used for energy",
    "hdl": "HDL cholesterol, often called 'good' cholesterol",
    "ldl": "LDL cholesterol, often called 'bad' cholesterol",
    "vldl": "VLDL, a particle that carries mostly triglycerides",
    "non_hdl": "all cholesterol except HDL",
    "tc_hdl_ratio": "total cholesterol divided by HDL cholesterol",
    "ldl_hdl_ratio": "LDL cholesterol divided by HDL cholesterol",
    "tsh": "TSH, a hormone from the pituitary gland that controls the thyroid",
    "t3_total": "T3, a thyroid hormone",
    "t4_total": "T4, the main hormone made by the thyroid",
    "ft3": "the unbound (free) part of the thyroid hormone T3",
    "ft4": "the unbound (free) part of the thyroid hormone T4",
    "glucose_fasting": "blood sugar after not eating for several hours",
    "glucose_pp": "blood sugar measured a set time after a meal",
    "glucose_random": "blood sugar at the time the sample was taken",
    "hba1c": "average blood sugar over roughly the past 2-3 months",
    "eag": "an average glucose value calculated from HbA1c",
    "vitamin_b12": "vitamin B12, which helps keep nerve and blood cells healthy",
    "vitamin_d": "vitamin D (25-OH), which helps the body absorb calcium",
    "ferritin": "ferritin, a protein that stores iron",
    "iron": "the iron circulating in your blood",
    "crp": "CRP, a general marker of inflammation made by the liver",
}

def about_text(parameter_id: str | None) -> str | None:
    """Plain-language 'what it measures' - hand-written ABOUT first, then the dictionary's `about` field."""
    if not parameter_id:
        return None
    return ABOUT.get(parameter_id) or (dictionaries.parameters().get(parameter_id) or {}).get("about")


PAIRS = [("hemoglobin", "mcv"), ("hemoglobin", "hematocrit"), ("tsh", "ft4"), ("tsh", "t4_total"), ("ldl", "hdl"),
         ("creatinine", "urea"), ("ast_sgot", "alt_sgpt"), ("glucose_fasting", "hba1c"), ("vitamin_d", "calcium"),
         ("ferritin", "hemoglobin")]

STATUS_PHRASE = {"WITHIN": "within", "BELOW": "below", "ABOVE": "above", "UNKNOWN": "not compared with"}


def _name(p: Parameter) -> str:
    meta = dictionaries.parameters().get(p.parameter_id or "")
    return meta["canonical_name"] if meta else p.name_raw


def _range_text(p: Parameter) -> str:
    return p.ref_raw or "not printed"


def report_payload(doc: Document) -> dict:
    """The ONLY data the LLM sees: verified values, the lab's own ranges, no names/addresses."""
    return {
        "category": doc.report_category, "report_date": doc.report_date.isoformat() if doc.report_date else None,
        "parameters": [{
            "row_id": str(p.id), "name": _name(p), "value": p.value_raw, "unit": p.unit,
            "lab_reference_range": p.ref_raw, "status_vs_lab_range": p.status, "lab_flag": p.lab_flag,
        } for p in doc.parameters if p.verified],
    }


def _status_sentence(p: Parameter) -> str:
    v = f"{p.value_raw}{(' ' + p.unit) if p.unit else ''}"
    if p.status == "UNKNOWN":
        return f"Your value is {v}. The lab's range ({_range_text(p)}) could not be compared automatically."
    return f"Your value of {v} is {STATUS_PHRASE[p.status]} the lab's reference range ({_range_text(p)})."


def _collect_sources(params: list[Parameter]) -> tuple[list[Source], dict[str, list[int]]]:
    sources: list[Source] = []
    per_param: dict[str, list[int]] = {}
    for p in params:
        idxs = []
        for s in retrieve(_name(p), k=2, parameter_id=p.parameter_id):
            existing = next((i for i, x in enumerate(sources) if x.chunk_id == s.chunk_id), None)
            if existing is None:
                sources.append(s)
                existing = len(sources) - 1
            idxs.append(existing)
        per_param[str(p.id)] = idxs
    return sources, per_param


def _template(doc: Document, params: list[Parameter], sources: list[Source], per_param: dict[str, list[int]]) -> dict:
    explanations = []
    for p in params:
        about = about_text(p.parameter_id)
        lead = f"{_name(p)} measures {about}. " if about else f"{_name(p)} is one of the values on this report. "
        idxs = per_param.get(str(p.id), [])
        context = (f"General information: {sources[idxs[0]].title} [S{idxs[0] + 1}]."
                   if idxs else "No source in FITSCAN's library for this parameter.")
        explanations.append({"row_id": str(p.id), "explanation": lead + _status_sentence(p), "context": context})
    return {"explanations": explanations, "observations": _observations(params), "doctor_questions": _questions(params)}


def _observations(params: list[Parameter]) -> list[str]:
    obs = []
    outside = [p for p in params if p.status in ("ABOVE", "BELOW")]
    if outside:
        names = ", ".join(f"{_name(p)} ({STATUS_PHRASE[p.status]})" for p in outside[:6])
        obs.append(f"{len(outside)} of {len(params)} verified values are outside the lab's reference range: {names}. "
                   "A value outside the range is not, by itself, a diagnosis.")
    else:
        obs.append(f"All {len(params)} verified values with a printed range are within the lab's reference range.")
    by_pid = {p.parameter_id: p for p in params if p.parameter_id}
    for a, b in PAIRS:
        if a in by_pid and b in by_pid and (by_pid[a].status in ("ABOVE", "BELOW") or by_pid[b].status in ("ABOVE", "BELOW")):
            pa, pb = by_pid[a], by_pid[b]
            obs.append(f"{_name(pa)} and {_name(pb)} are often looked at together; here {_name(pa)} is "
                       f"{STATUS_PHRASE[pa.status]} and {_name(pb)} is {STATUS_PHRASE[pb.status]} the lab's range.")
        if len(obs) >= 4:
            break
    return obs


def _questions(params: list[Parameter]) -> list[str]:
    qs = [f"What could explain my {_name(p)} being {STATUS_PHRASE[p.status]} the lab's range?"
          for p in params if p.status in ("ABOVE", "BELOW")][:3]
    qs += ["Could any of my current medicines, supplements or routines affect these results?",
           "How do these results compare with my earlier reports?",
           "When would you like to review these results with me again?"]
    return qs[:5]


def _validate_text(raw: str) -> str:
    try:
        d = parse_json(raw)
    except Exception:
        return raw
    parts = [e.get("explanation", "") + " " + e.get("context", "") for e in d.get("explanations", [])]
    return "\n".join(parts + d.get("observations", []) + d.get("doctor_questions", []))


def generate_analysis(db: Session, owner, doc: Document) -> Analysis:
    params = [p for p in doc.parameters if p.verified]
    if not params:
        raise AppError("NOT_VERIFIED", "Please review and confirm the extracted values before running the analysis.", 409)
    excluded = [p for p in doc.parameters if not p.verified]
    sources, per_param = _collect_sources(params)
    src_dicts = [s.model_dump() for s in sources]
    llm = get_llm()
    payload = report_payload(doc)

    def gen(feedback):
        messages = [{"role": "user", "content": prompts.analysis_prompt(payload, src_dicts)}]
        if feedback:
            messages.append({"role": "user", "content": prompts.regenerate_feedback(feedback)})
        return llm.complete(prompts.SYSTEM_RULES, messages, max_tokens=6000, json_schema=prompts.ANALYSIS_SCHEMA)

    content = None
    used_llm = False
    if llm.available:
        raw, used_llm = generate_safely(gen, lambda: "", "analysis", extract=_validate_text)
        if used_llm:
            try:
                content = parse_json(raw)
            except Exception:
                used_llm = False
    if not content:
        content = _template(doc, params, sources, per_param)

    expl = {e["row_id"]: e for e in content.get("explanations", [])}
    rows = []
    for p in params:
        e = expl.get(str(p.id)) or _template(doc, [p], sources, per_param)["explanations"][0]
        rows.append({
            "row_id": str(p.id), "parameter_id": p.parameter_id, "name": _name(p), "value": p.value_raw,
            "value_num": p.value_num, "unit": p.unit, "ref_raw": p.ref_raw, "ref_low": p.ref_low, "ref_high": p.ref_high,
            "status": p.status, "lab_flag": p.lab_flag, "finding_class": p.finding_class,
            "value_source": p.source_tag,  # EXTRACTED or USER_CORRECTED
            "explanation": e["explanation"], "context": e["context"], "explanation_source": SourceTag.AI_GENERATED,
            "urgent_message": URGENT_UI_TEXT if p.finding_class == FindingClass.URGENT else None,
            "source_refs": [i + 1 for i in per_param.get(str(p.id), [])],
        })
    counts = {
        "total": len(doc.parameters), "verified": len(params),
        "within": sum(p.status == "WITHIN" for p in params), "below": sum(p.status == "BELOW" for p in params),
        "above": sum(p.status == "ABOVE" for p in params), "unknown": sum(p.status == "UNKNOWN" for p in params),
        "needs_verification": len(excluded),
    }
    summary = {
        "category": doc.report_category, "lab_name": doc.lab_name,
        "report_date": doc.report_date.isoformat() if doc.report_date else None,
        "counts": counts, "parameters": rows,
        "excluded": [{"row_id": str(p.id), "name": _name(p), "reason": "Not verified - excluded from analysis"} for p in excluded],
        "urgent": [r for r in rows if r["urgent_message"]],
        "doctor_questions": content.get("doctor_questions", [])[:5],
        "generated_by": llm.name if used_llm else "fitscan-template",
        "disclaimer": DISCLAIMER_TEXT,
    }
    analysis = Analysis(document_id=doc.id, summary_json=summary, observations_json=content.get("observations", [])[:5],
                        model=llm.name if used_llm else "fitscan-template", prompt_version=prompts.PROMPT_VERSION,
                        sources_json=src_dicts)
    db.add(analysis)
    doc.status = DocumentStatus.ANALYZED
    audit.record(db, owner, "ANALYSIS", "document", doc.id, f"AI analysis generated: {doc.original_filename}", commit=False)
    db.commit()
    db.refresh(analysis)
    return analysis


def latest_analysis(db: Session, doc: Document) -> Analysis | None:
    return db.scalar(select(Analysis).where(Analysis.document_id == doc.id).order_by(Analysis.created_at.desc()))


# ------------------------------------------------------------------ chat (FR-AI-6, API-08)
_ADVICE_BAIT = re.compile(
    r"\b(?:what|which|how much|how many)\b.{0,40}\b(?:dose|dosage|mg|tablets?|medicine|medication|pills?|supplement)s?\b"
    r"|\bshould i (?:take|stop|start|increase|decrease|reduce|change|skip)\b|\bcan i (?:stop|skip|reduce|increase)\b"
    r"|\bprescribe\b", re.I)
_DIAGNOSIS_BAIT = re.compile(r"\b(?:do i have|have i got|am i (?:diabetic|anemic|sick|ill)|is (?:it|this) (?:cancer|diabetes|serious)|what disease)\b", re.I)

ADVICE_REPLY = ("I can't give advice about medicines, supplements or doses - your doctor or pharmacist is the right "
                "person for that, because they know your full history. I'm happy to explain what any value on your "
                "report measures and how it compares with the lab's reference range.")
DIAGNOSIS_PREFIX = ("I can't tell you whether you have a condition - only a doctor can make a diagnosis using your "
                    "history, symptoms and other tests. ")
NO_SOURCE_REPLY = ("I couldn't find a source in FITSCAN's library that covers this, so I'd rather not guess. "
                   "Your doctor is the best person to ask.")


def _mentioned_params(question: str, doc: Document) -> list[Parameter]:
    q = question.lower()
    out = []
    for p in doc.parameters:
        if not p.verified:
            continue
        meta = dictionaries.parameters().get(p.parameter_id or "")
        names = [p.name_raw.lower()] + ([meta["canonical_name"].lower()] + [s for s in meta["synonyms"] if len(s) > 2] if meta else [])
        if any(re.search(rf"\b{re.escape(n)}\b", q) for n in names):
            out.append(p)
    return out


def _template_answer(question: str, doc: Document, sources: list[Source]) -> str:
    parts = []
    if _DIAGNOSIS_BAIT.search(question):
        parts.append(DIAGNOSIS_PREFIX)
    for p in _mentioned_params(question, doc)[:3]:
        parts.append(f"On this report, {_name(p)}: {_status_sentence(p)}")
    if sources:
        first = re.split(r"(?<=[.!?])\s+", sources[0].text)
        parts.append(" ".join(first[:2]) + " [S1]")
        parts.append("Please talk your results through with your doctor.")
    elif not parts or parts == [DIAGNOSIS_PREFIX]:
        parts.append(NO_SOURCE_REPLY)
    return " ".join(parts).strip()


def chat(db: Session, owner, doc: Document, question: str) -> ChatMessage:
    question = question.strip()
    if not question:
        raise AppError("VALIDATION_ERROR", "Please type a question.", 422)
    db.add(ChatMessage(document_id=doc.id, role="user", content=question, sources_json=[]))
    db.flush()  # history below includes this question as its last item; it is replaced by the full prompt

    sources: list[Source] = []
    if _ADVICE_BAIT.search(question):
        answer = ADVICE_REPLY
    else:
        mentioned = _mentioned_params(question, doc)
        pid = mentioned[0].parameter_id if mentioned else None
        sources = retrieve(question, k=4, parameter_id=pid)
        llm = get_llm()
        src = [s.model_dump() for s in sources]
        history = db.scalars(select(ChatMessage).where(ChatMessage.document_id == doc.id)
                             .order_by(ChatMessage.created_at.desc()).limit(6)).all()[::-1]

        def gen(feedback):
            msgs = [{"role": m.role, "content": m.content} for m in history if m.role in ("user", "assistant")][:-1]
            while msgs and msgs[0]["role"] != "user":
                msgs.pop(0)
            msgs.append({"role": "user", "content": prompts.chat_prompt(question, report_payload(doc), src)})
            if feedback:
                msgs.append({"role": "user", "content": prompts.regenerate_feedback(feedback)})
            return llm.complete(prompts.SYSTEM_RULES, msgs, max_tokens=2000)

        if llm.available:
            answer, _ = generate_safely(gen, lambda: _template_answer(question, doc, sources), "chat")
        else:
            answer = _template_answer(question, doc, sources)
        if not sources and "[S" not in answer and NO_SOURCE_REPLY not in answer:
            answer += " (No source from FITSCAN's library was found for this answer.)"

    cited = [s.model_dump() for i, s in enumerate(sources) if f"[S{i + 1}]" in answer]
    msg = ChatMessage(document_id=doc.id, role="assistant", content=answer, sources_json=cited)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
