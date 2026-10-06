# Clinic Appointment Tracker

A Python and SQL command-line tool for managing clinic appointments and spotting patients who have slipped through the cracks on follow-up care. Built with SQLite and the Python standard library (no external dependencies).

> **All data is synthetic.** Names, dates of birth, phone numbers, and visit notes are randomly generated. No real patient information is used anywhere in this project.

## Why I built it

I worked in clinical settings using EHR and practice-management systems, where a common problem is patients who need a follow-up but never get rescheduled. This project models that problem with a relational database and answers it with SQL.

## Features

- Relational schema with four linked tables, foreign keys, and `CHECK` constraints
- Synthetic data generator (reproducible via a fixed random seed)
- Six SQL reports:
   - Six SQL reports:
  - **Upcoming appointments**, optionally filtered by provider
  - **Overdue follow-ups**: patients whose follow-up deadline passed with no later appointment booked
  - **No-show rate by provider**
  - **Appointments per month** by status
  - **Patient history**
  - **Frequent no-shows**: patients with repeated missed appointments
- Parameterized queries to prevent SQL injection
- Unit tests for every query

## Database design

```
patients ──< appointments >── providers
                 │
                 └── 1:1 ── visits (follow_up_needed, follow_up_by)
```

| Table | Purpose |
| --- | --- |
| `patients` | Fake patient demographics |
| `providers` | Clinicians and their specialty |
| `appointments` | One row per appointment, with status: scheduled, completed, cancelled, or no_show |
| `visits` | Visit summary for completed appointments, plus follow-up flag and deadline |

See [`schema.sql`](schema.sql) for the full definitions.

## Getting started

Requires Python 3.9+. Nothing to install.

```bash
git clone https://github.com/inepal7/clinic-tracker.git
cd clinic-tracker

python main.py init                 # create clinic.db with synthetic data
python main.py upcoming --limit 5   # next scheduled appointments
python main.py overdue              # patients overdue for follow-up
python main.py noshows              # no-show rate by provider
python main.py monthly              # appointments per month
python main.py frequent --min 2     # patients with more than 2 no-shows
python main.py history 12           # history for patient 12
```

## Example output

```
$ python main.py overdue

PATIENT_ID  PATIENT       LAST_VISIT  FOLLOW_UP_BY  DAYS_OVERDUE
----------  ------------  ----------  ------------  ------------
7           Layla Dubois  2025-10-20  2025-11-11    329
59          Omar Lopez    2026-01-16  2026-03-27    193
41          Hana Park     2026-03-16  2026-05-30    129
```

## The key query

Finding overdue follow-ups uses a correlated `NOT EXISTS` subquery to exclude patients who already have a later scheduled or completed appointment:

```sql
SELECT p.first_name || ' ' || p.last_name AS patient, v.follow_up_by
FROM visits v
JOIN appointments a ON a.appointment_id = v.appointment_id
JOIN patients     p ON p.patient_id     = a.patient_id
WHERE v.follow_up_needed = 1
  AND v.follow_up_by < :today
  AND NOT EXISTS (
      SELECT 1 FROM appointments later
      WHERE later.patient_id = a.patient_id
        AND later.appointment_date > a.appointment_date
        AND later.status IN ('scheduled', 'completed')
  );
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```
clinic-tracker/
├── schema.sql        # table definitions
├── database.py       # connection and setup
├── seed_data.py      # synthetic data generator
├── queries.py        # SQL reports
├── main.py           # command-line interface
└── tests/
    └── test_queries.py
```

## Possible next steps

- Add a Flask or FastAPI layer to expose the reports as a REST API
- Deploy the API on AWS
- Add a simple dashboard for the no-show and monthly reports

## Tech

Python, SQL (SQLite), unittest
