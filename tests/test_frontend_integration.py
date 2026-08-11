from pathlib import Path


def test_frontend_has_live_media_and_analytics_hooks():
    root = Path(__file__).parent.parent
    analytics_page = (root / "frontend" / "analytics.html").read_text(encoding="utf-8")
    dashboard_page = (root / "frontend" / "index.html").read_text(encoding="utf-8")

    assert "analytics-activity" in analytics_page
    assert "API.Analytics" in analytics_page
    assert "media-upload-form" in dashboard_page
    assert "media-list" in dashboard_page
    assert "API.Media.upload" in dashboard_page
