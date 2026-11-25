import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
for v in ("HF_TOKEN", "HUGGINGFACE_API_KEY", "IG_ACCESS_TOKEN", "APIFY_TOKEN", "IG_USER_ID", "KV_REST_API_URL", "UPSTASH_REDIS_REST_URL"):
    os.environ.pop(v, None)

from fastapi.testclient import TestClient  # noqa: E402

from api.index import app  # noqa: E402
from backend.reelsense.errors import InvalidUrl, UnsupportedReel  # noqa: E402
from backend.reelsense.nlp.analytics import is_question  # noqa: E402
from backend.reelsense.nlp.text import detect_language  # noqa: E402
from backend.reelsense.utils import extract_shortcode  # noqa: E402

client = TestClient(app)


@pytest.fixture(scope="module")
def demo():
    r = client.post("/api/analyze", json={"mode": "demo"})
    assert r.status_code == 200, r.text
    return r.json()


def test_url_validation():
    assert extract_shortcode("https://www.instagram.com/reel/C9abcDEF123/?igsh=x") == "C9abcDEF123"
    with pytest.raises(InvalidUrl):
        extract_shortcode("https://example.com/reel/abc123")
    with pytest.raises(InvalidUrl):
        extract_shortcode("")
    with pytest.raises(UnsupportedReel):
        extract_shortcode("https://www.instagram.com/stories/foo/12345/")


def test_language_detection():
    assert detect_language("बहुत बढ़िया वीडियो")[0] == "hi"
    assert detect_language("ખૂબ સરસ વીડિયો")[0] == "gu"
    assert detect_language("Bhai ekdum mast review hai")[0] == "hinglish"
    assert detect_language("Great video, loved it")[0] == "en"
    assert detect_language("🔥🔥🔥")[0] == "emoji"


def test_questions():
    assert is_question("Where can I buy this?")
    assert is_question("Iski price kitni hai")
    assert is_question("આની કિંમત કેટલી છે?")
    assert not is_question("Great video")


def test_demo_shape(demo):
    assert demo["is_demo"] and demo["summary"]["fetched"] >= 100
    langs = {c["language"] for c in demo["comments"]}
    assert {"English", "Hindi", "Gujarati", "Hinglish", "Emoji"} <= langs
    s = demo["sentiment"]["counts"]
    assert sum(s.values()) == demo["summary"]["analyzed"]
    assert all(c["sentiment"] in ("positive", "negative", "neutral") for c in demo["comments"])
    assert all(c["emotion"] in ("Happy", "Excited", "Angry", "Sad", "Frustrated", "Neutral") for c in demo["comments"])
    assert demo["summary"]["spam"] >= 5 and demo["summary"]["duplicates"] >= 2
    assert demo["nlp"]["faqs"] and demo["nlp"]["keywords"] and demo["nlp"]["aspects"]
    assert demo["nlp"]["topics"]["available"]
    assert demo["insights"]["executive_summary"]
    # formula
    k = demo["kpis"]
    assert k["engagement_rate"] == round((12847 + 1284) / 184320 * 100, 2)
    # original text preserved
    assert any(c["text"] == "बहुत बढ़िया वीडियो, मज़ा आ गया!" for c in demo["comments"])


def test_demo_sentiment_sane(demo):
    by = {c["text"]: c for c in demo["comments"]}
    assert by["Best creator on my feed, never disappoints"]["sentiment"] == "positive"
    assert by["Way too expensive for what you get. Not worth it"]["sentiment"] == "negative"


def test_engagement_missing_values():
    from backend.reelsense.engagement import engagement_rate
    assert engagement_rate({"views": None, "likes": 5, "comments_count": 2})[0] is None
    assert engagement_rate({"views": 100, "likes": 5, "comments_count": 5})[0] == 10.0


def test_live_without_credentials():
    r = client.post("/api/analyze", json={"mode": "live", "url": "https://www.instagram.com/reel/ABCDE12345/"})
    assert r.status_code == 503
    e = r.json()["error"]
    assert e["code"] == "credentials_missing" and e["can_use_demo"]


