from db.connection import get_stres_connection

class PredictionRepository:
    @staticmethod
    def init_db():
        """Initialize prediction table (only if it doesn't exist)."""
        with get_stres_connection() as conn:
            # Create table only if it doesn't exist - don't drop it!
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prediction (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    varsta INTEGER,
                    cesti_cafea_zi INTEGER,
                    ore_somn REAL,
                    nivel_stres INTEGER,
                    predictie_stres REAL,
                    symptom_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user(id)
                )
            """)
            conn.commit()

    @staticmethod
    def save_prediction(user_id: int, varsta: int, cesti_cafea_zi: int,
                       ore_somn: float, nivel_stres: int,
                       predictie_stres: float, symptom_score: float) -> int:
        """Save prediction to database."""
        with get_stres_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO prediction 
                   (user_id, varsta, cesti_cafea_zi, ore_somn, nivel_stres, predictie_stres, symptom_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, varsta, cesti_cafea_zi, ore_somn, nivel_stres, predictie_stres, symptom_score)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_user_predictions(user_id: int, limit: int = 50):
        """Get predictions for a specific user."""
        with get_stres_connection() as conn:
            rows = conn.execute(
                """SELECT id, varsta, cesti_cafea_zi, ore_somn, nivel_stres, 
                          predictie_stres, symptom_score, created_at
                   FROM prediction WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]
