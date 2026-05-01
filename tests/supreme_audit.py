import json
from pathlib import Path

from src.engine.core import BaziEngine
from src.engine.models import BaziRequest


CASE_FILE = Path(__file__).with_name("supreme_audit.json")
UNMARKED = "古籍未标注"


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
            missing = [item for item in expected if item not in actual_desc]
            if missing:
                failures.append(f"干支作用缺失 expected_contains={missing} actual={sorted(actual_desc)}")

    if "stars" in expected_analysis:
        expected = expected_analysis["stars"]
        if not is_unmarked(expected):
            actual_names = {item.name for item in result.stars}
            missing = [item for item in expected if item not in actual_names]
            if missing:
                failures.append(f"神煞缺失 expected_contains={missing} actual={sorted(actual_names)}")

    return failures


def evaluate_cases():
    engine = BaziEngine()
    rows = []
    for case in load_cases():
        result = engine.arrange(build_request(case))
        rows.append((case, result, collect_failures(case, result)))
    return rows


def run_supreme_audit():
    rows = evaluate_cases()
    stats = {
        "total": len(rows),
        "pillars_ok": 0,
        "geju_ok": 0,
        "strength_ok": 0,
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
        geju_ok = geju_matches(expected_analysis["geju"], actual_geju)
        if geju_ok:
            stats["geju_ok"] += 1

        actual_strength = result.analysis.strength_level
        strength_ok = strength_matches(expected_analysis["strength"], actual_strength)
        if strength_ok:
            stats["strength_ok"] += 1

        if not failures:
            stats["perfect"] += 1

        p_display = f"{'OK' if pillars_ok else 'FAIL'} {' '.join(actual_pillars)}"
        g_display = f"{'OK' if geju_ok else 'WARN'} {actual_geju}"
        s_display = f"{'OK' if strength_ok else 'WARN'} {actual_strength}"
        overall = "PASS" if not failures else "FAIL"
        line = f"{name[:10]:<10} {p_display:<25} | {g_display:<15} | {s_display:<15} | {overall}"
        print(line)

    total = stats["total"] or 1
    print("-" * 120)
    print("  [审计统计结果]")
    print(f"  > 1. 基础干支准确率: {stats['pillars_ok'] / total * 100:.1f}% ({stats['pillars_ok']}/{stats['total']})")
    print(f"  > 2. 格局判定准确率: {stats['geju_ok'] / total * 100:.1f}% ({stats['geju_ok']}/{stats['total']})")
    print(f"  > 3. 强弱判定准确率: {stats['strength_ok'] / total * 100:.1f}% ({stats['strength_ok']}/{stats['total']})")
    print(f"  > 4. 全字段通过率: {stats['perfect'] / total * 100:.1f}% ({stats['perfect']}/{stats['total']})")
    print("=" * 120 + "\n")

    return stats


def test_supreme_audit_cases():
    failures = []
    for case, _result, case_failures in evaluate_cases():
        failures.extend(f"{case['case_name']}: {item}" for item in case_failures)
    assert not failures, "\n".join(failures)


if __name__ == "__main__":
    run_supreme_audit()
