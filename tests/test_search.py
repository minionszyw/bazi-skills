from src.search import load_entries, search


def test_yuanhai_docx_is_split_into_searchable_entries():
    entries = load_entries()

    assert len(entries) > 100
    assert any(entry.title == "论月令" for entry in entries)


def test_yuanhai_search_returns_relevant_source_text():
    results = search("月令", limit=3, max_chars=120)

    assert results
    assert any("月令" in item["title"] or "月令" in item["text"] for item in results)
    assert {"id", "source", "title", "text", "score"} <= set(results[0])
    assert results[0]["source"] == "《渊海子平》"
