import os
import sys
import tempfile
import unittest
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.model import Store, add_months, hhmm, is_night, split_by_day  # noqa: E402


def dt(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


class ModelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_hhmm(self):
        self.assertEqual(hhmm(510), "08:30")
        self.assertEqual(hhmm(0), "00:00")
        self.assertEqual(hhmm(1505), "25:05")

    def test_check_in_out_and_persist(self):
        self.store.check_in(dt("2026-11-19 08:00"))
        sh = self.store.check_out(dt("2026-11-19 16:30"))
        self.assertEqual(sh.minutes(None), 510)
        again = Store(self.tmp.name)
        self.assertEqual(len(again.shifts), 1)
        self.assertIsNone(again.open_start)

    def test_split_midnight(self):
        parts = split_by_day(dt("2026-11-19 22:45"), dt("2026-11-20 07:00"))
        self.assertEqual(parts, {date(2026, 11, 19): 75, date(2026, 11, 20): 420})

    def test_night_rules(self):
        self.assertTrue(is_night(dt("2026-11-19 22:30"), dt("2026-11-19 23:00")))
        self.assertTrue(is_night(dt("2026-11-19 15:00"), dt("2026-11-19 23:00")))
        self.assertFalse(is_night(dt("2026-11-19 15:00"), dt("2026-11-19 22:30")))
        self.assertFalse(is_night(dt("2026-11-19 08:00"), dt("2026-11-19 17:00")))
        self.assertTrue(is_night(dt("2026-11-20 02:00"), dt("2026-11-20 06:00")))

    def test_night_marks_both_days_and_month_split(self):
        self.store.check_in(dt("2026-11-30 23:00"))
        self.store.check_out(dt("2026-12-01 07:00"))
        dm = self.store.day_map(dt("2026-12-01 12:00"))
        self.assertTrue(dm[date(2026, 11, 30)].night)
        self.assertTrue(dm[date(2026, 12, 1)].night)
        nov = self.store.month_summary(2026, 11, dt("2026-12-01 12:00"))
        dec = self.store.month_summary(2026, 12, dt("2026-12-01 12:00"))
        self.assertEqual(nov["minutes"], 60)
        self.assertEqual(dec["minutes"], 420)

    def test_two_shifts_one_day(self):
        for a, b in (("08:00", "12:00"), ("13:00", "17:30")):
            self.store.check_in(dt("2026-11-19 " + a))
            self.store.check_out(dt("2026-11-19 " + b))
        info = self.store.day_map(dt("2026-11-19 18:00"))[date(2026, 11, 19)]
        self.assertEqual(info.minutes, 510)
        self.assertEqual(len(info.shifts), 2)

    def test_open_shift_counts_live(self):
        self.store.settings.rate = 10
        self.store.check_in(dt("2026-11-19 08:00"))
        s = self.store.month_summary(2026, 11, dt("2026-11-19 10:00"))
        self.assertEqual(s["minutes"], 120)
        self.assertAlmostEqual(s["money"], 20)

    def test_alerts(self):
        self.store.check_in(dt("2026-11-19 08:00"))
        self.assertEqual(self.store.due_alerts(dt("2026-11-19 15:59")), [])
        self.assertEqual(self.store.due_alerts(dt("2026-11-19 16:00")), [8])
        self.store.mark_notified(self.store.open_start, 8)
        self.assertEqual(self.store.due_alerts(dt("2026-11-19 17:00")), [])
        self.assertEqual(self.store.due_alerts(dt("2026-11-19 20:00")), [12])
        self.store.settings.notify = False
        self.assertEqual(self.store.due_alerts(dt("2026-11-19 20:00")), [])

    def test_add_months(self):
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(add_months(date(2026, 12, 15), 1), date(2027, 1, 15))
        self.assertEqual(add_months(date(2026, 1, 15), -1), date(2025, 12, 15))

    def test_delete(self):
        self.store.check_in(dt("2026-11-19 08:00"))
        sh = self.store.check_out(dt("2026-11-19 09:00"))
        self.store.delete(sh)
        self.assertEqual(self.store.shifts, [])


if __name__ == "__main__":
    unittest.main()
