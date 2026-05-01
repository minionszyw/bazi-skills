import json
from pathlib import Path
from types import SimpleNamespace

from src.engine.core import BaziEngine
from src.engine.algorithms.analysis import AnalysisEngine
from src.engine.algorithms.energy import EnergyModel
from src.engine.algorithms.geju import GejuAnalyzer
from src.engine.algorithms.interactions import InteractionDetector
from src.engine.algorithms.stars import StarDetector
from src.engine.models import BaziRequest
from src.engine.schemas import FiveElementsResult


CASE_FILE = Path(__file__).with_name("supreme_audit.json")
UNMARKED = "古籍未标注"

HIDE_GAN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

STEM_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

STEM_YANG = {"甲", "丙", "戊", "庚", "壬"}
ELEMENT_CYCLE = ["木", "火", "土", "金", "水"]


def load_cases():
    with CASE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_request(case):
    data = case["input"]
    return BaziRequest(
        name=data["name"],
        gender=data["gender"],
        calendar_type=data["calendar_type"],
        birth_datetime=data["birth_datetime"],
        birth_location=data["birth_location"],
        longitude=data.get("longitude"),
        time_mode=data["time_mode"],
        month_mode=data["month_mode"],
        zi_shi_mode=data["zi_shi_mode"],
    )


def shishen(day_gan, target_gan):
    if day_gan == target_gan:
        return "日主"

    day_elem = STEM_ELEMENT[day_gan]
    target_elem = STEM_ELEMENT[target_gan]
    same_polarity = (day_gan in STEM_YANG) == (target_gan in STEM_YANG)
    day_idx = ELEMENT_CYCLE.index(day_elem)
    target_idx = ELEMENT_CYCLE.index(target_elem)

    if target_elem == day_elem:
        return "比肩" if same_polarity else "劫财"
    if target_idx == (day_idx + 1) % 5:
        return "食神" if same_polarity else "伤官"
    if target_idx == (day_idx + 2) % 5:
        return "偏财" if same_polarity else "正财"
    if target_idx == (day_idx - 1) % 5:
        return "偏印" if same_polarity else "正印"
    if target_idx == (day_idx - 2) % 5:
        return "七杀" if same_polarity else "正官"
    return "未知"


class FakeEightChar:
    def __init__(self, pillars):
        self.stems = [pillar[0] for pillar in pillars]
        self.branches = [pillar[1] for pillar in pillars]

    def getYear(self): return self.stems[0] + self.branches[0]
    def getMonth(self): return self.stems[1] + self.branches[1]
    def getDay(self): return self.stems[2] + self.branches[2]
    def getTime(self): return self.stems[3] + self.branches[3]
    def getYearGan(self): return self.stems[0]
    def getMonthGan(self): return self.stems[1]
    def getDayGan(self): return self.stems[2]
    def getTimeGan(self): return self.stems[3]
    def getYearZhi(self): return self.branches[0]
    def getMonthZhi(self): return self.branches[1]
    def getDayZhi(self): return self.branches[2]
    def getTimeZhi(self): return self.branches[3]

    def getYearHideGan(self): return HIDE_GAN[self.branches[0]]
    def getMonthHideGan(self): return HIDE_GAN[self.branches[1]]
    def getDayHideGan(self): return HIDE_GAN[self.branches[2]]
    def getTimeHideGan(self): return HIDE_GAN[self.branches[3]]

    def getYearShiShenGan(self): return shishen(self.getDayGan(), self.getYearGan())
    def getMonthShiShenGan(self): return shishen(self.getDayGan(), self.getMonthGan())
    def getTimeShiShenGan(self): return shishen(self.getDayGan(), self.getTimeGan())

    def getYearShiShenZhi(self): return [shishen(self.getDayGan(), gan) for gan in self.getYearHideGan()]
    def getMonthShiShenZhi(self): return [shishen(self.getDayGan(), gan) for gan in self.getMonthHideGan()]
    def getDayShiShenZhi(self): return [shishen(self.getDayGan(), gan) for gan in self.getDayHideGan()]
    def getTimeShiShenZhi(self): return [shishen(self.getDayGan(), gan) for gan in self.getTimeHideGan()]


