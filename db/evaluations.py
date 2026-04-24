from db.connection import get_stres_connection
import datetime

class EvaluationRepository:
    @staticmethod
    def init_db():
        """Initialize evaluations table (only if it doesn't exist)."""
        with get_stres_connection() as conn:
            # Create table only if it doesn't exist - don't drop it!
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    coffee_intake_day INTEGER NOT NULL,
                    sleep_hours_night REAL NOT NULL,
                    bmi REAL NOT NULL,
                    heart_rate INTEGER NOT NULL,
                    stress_level TEXT NOT NULL,
                    stress_score REAL NOT NULL,
                    physical_activity REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id)
                )
            """)
            conn.commit()

    @staticmethod
    def save_evaluation(user_id: int, coffee_intake_day: int, sleep_hours_night: float,
                       bmi: float, heart_rate: int, stress_level: str,
                       stress_score: float, physical_activity: float) -> int:
        """Save evaluation to database."""
        with get_stres_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO evaluations
                   (user_id, coffee_intake_day, sleep_hours_night, bmi, heart_rate, stress_level, stress_score, physical_activity)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, coffee_intake_day, sleep_hours_night, bmi, heart_rate, stress_level, stress_score, physical_activity)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_user_evaluations(user_id: int, limit: int = 50):
        """Get evaluations for a specific user."""
        with get_stres_connection() as conn:
            rows = conn.execute(
                """SELECT id, date, coffee_intake_day, sleep_hours_night, bmi, heart_rate,
                          stress_level, stress_score, physical_activity
                   FROM evaluations WHERE user_id = ?
                   ORDER BY date DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_user_evaluations_last_week(user_id: int):
        """Get evaluations for the last 7 days."""
        week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        with get_stres_connection() as conn:
            rows = conn.execute(
                """SELECT date, coffee_intake_day, sleep_hours_night, bmi, heart_rate,
                          stress_level, stress_score, physical_activity
                   FROM evaluations WHERE user_id = ? AND date >= ?
                   ORDER BY date ASC""",
                (user_id, week_ago.isoformat())
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_weekly_comparison(user_id: int):
        """Get comparison between this week and last week."""
        now = datetime.datetime.now()
        this_week_start = now - datetime.timedelta(days=7)
        last_week_start = now - datetime.timedelta(days=14)
        last_week_end = now - datetime.timedelta(days=7)

        with get_stres_connection() as conn:
            # This week
            this_week = conn.execute(
                """SELECT AVG(coffee_intake_day) as avg_coffee,
                          AVG(sleep_hours_night) as avg_sleep,
                          AVG(physical_activity) as avg_activity,
                          AVG(stress_score) as avg_stress,
                          COUNT(*) as count
                   FROM evaluations WHERE user_id = ? AND date >= ?""",
                (user_id, this_week_start.isoformat())
            ).fetchone()

            # Last week
            last_week = conn.execute(
                """SELECT AVG(coffee_intake_day) as avg_coffee,
                          AVG(sleep_hours_night) as avg_sleep,
                          AVG(physical_activity) as avg_activity,
                          AVG(stress_score) as avg_stress,
                          COUNT(*) as count
                   FROM evaluations WHERE user_id = ? AND date >= ? AND date < ?""",
                (user_id, last_week_start.isoformat(), last_week_end.isoformat())
            ).fetchone()

            return {
                'this_week': dict(this_week) if this_week else None,
                'last_week': dict(last_week) if last_week else None
            }