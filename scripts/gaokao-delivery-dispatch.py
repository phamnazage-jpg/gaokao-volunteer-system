from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from admin.config import load_settings
    from data.notifications.dispatcher import DeliveryDispatcher
    from data.notifications.smtp_sender import SMTPDeliverySender, SMTPSettings

    parser = argparse.ArgumentParser(
        description="Dispatch delivery notification events"
    )
    parser.add_argument("--channel", default="station")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    settings = load_settings()
    email_sender = None
    if args.channel == "email" and settings.smtp_host:
        email_sender = SMTPDeliverySender(
            SMTPSettings(
                host=settings.smtp_host,
                port=settings.smtp_port,
                sender=settings.smtp_sender,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
                use_ssl=settings.smtp_use_ssl,
            )
        )
    dispatcher = DeliveryDispatcher.for_db(
        settings.orders_db_path,
        email_sender=email_sender,
    )
    try:
        result = dispatcher.dispatch_ready_events(
            channel=args.channel, limit=args.limit
        )
    finally:
        dispatcher.close()
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
