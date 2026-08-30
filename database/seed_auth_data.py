import sqlite3
from pathlib import Path

AUTH_DB_PATH = Path(__file__).parent / "users_auth.db"
AUTH_SCHEMA_PATH = Path(__file__).parent / "auth_schema.sql"

def init_auth_db():
    print(f"[Auth DB Setup] Initializing authentication database at {AUTH_DB_PATH}...")
    conn = sqlite3.connect(AUTH_DB_PATH)
    cursor = conn.cursor()

    # Read and execute schema
    with open(AUTH_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    # Check existing users
    cursor.execute("SELECT COUNT(*) FROM UserAuth")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        print("[Auth DB Setup] Inserting demo user authentication credentials...")
        users = [
            (1, "Alex Rivera", "alex@example.com", "password123", "athlete"),
            (2, "Sarah Chen", "sarah@example.com", "password123", "athlete"),
            (3, "Marcus Vance", "marcus@example.com", "password123", "coach")
        ]
        cursor.executemany("""
            INSERT INTO UserAuth (UserID, Name, Email, Password, Role)
            VALUES (?, ?, ?, ?, ?)
        """, users)

        # Audit log entry
        cursor.execute("""
            INSERT INTO LoginAuditLogs (Email, LoginStatus)
            VALUES (?, ?)
        """, ("alex@example.com", "SUCCESS_INITIAL_SEED"))

        conn.commit()
        print("[Auth DB Setup] Auth database initialized with 3 default users!")
    else:
        print("[Auth DB Setup] Authentication database already contains user data.")

    conn.close()

if __name__ == "__main__":
    init_auth_db()
