-- AI Fitness Assessment & Recommendation System Schema

CREATE TABLE IF NOT EXISTS Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Email TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    Age INTEGER,
    Gender TEXT,
    Height REAL,
    Weight REAL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Assessments (
    AssessmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL,
    Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FitnessScore REAL NOT NULL,
    StrengthScore REAL NOT NULL,
    FlexibilityScore REAL NOT NULL,
    BalanceScore REAL NOT NULL,
    PostureScore REAL NOT NULL,
    SquatReps INTEGER DEFAULT 0,
    PushupReps INTEGER DEFAULT 0,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Recommendations (
    RecommendationID INTEGER PRIMARY KEY AUTOINCREMENT,
    AssessmentID INTEGER NOT NULL,
    Exercise TEXT NOT NULL,
    Duration TEXT NOT NULL,
    Frequency TEXT NOT NULL,
    Source TEXT DEFAULT 'RuleEngine',
    FOREIGN KEY (AssessmentID) REFERENCES Assessments(AssessmentID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS WorkoutPlans (
    PlanID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL,
    WeekNumber INTEGER NOT NULL,
    Exercise TEXT NOT NULL,
    Sets INTEGER NOT NULL,
    Reps INTEGER NOT NULL,
    Status TEXT DEFAULT 'Pending',
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_assessments_user ON Assessments(UserID);
CREATE INDEX IF NOT EXISTS idx_recommendations_assessment ON Recommendations(AssessmentID);
CREATE INDEX IF NOT EXISTS idx_workoutplans_user_week ON WorkoutPlans(UserID, WeekNumber);
