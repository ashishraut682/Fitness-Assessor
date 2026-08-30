-- AI Fitness Authentication Database Schema
-- File Extension: .db (SQLite 3 Database)

CREATE TABLE IF NOT EXISTS UserAuth (
    AuthID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER NOT NULL UNIQUE,
    Name TEXT NOT NULL,
    Email TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    Role TEXT DEFAULT 'user',
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastLogin DATETIME
);

CREATE TABLE IF NOT EXISTS LoginAuditLogs (
    LogID INTEGER PRIMARY KEY AUTOINCREMENT,
    Email TEXT NOT NULL,
    LoginStatus TEXT NOT NULL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_userauth_email ON UserAuth(Email);
