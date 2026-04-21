from db.connection import get_stres_connection
from models.schemas import UserRole
from services.auth_service import AuthService

class UserRepository:
    @staticmethod
    def init_db():
        """Initialize user table (only if it doesn't exist)."""
        with get_stres_connection() as conn:
            # Create table only if it doesn't exist - don't drop it!
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    @staticmethod
    def create_user(username: str, password: str, role: str = UserRole.USER.value) -> int:
        """Create a new user with hashed password."""
        password_hash = AuthService.hash_password(password)
        with get_stres_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_user_by_username(username: str) -> dict:
        """Fetch user by username."""
        with get_stres_connection() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, role FROM user WHERE username = ?",
                (username,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def user_exists(username: str) -> bool:
        """Check if user exists."""
        with get_stres_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM user WHERE username = ?",
                (username,)
            ).fetchone()
            return row is not None
