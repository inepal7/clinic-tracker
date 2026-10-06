"""Unit tests for queries.py, using a tiny hand-built in-memory database."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database
import queries

TODAY = "2026-10-06"


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.conn = database.connect(":memory:")
        database.init_db(self.conn)
        c = self.conn
        c.executemany(
            "INSERT INTO patients (patient_id, first_name, last_name, date_of_birth) "
            "VALUES (?, ?, ?, ?)",
            [(1, "Ann", "A", "1980-01-01"), (2, "Ben", "B", "1975-05-05"),
             (3, "Cara", "C", "1990-09-09")],
        )
        c.executemany(
            "INSERT INTO providers (provider_id, name, specialty) VALUES (?, ?, ?)",
            [(1, "Dr. One", "Family"), (2, "Dr. Two", "Cardiology")],
        )
        self.add_appt(1, 1, 1, "2026-06-01", "completed")   # Ann: follow-up needed
        self.add_appt(2, 2, 1, "2026-06-02", "completed")   # Ben: follow-up needed
        self.add_appt(3, 2, 1, "2026-10-20", "scheduled")   # Ben already rebooked
        self.add_appt(4, 3, 1, "2026-06-03", "completed")   # Cara: follow-up in future
        self.add_appt(5, 1, 1, "2026-07-01", "no_show")
        self.add_appt(6, 3, 2, "2026-07-02", "completed")
        self.add_appt(7, 3, 2, "2026-07-03", "cancelled")
        self.add_appt(8, 3, 2, "2026-11-05", "scheduled")
        self.add_visit(1, 1, "2026-08-01")   # overdue, no later completed/scheduled appt
        self.add_visit(2, 2, "2026-08-01")   # not overdue: rebooked
        self.add_visit(3, 4, "2026-12-01")   # not overdue: deadline in the future
        c.commit()

    def add_appt(self, appt_id, patient_id, provider_id, appt_date, status):
        self.conn.execute(
            "INSERT INTO appointments VALUES (?, ?, ?, ?, ?, 'Checkup')",
            (appt_id, patient_id, provider_id, appt_date, status),
        )

    def add_visit(self, visit_id, appt_id, follow_up_by):
        self.conn.execute(
            "INSERT INTO visits VALUES (?, ?, 'note', 1, ?)",
            (visit_id, appt_id, follow_up_by),
        )

    def test_overdue_followups_only_returns_unbooked_past_due(self):
        rows = queries.overdue_followups(self.conn, TODAY)
        self.assertEqual([r["patient_id"] for r in rows], [1])
        self.assertEqual(rows[0]["days_overdue"], 66)

    def test_no_show_rate_ignores_cancelled_and_scheduled(self):
        rows = {r["provider"]: r for r in queries.no_show_rate_by_provider(self.conn)}
        # Dr. One: 3 completed + 1 no-show = 4 visits, 25.0%
        self.assertEqual(rows["Dr. One"]["total_visits"], 4)
        self.assertEqual(rows["Dr. One"]["no_show_pct"], 25.0)
        # Dr. Two: 1 completed (the cancelled one is excluded), 0%
        self.assertEqual(rows["Dr. Two"]["no_show_pct"], 0.0)

    def test_upcoming_is_sorted_and_only_scheduled_future(self):
        rows = queries.upcoming_appointments(self.conn, TODAY)
        self.assertEqual([r["appointment_date"] for r in rows], ["2026-10-20", "2026-11-05"])

    def test_upcoming_can_filter_by_provider(self):
        rows = queries.upcoming_appointments(self.conn, TODAY, provider_id=2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["provider"], "Dr. Two")

    def test_monthly_counts(self):
        rows = {r["month"]: r for r in queries.appointments_per_month(self.conn)}
        self.assertEqual(rows["2026-06"]["total"], 3)
        self.assertEqual(rows["2026-07"]["no_show"], 1)
        self.assertEqual(rows["2026-07"]["cancelled"], 1)

    def test_patient_history_newest_first(self):
        rows = queries.patient_history(self.conn, 1)
        dates = [r["appointment_date"] for r in rows]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_status_check_constraint_rejects_bad_values(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.add_appt(99, 1, 1, "2026-09-01", "maybe")

    def test_frequent_no_shows(self):
        # Ann already has 1 no-show from setUp; add 2 more for a total of 3.
        self.add_appt(20, 1, 1, "2026-08-10", "no_show")
        self.add_appt(21, 1, 1, "2026-08-11", "no_show")
        self.conn.commit()
        rows = queries.frequent_no_shows(self.conn, 2)
        self.assertEqual([r["patient_id"] for r in rows], [1])
        self.assertEqual(rows[0]["no_shows"], 3)
        # Nobody has MORE than 3, so a threshold of 3 returns nothing.
        self.assertEqual(queries.frequent_no_shows(self.conn, 3), [])


if __name__ == "__main__":
    unittest.main()