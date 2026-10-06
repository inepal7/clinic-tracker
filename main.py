"""Command-line interface for the Clinic Appointment Tracker.

Examples:
    python main.py init
    python main.py upcoming --limit 5
    python main.py overdue
    python main.py noshows
    python main.py monthly
    python main.py history 12
"""
import argparse
import sys
from datetime import date
from pathlib import Path

import database
import queries
import seed_data

DEFAULT_DB = "clinic.db"


def print_table(rows, headers):
    """Print rows as an aligned text table."""
    if not rows:
        print("No results.")
        return
    data = [[str(row[h]) for h in headers] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in data)) for i, h in enumerate(headers)]
    line = "  ".join(h.upper().ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("  ".join("-" * w for w in widths))
    for r in data:
        print("  ".join(cell.ljust(w) for cell, w in zip(r, widths)))
    print(f"\n{len(data)} row(s)")


def build_parser():
    parser = argparse.ArgumentParser(description="Clinic Appointment Tracker (synthetic data)")
    parser.add_argument("--db", default=DEFAULT_DB, help="path to the SQLite database file")
    parser.add_argument("--today", default=None,
                        help="override today's date (YYYY-MM-DD), useful for repeatable demos")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create a fresh database filled with synthetic data")

    p = sub.add_parser("upcoming", help="list upcoming scheduled appointments")
    p.add_argument("--provider", type=int, default=None, help="filter by provider id")
    p.add_argument("--limit", type=int, default=10)

    sub.add_parser("overdue", help="patients overdue for a follow-up visit")
    sub.add_parser("noshows", help="no-show rate by provider")
    sub.add_parser("monthly", help="appointments per month by status")
    p = sub.add_parser("frequent", help="patients with repeated no-shows")
    p.add_argument("--min", type=int, default=2, dest="min_no_shows",
                   help="show patients with MORE than this many no-shows")

    p = sub.add_parser("history", help="appointment history for one patient")
    p.add_argument("patient_id", type=int)
    return parser



def main(argv=None):
    args = build_parser().parse_args(argv)
    today = args.today or date.today().isoformat()

    if args.command == "init":
        db_file = Path(args.db)
        if db_file.exists():
            db_file.unlink()  # start fresh
        conn = database.connect(args.db)
        database.init_db(conn)
        seed_data.seed(conn, today)
        print(f"Created {args.db} with synthetic data (dates relative to {today}).")
        return 0

    if not Path(args.db).exists():
        print(f"No database found at {args.db}. Run: python main.py init")
        return 1
    conn = database.connect(args.db)

    if args.command == "upcoming":
        rows = queries.upcoming_appointments(conn, today, args.provider, args.limit)
        print_table(rows, ["appointment_date", "patient", "provider", "reason"])
    elif args.command == "overdue":
        rows = queries.overdue_followups(conn, today)
        print_table(rows, ["patient_id", "patient", "last_visit", "follow_up_by", "days_overdue"])
    elif args.command == "noshows":
        rows = queries.no_show_rate_by_provider(conn)
        print_table(rows, ["provider", "total_visits", "no_shows", "no_show_pct"])
    elif args.command == "monthly":
        rows = queries.appointments_per_month(conn)
        print_table(rows, ["month", "total", "completed", "no_show", "cancelled"])
    elif args.command == "frequent":
        rows = queries.frequent_no_shows(conn, args.min_no_shows)
        print_table(rows, ["patient_id", "patient", "no_shows"])
    elif args.command == "history":
        rows = queries.patient_history(conn, args.patient_id)
        print_table(rows, ["appointment_date", "provider", "status", "reason", "follow_up_by"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