class FakeLunar:
    def __init__(self, eight_char):
        self.eight_char = eight_char

    def getEightChar(self):
        return self.eight_char


class FakeSolar:
    def __init__(self, eight_char):
        self.lunar = FakeLunar(eight_char)

    def getLunar(self):
        return self.lunar


def arrange_pillar_case(case):
    pillars = case["pillar_input"]["pillars"]
    eight_char = FakeEightChar(pillars)
    ctx = SimpleNamespace(
        solar=FakeSolar(eight_char),
        request=SimpleNamespace(gender=case["pillar_input"].get("gender", 1)),
    )

    energy_data = EnergyModel.calculate_scores(ctx)
    five_elements = FiveElementsResult(
        scores={k: v["score"] for k, v in energy_data.items()},
        states={k: v["state"] for k, v in energy_data.items()}
    )
    interactions = InteractionDetector.detect_all(ctx)
    InteractionDetector.validate_transformations(interactions, ctx)
    geju = GejuAnalyzer.analyze(ctx, interactions, five_elements.scores)
    analysis = AnalysisEngine.analyze(ctx, energy_data, geju)
    stars = StarDetector.detect(ctx)

    def column(pillar):
        return SimpleNamespace(gan=pillar[0], zhi=pillar[1])

    return SimpleNamespace(
        core=SimpleNamespace(
            year=column(pillars[0]),
            month=column(pillars[1]),
            day=column(pillars[2]),
            time=column(pillars[3]),
        ),
        geju=geju,
        analysis=analysis,
        five_elements=five_elements,
        interactions=interactions,
        stars=stars,
        month_command=SimpleNamespace(current=UNMARKED, detail=UNMARKED),
    )


def get_pillars(result):
    return [
        f"{result.core.year.gan}{result.core.year.zhi}",
        f"{result.core.month.gan}{result.core.month.zhi}",
        f"{result.core.day.gan}{result.core.day.zhi}",
        f"{result.core.time.gan}{result.core.time.zhi}",
    ]


def geju_matches(expected, actual):
    expected_key = expected.replace("格", "")
    actual_key = actual.replace("格", "")
    compatible = {
        "七杀": {"杀印相生", "从官", "官印两透"},
        "正官": {"从官", "官印两透"},
        "食神": {"从食"},
        "伤官": {"伤官佩印", "从食", "从伤官"},
        "正印": {"官印两透", "伤官佩印"},
        "偏印": {"官印两透", "伤官佩印"},
        "正财": {"从财"},
        "偏财": {"从财"},
        "交禄": {"交互得禄"},
        "建禄月劫": {"建禄", "月刃"},
    }
    if actual_key in compatible.get(expected_key, set()):
        return True
    return expected_key in actual or actual_key in expected


def strength_matches(expected, actual):
    expected_map = {
        "身强": {"偏强", "极强"},
        "身弱": {"偏弱", "极弱"},
        "中和": {"中和"},
    }
    if expected in expected_map:
        return actual in expected_map[expected]
    return expected == actual


def is_unmarked(expected):
    return expected == UNMARKED


def check_equal(failures, label, expected, actual):
    if is_unmarked(expected):
        return
    if expected != actual:
        failures.append(f"{label} expected={expected} actual={actual}")


