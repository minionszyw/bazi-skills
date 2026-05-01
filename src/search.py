import argparse
import json
import re
import sys
from dataclasses import dataclass
from importlib import resources
from typing import Iterable, Optional
from xml.etree import ElementTree as ET
from zipfile import ZipFile


BOOKS = {
    "yuanhai": {
        "title": "《渊海子平》",
        "package": "src",
        "filename": "yuanhaiziping.docx",
    },
}
TITLE_RE = re.compile(r"^(卷[一二三四五六七八九十]+|[又]?论|详解|起|子平|继善|喜忌|群兴|宝法|寸金|玄机|幽微|五言|四言|六神|女命|小儿|定妇人|六亲|看命|正官|偏官|印绶|杂气|时上一位|飞天|倒冲|井栏|六乙|合禄|子遥|丑遥|刑合|壬骑|拱禄|归禄|羊刃|金神|魁罡|日德|福德|弃命|曲直|炎上|润下|从革|稼穑|化气|建禄|月刃)")
WORD_RE = re.compile(r"[\w\u4e00-\u9fff]+")


@dataclass
class Entry:
    id: int
    source: str
    title: str
    text: str

    def as_dict(self, *, snippet: Optional[str] = None, score: Optional[int] = None) -> dict:
        data = {"id": self.id, "source": self.source, "title": self.title, "text": snippet or self.text}
        if score is not None:
            data["score"] = score
        return data


def _docx_path(book: str):
    config = BOOKS[book]
    return resources.files(config["package"]).joinpath(f"data/{config['filename']}")


def extract_paragraphs(book: str = "yuanhai", docx_path=None) -> list[str]:
    path = docx_path or _docx_path(book)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))

    paragraphs: list[str] = []
    for para in root.findall(".//w:p", ns):
        text = "".join(t.text for t in para.findall(".//w:t", ns) if t.text).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def _looks_like_title(text: str) -> bool:
    if len(text) > 32:
        return False
    if text.startswith(("《", "（", "目", "序")):
        return False
    if re.search(r"[。；，、：]", text):
        return False
    return bool(TITLE_RE.match(text))


def load_entries(book: str = "yuanhai", docx_path=None) -> list[Entry]:
    paragraphs = extract_paragraphs(book, docx_path)
    entries: list[Entry] = []
    source = BOOKS[book]["title"]
    title = "卷首"
    body: list[str] = []

    def flush():
        if body:
            text = "\n".join(body).strip()
            entries.append(Entry(id=len(entries) + 1, source=source, title=title, text=text))

    for para in paragraphs:
        if _looks_like_title(para):
            flush()
            title = para
            body = []
        else:
            body.append(para)
    flush()
    return entries


def _tokens(query: str) -> list[str]:
    raw = WORD_RE.findall(query)
    tokens = [t for t in raw if t.strip()]
    compact = re.sub(r"\s+", "", query)
    if compact and compact not in tokens:
        tokens.insert(0, compact)
    return tokens


def _score(entry: Entry, tokens: Iterable[str]) -> int:
    score = 0
    title = entry.title
    text = entry.text
    for token in tokens:
        if not token:
            continue
        score += title.count(token) * 80
        score += text.count(token) * 30
        for char in token:
            if "\u4e00" <= char <= "\u9fff":
                score += title.count(char)
    return score


def _snippet(entry: Entry, tokens: list[str], max_chars: int) -> str:
    text = entry.text
    positions = [text.find(token) for token in tokens if token and text.find(token) >= 0]
    if not positions:
        return text[:max_chars]
    center = min(positions)
    start = max(0, center - max_chars // 3)
    end = min(len(text), start + max_chars)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def search(query: str, *, book: str = "yuanhai", limit: int = 5, max_chars: int = 500, docx_path=None) -> list[dict]:
    tokens = _tokens(query)
    ranked = []
    for entry in load_entries(book, docx_path):
        score = _score(entry, tokens)
        if score > 0:
            ranked.append((score, entry))
    ranked.sort(key=lambda item: (-item[0], item[1].id))
    return [
        entry.as_dict(snippet=_snippet(entry, tokens, max_chars), score=score)
        for score, entry in ranked[:limit]
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="search",
        description="本地古籍全文检索 CLI，供 Agent 主动检索原文",
    )
    parser.add_argument("query", help="检索词，例如：偏印格、论月令、天乙贵人")
    parser.add_argument("--book", choices=sorted(BOOKS), default="yuanhai", help="检索古籍，默认 yuanhai")
    parser.add_argument("--limit", type=int, default=5, help="返回条数，默认 5")
    parser.add_argument("--max-chars", type=int, default=500, help="每条正文最大字符数，默认 500")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    results = search(args.query, book=args.book, limit=args.limit, max_chars=args.max_chars)
    if args.format == "text":
        for item in results:
            print(f"[{item['source']} #{item['id']}] {item['title']} score={item['score']}")
            print(item["text"])
            print()
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
