"""Conservative detector for directly opposed policy statements.

This intentionally catches only sentence pairs that are otherwise identical
after removing one explicit Chinese negation marker (for example, ``保证`` vs
``不保证``). It is not a semantic contradiction detector.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from support_agent.rag.retrieval import RetrievedPolicy


_SENTENCE_SPLIT = re.compile(r"[。！？!?；;\n]+")
# Do not include 「无」 as a generic marker: it is lexical in phrases such as
# 「无理由退货」 and would misclassify affirmative statements.
_NEGATION = re.compile(r"不|没|未")
_NORMALIZE = re.compile(r"[^\u4e00-\u9fffA-Za-z0-9%]")
_TOPIC_ANCHORS = (
    "退款", "到账", "退货", "无理由", "保修", "发票", "专票", "运费",
    "邮费", "发货", "送达", "换货", "质量", "维修", "物流",
)


@dataclass(frozen=True)
class EvidenceConflict:
    source_ids: tuple[str, ...]
    statement_without_negation: str
    positive_statement: str
    negative_statement: str


def _sentences(evidence: RetrievedPolicy) -> list[tuple[str, bool, str]]:
    result: list[tuple[str, bool, str]] = []
    for raw in _SENTENCE_SPLIT.split(evidence.content):
        sentence = re.sub(r"^\s*(?:#{1,6}|>|[-*])\s*", "", raw).strip()
        if len(sentence) < 8:
            continue
        negative = bool(_NEGATION.search(sentence))
        normalized = _NORMALIZE.sub("", _NEGATION.sub("", sentence))
        if len(normalized) >= 8:
            result.append((normalized, negative, sentence))
    return result


def find_explicit_evidence_conflicts(
    evidence: list[RetrievedPolicy], *, question: str,
) -> list[EvidenceConflict]:
    """Return high-confidence direct polarity inversions in retrieved evidence.

    The normalized proposition must match exactly and one sentence must have an
    explicit negation marker while the other has none. Conditional or scoped
    differences remain distinct and are not treated as contradictions.
    """
    by_proposition: dict[str, dict[bool, list[tuple[str, str]]]] = {}
    for item in evidence:
        for proposition, negative, sentence in _sentences(item):
            polarities = by_proposition.setdefault(proposition, {False: [], True: []})
            polarities[negative].append((item.source_id, sentence))

    conflicts: list[EvidenceConflict] = []
    for proposition, polarities in by_proposition.items():
        if not any(anchor in question and anchor in proposition for anchor in _TOPIC_ANCHORS):
            continue
        positive = polarities[False]
        negative = polarities[True]
        if not positive or not negative:
            continue
        # Deduplicate repeated copies while retaining source citations.
        positive_sentence = positive[0][1]
        negative_sentence = negative[0][1]
        source_ids = tuple(dict.fromkeys(
            [source_id for source_id, _ in positive]
            + [source_id for source_id, _ in negative]
        ))
        conflicts.append(EvidenceConflict(
            source_ids=source_ids,
            statement_without_negation=proposition,
            positive_statement=positive_sentence,
            negative_statement=negative_sentence,
        ))
    return conflicts
