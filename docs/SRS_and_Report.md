# Software Requirements Specification (SRS) & System Architecture Report

## Project Title
**AI Fitness Assessment and Personalized Training Recommendation System**

---

# CHAPTER 1: INTRODUCTION

## 1.1 Problem Statement
In modern fitness regimens, improper posture and incorrect execution of exercises (such as squats and pushups) lead to acute joint injuries, chronic musculoskeletal strain, and suboptimal athletic progress. Traditional personal training offers human oversight but is costly, geographically constrained, and unavailable during home or remote workouts. Existing mobile fitness applications primarily track time or calories burned without evaluating joint mechanics, range of motion, or movement form in real-time. There is a critical need for an automated, accessible, computer vision-driven system capable of providing real-time pose detection, movement metric analysis, objective performance scoring, and intelligent exercise recommendations using standard smartphone or webcam camera feeds.

## 1.2 Objectives
The primary objectives of this system are:
1. **Automated Landmark Tracking**: Detect and track 33 key human body landmarks in real-time using MediaPipe Pose estimation without requiring specialized wearable sensors or depth cameras.
2. **Kinematic & Angle Analysis**: Compute exact joint angles (knee, hip, elbow, shoulder) and body center of mass stability during exercise execution.
3. **Automated Repetition & Depth Counting**: Accurately count exercise repetitions (Squats, Pushups) and validate form depth thresholds (e.g., knee bend angle < 90° for full squat depth).
4. **Multi-Factor Scoring Engine**: Calculate a unified Fitness Score (0–100) derived from weighted sub-scores: Strength (30%), Flexibility (25%), Balance (20%), and Posture (25%).
5. **Hybrid Recommendation Engine**: Provide immediate rule-based form feedback and train a Machine Learning classifier (`RandomForestClassifier`) to auto-predict customized workout plans based on individual posture and fitness sub-scores.
6. **Cross-Platform UI & Progress Tracking**: Deliver an intuitive Flutter-styled user interface with interactive dashboards, historical trend tracking, and video analysis capabilities.

## 1.3 Scope
- **Target Exercises (MVP)**: Squats (lower body strength/depth), Pushups (upper body & core alignment), Static Plank/Balance (body stability).
- **Camera Setup**: Single RGB camera feed (standard smartphone camera or desktop webcam).
- **Core Modules**:
  1. User Authentication & Profile Management
  2. Video Recording / Live Pose Stream Integration
  3. MediaPipe Pose Landmark Detection
  4. Kinematic Metric & Form Calculation Engine
  5. Weighted Fitness & Posture Scoring Engine
  6. Exercise Recommendation Engine (Rule-Based + RandomForest ML Classifier)
  7. Personal Workout Plan Generator
  8. Historical Progress Dashboard

---

# CHAPTER 2: SYSTEM REQUIREMENTS

## 2.1 Functional Requirements
- **FR-1 (User Management)**: The system shall allow users to register, log in, manage personal metrics (Age, Gender, Height, Weight), and store workout sessions securely.
- **FR-2 (Pose Estimation & Video Stream)**: The system shall process webcam feeds or uploaded video files to extract 33 spatial body landmarks $(X, Y, Z, \text{visibility})$.
- **FR-3 (Angle Math & Rep Detection)**: The system shall calculate joint vector angles in real-time and transition between `UP` and `DOWN` states to count valid repetitions.
- **FR-4 (Form Evaluation)**: The system shall detect improper form (e.g., knee caving, insufficient squat depth, flared elbows, arched lower back) and trigger immediate UI feedback.
- **FR-5 (Fitness Scoring)**: The system shall calculate composite scores from Strength, Flexibility, Balance, and Posture components.
- **FR-6 (AI Workout Recommendation)**: The system shall generate tailored exercise recommendations using heuristic rules and ML classifier predictions.
- **FR-7 (Progress Dashboard)**: The system shall plot historical fitness trends, posture scores, and weekly workout plans.