def collect_failures(case, result):
    failures = []
    expected_core = case["expected_core"]
    expected_analysis = case["expected_analysis"]

    actual_pillars = get_pillars(result)
    expected_pillars = expected_core["pillars"]
    if actual_pillars != expected_pillars:
        failures.append(f"四柱 expected={expected_pillars} actual={actual_pillars}")

    expected_geju = expected_analysis["geju"]
    actual_geju = result.geju.name
    if not is_unmarked(expected_geju) and not geju_matches(expected_geju, actual_geju):
        failures.append(f"格局 expected={expected_geju} actual={actual_geju}")
    check_equal(failures, "格局类型", expected_analysis.get("geju_type", UNMARKED), result.geju.type)
    check_equal(failures, "格局状态", expected_analysis.get("geju_status", UNMARKED), result.geju.status)
    check_equal(failures, "格局细节", expected_analysis.get("geju_detail", UNMARKED), result.geju.detail)

    expected_strength = expected_analysis["strength"]
    actual_strength = result.analysis.strength_level
    if not is_unmarked(expected_strength) and not strength_matches(expected_strength, actual_strength):
        failures.append(f"强弱 expected={expected_strength} actual={actual_strength}")

    optional_checks = {
        "strength_score": result.analysis.strength_score,
        "yong_shen": result.analysis.yong_shen,
        "xi_shen": result.analysis.xi_shen,
        "ji_shen": result.analysis.ji_shen,
        "chou_shen": result.analysis.chou_shen,
        "logic_type": result.analysis.logic_type,
    }
    for field, actual in optional_checks.items():
        if field in expected_analysis:
            check_equal(failures, field, expected_analysis[field], actual)

    if "month_command" in expected_analysis:
        expected = expected_analysis["month_command"]
        if isinstance(expected, dict):
            check_equal(failures, "月令司令", expected.get("current", UNMARKED), result.month_command.current)
            check_equal(failures, "月令司令细节", expected.get("detail", UNMARKED), result.month_command.detail)
        elif not is_unmarked(expected):
            check_equal(failures, "月令司令", expected, result.month_command.current)

    if "five_elements" in expected_analysis:
        expected = expected_analysis["five_elements"]
        if not is_unmarked(expected):
            expected_scores = expected.get("scores", {})
            for element, expected_score in expected_scores.items():
                actual_score = result.five_elements.scores.get(element)
                check_equal(failures, f"五行分数.{element}", expected_score, actual_score)

            expected_states = expected.get("states", {})
            for element, expected_state in expected_states.items():
                actual_state = result.five_elements.states.get(element)
                check_equal(failures, f"五行状态.{element}", expected_state, actual_state)

    if "interactions" in expected_analysis:
        expected = expected_analysis["interactions"]
        if not is_unmarked(expected):
            actual_desc = {item.desc for item in result.interactions}
            missing = [item for item in expected if not any(item in desc for desc in actual_desc)]
            if missing:
                failures.append(f"干支作用缺失 expected_contains={missing} actual={sorted(actual_desc)}")

    if "stars" in expected_analysis:
        expected = expected_analysis["stars"]
        if not is_unmarked(expected):
            actual_names = {item.name for item in result.stars}
            missing = [item for item in expected if not any(item in name for name in actual_names)]
            if missing:
                failures.append(f"神煞缺失 expected_contains={missing} actual={sorted(actual_names)}")

    return failures


def evaluate_cases():
    engine = BaziEngine()
    rows = []
    for case in load_cases():
        if "input" in case:
            result = engine.arrange(build_request(case))
        else:
            result = arrange_pillar_case(case)
        rows.append((case, result, collect_failures(case, result)))
    return rows


