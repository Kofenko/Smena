"""Фоновый сервис Android: следит за открытой сменой и шлёт уведомления."""
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.model import Store, alert_text  # noqa: E402
import notifier  # noqa: E402


def main():
    arg = json.loads(os.environ.get("PYTHON_SERVICE_ARGUMENT") or "{}")
    folder = arg.get("data")
    if not folder:
        return
    while True:
        store = Store(folder)
        if store.open_start is None or not store.settings.notify:
            break
        now = datetime.now()
        for h in store.due_alerts(now):
            notifier.send(*alert_text(h, store.open_start), nid=100 + h)
            for hh in (8, 12):
                if hh <= h:
                    store.mark_notified(store.open_start, hh)
        if 12 in store.notified().get(store.open_start.strftime("%Y-%m-%dT%H:%M"), []):
            break
        time.sleep(30)


try:
    main()
finally:
    try:
        from jnius import autoclass
        autoclass("org.kivy.android.PythonService").mService.stopSelf()
    except Exception:
        pass
