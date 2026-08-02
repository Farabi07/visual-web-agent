from visual_web_agent.models import BookSpec


def test_search_text_includes_authors() -> None:
    spec = BookSpec(title="Example Title", authors=("Author One", "Author Two"))
    assert spec.search_text == "Example Title Author One Author Two"
