import json
import subprocess
import sys
from pathlib import Path

from src.analysis import SUPPORTED_TOPICS, analyze_chart
from src.analysis.methods import all_methods, methods_for_kind
from src.search import search


ROOT = Path(__file__).resolve().parents[1]
CHART = json.loads((ROOT / "tests" / "bazi.json").read_text(encoding="utf-8"))


def test_analyze_overall_builds_method_steps_and_queries():
    result = analyze_chart(CHART, topic="overall")

    assert result["topic"] == "overall"
    assert result["chart_summary"]["day_master"] == "壬"
    assert result["chart_summary"]["geju"]["name"] == "七杀格"
    assert len(result["steps"]) >= 5
    assert result["search_query_layers"]["required"]
    assert "月令" in result["search_queries"]
    assert "月令" in result["search_query_layers"]["required"]
    assert any(step["search_queries"] for step in result["steps"])
    assert result["evidence_plan"]
    assert result["judgement_hierarchy"]
    assert all(step["evidence_queries"] for step in result["steps"])
    assert all(step["method_refs"] for step in result["steps"])
    assert any(ref["id"] == "yuanhai.kanming.foundation" for ref in result["steps"][0]["method_refs"])


def test_analyze_career_includes_official_and_output_steps():
    result = analyze_chart(CHART, topic="career")
    step_names = [step["name"] for step in result["steps"]]

    assert "看官杀印星" in step_names
    assert "看食伤才华" in step_names
    assert any("正官" in query or "偏官" in query for query in result["search_queries"])
    assert any("食神" in query for query in result["search_queries"])
    assert any("正官" in query or "偏官" in query for query in result["search_query_layers"]["topic_specific"])


def test_all_supported_topics_build_steps_and_queries():
    for topic in SUPPORTED_TOPICS:
        result = analyze_chart(CHART, topic=topic)

        assert result["topic"] == topic
        assert result["title"]
        assert result["judgement_hierarchy"]["priority"]
        assert result["steps"]
        assert result["search_queries"]
        assert all(step["method_refs"] for step in result["steps"])


def test_judgement_hierarchy_encodes_primary_secondary_rules():
    result = analyze_chart(CHART, topic="overall")
    hierarchy = result["judgement_hierarchy"]

    names = [item["name"] for item in hierarchy["priority"]]
    assert names[:3] == ["日主与月令", "格局成败", "用神喜忌"]
    assert names[-1] == "神煞辅证"
    assert any("凶煞不单独定凶" in item["rule"] for item in hierarchy["priority"])
    assert any("神煞只提示局部取象" in rule for rule in hierarchy["conflict_rules"])
    assert any("七杀格" in item for item in hierarchy["current_chart_application"])


def test_topic_step_kinds_are_backed_by_yuanhai_methods():
    for topic in SUPPORTED_TOPICS:
        result = analyze_chart(CHART, topic=topic)
        for step in result["steps"]:
            assert methods_for_kind(step["kind"]), step["kind"]


def test_yuanhai_method_sources_are_searchable():
    for method in all_methods():
        results = search(method.audit_query, book=method.book, limit=3, max_chars=240)

        assert results, method.id
        matched = [
            item
            for item in results
            if item["title"] == method.expected_title
            and all(term in item["text"] or term in item["title"] for term in method.expected_terms)
        ]
        assert matched, method.id


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
            "--no-evidence",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    result = json.loads(completed.stdout)
    assert result["topic"] == "wealth"
    assert "judgement_hierarchy" in result
    assert "search_queries" not in result
    assert "search_query_layers" not in result
    assert "evidence" not in result


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
    assert "evidence_meta" not in result
    assert "evidence_plan" not in result
    assert any(items for items in result["evidence"].values())


def test_analyze_cli_attaches_evidence_by_default(tmp_path):
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
    assert "论偏官即七杀" in result["evidence"]
    assert "刑冲破害" in result["evidence"]
    assert "论起大运法" in result["evidence"]


def test_default_evidence_plan_covers_each_step_method_audit_query():
    result = analyze_chart(CHART, topic="overall")

    for step in result["steps"]:
        planned = set(step["evidence_queries"])
        audits = {ref["audit_query"] for ref in step["method_refs"]}
        assert audits <= planned


def test_layer_evidence_mode_is_still_available(tmp_path):
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
            "--view",
            "full",
            "--evidence-tier",
            "required",
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
    assert result["evidence_meta"]["mode"] == "layers"
    assert result["evidence_meta"]["tiers"] == ["required"]
    assert set(result["evidence"]).issubset(set(result["search_query_layers"]["required"]))


def test_analyze_cli_full_view_includes_audit_fields(tmp_path):
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
            "--view",
            "full",
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
    assert result["evidence_meta"]["mode"] == "step_plan"
    assert result["evidence_meta"]["tiers"] == []
    assert result["evidence_plan"]
    assert result["search_queries"]
    assert result["search_query_layers"]
    assert result["steps"][0]["method_refs"]
    assert result["steps"][0]["evidence_queries"]
