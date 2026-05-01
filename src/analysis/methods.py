"""古籍方法库：把分析步骤绑定到可检索、可审计的古籍来源。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any


@dataclass(frozen=True)
class Method:
    id: str
    book: str
    title: str
    topic_tags: tuple[str, ...]
    kinds: tuple[str, ...]
    principle: str
    queries: tuple[str, ...]
    audit_query: str
    expected_title: str
    expected_terms: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Method":
        return cls(
            id=data["id"],
            book=data["book"],
            title=data["title"],
            topic_tags=tuple(data.get("topic_tags", [])),
            kinds=tuple(data.get("kinds", [])),
            principle=data["principle"],
            queries=tuple(data.get("queries", [])),
            audit_query=data["audit_query"],
            expected_title=data["expected_title"],
            expected_terms=tuple(data.get("expected_terms", [])),
        )

    def as_ref(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "book": self.book,
            "title": self.title,
            "principle": self.principle,
            "queries": list(self.queries),
            "audit_query": self.audit_query,
            "expected_title": self.expected_title,
        }


@lru_cache(maxsize=1)
def all_methods() -> tuple[Method, ...]:
    path = resources.files("src.analysis").joinpath("methods/yuanhai.json")
    raw = path.read_text(encoding="utf-8")
    return tuple(Method.from_dict(item) for item in json.loads(raw))


@lru_cache(maxsize=None)
def methods_for_kind(kind: str) -> tuple[Method, ...]:
    return tuple(method for method in all_methods() if kind in method.kinds)


def method_queries_for_kind(kind: str) -> list[str]:
    queries: list[str] = []
    for method in methods_for_kind(kind):
        queries.extend(method.queries)
    return _dedupe(queries)


def _dedupe(items) -> list[str]:
    seen = set()
    result = []
    for item in items:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
