import json
import subprocess
import sys
from pathlib import Path

from src.analysis import SUPPORTED_TOPICS, analyze_chart


ROOT = Path(__file__).resolve().parents[1]
CHART = json.loads((ROOT / "tests" / "bazi.json").read_text(encoding="utf-8"))


def test_analyze_overall_builds_method_steps_and_queries():
    result = analyze_chart(CHART, topic="overall")

    assert result["topic"] == "overall"
    assert result["chart_summary"]["day_master"] == "癸"
    assert result["chart_summary"]["geju"]["name"] == "偏印格"
    assert len(result["steps"]) >= 5
    assert "月令" in result["search_queries"]
    assert any(step["search_queries"] for step in result["steps"])


def test_analyze_career_includes_official_and_output_steps():
    result = analyze_chart(CHART, topic="career")
    step_names = [step["name"] for step in result["steps"]]

    assert "看官杀印星" in step_names
    assert "看食伤才华" in step_names
    assert any("正官" in query or "偏官" in query for query in result["search_queries"])
    assert any("食神" in query for query in result["search_queries"])


def test_all_supported_topics_build_steps_and_queries():
    for topic in SUPPORTED_TOPICS:
        result = analyze_chart(CHART, topic=topic)

        assert result["topic"] == topic
        assert result["title"]
        assert result["steps"]
        assert result["search_queries"]


def test_analyze_family_and_health_topics_include_expected_methods():
    health = analyze_chart(CHART, topic="health")
    study = analyze_chart(CHART, topic="study")
    parents = analyze_chart(CHART, topic="parents")
    children = analyze_chart(CHART, topic="children")

    assert any(step["name"] == "看五行偏枯" for step in health["steps"])
    assert any("五行偏枯" in query for query in health["search_queries"])
    assert any(step["name"] == "看印星资质" for step in study["steps"])
    assert any(step["name"] == "看父母星" for step in parents["steps"])
    assert any(step["name"] == "看子女星" for step in children["steps"])


def test_analyze_cli_reads_chart_file(tmp_path):
    chart_path = tmp_path / "chart.json"
    chart_path.write_text(json.dumps(CHART, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.analyze",
            "--chart",
            str(chart_path),
            "--topic",
            "wealth",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    result = json.loads(completed.stdout)
    assert result["topic"] == "wealth"
    assert "search_queries" in result


def test_analyze_cli_can_attach_evidence(tmp_path):
    chart_path = tmp_path / "chart.json"
    chart_path.write_text(json.dumps(CHART, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.analyze",
            "--chart",
            str(chart_path),
            "--topic",
            "overall",
            "--with-evidence",
            "--limit",
            "1",
            "--max-chars",
            "80",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    result = json.loads(completed.stdout)
    assert result["evidence"]
    assert any(items for items in result["evidence"].values())