def test_live_invalid_and_missing_url():
    r = client.post("/api/analyze", json={"mode": "live", "url": "https://foo.com/x"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_url"
    assert client.post("/api/analyze", json={"mode": "live"}).status_code == 422


def test_stream():
    with client.stream("POST", "/api/analyze", json={"mode": "demo", "stream": True}) as r:
        events = [json.loads(l) for l in r.iter_lines() if l]
    assert events[0]["type"] == "progress" and events[-1]["type"] == "result"
    pcts = [e["percent"] for e in events if e["type"] == "progress"]
    assert pcts == sorted(pcts) and pcts[-1] >= 90
    with client.stream("POST", "/api/analyze", json={"mode": "live", "url": "https://www.instagram.com/reel/ABCDE12345/", "stream": True}) as r:
        ev = [json.loads(l) for l in r.iter_lines() if l]
    assert ev[-1]["type"] == "error"


def test_get_endpoints(demo):
    aid = demo["id"]
    assert client.get(f"/api/analysis/{aid}").json()["id"] == aid
    c = client.get(f"/api/analysis/{aid}/comments", params={"sentiment": "negative", "page_size": 5, "sort": "likes"}).json()
    assert c["total"] > 0 and all(i["sentiment"] == "negative" for i in c["items"]) and len(c["items"]) <= 5
    c2 = client.get(f"/api/analysis/{aid}/comments", params={"language": "Hindi"}).json()
    assert c2["total"] > 0
    assert client.get(f"/api/analysis/{aid}/insights").json()["insights"]["next_content_ideas"]
    assert client.get("/api/analysis/nope").status_code == 404


@pytest.mark.parametrize("fmt,magic", [("csv", b"\xef\xbb\xbf"), ("excel", b"PK"), ("pdf", b"%PDF")])
def test_exports(demo, fmt, magic):
    r = client.get(f"/api/analysis/{demo['id']}/export/{fmt}")
    assert r.status_code == 200 and r.content.startswith(magic) and len(r.content) > 500
    r2 = client.post(f"/api/export/{fmt}", content=json.dumps(demo), headers={"content-type": "application/json"})
    assert r2.status_code == 200 and r2.content.startswith(magic)


def test_health():
    h = client.get("/api/health").json()
    assert h["status"] == "ok"


def test_apify_provider_live_flow(monkeypatch):
    from backend.reelsense.pipeline import run_analysis
    from backend.reelsense.providers.apify import ApifyProvider
    monkeypatch.setenv("APIFY_TOKEN", "apify_test")

    def fake_run(self, actor, body, timeout_s):
        assert body.get("username") == ["https://www.instagram.com/reel/ABCDE12345/"] or body.get("directUrls") == ["https://www.instagram.com/reel/ABCDE12345/"]
        if "reel" in actor:
            return [{"url": "https://www.instagram.com/reel/ABCDE12345/", "shortCode": "ABCDE12345", "id": "1", "ownerUsername": "someone",
                     "caption": "hi #x", "videoPlayCount": 1000, "likesCount": 100, "commentsCount": 20, "videoDuration": 12.5,
                     "timestamp": "2026-11-01T10:00:00.000Z", "displayUrl": "https://x/y.jpg"}]
        return [{"id": str(i), "text": t, "ownerUsername": f"u{i}", "timestamp": f"2026-11-0{1 + i % 5}T10:00:00.000Z", "likesCount": i, "repliesCount": 0}
                for i, t in enumerate(["Great video, loved it", "Terrible audio, waste of time", "Where can I buy this?"] * 6)] + [
                {"id": "0", "text": "dup id", "ownerUsername": "z"}]

    monkeypatch.setattr(ApifyProvider, "_run", fake_run)
    a = run_analysis("live", "https://www.instagram.com/reel/ABCDE12345/?igsh=zzz")
    assert not a["is_demo"] and a["provider"] == "apify-instagram"
    assert a["kpis"]["views"] == 1000 and a["kpis"]["engagement_rate"] == 12.0
    assert a["summary"]["fetched"] == 18  # duplicate id dropped


def test_apify_private_reel(monkeypatch):
    from backend.reelsense.providers.apify import ApifyProvider
    monkeypatch.setenv("APIFY_TOKEN", "apify_test")
    monkeypatch.setattr(ApifyProvider, "_run", lambda self, a, b, t: [])
    monkeypatch.undo  # noqa
    r = client.post("/api/analyze", json={"mode": "live", "url": "https://www.instagram.com/reel/ABCDE12345/"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "unsupported_reel"


def test_token_via_header(monkeypatch):
    from backend.reelsense.providers.apify import ApifyProvider
    seen = {}
    def fake_run(self, actor, body, t):
        seen["tok"] = self.token
        return []
    monkeypatch.setattr(ApifyProvider, "_run", fake_run)
    r = client.post("/api/analyze", json={"mode": "live", "url": "https://www.instagram.com/reel/ABCDE12345/"}, headers={"X-Apify-Token": "apify_api_abc"})
    assert seen["tok"] == "apify_api_abc" and r.status_code == 422
    assert client.post("/api/apify/verify").status_code == 503

