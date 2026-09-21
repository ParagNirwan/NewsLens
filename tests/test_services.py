from backend.app.services import classify, relevance_score, UNSUITABLE_SOURCE_HOSTS
from backend.app.models import Source
from backend.app.models import SourceType
def test_primary_source_classification(): assert classify("https://www.destatis.de/example") == SourceType.PRIMARY
def test_news_source_classification(): assert classify("https://www.reuters.com/example") == SourceType.NEWS

def test_relevance_score_rejects_unrelated_result():
    source = Source(id="1", title="Volvo vehicle demonstration", url="https://example.com", publisher="Example", excerpt="A car safety story.")
    assert relevance_score("What happened regarding Germany migration legislation?", source) == 0

def test_social_media_is_not_an_inspected_news_source():
    assert "facebook.com" in UNSUITABLE_SOURCE_HOSTS
