"""Tests for motion notification backends and the manager."""

import json

from motion_detector.config.defaults import NotificationConfig
from motion_detector.utils import notifier as notifier_mod
from motion_detector.utils.notifier import (
    NotificationManager,
    NullNotifier,
    TelegramNotifier,
    WebhookNotifier,
    create_notifier,
)


class _FakeResponse:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _capture_urlopen(monkeypatch, status=200):
    """Patch urlopen and record the request that was sent."""
    calls = {}

    def fake_urlopen(request, timeout=None):
        calls["url"] = request.full_url
        calls["data"] = request.data
        calls["timeout"] = timeout
        return _FakeResponse(status)

    monkeypatch.setattr(notifier_mod.urllib.request, "urlopen", fake_urlopen)
    return calls


def test_create_notifier_none_returns_null():
    assert isinstance(create_notifier(NotificationConfig()), NullNotifier)


def test_create_notifier_webhook_without_url_disables():
    cfg = NotificationConfig(enabled=True, backend="webhook", webhook_url="")
    assert isinstance(create_notifier(cfg), NullNotifier)


def test_create_notifier_telegram_requires_credentials():
    cfg = NotificationConfig(enabled=True, backend="telegram", telegram_bot_token="x")
    assert isinstance(create_notifier(cfg), NullNotifier)


def test_webhook_posts_json_payload(monkeypatch):
    calls = _capture_urlopen(monkeypatch)
    ok = WebhookNotifier("https://example.test/hook").send("Motion", "Area: 1200")
    assert ok is True
    assert calls["url"] == "https://example.test/hook"
    body = json.loads(calls["data"].decode())
    assert body == {"title": "Motion", "message": "Area: 1200", "snapshot": None}


def test_webhook_returns_false_on_error_status(monkeypatch):
    _capture_urlopen(monkeypatch, status=500)
    assert WebhookNotifier("https://example.test/hook").send("t", "m") is False


def test_telegram_targets_bot_api(monkeypatch):
    calls = _capture_urlopen(monkeypatch)
    ok = TelegramNotifier("BOTTOKEN", "12345").send("Motion", "hello")
    assert ok is True
    assert "api.telegram.org/botBOTTOKEN/sendMessage" in calls["url"]
    assert b"chat_id=12345" in calls["data"]


def test_telegram_send_photo_uses_multipart(monkeypatch, tmp_path):
    image = tmp_path / "shot.jpg"
    image.write_bytes(b"\xff\xd8\xff\xe0FAKEJPEGDATA")
    calls = _capture_urlopen(monkeypatch)

    ok = TelegramNotifier("TOK", "42").send("Motion", "hi", str(image))

    assert ok is True
    assert "sendPhoto" in calls["url"]
    assert b"FAKEJPEGDATA" in calls["data"]
    assert b'name="photo"; filename="shot.jpg"' in calls["data"]


def test_telegram_falls_back_to_text_when_image_missing(monkeypatch):
    calls = _capture_urlopen(monkeypatch)
    TelegramNotifier("TOK", "42").send("Motion", "hi", "/nonexistent/none.jpg")
    assert "sendMessage" in calls["url"]


def test_manager_omits_snapshot_when_disabled(monkeypatch, tmp_path):
    image = tmp_path / "shot.jpg"
    image.write_bytes(b"data")
    calls = _capture_urlopen(monkeypatch)
    cfg = NotificationConfig(
        enabled=True,
        backend="telegram",
        telegram_bot_token="TOK",
        telegram_chat_id="42",
        include_snapshot=False,
        min_interval=0,
    )
    NotificationManager(cfg).notify_motion(1000, 2, str(image))
    # Snapshot suppressed -> text endpoint, not sendPhoto.
    assert "sendMessage" in calls["url"]


def test_manager_disabled_never_sends(monkeypatch):
    calls = _capture_urlopen(monkeypatch)
    manager = NotificationManager(NotificationConfig(enabled=False))
    assert manager.notify_motion(1000, 2) is False
    assert calls == {}


def test_manager_rate_limits(monkeypatch):
    _capture_urlopen(monkeypatch)
    cfg = NotificationConfig(
        enabled=True, backend="webhook", webhook_url="https://x.test", min_interval=999
    )
    manager = NotificationManager(cfg)
    assert manager.notify_motion(1000, 2) is True
    # Second call within the interval is suppressed.
    assert manager.notify_motion(1000, 2) is False


def test_manager_sends_again_after_interval(monkeypatch):
    _capture_urlopen(monkeypatch)
    cfg = NotificationConfig(
        enabled=True, backend="webhook", webhook_url="https://x.test", min_interval=0
    )
    manager = NotificationManager(cfg)
    assert manager.notify_motion(1000, 2) is True
    assert manager.notify_motion(1000, 2) is True
    assert manager.backend_name == "webhook"
