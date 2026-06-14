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

    parser = argparse.ArgumentParser(description="Watch delivery dispatch health")
    parser.add_argument("--channel", default="station")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    settings = load_settings()
    dispatcher = DeliveryDispatcher.for_db(settings.orders_db_path)
    try:
        result = dispatcher.dispatch_ready_events(
            channel=args.channel, limit=args.limit
        )
    finally:
        dispatcher.close()

    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 2 if result.failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
