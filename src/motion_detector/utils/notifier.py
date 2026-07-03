"""
Motion Notifications

Delivers an alert when motion is detected. Backends are pluggable and
dependency-free (they use the standard-library ``urllib``), so no extra
packages are required:

* ``webhook``  - HTTP POST of a JSON payload to a configured URL.
* ``telegram`` - a message via the Telegram Bot API.
* ``none``     - a no-op used when notifications are disabled.

``NotificationManager`` owns backend selection and rate-limiting so the
detector only has to call :meth:`NotificationManager.notify_motion`.
"""

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Optional, Tuple

_MULTIPART_BOUNDARY = "----motiondetectorboundary7MA4YWxkTrZu0gW"


def _encode_multipart(
    fields: dict, file_field: str, filename: str, file_bytes: bytes
) -> Tuple[bytes, str]:
    """Build a multipart/form-data body for a file upload.

    Returns the encoded body and the matching Content-Type header value.
    """
    boundary = _MULTIPART_BOUNDARY
    parts = []
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())

    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode()
    )
    parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
    parts.append(file_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode())

    body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


class Notifier(ABC):
    """Interface for a single notification delivery backend."""

    name = "base"

    def __init__(self, logger: Optional[logging.Logger] = None, timeout: float = 5.0):
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = timeout

    @abstractmethod
    def send(self, title: str, message: str, image_path: Optional[str] = None) -> bool:
        """Deliver a notification, optionally attaching an image.

        Backends that cannot attach an image simply ignore ``image_path``.
        """

    def _post(self, url: str, data: bytes, headers: dict) -> bool:
        """POST ``data`` to ``url``; return True on a 2xx response."""
        request = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                return 200 <= status < 300
        except Exception as exc:
            self.logger.warning(f"{self.name} notification failed: {exc}")
            return False


class NullNotifier(Notifier):
    """No-op backend used when notifications are disabled."""

    name = "none"

    def send(self, title: str, message: str, image_path: Optional[str] = None) -> bool:
        return True


class WebhookNotifier(Notifier):
    """POST a JSON payload to an arbitrary webhook URL."""

    name = "webhook"

    def __init__(self, url: str, logger: Optional[logging.Logger] = None, timeout: float = 5.0):
        super().__init__(logger, timeout)
        self.url = url

    def send(self, title: str, message: str, image_path: Optional[str] = None) -> bool:
        # The snapshot path is included in the JSON; binary upload is left to
        # the Telegram backend where the API is well defined.
        payload = json.dumps(
            {"title": title, "message": message, "snapshot": image_path}
        ).encode("utf-8")
        return self._post(self.url, payload, {"Content-Type": "application/json"})


class TelegramNotifier(Notifier):
    """Send a message through the Telegram Bot API."""

    name = "telegram"

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        logger: Optional[logging.Logger] = None,
        timeout: float = 5.0,
    ):
        super().__init__(logger, timeout)
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, title: str, message: str, image_path: Optional[str] = None) -> bool:
        if image_path and os.path.exists(image_path):
            return self._send_photo(title, message, image_path)
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = urllib.parse.urlencode(
            {"chat_id": self.chat_id, "text": f"{title}\n{message}"}
        ).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return self._post(url, data, headers)

    def _send_photo(self, title: str, message: str, image_path: str) -> bool:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        try:
            with open(image_path, "rb") as fh:
                image_bytes = fh.read()
        except OSError as exc:
            self.logger.warning(f"Could not read snapshot {image_path}: {exc}")
            return False

        fields = {"chat_id": self.chat_id, "caption": f"{title}\n{message}"}
        body, content_type = _encode_multipart(
            fields, "photo", os.path.basename(image_path), image_bytes
        )
        return self._post(url, body, {"Content-Type": content_type})


def create_notifier(config, logger: Optional[logging.Logger] = None) -> Notifier:
    """Build the notifier selected by ``config.backend``.

    Falls back to :class:`NullNotifier` for the "none" backend or when a
    backend is misconfigured (e.g. a webhook with no URL).
    """
    logger = logger or logging.getLogger(__name__)
    backend = getattr(config, "backend", "none")

    if backend == "webhook":
        if not config.webhook_url:
            logger.warning("Webhook notifier enabled but webhook_url is empty; disabling")
            return NullNotifier(logger)
        return WebhookNotifier(config.webhook_url, logger)

    if backend == "telegram":
        if not (config.telegram_bot_token and config.telegram_chat_id):
            logger.warning("Telegram notifier enabled but token/chat_id missing; disabling")
            return NullNotifier(logger)
        return TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id, logger)

    return NullNotifier(logger)


class NotificationManager:
    """Selects a notifier and rate-limits motion alerts."""

    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = bool(getattr(config, "enabled", False))
        self.min_interval = float(getattr(config, "min_interval", 30.0))
        self.include_snapshot = bool(getattr(config, "include_snapshot", True))
        self._last_sent = 0.0
        self._notifier = create_notifier(config, self.logger) if self.enabled else NullNotifier()

    @property
    def backend_name(self) -> str:
        return self._notifier.name

    def notify_motion(
        self, area: float, contour_count: int, filepath: Optional[str] = None
    ) -> bool:
        """Send a motion alert, respecting the configured minimum interval.

        Returns:
            bool: True if a notification was actually sent.
        """
        if not self.enabled:
            return False

        now = time.time()
        if now - self._last_sent < self.min_interval:
            return False

        title = "Motion detected"
        message = f"Area: {area:.0f}, contours: {contour_count}"

        image_path = filepath if self.include_snapshot else None
        sent = self._notifier.send(title, message, image_path)
        if sent:
            self._last_sent = now
        return sent
