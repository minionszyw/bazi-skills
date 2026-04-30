import argparse
import math
import sys

from src.engine.core import BaziEngine
from src.engine.config import config
from src.engine.models import BaziRequest, Gender, CalendarType, TimeMode, MonthMode, ZiShiMode
from src.engine.preprocessor import SolarTimeCalculator


def _print_input(req: BaziRequest):
    print("\n" + "═" * 75)
    print("  用户输入参数")
    print("─" * 75)
    print(f"  姓名 (name):          {req.name}")
    print(f"  性别 (gender):        {'男 (1)' if req.gender == Gender.MALE else '女 (0)'}")
    print(f"  历法 (calendar_type): {'公历 (SOLAR)' if req.calendar_type == CalendarType.SOLAR else '农历 (LUNAR)'}")
    print(f"  时间 (birth_datetime):{req.birth_datetime}")
    print(f"  地点 (birth_location):{req.birth_location}")
    print(f"  时间模式 (time_mode): {'真太阳时 (TRUE_SOLAR)' if req.time_mode == TimeMode.TRUE_SOLAR else '平太阳时 (MEAN_SOLAR)'}")
    print(f"  月柱模式 (month_mode):{'节气定月 (SOLAR_TERM)' if req.month_mode == MonthMode.SOLAR_TERM else '农历月定月 (LUNAR_MONTH)'}")
    print(f"  子时模式 (zi_shi):    {'晚子时不换日' if req.zi_shi_mode == ZiShiMode.LATE_ZI_IN_DAY else '23点换日'}")
    print("═" * 75 + "\n")


def _print_internals(res, longitude: float):
    from lunar_python import Solar
    date_str = res.birth_solar_datetime.split(" ")[0]
    y, m, d = map(int, date_str.split("-"))
    eot = SolarTimeCalculator.get_eot(Solar.fromYmd(y, m, d))
    lon_offset = (longitude - 120.0) * 4
    print("  [引擎计算详情 - 真太阳时校正]")
    print(f"  > 检索经度: {longitude}° (地名: {res.request.birth_location})")
    print(f"  > 均时差 (EoT): {eot:+.2f} 分钟")
    print(f"  > 经度修正: {lon_offset:+.2f} 分钟")
    print(f"  > 总计偏移: {eot + lon_offset:+.2f} 分钟")
    print(f"  > 标准新历 (UTC+8): {res.request.birth_datetime}")
    print(f"  > 校正后新历 (Solar): {res.birth_solar_datetime}")
    print(f"  > 校正后农历 (Lunar): {res.birth_lunar_datetime}")
    print("─" * 75)


def _print_chart(res):
    core = res.core
    fortune = res.fortune
    aux = res.auxiliary
    cols = [core.year, core.month, core.day, core.time]

    print("  [命盘]")
    print("  十神：", end="")
    for col in cols:
        print(f"{col.shi_shen_gan.center(12)}", end="")
    print()
    print("  天干：", end="")
    for col in cols:
        print(f"{col.gan.center(14)}", end="")
    print()
    print("  地支：", end="")
    for col in cols:
        print(f"{col.zhi.center(14)}", end="")
    print()
    print("  藏干：", end="")
    for col in cols:
        print(f"{'/'.join(col.hide_gan).center(14)}", end="")
    print()
    print("  副星：", end="")
    for col in cols:
        print(f"{'/'.join(col.shi_shen_zhi).center(14)}", end="")
    print()
    print("  纳音：", end="")
    for col in cols:
        print(f"{col.na_yin.center(12)}", end="")
    print()
    print("  空亡：", end="")
    for col in cols:
        print(f"{''.join(col.xun_kong).center(14)}", end="")
    print()

    print("─" * 75)
    print("  [辅助信息]")
    print(f"  上一节气：【{core.jie_qi.prev_name}】 {core.jie_qi.prev_jie}")
    print(f"  下一节气：【{core.jie_qi.next_name}】 {core.jie_qi.next_jie}")
    print(f"  胎元：{aux.tai_yuan}({aux.tai_yuan_na_yin})  命宫：{aux.ming_gong}({aux.ming_gong_na_yin})  身宫：{aux.shen_gong}({aux.shen_gong_na_yin})")

    print("─" * 75)
    print("  [运程流转]")
    print(f"  正式起运时刻：{fortune.start_solar}")
    print(f"  起运前小运：", end="")
    print(" -> ".join(xy.gan_zhi for xy in fortune.before_start_xiao_yun))
    print("\n  前五步大运：")
    for dy in fortune.da_yun[:5]:
        print(f"  [{dy.gan_zhi}] {dy.start_year}年起 (岁数: {dy.start_age}) | 旬: {dy.xun}")

    print("─" * 75)
    print("  [深度分析 (Phase 3)]")
    if res.month_command:
        print(f"  > 月令分司：{res.month_command.detail}")
    if res.geju:
        print(f"  > 格局判定：{res.geju.name} ({res.geju.type}) | 状态: {res.geju.status}")
    if res.analysis:
        a = res.analysis
        print(f"  > 日主强弱：{a.strength_level} (得分: {a.strength_score})")
        print(f"  > 喜用神：用神[{a.yong_shen}] 喜神[{a.xi_shen}] | 忌神[{a.ji_shen}] 仇神[{a.chou_shen}]")
        print(f"  > 推导逻辑：{a.logic_type}")
    if res.stars:
        print(f"  > 核心神煞：{', '.join(f'{s.name}({s.pos})' for s in res.stars)}")

    print("─" * 75)
    for step in res.analysis_trace:
        val_str = f" | 变动: {step.value}" if step.value is not None else ""
        print(f"  * [{step.module}] {step.desc}{val_str}")
    print("═" * 75 + "\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python3 -m src.cli",
        description="八字排盘引擎 CLI（基于《渊海子平》）",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--name",     "-n", required=True,  help="姓名")
    p.add_argument("--gender",   "-g", required=True,  type=int, choices=[0, 1],
                   help="性别：1=男  0=女")
    p.add_argument("--calendar", "-c", required=True,  choices=["SOLAR", "LUNAR"],
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
        result = engine.arrange(req)
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    longitude = config.get_longitude(req.birth_location)

    _print_input(req)
    _print_internals(result, longitude)
    _print_chart(result)


if __name__ == "__main__":
    main()
