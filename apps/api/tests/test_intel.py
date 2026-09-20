"""backend-ai lane. Real logic, no network: mapping is pure, and the recommender
takes an injected client so Broader/Deeper behaviour is tested deterministically.
"""
from openalex import mapping
from intel import recommend as rec


def _work(wid, title, year, cited, *, topic="T1", keywords=(), wtype="article"):
    return {
        "id": f"https://openalex.org/{wid}",
        "title": title,
        "publication_year": year,
        "cited_by_count": cited,
        "type": wtype,
        "topics": [{"id": f"https://openalex.org/{topic}", "display_name": "NLP",
                    "subfield": {"display_name": "AI"}, "field": {"display_name": "CS"},
                    "domain": {"display_name": "Physical Sciences"}}],
        "keywords": [{"display_name": k} for k in keywords],
        "authorships": [{"author": {"display_name": "A. Author"}}],
    }


SOURCE = _work("W1", "Attention Is All You Need", 2017, 100000,
               keywords=("transformer", "machine translation", "encoder"))
SURVEY = _work("W2", "A Survey of Transformer Architectures", 2015, 90000,
               keywords=("transformer",), wtype="review")
NEW_SPECIFIC = _work("W3", "Improving Transformers: a case study in ablation", 2023, 40,
                     keywords=("transformer", "machine translation", "ablation"))


class FakeClient:
    """Stands in for OpenAlexProvider — every pool returns known works."""
    def __init__(self, out=(), inc=(), topic=(), semantic=()):
        self._out, self._in, self._topic, self._semantic = out, inc, topic, semantic

    def get_work(self, work_id):
        return SOURCE

    def get_citations(self, work_id, *, direction):
        return list(self._out if direction == "out" else self._in)

    def works_in_topic(self, topic_id, *, sort="cited_by_count:desc", per_page=25, extra_filter=None):
        return list(self._topic)

    def search_works(self, query, *, mode="keyword", per_page=10, filters=None):
        return list(self._semantic)


# ---- mapping ----

def test_abstract_inverted_index_rebuilds_prose():
    assert mapping.abstract_text({"Attention": [0], "is": [1], "all": [2]}) == "Attention is all"
    assert mapping.abstract_text(None) is None


def test_short_id_and_preview():
    assert mapping.short_id("https://openalex.org/W123") == "W123"
    p = mapping.to_paper_preview(SOURCE)
    assert p["openalexId"] == "W1"
    assert p["citedByCount"] == 100000
    assert p["authors"] == ["A. Author"]


# ---- Broader vs Deeper must use DIFFERENT logic (PRD §13) ----

def test_broader_prefers_foundational_survey_over_recent_specific():
    c = FakeClient(out=[SURVEY], topic=[SURVEY, NEW_SPECIFIC])
    out = rec.recommend(openalex_id="W1", mode="broader", client=c)
    assert out, "broader should return candidates"
    assert out[0]["paper"]["openalexId"] == "W2"
    assert out[0]["mode"] == "broader"


def test_deeper_prefers_recent_specific_over_survey():
    c = FakeClient(inc=[NEW_SPECIFIC], topic=[SURVEY, NEW_SPECIFIC])
    out = rec.recommend(openalex_id="W1", mode="deeper", client=c)
    assert out, "deeper should return candidates"
    assert out[0]["paper"]["openalexId"] == "W3"
    assert out[0]["mode"] == "deeper"


def test_same_pool_ranks_oppositely_by_mode():
    # The discriminating test: identical candidates, opposite winners.
    c = FakeClient(out=[SURVEY, NEW_SPECIFIC], inc=[SURVEY, NEW_SPECIFIC],
                   topic=[SURVEY, NEW_SPECIFIC])
    broader = rec.recommend(openalex_id="W1", mode="broader", client=c)
    deeper = rec.recommend(openalex_id="W1", mode="deeper", client=c)
    assert broader[0]["paper"]["openalexId"] != deeper[0]["paper"]["openalexId"]


def test_source_and_excluded_never_recommended():
    c = FakeClient(topic=[SOURCE, SURVEY, NEW_SPECIFIC])
    out = rec.recommend(openalex_id="W1", mode="broader", client=c, exclude_ids={"W2"})
    ids = {r["paper"]["openalexId"] for r in out}
    assert "W1" not in ids  # never recommend the anchor back to itself
    assert "W2" not in ids  # suppression list honoured


def test_offset_pages_without_repeating():
    c = FakeClient(topic=[SURVEY, NEW_SPECIFIC])
    first = rec.recommend(openalex_id="W1", mode="broader", client=c, count=1, offset=0)
    second = rec.recommend(openalex_id="W1", mode="broader", client=c, count=1, offset=1)
    assert first[0]["paper"]["openalexId"] != second[0]["paper"]["openalexId"]


def test_recommendation_carries_label_and_reason():
    c = FakeClient(out=[SURVEY], topic=[SURVEY])
    r = rec.recommend(openalex_id="W1", mode="broader", client=c)[0]
    assert r["relationshipLabel"]
    assert r["reason"]
    assert isinstance(r["score"], float)


def test_pdf_url_prefers_any_oa_pdf_then_arxiv_and_never_a_landing_page():
    from openalex import mapping

    # A pdf on a non-primary location still counts.
    assert mapping.pdf_url({
        "best_oa_location": {"landing_page_url": "https://example.com/abs/1"},
        "locations": [{"pdf_url": "https://example.com/paper.pdf"}],
    }) == "https://example.com/paper.pdf"

    # arXiv landing pages are mechanically turned into the pdf.
    assert mapping.pdf_url({
        "best_oa_location": {"landing_page_url": "https://arxiv.org/abs/1706.03762v5"},
    }) == "https://arxiv.org/pdf/1706.03762"

    # An HTML landing page is worse than nothing: the node shows the abstract.
    assert mapping.pdf_url({
        "open_access": {"oa_url": "https://journal.example.org/article/view/42"},
    }) is None
