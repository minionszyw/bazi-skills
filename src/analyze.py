import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.analysis import SUPPORTED_TOPICS, analyze_chart
from src.search import search


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze",
        description="命理分析层 CLI：根据排盘 JSON 生成古法分析步骤与古籍检索词",
    )
    parser.add_argument(
        "--chart",
        "-f",
        default="-",
        help="排盘 JSON 文件路径；默认从 stdin 读取",
    )
    parser.add_argument(
        "--topic",
        "-t",
        choices=SUPPORTED_TOPICS,
        default="overall",
        help="分析主题，默认 overall",
    )
    parser.add_argument(
        "--with-evidence",
        action="store_true",
        help="同时调用 search，把古籍检索结果嵌入输出",
    )
    parser.add_argument("--book", default="yuanhai", help="古籍代号，默认 yuanhai")
    parser.add_argument("--limit", type=int, default=2, help="每个检索词返回条数，默认 2")
    parser.add_argument("--max-chars", type=int, default=260, help="每条原文最大字符数，默认 260")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    return parser


def load_chart(path: str) -> dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"排盘 JSON 解析失败：{exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("排盘 JSON 顶层必须是对象")
    return data


def attach_evidence(result: dict[str, Any], *, book: str, limit: int, max_chars: int) -> dict[str, Any]:
    evidence = {}
    for query in result["search_queries"]:
        evidence[query] = search(query, book=book, limit=limit, max_chars=max_chars)
    result["evidence"] = evidence
    return result


def render_text(result: dict[str, Any]) -> str:
    lines = [
        f"{result['title']} ({result['topic']})",
        "",
        "命盘摘要：",
    ]
    summary = result["chart_summary"]
    pillars = summary["four_pillars"]
    lines.append(
        f"- 四柱：{pillars['year']}年、{pillars['month']}月、{pillars['day']}日、{pillars['time']}时"
    )
    lines.append(f"- 日主/月令：{summary.get('day_master')}日，{summary.get('month_branch')}月")
    lines.append(f"- 格局：{summary['geju'].get('name')}（{summary['geju'].get('status')}）")
    lines.append(
        f"- 旺衰：{summary['strength'].get('level')}，用神 {summary['useful_gods'].get('yong_shen')}，喜神 {summary['useful_gods'].get('xi_shen')}"
    )
    lines.append("")
    lines.append("分析步骤：")
    for index, step in enumerate(result["steps"], start=1):
        lines.append(f"{index}. {step['name']}")
        lines.append(f"   方法：{step['method']}")
        lines.append(f"   依据：{'；'.join(step['inputs'])}")
        lines.append(f"   结论：{step['conclusion']}")
        lines.append(f"   检索词：{'、'.join(step['search_queries'])}")
    if "evidence" in result:
        lines.append("")
        lines.append("古籍检索：")
        for query, items in result["evidence"].items():
            if not items:
                continue
            first = items[0]
            lines.append(f"- {query}：{first['source']}《{first['title']}》 {first['text']}")
    return "\n".join(lines)


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        chart = load_chart(args.chart)
        result = analyze_chart(chart, topic=args.topic)
        if args.with_evidence:
            result = attach_evidence(result, book=args.book, limit=args.limit, max_chars=args.max_chars)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    if args.format == "text":
        print(render_text(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
