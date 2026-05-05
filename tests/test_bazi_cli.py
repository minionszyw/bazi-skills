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
