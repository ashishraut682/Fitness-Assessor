import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "fitness_app.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def init_db():
    print(f"[DB Setup] Initializing database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read and execute schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    # Check if sample user already exists
    cursor.execute("SELECT COUNT(*) FROM Users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        print("[DB Setup] Inserting initial demo data...")
        # Insert Demo Users
        users = [
            (1, "Alex Rivera", "alex@example.com", "password123", 24, "Male", 178.0, 72.5),
            (2, "Sarah Chen", "sarah@example.com", "password123", 26, "Female", 165.0, 58.0),
            (3, "Marcus Vance", "marcus@example.com", "password123", 30, "Male", 182.0, 80.0)
        ]
        cursor.executemany("""
            INSERT INTO Users (UserID, Name, Email, Password, Age, Gender, Height, Weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, users)
        user_id = 1

        # Insert Initial Assessment
        cursor.execute("""
            INSERT INTO Assessments (UserID, FitnessScore, StrengthScore, FlexibilityScore, BalanceScore, PostureScore, SquatReps, PushupReps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, 76.5, 70.0, 65.0, 85.0, 80.0, 15, 20))
        assessment_id = cursor.lastrowid

        # Insert Recommendations
        recommendations = [
            (assessment_id, "Bodyweight Squats & Romanian Deadlifts", "20 mins", "3x / week", "RandomForestML"),
            (assessment_id, "Hamstring & Hip Flexor Stretching", "15 mins", "Daily", "RuleEngine"),
            (assessment_id, "Standard Pushups & Plank Hold", "15 mins", "3x / week", "RuleEngine")
        ]
        cursor.executemany("""
            INSERT INTO Recommendations (AssessmentID, Exercise, Duration, Frequency, Source)
            VALUES (?, ?, ?, ?, ?)
        """, recommendations)

        # Insert 4-Week Workout Plan
        plans = [
            (user_id, 1, "Goblet Squats", 3, 12, "Completed"),
            (user_id, 1, "Pushups", 3, 15, "Completed"),
            (user_id, 1, "Plank Hold", 3, 60, "Completed"),
            (user_id, 2, "Bodyweight Squats", 4, 15, "Pending"),
            (user_id, 2, "Diamond Pushups", 3, 10, "Pending"),
            (user_id, 2, "Single-Leg Balance Drill", 3, 45, "Pending"),
            (user_id, 3, "Bulgarian Split Squats", 3, 10, "Pending"),
            (user_id, 3, "Incline Pushups", 3, 15, "Pending"),
            (user_id, 4, "Jump Squats", 4, 12, "Pending"),
            (user_id, 4, "Decline Pushups", 3, 12, "Pending")
        ]
        cursor.executemany("""
            INSERT INTO WorkoutPlans (UserID, WeekNumber, Exercise, Sets, Reps, Status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, plans)

        conn.commit()
        print("[DB Setup] Seed data inserted successfully!")
    else:
        print("[DB Setup] Database already populated.")

    conn.close()

if __name__ == "__main__":
    init_db()
