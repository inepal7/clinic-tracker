"""Generate synthetic (fake) clinic data for the tracker.

Uses a fixed random seed so the same data is produced every run.
"""
import random
from datetime import date, timedelta

FIRST_NAMES = [
    "Ava", "Liam", "Maya", "Noah", "Priya", "Ethan", "Sofia", "Lucas", "Amira",
    "Mateo", "Hana", "Omar", "Elena", "Jonah", "Layla", "Diego", "Nora", "Kai",
    "Zara", "Theo",
]
LAST_NAMES = [
    "Nguyen", "Patel", "Garcia", "Kim", "Johnson", "Rivera", "Singh", "Lee",
    "Martinez", "Cohen", "Ali", "Tran", "Brown", "Lopez", "Shah", "Park",
    "Reyes", "Chen", "Dubois", "Haddad",
]
PROVIDERS = [
    ("Dr. Amara Okafor", "Family Medicine"),
    ("Dr. Daniel Brooks", "Internal Medicine"),
    ("Dr. Mei Tanaka", "Pediatrics"),
    ("Dr. Rafael Ortiz", "Dermatology"),
    ("Dr. Sara Lindqvist", "Cardiology"),
]
REASONS = [
    "Annual checkup", "Blood pressure follow-up", "Flu symptoms",
    "Skin rash", "Lab results review", "Vaccination", "Back pain",
    "Medication review",
]
SUMMARIES = [
    "Routine exam, no concerns.", "Symptoms improving, continue treatment.",
    "Labs ordered, review results next visit.", "Medication adjusted.",
    "Referred for further testing.",
]


def _next_weekday(d):
    """Move a date forward to Monday if it lands on a weekend."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def seed(conn, today, n_patients=60, rng_seed=42):
    """Fill the database with fake patients, providers, appointments and visits.

    `today` is an ISO date string; appointments are spread from one year
    before it to about two months after it.
    """
    rng = random.Random(rng_seed)
    today_date = date.fromisoformat(today)
    cur = conn.cursor()

    cur.executemany(
        "INSERT INTO providers (name, specialty) VALUES (?, ?)", PROVIDERS
    )
    provider_ids = [row[0] for row in cur.execute("SELECT provider_id FROM providers")]

    patient_ids = []
    for _ in range(n_patients):
        dob = date(1940, 1, 1) + timedelta(days=rng.randint(0, 25000))
        phone = f"(555) 010-{rng.randint(0, 9999):04d}"  # fictional number format
        cur.execute(
            "INSERT INTO patients (first_name, last_name, date_of_birth, phone) "
            "VALUES (?, ?, ?, ?)",
            (rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES), dob.isoformat(), phone),
        )
        patient_ids.append(cur.lastrowid)

    for patient_id in patient_ids:
        for _ in range(rng.randint(2, 8)):
            appt_date = _next_weekday(today_date + timedelta(days=rng.randint(-365, 60)))
            if appt_date < today_date:
                status = rng.choices(
                    ["completed", "no_show", "cancelled"], weights=[75, 12, 13]
                )[0]
            else:
                status = rng.choices(["scheduled", "cancelled"], weights=[92, 8])[0]

            cur.execute(
                "INSERT INTO appointments "
                "(patient_id, provider_id, appointment_date, status, reason) "
                "VALUES (?, ?, ?, ?, ?)",
                (patient_id, rng.choice(provider_ids), appt_date.isoformat(),
                 status, rng.choice(REASONS)),
            )
            appointment_id = cur.lastrowid

            if status == "completed":
                needs_follow_up = rng.random() < 0.30
                follow_up_by = None
                if needs_follow_up:
                    follow_up_by = (appt_date + timedelta(days=rng.randint(14, 90))).isoformat()
                cur.execute(
                    "INSERT INTO visits "
                    "(appointment_id, summary, follow_up_needed, follow_up_by) "
                    "VALUES (?, ?, ?, ?)",
                    (appointment_id, rng.choice(SUMMARIES), int(needs_follow_up), follow_up_by),
                )

    conn.commit()
