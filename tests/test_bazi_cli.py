import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "tests" / "bazi.json"


def run_ask(*args):
    completed = subprocess.run(
        [sys.executable, "-m", "src.bazi", "ask", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_bazi_ask_requests_missing_birth_inputs():
    result = run_ask("--question", "请你帮我进行八字命理分析")

    assert result["required_inputs"] == ["name", "gender", "calendar", "birth", "location"]
    assert result["intent"]["topic"] == "overall"
    assert "result" not in result


def test_bazi_ask_wealth_followup_reuses_chart():
    result = run_ask("--question", "分析我的财运", "--chart", str(CHART), "--no-evidence")

    assert result["required_inputs"] == []
    assert result["intent"]["name"] == "wealth"
    assert result["result"]["topic"] == "wealth"
    assert result["result"]["title"] == "财运分析"


def test_bazi_ask_improve_wealth_maps_to_focused_remedy():
    result = run_ask("--question", "如何提升财运？", "--chart", str(CHART), "--no-evidence")

    step_kinds = [step["kind"] for step in result["result"]["steps"]]
    assert result["intent"]["name"] == "improve-wealth"
    assert result["result"]["topic"] == "remedy"
    assert result["result"]["focus"] == "wealth"
    assert "wealth" in step_kinds
    assert "remedy_scene" in step_kinds


def test_bazi_ask_today_regenerates_query_date_from_chart():
    result = run_ask(
        "--question",
        "今日运势分析",
        "--chart",
        str(CHART),
        "--today",
        "2026-05-05",
        "--no-evidence",
    )

    fortune_steps = [step for step in result["result"]["steps"] if step["kind"] == "fortune"]
    assert result["intent"]["name"] == "daily"
    assert result["intent"]["date"] == "2026-05-05"
    assert fortune_steps
    assert any("流日：" in item for item in fortune_steps[0]["inputs"])


def test_bazi_ask_tomorrow_sets_query_date():
    result = run_ask(
        "--question",
        "明天运势如何",
        "--chart",
        str(CHART),
        "--today",
        "2026-05-05",
        "--no-evidence",
    )

    assert result["intent"]["name"] == "daily"
    assert result["intent"]["date"] == "2026-05-06"
    assert result["intent"]["time_scope"] == "day"


def test_bazi_ask_year_career_sets_year_scope_and_career_topic():
    result = run_ask("--question", "2026年事业运", "--chart", str(CHART), "--no-evidence")

    assert result["intent"]["topic"] == "career"
    assert result["intent"]["date"] == "2026-01-01"
    assert result["intent"]["time_scope"] == "year"
    assert result["result"]["title"] == "事业分析"


def test_bazi_ask_month_and_range_scopes():
    month = run_ask(
        "--question",
        "这个月运势",
        "--chart",
        str(CHART),
        "--today",
        "2026-05-05",
        "--no-evidence",
    )
    range_result = run_ask(
        "--question",
        "未来三个月财运",
        "--chart",
        str(CHART),
        "--today",
        "2026-05-05",
        "--no-evidence",
    )

    assert month["intent"]["date"] == "2026-05-01"
    assert month["intent"]["time_scope"] == "month"
    assert range_result["intent"]["topic"] == "wealth"
    assert range_result["intent"]["time_scope"] == "range_3_months"


def test_bazi_ask_decision_scenarios_map_to_relevant_topics():
    job = run_ask("--question", "适合换工作吗", "--chart", str(CHART), "--no-evidence")
    investment = run_ask("--question", "适合投资吗", "--chart", str(CHART), "--no-evidence")

    assert job["intent"]["topic"] == "career"
    assert job["intent"]["scenario"] == "job_change"
    assert investment["intent"]["topic"] == "wealth"
    assert investment["intent"]["scenario"] == "investment"
