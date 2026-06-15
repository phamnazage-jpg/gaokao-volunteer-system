from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass(frozen=True)
class SMTPSettings:
    host: str
    port: int
    sender: str
    username: str = ""
    password: str = ""
    use_tls: bool = False
    use_ssl: bool = False


class SMTPDeliverySender:
    def __init__(self, settings: SMTPSettings) -> None:
        self._settings = settings

    def send_report_ready(
        self,
        *,
        recipient: str,
        order_id: str,
        subject: str,
        body: str,
    ) -> dict[str, str]:
        if not self._settings.host:
            raise ValueError("smtp host not configured")
        if not self._settings.sender:
            raise ValueError("smtp sender not configured")
        message = EmailMessage()
        message["From"] = self._settings.sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        if self._settings.use_ssl:
            client: smtplib.SMTP = smtplib.SMTP_SSL(
                self._settings.host,
                self._settings.port,
                timeout=10,
            )
        else:
            client = smtplib.SMTP(
                self._settings.host,
                self._settings.port,
                timeout=10,
            )
        with client:
            if self._settings.use_tls:
                client.starttls()
            if self._settings.username:
                client.login(self._settings.username, self._settings.password)
            client.send_message(message)
        return {
            "recipient": recipient,
            "order_id": order_id,
            "subject": subject,
            "body": body,
        }
