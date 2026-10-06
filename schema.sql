-- Clinic Appointment Tracker schema (SQLite)
-- All data in this project is synthetic. No real patient information.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS patients (
    patient_id    INTEGER PRIMARY KEY,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,          -- ISO format: YYYY-MM-DD
    phone         TEXT
);

CREATE TABLE IF NOT EXISTS providers (
    provider_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    specialty   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id   INTEGER PRIMARY KEY,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id),
    provider_id      INTEGER NOT NULL REFERENCES providers(provider_id),
    appointment_date TEXT NOT NULL,       -- ISO format: YYYY-MM-DD
    status           TEXT NOT NULL
        CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show')),
    reason           TEXT NOT NULL
);

-- One visit record per completed appointment.
CREATE TABLE IF NOT EXISTS visits (
    visit_id         INTEGER PRIMARY KEY,
    appointment_id   INTEGER NOT NULL UNIQUE REFERENCES appointments(appointment_id),
    summary          TEXT,
    follow_up_needed INTEGER NOT NULL DEFAULT 0 CHECK (follow_up_needed IN (0, 1)),
    follow_up_by     TEXT                 -- ISO date, only set when follow_up_needed = 1
);

-- Indexes speed up the lookups our queries do most often.
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date    ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status  ON appointments(status);
