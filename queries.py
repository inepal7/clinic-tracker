"""SQL queries for the Clinic Appointment Tracker.

Every function takes an open connection and returns a list of rows.
Values are passed as named parameters (never string-formatted into the SQL)
to avoid SQL injection.
"""


def upcoming_appointments(conn, today, provider_id=None, limit=10):
    """Next scheduled appointments from `today`, optionally for one provider."""
    sql = """
        SELECT a.appointment_id,
               a.appointment_date,
               p.first_name || ' ' || p.last_name AS patient,
               pr.name AS provider,
               a.reason
        FROM appointments a
        JOIN patients  p  ON p.patient_id   = a.patient_id
        JOIN providers pr ON pr.provider_id = a.provider_id
        WHERE a.status = 'scheduled'
          AND a.appointment_date >= :today
          AND (:provider_id IS NULL OR a.provider_id = :provider_id)
        ORDER BY a.appointment_date, a.appointment_id
        LIMIT :limit
    """
    params = {"today": today, "provider_id": provider_id, "limit": limit}
    return conn.execute(sql, params).fetchall()


def overdue_followups(conn, today):
    """Patients whose follow-up deadline passed with no later appointment booked."""
    sql = """
        SELECT p.patient_id,
               p.first_name || ' ' || p.last_name AS patient,
               a.appointment_date AS last_visit,
               v.follow_up_by,
               CAST(julianday(:today) - julianday(v.follow_up_by) AS INTEGER) AS days_overdue
        FROM visits v
        JOIN appointments a ON a.appointment_id = v.appointment_id
        JOIN patients     p ON p.patient_id     = a.patient_id
        WHERE v.follow_up_needed = 1
          AND v.follow_up_by < :today
          AND NOT EXISTS (
              SELECT 1
              FROM appointments later
              WHERE later.patient_id = a.patient_id
                AND later.appointment_date > a.appointment_date
                AND later.status IN ('scheduled', 'completed')
          )
        ORDER BY days_overdue DESC, p.patient_id
    """
    return conn.execute(sql, {"today": today}).fetchall()


def no_show_rate_by_provider(conn):
    """No-show percentage per provider, counting only completed and no-show visits."""
    sql = """
        SELECT pr.name AS provider,
               COUNT(*) AS total_visits,
               SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) AS no_shows,
               ROUND(100.0 * SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END)
                     / COUNT(*), 1) AS no_show_pct
        FROM appointments a
        JOIN providers pr ON pr.provider_id = a.provider_id
        WHERE a.status IN ('completed', 'no_show')
        GROUP BY pr.provider_id
        ORDER BY no_show_pct DESC, pr.name
    """
    return conn.execute(sql).fetchall()


def appointments_per_month(conn):
    """Appointment counts by month, broken down by status."""
    sql = """
        SELECT strftime('%Y-%m', appointment_date) AS month,
               COUNT(*) AS total,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN status = 'no_show'   THEN 1 ELSE 0 END) AS no_show,
               SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
        FROM appointments
        GROUP BY month
        ORDER BY month
    """
    return conn.execute(sql).fetchall()


def frequent_no_shows(conn, min_no_shows=2):
    """Patients with more than `min_no_shows` missed appointments."""
    sql = """
        SELECT p.patient_id,
               p.first_name || ' ' || p.last_name AS patient,
               COUNT(*) AS no_shows
        FROM appointments a
        JOIN patients p ON p.patient_id = a.patient_id
        WHERE a.status = 'no_show'
        GROUP BY p.patient_id
        HAVING COUNT(*) > :min_no_shows
        ORDER BY no_shows DESC
    """
    return conn.execute(sql, {"min_no_shows": min_no_shows}).fetchall()


def patient_history(conn, patient_id):
    """Full appointment history for one patient, newest first."""
    sql = """
        SELECT a.appointment_date,
               pr.name AS provider,
               a.status,
               a.reason,
               COALESCE(v.summary, '')      AS summary,
               COALESCE(v.follow_up_by, '') AS follow_up_by
        FROM appointments a
        JOIN providers pr ON pr.provider_id = a.provider_id
        LEFT JOIN visits v ON v.appointment_id = a.appointment_id
        WHERE a.patient_id = :patient_id
        ORDER BY a.appointment_date DESC
    """
    return conn.execute(sql, {"patient_id": patient_id}).fetchall()
