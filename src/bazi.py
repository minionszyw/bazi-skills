import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

from src.analysis import analyze_chart
from src.analyze import attach_evidence, compact_result
from src.engine.core import BaziEngine
from src.engine.models import BaziRequest, CalendarType, Gender, MonthMode, TimeMode, ZiShiMode


REQUIRED_INPUTS = ["name", "gender", "calendar", "birth", "location"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bazi",
        description="八字命理编排 CLI：按用户问题自动编排排盘、分析与证据检索",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    ask = subparsers.add_parser("ask", help="根据自然语言问题编排命理分析")
    ask.add_argument("--question", "-q", required=True, help="用户问题，例如：今日运势分析")
    ask.add_argument("--chart", help="已有命盘 JSON；有后续追问时优先传入")
    ask.add_argument("--save-chart", help="保存或更新命盘 JSON 的路径")
    ask.add_argument("--name", help="姓名或称呼")
    ask.add_argument("--gender", type=int, choices=[0, 1], help="性别：1=男 0=女")
    ask.add_argument("--calendar", choices=["SOLAR", "LUNAR"], help="历法")
    ask.add_argument("--birth", help="出生时间，格式：YYYY-MM-DD HH:MM:SS")
    ask.add_argument("--location", help="出生地")
    ask.add_argument("--date", help="指定运势查询日期，格式 YYYY-MM-DD；不传则从问题识别")
    ask.add_argument("--today", default=None, help=argparse.SUPPRESS)
    ask.add_argument("--view", choices=["compact", "full"], default="compact", help="输出视图")
    ask.add_argument("--limit", type=int, default=2, help="每个检索词返回条数")
    ask.add_argument("--max-chars", type=int, default=260, help="每条原文最大字符数")
    ask.add_argument("--no-evidence", action="store_true", help="不嵌入古籍 evidence")
    return parser


def load_json(path: str) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("命盘 JSON 顶层必须是对象")
    return data


def resolve_intent(question: str, explicit_date: Optional[str], today: Optional[str]) -> dict[str, Any]:
    query_date = explicit_date or _date_from_question(question, today)
    topic = "overall"
    focus = None
    name = "overall"

    if any(word in question for word in ["提升财运", "改善财运", "增强财运", "如何提升财运"]):
        topic, focus, name = "remedy", "wealth", "improve-wealth"
    elif any(word in question for word in ["财运", "财富", "求财"]):
        topic, name = "wealth", "wealth"
    elif any(word in question for word in ["提升事业", "改善事业", "事业提升"]):
        topic, focus, name = "remedy", "career", "improve-career"
    elif "事业" in question:
        topic, name = "career", "career"
    elif any(word in question for word in ["改善婚姻", "提升婚姻", "感情改善"]):
        topic, focus, name = "remedy", "marriage", "improve-marriage"
    elif any(word in question for word in ["婚姻", "感情", "恋爱"]):
        topic, name = "marriage", "marriage"
    elif any(word in question for word in ["健康"]):
        topic, name = "health", "health"
    elif any(word in question for word in ["学业", "学习"]):
        topic, name = "study", "study"
    elif any(word in question for word in ["父母"]):
        topic, name = "parents", "parents"
    elif any(word in question for word in ["子女", "孩子"]):
        topic, name = "children", "children"
    elif any(word in question for word in ["兄弟", "朋友"]):
        topic, name = "siblings", "siblings"
    elif any(word in question for word in ["人际", "合作"]):
        topic, name = "social", "social"
    elif any(word in question for word in ["提升", "改善", "化解", "趋避"]):
        topic, name = "remedy", "remedy"

    if query_date and name == "overall":
        name = "daily"

    return {"name": name, "topic": topic, "focus": focus, "date": query_date}


def _date_from_question(question: str, today: Optional[str]) -> Optional[str]:
    if any(word in question for word in ["今日", "今天", "当日", "今日运势", "今天运势"]):
        return today or date.today().isoformat()
    return None


def missing_inputs(args: argparse.Namespace, chart: Optional[dict[str, Any]]) -> list[str]:
    if chart:
        return []
    missing = []
    for field, attr in [
        ("name", "name"),
        ("gender", "gender"),
        ("calendar", "calendar"),
        ("birth", "birth"),
        ("location", "location"),
    ]:
        if getattr(args, attr) is None:
            missing.append(field)
    return missing


def chart_from_args(args: argparse.Namespace, query_date: Optional[str], existing: Optional[dict[str, Any]]) -> dict[str, Any]:
    if existing:
        request = existing.get("request") or {}
        if query_date and request:
            chart = arrange_chart(
                name=request.get("name"),
                gender=request.get("gender"),
                calendar=request.get("calendar_type"),
                birth=request.get("birth_datetime"),
                location=request.get("birth_location"),
                query_date=query_date,
            )
        else:
            chart = existing
    else:
        chart = arrange_chart(
            name=args.name,
            gender=args.gender,
            calendar=args.calendar,
            birth=args.birth,
            location=args.location,
            query_date=query_date,
        )
    if args.save_chart:
        Path(args.save_chart).write_text(json.dumps(chart, ensure_ascii=False, indent=2), encoding="utf-8")
    return chart


def arrange_chart(
    *,
    name: str,
    gender: int,
    calendar: str,
    birth: str,
    location: str,
    query_date: Optional[str],
) -> dict[str, Any]:
    request = BaziRequest(
        name=name,
        gender=Gender(gender),
        calendar_type=CalendarType(calendar),
        birth_datetime=birth,
        birth_location=location,
        time_mode=TimeMode("TRUE_SOLAR"),
        month_mode=MonthMode("SOLAR_TERM"),
        zi_shi_mode=ZiShiMode("LATE_ZI_IN_DAY"),
    )
    result = BaziEngine().arrange(request, query_date=query_date)
    return json.loads(result.model_dump_json())


def build_response(args: argparse.Namespace) -> dict[str, Any]:
    chart = load_json(args.chart) if args.chart else None
    intent = resolve_intent(args.question, args.date, args.today)
    missing = missing_inputs(args, chart)
    response = {
        "question": args.question,
        "intent": intent,
        "required_inputs": missing,
    }
    if missing:
        return response

    chart_data = chart_from_args(args, intent["date"], chart)
    result = analyze_chart(chart_data, topic=intent["topic"], focus=intent["focus"])
    if not args.no_evidence:
        result = attach_evidence(result, book="yuanhai", limit=args.limit, max_chars=args.max_chars)
    response["chart_saved_to"] = args.save_chart
    response["result"] = result if args.view == "full" else compact_result(result)
    return response


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "ask":
            print(json.dumps(build_response(args), ensure_ascii=False, indent=2))
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
