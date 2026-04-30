import argparse
import json
import sys

from src.engine.core import BaziEngine
from src.engine.models import BaziRequest, Gender, CalendarType, TimeMode, MonthMode, ZiShiMode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python3 -m src.cli",
        description="八字排盘引擎 CLI（基于《渊海子平》），输出 JSON",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--name",     "-n", required=True, help="姓名")
    p.add_argument("--gender",   "-g", required=True, type=int, choices=[0, 1],
                   help="性别：1=男  0=女")
    p.add_argument("--calendar", "-c", required=True, choices=["SOLAR", "LUNAR"],
                   help="历法：SOLAR=公历  LUNAR=农历")
    p.add_argument("--birth",    "-b", required=True,
                   help="出生时间，格式：YYYY-MM-DD HH:MM:SS")
    p.add_argument("--location", "-l", required=True,
                   help="出生地，如：深圳 / 广州市 / 天河区")
    p.add_argument("--time-mode", default="TRUE_SOLAR", choices=["TRUE_SOLAR", "MEAN_SOLAR"],
                   help="时间模式（默认 TRUE_SOLAR 真太阳时）")
    p.add_argument("--month-mode", default="SOLAR_TERM", choices=["SOLAR_TERM", "LUNAR_MONTH"],
                   help="月柱模式（默认 SOLAR_TERM 节气定月）")
    p.add_argument("--zi-shi-mode", default="LATE_ZI_IN_DAY", choices=["LATE_ZI_IN_DAY", "NEXT_DAY"],
                   help="子时换日规则（默认 LATE_ZI_IN_DAY 晚子时不换日）")
    p.add_argument("--date", "-d", default=None,
                   help="查询特定日期的流年/流月/流日，格式：YYYY-MM-DD")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        req = BaziRequest(
            name=args.name,
            gender=Gender(args.gender),
            calendar_type=CalendarType(args.calendar),
            birth_datetime=args.birth,
            birth_location=args.location,
            time_mode=TimeMode(args.time_mode),
            month_mode=MonthMode(args.month_mode),
            zi_shi_mode=ZiShiMode(args.zi_shi_mode),
        )
    except ValueError as e:
        parser.error(str(e))

    engine = BaziEngine()
    try:
        result = engine.arrange(req, query_date=args.date)
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
