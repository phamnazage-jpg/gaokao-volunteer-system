from __future__ import annotations

import sys
import threading
import time
from typing import cast

import pytest

from data.notifications.smtp_sender import SMTPDeliverySender, SMTPSettings


@pytest.mark.skipif(
    sys.version_info >= (3, 12), reason="stdlib smtpd/asyncore removed in Python 3.12+"
)
def test_smtp_delivery_sender_sends_message_over_local_stub():
    import asyncore
    import smtpd

    class _CapturingSMTPServer(smtpd.SMTPServer):
        def __init__(self, localaddr, remoteaddr):
            super().__init__(localaddr, remoteaddr)
            self.messages: list[dict[str, object]] = []

        def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
            self.messages.append({
                "peer": peer,
                "mailfrom": mailfrom,
                "rcpttos": rcpttos,
                "data": data,
            })
            return None

    server = _CapturingSMTPServer(("127.0.0.1", 0), None)
    port = server.socket.getsockname()[1]
    thread = threading.Thread(
        target=asyncore.loop, kwargs={"timeout": 0.1}, daemon=True
    )
    thread.start()
    try:
        sender = SMTPDeliverySender(
            SMTPSettings(
                host="127.0.0.1",
                port=port,
                sender="noreply@example.com",
            )
        )
        result = sender.send_report_ready(
            recipient="parent@example.com",
            order_id="GKO-EMAIL-STUB",
            subject="报告已就绪",
            body="请查看 portal。",
        )
        deadline = time.time() + 2
        while time.time() < deadline and not server.messages:
            time.sleep(0.05)
        assert server.messages, "stub smtp server did not receive message"
        assert result["recipient"] == "parent@example.com"
        raw = cast(bytes, server.messages[0]["data"])
        assert b"Subject: =?utf-8?" in raw or b"Subject: " in raw
        assert b"parent@example.com" in raw
    finally:
        server.close()
