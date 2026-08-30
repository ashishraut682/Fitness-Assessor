# 🏋️ AI Multi-Sport Fitness Assessment & Personalized Training Recommendation System

An advanced, real-time computer vision web application that evaluates human movement kinematics across **5 sports modules** (Gym, Yoga, Basketball, Cricket, and Athletics). Using **MediaPipe Pose 33-landmark estimation**, the system tracks joint angles, body center of mass stability, rep counts, and posture alignment, delivering objective performance scoring, machine learning recommendations, and printable personalized improvement reports.

---

## 🌟 Key Features

* 🏆 **5-Sport Kinematic Motion Engine:**
  * 🏋️ **Gym & Resistance:** Squats (depth $<90^\circ$), Pushups (elbow flex & plank line), Core Planks ($\ge 165^\circ$), Lunges ($90^\circ$ stride).
  * 🧘 **Yoga & Mobility:** Tree Pose (*Vrksasana* balance), Warrior II (*Virabhadrasana II* arm horizon), Cobra Pose (*Bhujangasana* lumbar extension).
  * 🏀 **Basketball:** Shooting Form (90° L-elbow set point & wrist snap), Defensive Stance (low center of gravity knee dip).
  * 🏏 **Cricket:** Batting Stance (high backlift elbow), Bowling Action Straightness (ICC legal $<15^\circ$ elbow flex compliance check).
  * 🏃 **Athletics & Sprint:** Running Gait (high knee drive & $5^\circ$--$10^\circ$ torso forward lean), Sprint Block Stance (front $90^\circ$ / rear $120^\circ$ knee set angles).
* 🔒 **Dual-Database Architecture (SQLite 3 - `.db` files):**
  * `database/users_auth.db`: Dedicated authentication database for user credentials, hashed passwords, roles, and security audit logs (`UserAuth`, `LoginAuditLogs`).
  * `database/fitness_app.db`: Dedicated application database for kinematic scores, biometric profiles, recommendations, and workout schedules (`Users`, `Assessments`, `Recommendations`, `WorkoutPlans`).
* 🤖 **Hybrid AI Recommendation Engine:**
  * Combines a pre-trained **Scikit-Learn `RandomForestClassifier`** with a **Biomechanical Rule Engine** to auto-generate customized 4-week training schedules and daily mobility drills.
* 🎥 **Flexible On-Demand Input Modes:**
  * **Live Webcam Recording:** Activate live camera feed on demand.
  * **Offline Video File Upload:** Process pre-recorded videos frame-by-frame via OpenCV + MediaPipe without activating or requesting the webcam.
  * **Motion Simulation Demo:** Built-in kinematic wireframe simulator to preview angle tracking and rep counting.
* 📋 **Personalized Improvement & Practice Report Generator:**
  * Instant generation of a printable **Fitness Improvement & Regular Practice Action Plan** highlighting specific form weaknesses, daily morning practice routines, and a 4-week workout schedule (exportable as PDF).
* 🧭 **Modern Navigation & Security:**
  * Full page history stack with **Back (`<`)** and **Forward (`>`)** navigation buttons.
  * Multi-location **Log Out** buttons (Navbar, Sidebar Footer, and Account Settings).

---

## 📊 Scoring Model & Formulas

The overall **Fitness Score (0--100)** is computed using a weighted 4-factor scoring model:

$$\text{Fitness Score} = (0.30 \times \text{Strength}) + (0.25 \times \text{Flexibility}) + (0.20 \times \text{Balance}) + (0.25 \times \text{Posture})$$

* **Strength Score (30%):** Calculated from repetition volume power output.
* **Flexibility Score (25%):** Calculated from joint Range of Motion (ROM) depth reached.
* **Balance Score (20%):** Computed from horizontal shoulder and hip tilt symmetry index.
* **Posture Score (25%):** Computed from vertical spinal alignment and ear-to-hip forward lean.

*(Note: Videos with 0 reps or idle motion yield a `0.0%` score with tier `No Reps / Idle Video (0% Score)` and remedial beginner plans).*

---

## 📂 Project Directory Structure

```
fitness-accessor/
├── backend/
│   ├── app.py                   # Flask Web Server & API Routes
│   ├── exercise_analyzer.py     # 5-Sport Motion Kinematics Engine
│   ├── metrics.py               # 2D/3D Joint Angle & Stability Formulas
│   ├── ml_model.py              # RandomForest Recommendation Model Trainer
│   ├── pose_detection.py        # MediaPipe 33-Landmark Detector
│   ├── recommendation.py        # Hybrid ML & Rule Recommendation Engine
│   ├── scoring.py               # Weighted Sub-Score Calculator
│   └── recommendation_model.pkl # Saved RandomForest Model Binary
├── database/
│   ├── users_auth.db            # Separate User Authentication Database (SQLite 3)
│   ├── fitness_app.db           # Main Fitness Application Database (SQLite 3)
│   ├── auth_schema.sql          # Auth Schema (UserAuth, LoginAuditLogs)
│   ├── schema.sql               # Fitness App Schema (Users, Assessments, etc.)
│   ├── seed_auth_data.py        # Seeding Script for Auth DB
│   └── seed_data.py             # Seeding Script for Main Fitness DB
├── docs/
│   └── SRS_and_Report.md        # Software Requirements Specification (SRS) Document
├── frontend/
│   ├── index.html               # Single-Page Web Application UI
│   ├── styles.css               # Modern Glassmorphic Styling System
│   └── app.js                   # Client Logic, History Navigation & Camera Manager
├── .gitignore                   # Git Ignore Specification
└── README.md                    # Project Documentation
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
Ensure Python 3.8+ is installed on your system.

### 2. Install Required Dependencies
```bash
pip install flask opencv-python mediapipe numpy scikit-learn
```

### 3. Initialize & Seed Databases
```bash
python database/seed_auth_data.py
python database/seed_data.py
```

### 4. Start the Application Server
```bash
python backend/app.py
```

### 5. Access the Web Application
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Login Credentials

You can sign in using demo accounts or click the **"Quick Sign In as Demo User"** button on the login screen:

* **Demo User:** `alex@example.com` / `password123`
* **Demo Athlete:** `jordan@example.com` / `athlete123`

---

## 📜 License & Acknowledgments
Built with Python, Flask, MediaPipe Pose, OpenCV, Scikit-Learn, and Vanilla JavaScript/CSS.