def run_supreme_audit():
    rows = evaluate_cases()
    stats = {
        "total": len(rows),
        "pillars_ok": 0,
        "pillars_total": len(rows),
        "geju_ok": 0,
        "geju_total": 0,
        "strength_ok": 0,
        "strength_total": 0,
        "yong_shen_ok": 0,
        "yong_shen_total": 0,
        "interactions_ok": 0,
        "interactions_total": 0,
        "stars_ok": 0,
        "stars_total": 0,
        "perfect": 0,
    }

    print("\n" + "=" * 120)
    print("  八字排盘引擎：终极全流程审计报告 (Supreme Audit)")
    print("-" * 120)
    header = f"{'命例名称':<10} {'[1] 基础干支对账':<25} | {'[2] 格局定性':<15} | {'[3] 强弱判定':<15} | 状态"
    print(header)
    print("-" * 120)

    for case, result, failures in rows:
        name = case["case_name"]
        expected_core = case["expected_core"]
        expected_analysis = case["expected_analysis"]

        actual_pillars = get_pillars(result)
        pillars_ok = actual_pillars == expected_core["pillars"]
        if pillars_ok:
            stats["pillars_ok"] += 1

        actual_geju = result.geju.name
        geju_expected = expected_analysis["geju"]
        geju_ok = is_unmarked(geju_expected) or geju_matches(geju_expected, actual_geju)
        if not is_unmarked(geju_expected):
            stats["geju_total"] += 1
        if geju_ok:
            if not is_unmarked(geju_expected):
                stats["geju_ok"] += 1

        actual_strength = result.analysis.strength_level
        strength_expected = expected_analysis["strength"]
        strength_ok = is_unmarked(strength_expected) or strength_matches(strength_expected, actual_strength)
        if not is_unmarked(strength_expected):
            stats["strength_total"] += 1
        if strength_ok:
            if not is_unmarked(strength_expected):
                stats["strength_ok"] += 1

        yong_shen_expected = expected_analysis.get("yong_shen", UNMARKED)
        if not is_unmarked(yong_shen_expected):
            stats["yong_shen_total"] += 1
            if yong_shen_expected == result.analysis.yong_shen:
                stats["yong_shen_ok"] += 1

        interactions_expected = expected_analysis.get("interactions", UNMARKED)
        if not is_unmarked(interactions_expected):
            stats["interactions_total"] += 1
            actual_desc = {item.desc for item in result.interactions}
            if all(any(item in desc for desc in actual_desc) for item in interactions_expected):
                stats["interactions_ok"] += 1

        stars_expected = expected_analysis.get("stars", UNMARKED)
        if not is_unmarked(stars_expected):
            stats["stars_total"] += 1
            actual_names = {item.name for item in result.stars}
            if all(any(item in name for name in actual_names) for item in stars_expected):
                stats["stars_ok"] += 1

        if not failures:
            stats["perfect"] += 1

        p_display = f"{'OK' if pillars_ok else 'FAIL'} {' '.join(actual_pillars)}"
        g_status = "SKIP" if is_unmarked(geju_expected) else "OK" if geju_ok else "WARN"
        s_status = "SKIP" if is_unmarked(strength_expected) else "OK" if strength_ok else "WARN"
        g_display = f"{g_status} {actual_geju}"
        s_display = f"{s_status} {actual_strength}"
        overall = "PASS" if not failures else "FAIL"
        line = f"{name[:10]:<10} {p_display:<25} | {g_display:<15} | {s_display:<15} | {overall}"
        print(line)

    def metric_line(index, label, ok, marked):
        accuracy_base = marked or 1
        coverage_base = stats["total"] or 1
        accuracy = ok / accuracy_base * 100
        coverage = marked / coverage_base * 100
        return (
            f"  > {index}. {label}: {accuracy:.1f}% ({ok}/{marked}), "
            f"覆盖率: {coverage:.1f}% ({marked}/{stats['total']})"
        )

    total = stats["total"] or 1
    print("-" * 120)
    print("  [审计统计结果]")
    print(f"  > 1. 基础干支准确率: {stats['pillars_ok'] / total * 100:.1f}% ({stats['pillars_ok']}/{stats['pillars_total']}), 覆盖率: 100.0% ({stats['pillars_total']}/{stats['total']})")
    print(metric_line(2, "格局判定准确率", stats["geju_ok"], stats["geju_total"]))
    print(metric_line(3, "强弱判定准确率", stats["strength_ok"], stats["strength_total"]))
    print(metric_line(4, "用神判定准确率", stats["yong_shen_ok"], stats["yong_shen_total"]))
    print(metric_line(5, "干支作用准确率", stats["interactions_ok"], stats["interactions_total"]))
    print(metric_line(6, "神煞判定准确率", stats["stars_ok"], stats["stars_total"]))
    print(f"  > 7. 全字段通过率: {stats['perfect'] / total * 100:.1f}% ({stats['perfect']}/{stats['total']}), 覆盖率: 100.0% ({stats['total']}/{stats['total']})")
    print("=" * 120 + "\n")

    return stats


def test_supreme_audit_cases():
    failures = []
    for case, _result, case_failures in evaluate_cases():
        failures.extend(f"{case['case_name']}: {item}" for item in case_failures)
    assert not failures, "\n".join(failures)


if __name__ == "__main__":
    run_supreme_audit()