## 2.2 Non-Functional Requirements
- **NFR-1 (Performance)**: Pose detection and angle calculation shall process at minimum 24-30 Frames Per Second (FPS) on consumer hardware.
- **NFR-2 (Accuracy)**: Repetition counting accuracy shall exceed 95% under standard indoor lighting conditions.
- **NFR-3 (Usability)**: The UI shall adhere to modern responsive design standards with intuitive visual cues (green skeleton overlay for good form, red/orange for warnings).
- **NFR-4 (Security)**: User authentication passwords shall be hashed and stored securely.
- **NFR-5 (Scalability)**: The modular architecture shall support expanding pose detection rules to additional sports/activities without redesigning core pipelines.

## 2.3 Hardware Requirements
- **Processor**: Dual-Core 2.0 GHz Intel/AMD processor or ARM equivalent (Apple Silicon, Snapdragon).
- **RAM**: 4 GB minimum (8 GB recommended for simultaneous video processing & web UI).
- **Camera**: Standard integrated RGB webcam or external smartphone camera (720p @ 30 FPS minimum).
- **Storage**: 500 MB available disk space.

## 2.4 Software Requirements
- **Operating System**: Windows 10/11, macOS 11+, or Ubuntu 20.04+.
- **Runtime Environment**: Python 3.10+ (tested on Python 3.14).
- **Computer Vision & ML Libraries**: `mediapipe`, `opencv-python`, `numpy`, `scikit-learn`.
- **Backend Framework**: `Flask`, `Flask-CORS`.
- **Database**: SQLite3 / Firebase Firestore compatible schema.
- **Frontend Stack**: Modern HTML5, CSS3, ES6 JavaScript (Flutter UI responsive frame layout).

---

# CHAPTER 3: DATABASE DESIGN

## 3.1 Relational Schema & Entity-Relationship Mapping
The database is structured around four primary entities: `Users`, `Assessments`, `Recommendations`, and `WorkoutPlans`.

### 1. `Users` Table
- `UserID` (INTEGER, Primary Key, Auto Increment)
- `Name` (VARCHAR(100), Not Null)
- `Email` (VARCHAR(150), Unique, Not Null)
- `Password` (VARCHAR(255), Not Null)
- `Age` (INTEGER)
- `Gender` (VARCHAR(20))
- `Height` (REAL) -- in cm
- `Weight` (REAL) -- in kg
- `CreatedAt` (DATETIME, Default CURRENT_TIMESTAMP)

### 2. `Assessments` Table
- `AssessmentID` (INTEGER, Primary Key, Auto Increment)
- `UserID` (INTEGER, Foreign Key referencing Users.UserID)
- `Date` (DATETIME, Default CURRENT_TIMESTAMP)
- `FitnessScore` (REAL) -- composite 0-100 score
- `StrengthScore` (REAL) -- 30% weight component
- `FlexibilityScore` (REAL) -- 25% weight component
- `BalanceScore` (REAL) -- 20% weight component
- `PostureScore` (REAL) -- 25% weight component
- `SquatReps` (INTEGER)
- `PushupReps` (INTEGER)

### 3. `Recommendations` Table
- `RecommendationID` (INTEGER, Primary Key, Auto Increment)
- `AssessmentID` (INTEGER, Foreign Key referencing Assessments.AssessmentID)
- `Exercise` (VARCHAR(100), Not Null)
- `Duration` (VARCHAR(50)) -- e.g., "15 mins"
- `Frequency` (VARCHAR(50)) -- e.g., "3x / week"
- `Source` (VARCHAR(50)) -- "RuleEngine" or "RandomForestML"

### 4. `WorkoutPlans` Table
- `PlanID` (INTEGER, Primary Key, Auto Increment)
- `UserID` (INTEGER, Foreign Key referencing Users.UserID)
- `WeekNumber` (INTEGER, Not Null)
- `Exercise` (VARCHAR(100), Not Null)
- `Sets` (INTEGER, Not Null)
- `Reps` (INTEGER, Not Null)
- `Status` (VARCHAR(20), Default 'Pending')
