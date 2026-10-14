import os
import sqlite3
import base64
import cv2
import numpy as np
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from pose_detection import PoseDetector
from exercise_analyzer import MultiSportAnalyzer
from scoring import FitnessScorer
from recommendation import RecommendationEngine

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

DB_PATH = Path(__file__).parent.parent / "database" / "fitness_app.db"
AUTH_DB_PATH = Path(__file__).parent.parent / "database" / "users_auth.db"

# Global Pose Detector and Multi-Sport Analyzer Instances
pose_detector = PoseDetector()
sport_analyzer = MultiSportAnalyzer()
rec_engine = RecommendationEngine()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_auth_db_connection():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online", 
        "system": "AI Fitness Assessment & Recommendation API", 
        "mediapipe": True,
        "auth_database": "users_auth.db",
        "database_engine": "SQLite 3 (.db extension)"
    })

@app.route("/api/auth/info", methods=["GET"])
def auth_info():
    try:
        auth_conn = get_auth_db_connection()
        users = auth_conn.execute("SELECT AuthID, UserID, Name, Email, Role, CreatedAt FROM UserAuth").fetchall()
        logs = auth_conn.execute("SELECT * FROM LoginAuditLogs ORDER BY LogID DESC LIMIT 10").fetchall()
        auth_conn.close()
        return jsonify({
            "database_engine": "SQLite 3",
            "database_file_extension": ".db",
            "auth_database_file": "database/users_auth.db",
            "main_database_file": "database/fitness_app.db",
            "user_auth_count": len(users),
            "users": [dict(u) for u in users],
            "recent_audit_logs": [dict(l) for l in logs]
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    try:
        auth_conn = get_auth_db_connection()
        user_auth = auth_conn.execute("SELECT * FROM UserAuth WHERE LOWER(Email) = ? AND Password = ?", (email, password)).fetchone()
        
        if user_auth:
            auth_conn.execute("INSERT INTO LoginAuditLogs (Email, LoginStatus) VALUES (?, ?)", (email, "SUCCESS"))
            auth_conn.commit()
            user_id = user_auth["UserID"]
            user_name = user_auth["Name"]
            user_email = user_auth["Email"]
            auth_conn.close()

            fit_conn = get_db_connection()
            user_profile = fit_conn.execute("SELECT * FROM Users WHERE UserID = ?", (user_id,)).fetchone()
            fit_conn.close()

            profile_data = {
                "id": user_id,
                "name": user_name,
                "email": user_email,
                "age": user_profile["Age"] if user_profile and "Age" in user_profile.keys() else 24,
                "gender": user_profile["Gender"] if user_profile and "Gender" in user_profile.keys() else "Male",
                "height": user_profile["Height"] if user_profile and "Height" in user_profile.keys() else 178.0,
                "weight": user_profile["Weight"] if user_profile and "Weight" in user_profile.keys() else 72.5
            }
            return jsonify({"success": True, "user": profile_data, "auth_database": "users_auth.db"})
        else:
            auth_conn.execute("INSERT INTO LoginAuditLogs (Email, LoginStatus) VALUES (?, ?)", (email, "FAILED"))
            auth_conn.commit()
            auth_conn.close()
            return jsonify({"success": False, "message": "Invalid email or password. Please try again."}), 401
    except Exception as e:
        # Fallback for testing if database is initialized
        return jsonify({"success": False, "message": f"Auth error: {str(e)}"}), 500

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    name = (data.get("name") or "New User").strip()
    email = (data.get("email") or "user@example.com").strip().lower()
    password = data.get("password") or "password"
    age = data.get("age", 25)
    gender = data.get("gender", "Other")
    height = data.get("height", 170.0)
    weight = data.get("weight", 65.0)

    auth_conn = get_auth_db_connection()
    # Check if email already registered in separate auth database
    existing_user = auth_conn.execute("SELECT * FROM UserAuth WHERE LOWER(Email) = ?", (email,)).fetchone()
    if existing_user:
        auth_conn.close()
        return jsonify({"success": False, "message": "An account with this email address already exists. Please sign in."}), 400

    fit_conn = get_db_connection()

    try:
        # Determine next available UserID across both databases to avoid key collisions
        max_fit = fit_conn.execute("SELECT MAX(UserID) FROM Users").fetchone()[0] or 0
        max_auth = auth_conn.execute("SELECT MAX(UserID) FROM UserAuth").fetchone()[0] or 0
        next_user_id = max(max_fit, max_auth) + 1

        # 1. Insert into UserAuth (users_auth.db)
        auth_cursor = auth_conn.cursor()
        auth_cursor.execute("""
            INSERT INTO UserAuth (UserID, Name, Email, Password, Role)
            VALUES (?, ?, ?, ?, ?)
        """, (next_user_id, name, email, password, "athlete"))
        auth_cursor.execute("""
            INSERT INTO LoginAuditLogs (Email, LoginStatus)
            VALUES (?, ?)
        """, (email, "SUCCESS_REGISTRATION"))
        auth_conn.commit()

        # 2. Insert into Users (fitness_app.db)
        fit_cursor = fit_conn.cursor()
        fit_cursor.execute("""
            INSERT INTO Users (UserID, Name, Email, Password, Age, Gender, Height, Weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (next_user_id, name, email, password, age, gender, height, weight))
        fit_conn.commit()

        auth_conn.close()
        fit_conn.close()

        user_data = {
            "id": next_user_id,
            "name": name,
            "email": email,
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight
        }

        return jsonify({
            "success": True, 
            "user": user_data, 
            "message": "Account created successfully in separate authentication database (users_auth.db)!"
        })
    except Exception as e:
        auth_conn.close()
        fit_conn.close()
        return jsonify({"success": False, "message": f"Registration error: {str(e)}"}), 400

@app.route("/api/analyze/frame", methods=["POST"])
def analyze_frame():
    """
    Receives base64 image frame or JSON landmark data, 
    runs MediaPipe pose detection, computes joint angles, rep count, and feedback for any sport category.
    """
    data = request.json or {}
    image_b64 = data.get("image")
    category = data.get("category", "gym")
    exercise_type = data.get("exercise", "squat")

    frame = None
    if image_b64:
        try:
            if "," in image_b64:
                image_b64 = image_b64.split(",")[1]
            img_bytes = base64.b64decode(image_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception:
            frame = None

    if frame is None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Run MediaPipe Pose Detection
    frame, landmarks = pose_detector.process_frame(frame, draw=True)

    # Run Multi-Sport Exercise Analysis
    analysis_result = sport_analyzer.analyze_frame(landmarks, category=category, exercise=exercise_type)

    # Encode processed frame back to base64 for live overlay UI preview
    _, buffer = cv2.imencode(".jpg", frame)
    annotated_b64 = base64.b64encode(buffer).decode("utf-8")

    return jsonify({
        "success": True,
        "category": category,
        "exercise": exercise_type,
        "landmarks_count": len(landmarks),
        "analysis": analysis_result,
        "annotated_image": f"data:image/jpeg;base64,{annotated_b64}"
    })

@app.route("/api/assess/submit", methods=["POST"])
def submit_assessment():
    """
    Submits completed exercise assessment metrics, computes final 4-component score, 
    saves assessment to DB, and returns recommendations & workout plans.
    """
    data = request.json or {}
    user_id = data.get("user_id", 1)
    squats = data.get("squats", 0)
    pushups = data.get("pushups", 0)
    flexibility = float(data.get("flexibility", 0.0))
    balance = float(data.get("balance", 0.0))
    posture = float(data.get("posture", 0.0))

    # If no reps or movement were detected at all (video doing nothing)
    if squats == 0 and pushups == 0 and flexibility == 0.0 and balance == 0.0 and posture == 0.0:
        scoring_result = {
            "fitness_score": 0.0,
            "tier": "No Reps / Idle Video (0% Score)",
            "breakdown": {
                "strength": 0.0,
                "flexibility": 0.0,
                "balance": 0.0,
                "posture": 0.0
            },
            "warning": "0 valid exercise reps or body movements detected in video!"
        }
        fitness_score = 0.0
        strength = 0.0
    else:
        # Compute Strength & Composite Fitness Score dynamically
        strength = FitnessScorer.compute_strength_from_reps(squats, pushups)
        scoring_result = FitnessScorer.calculate_fitness_score(strength, flexibility, balance, posture)
        fitness_score = scoring_result["fitness_score"]

    # Save Assessment to SQLite DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Assessments (UserID, FitnessScore, StrengthScore, FlexibilityScore, BalanceScore, PostureScore, SquatReps, PushupReps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, fitness_score, strength, flexibility, balance, posture, squats, pushups))
    assessment_id = cursor.lastrowid

    # Generate Recommendations & Workout Plan
    recommendations = rec_engine.generate_recommendations(strength, flexibility, balance, posture)
    for rec in recommendations:
        cursor.execute("""
            INSERT INTO Recommendations (AssessmentID, Exercise, Duration, Frequency, Source)
            VALUES (?, ?, ?, ?, ?)
        """, (assessment_id, rec["exercise"], rec["duration"], rec["frequency"], rec["source"]))

    workout_plan = rec_engine.generate_workout_plan(user_id, fitness_score)
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "assessment_id": assessment_id,
        "scoring": scoring_result,
        "recommendations": recommendations,
        "workout_plan": workout_plan
    })

@app.route("/api/dashboard/<int:user_id>", methods=["GET"])
def get_dashboard(user_id):
    """Fetches user metrics history, latest scores, and recommendations for Dashboard UI."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM Users WHERE UserID = ?", (user_id,)).fetchone()
    assessments = conn.execute("""
        SELECT * FROM Assessments WHERE UserID = ? ORDER BY Date DESC LIMIT 10
    """, (user_id,)).fetchall()

    if not assessments:
        # Generate default demo assessment if user is new
        latest_assessment = {
            "FitnessScore": 76.5,
            "StrengthScore": 70.0,
            "FlexibilityScore": 65.0,
            "BalanceScore": 85.0,
            "PostureScore": 80.0,
            "SquatReps": 15,
            "PushupReps": 20,
            "Date": "2026-08-19"
        }
        recs = [
            {"Exercise": "Bodyweight Squats & Romanian Deadlifts", "Duration": "20 mins", "Frequency": "3x / week", "Source": "RandomForestML"},
            {"Exercise": "Hamstring & Hip Flexor Stretching", "Duration": "15 mins", "Frequency": "Daily", "Source": "RuleEngine"}
        ]
        history = [76.5, 72.0, 68.5, 65.0]
    else:
        latest = assessments[0]
        latest_assessment = dict(latest)
        recs_rows = conn.execute("""
            SELECT * FROM Recommendations WHERE AssessmentID = ?
        """, (latest["AssessmentID"],)).fetchall()
        recs = [dict(r) for r in recs_rows]
        history = [a["FitnessScore"] for a in reversed(assessments)]

    plans_rows = conn.execute("""
        SELECT * FROM WorkoutPlans WHERE UserID = ? ORDER BY WeekNumber ASC
    """, (user_id,)).fetchall()
    plans = [dict(p) for p in plans_rows]

    conn.close()

    user_info = dict(user) if user else {"Name": "Alex Rivera", "Age": 24, "Height": 178.0, "Weight": 72.5}

    return jsonify({
        "user": user_info,
        "latest_assessment": latest_assessment,
        "recommendations": recs,
        "workout_plans": plans,
        "fitness_history": history
    })

@app.route("/api/pro-items", methods=["GET"])
def get_pro_items():
    """Returns curated catalogue of professional equipment and athlete gear for all 6 sport modules."""
    sport_filter = request.args.get("sport", "").lower()
    
    items = [
        # 1. Gym & Resistance
        {
            "id": "gym-1",
            "name": "Polly Carbon-Core Lever Powerlifting Belt",
            "sport": "gym",
            "sportLabel": "Gym & Resistance",
            "category": "Strength Gear",
            "price": 89.00,
            "rating": 4.9,
            "reviews": 240,
            "icon": "fa-solid fa-dumbbell",
            "badge": "IPF Approved",
            "specs": ["10mm Full-Grain Leather", "Titanium Quick-Release Lever", "Standard 4-inch Back Width"],
            "biomechanicalBenefit": "Maintains optimal intra-abdominal pressure during sub-90° squats and heavy deadlifts, minimizing spinal shear.",
            "targetMetric": "Strength & Posture",
            "recommendedFor": "Squats & Deadlifts"
        },
        {
            "id": "gym-2",
            "name": "Polly 7mm High-Rebound Neoprene Knee Sleeves",
            "sport": "gym",
            "sportLabel": "Gym & Resistance",
            "category": "Joint Support",
            "price": 49.00,
            "rating": 4.8,
            "reviews": 190,
            "icon": "fa-solid fa-bandage",
            "badge": "Heavy Duty",
            "specs": ["7mm High-Density SCR Neoprene", "3D Anatomical Seams", "Anti-Slip Silicone Grip Ring"],
            "biomechanicalBenefit": "Provides joint compression and thermal retention to stabilize knee tracking at deep flexion angles.",
            "targetMetric": "Strength & Balance",
            "recommendedFor": "Squats & Lunges"
        },
        {
            "id": "gym-3",
            "name": "Polly Laser-Calibrated Fractional Steel Plates (Set)",
            "sport": "gym",
            "sportLabel": "Gym & Resistance",
            "category": "Progression Gear",
            "price": 39.00,
            "rating": 4.9,
            "reviews": 85,
            "icon": "fa-solid fa-weight-hanging",
            "badge": "CNC Machined",
            "specs": ["0.5kg, 1.0kg, 1.5kg, 2.0kg Pairs", "Solid Zinc Plated Steel", "Precision +/- 5g Tolerance"],
            "biomechanicalBenefit": "Allows controlled progressive overload to break strength plateaus without compromising lift form.",
            "targetMetric": "Strength",
            "recommendedFor": "Progressive Overload"
        },
        # 2. Yoga & Mobility
        {
            "id": "yoga-1",
            "name": "Polly Alignment Pro Organic Cork Yoga Mat",
            "sport": "yoga",
            "sportLabel": "Yoga & Mobility",
            "category": "Mobility & Balance",
            "price": 65.00,
            "rating": 5.0,
            "reviews": 310,
            "icon": "fa-solid fa-spa",
            "badge": "Eco-Certified",
            "specs": ["100% Sustainable Natural Cork", "Laser-Etched Kinematic Alignment Grid", "Non-Slip Natural Rubber Base (5mm)"],
            "biomechanicalBenefit": "Laser-etched guidelines ensure exact foot placement and symmetrical shoulder alignment in Warrior II & Tree Pose.",
            "targetMetric": "Flexibility & Balance",
            "recommendedFor": "Tree Pose & Warrior II"
        },
        {
            "id": "yoga-2",
            "name": "Polly Spine-Relief Deep Tissue Mobility Wheel",
            "sport": "yoga",
            "sportLabel": "Yoga & Mobility",
            "category": "Mobility Gear",
            "price": 35.00,
            "rating": 4.8,
            "reviews": 145,
            "icon": "fa-solid fa-circle-notch",
            "badge": "Ergonomic Spine Channel",
            "specs": ["ABS Unbreakable Core (500 lbs limit)", "Sweat-Resistant Textured Padding", "Spine Canal Relief Groove"],
            "biomechanicalBenefit": "Facilitates safe thoracic extension in Bhujangasana (Cobra Pose) and releases anterior shoulder tightness.",
            "targetMetric": "Flexibility & Posture",
            "recommendedFor": "Cobra Pose (Bhujangasana)"
        },
        {
            "id": "yoga-3",
            "name": "Polly High-Density Beveled Bamboo Yoga Blocks (Pair)",
            "sport": "yoga",
            "sportLabel": "Yoga & Mobility",
            "category": "Stability Gear",
            "price": 28.00,
            "rating": 4.9,
            "reviews": 112,
            "icon": "fa-solid fa-cubes",
            "badge": "Solid Bamboo",
            "specs": ["Eco Solid Hardwood Bamboo", "Smooth Beveled Comfort Edges", "Non-Compressible High Stability"],
            "biomechanicalBenefit": "Extends reach and stabilizes pelvic tilt in standing balancing poses without wrist strain.",
            "targetMetric": "Balance & Flexibility",
            "recommendedFor": "Standing Mobility"
        },
        # 3. Basketball Form
        {
            "id": "bball-1",
            "name": "Polly SmartArc 9-Axis Sensor Basketball (Size 7)",
            "sport": "basketball",
            "sportLabel": "Basketball Form",
            "category": "Smart Sensor Gear",
            "price": 129.00,
            "rating": 4.9,
            "reviews": 175,
            "icon": "fa-solid fa-basketball",
            "badge": "Bluetooth 5.3 Telemetry",
            "specs": ["Embedded 9-Axis IMU Sensor", "Real-Time Shot Arc (45-52°) Tracking", "Backspin RPM & Release Velocity"],
            "biomechanicalBenefit": "Measures wrist snap speed, release trajectory, and entry angle to optimize consistent 90° shooting mechanics.",
            "targetMetric": "Posture & Strength",
            "recommendedFor": "Shooting Form Check"
        },
        {
            "id": "bball-2",
            "name": "Polly Precision 90° L-Elbow Shooting Guide Strap",
            "sport": "basketball",
            "sportLabel": "Basketball Form",
            "category": "Kinematic Guide",
            "price": 24.00,
            "rating": 4.7,
            "reviews": 98,
            "icon": "fa-solid fa-arrows-to-dot",
            "badge": "Form Corrector",
            "specs": ["Elastic Memory Webbing", "Adjustable Hook-and-Loop Band", "Prevents Guide-Hand Thumb Flick"],
            "biomechanicalBenefit": "Enforces proper vertical elbow alignment and prevents lateral arm drift during the shooting motion.",
            "targetMetric": "Posture",
            "recommendedFor": "Shooting Set Point"
        },
        {
            "id": "bball-3",
            "name": "Polly Heavy Weighted Training Basketball (1.3kg / 3 lbs)",
            "sport": "basketball",
            "sportLabel": "Basketball Form",
            "category": "Strength & Grip",
            "price": 38.00,
            "rating": 4.8,
            "reviews": 120,
            "icon": "fa-solid fa-hand-fist",
            "badge": "Weight Loaded",
            "specs": ["Official Size 7 Diameter", "Composite Microfiber Leather", "Internal Balanced Weight Core"],
            "biomechanicalBenefit": "Develops forearm and finger-extensor power for higher release points and crisp passing speed.",
            "targetMetric": "Strength",
            "recommendedFor": "Release Follow-Through"
        },
        # 4. Cricket Kinematics
        {
            "id": "cricket-1",
            "name": "Polly SmartSleeve ICC Compliance Bowling Tracker",
            "sport": "cricket",
            "sportLabel": "Cricket Biomechanics",
            "category": "Smart Sensor Gear",
            "price": 115.00,
            "rating": 4.9,
            "reviews": 160,
            "icon": "fa-solid fa-baseball-bat-ball",
            "badge": "ICC Legal <15° Check",
            "specs": ["Gyroscopic Flex Sensor (1000Hz)", "Live Elbow Angle Audio Feedback", "Ultra-Lightweight Compression Lycra"],
            "biomechanicalBenefit": "Instant acoustic alert when bowling arm flexion exceeds 15° legal limit during delivery swing.",
            "targetMetric": "Posture & Balance",
            "recommendedFor": "Bowling Action Straightness"
        },
        {
            "id": "cricket-2",
            "name": "Polly Pro Grade 1 English Willow Bat with Sensor Cavity",
            "sport": "cricket",
            "sportLabel": "Cricket Biomechanics",
            "category": "Pro Weaponry",
            "price": 199.00,
            "rating": 5.0,
            "reviews": 205,
            "icon": "fa-solid fa-shield-halved",
            "badge": "Grade 1 Willow",
            "specs": ["Unbleached Grade 1 English Willow", "Carbon Composite Handle Insertion", "High Sweet Spot for Quick Backlift"],
            "biomechanicalBenefit": "Light pickup weight enables rapid high backlift elevation while maintaining steady head alignment.",
            "targetMetric": "Balance & Strength",
            "recommendedFor": "Batting Stance & Backlift"
        },
        {
            "id": "cricket-3",
            "name": "Polly Micro-Radar Bowling Release Speed & Angle Gauge",
            "sport": "cricket",
            "sportLabel": "Cricket Biomechanics",
            "category": "Kinematic Radar",
            "price": 89.00,
            "rating": 4.8,
            "reviews": 88,
            "icon": "fa-solid fa-gauge-high",
            "badge": "Doppler Radar",
            "specs": ["Digital Doppler Radar (Up to 160 km/h)", "Tripod & Net Mountable", "Instant LED Speed Readout"],
            "biomechanicalBenefit": "Measures arm acceleration efficiency and velocity transfer from run-up stride to release.",
            "targetMetric": "Speed & Posture",
            "recommendedFor": "Bowling Pace Analysis"
        },
        # 5. Athletics & Track
        {
            "id": "ath-1",
            "name": "Polly Carbon-Fly Full-Length Carbon Plate Sprint Spikes",
            "sport": "athletics",
            "sportLabel": "Athletics & Gait",
            "category": "Track & Speed",
            "price": 145.00,
            "rating": 4.9,
            "reviews": 280,
            "icon": "fa-solid fa-person-running",
            "badge": "Full Carbon Plate",
            "specs": ["Full-Length Curved Carbon Fiber Plate", "6-Pin Replaceable Sprint Spike Array", "Engineered Monomesh (140g)"],
            "biomechanicalBenefit": "Provides high energy return at toe-off, naturally reinforcing high forward knee drive angles.",
            "targetMetric": "Speed & Strength",
            "recommendedFor": "Running Gait & Stride"
        },
        {
            "id": "ath-2",
            "name": "Polly Dual-Gate Infrared Laser Sprint Timing Gates",
            "sport": "athletics",
            "sportLabel": "Athletics & Gait",
            "category": "Precision Timing",
            "price": 185.00,
            "rating": 4.9,
            "reviews": 110,
            "icon": "fa-solid fa-stopwatch-20",
            "badge": "Millisecond Precision",
            "specs": ["Dual Optical Infrared Beams", "0.001s Time Resolution", "50m Wireless Range with App Sync"],
            "biomechanicalBenefit": "Captures exact split times from sprint block departure (front 90° / rear 120°) to maximum acceleration.",
            "targetMetric": "Speed",
            "recommendedFor": "Sprint Block Stance"
        },
        {
            "id": "ath-3",
            "name": "Polly Dynamic Drag Sprint Parachute (56-inch)",
            "sport": "athletics",
            "sportLabel": "Athletics & Gait",
            "category": "Resistance Speed",
            "price": 29.00,
            "rating": 4.7,
            "reviews": 150,
            "icon": "fa-solid fa-wind",
            "badge": "Variable Drag",
            "specs": ["Ripstop Aerodynamic Canopy", "360° Quick-Release Swivel Belt", "15-30 lbs Progressive Drag"],
            "biomechanicalBenefit": "Forces the sprinter to maintain a forward 5°-10° torso lean angle under acceleration.",
            "targetMetric": "Strength & Posture",
            "recommendedFor": "Torso Lean & Knee Drive"
        },
        # 6. Kabaddi & Pro Contact
        {
            "id": "kabaddi-1",
            "name": "Polly Pro Mat-Grip High-Traction Kabaddi Shoes",
            "sport": "kabaddi",
            "sportLabel": "Kabaddi & Agility",
            "category": "Court Performance",
            "price": 75.00,
            "rating": 5.0,
            "reviews": 230,
            "icon": "fa-solid fa-shoe-prints",
            "badge": "Mat-Optimized Gum Sole",
            "specs": ["High-Traction Gum Rubber Grip", "Padded Ankle Stabilization Collar", "Ultra-Lightweight Microfiber (220g)"],
            "biomechanicalBenefit": "Prevents court slippage during deep raider toe touches and enables rapid backward retreat deceleration.",
            "targetMetric": "Agility & Balance",
            "recommendedFor": "Raider Toe Touch & Reach"
        },
        {
            "id": "kabaddi-2",
            "name": "Polly Armor-Shield Kevlar Impact Knee & Elbow Guards",
            "sport": "kabaddi",
            "sportLabel": "Kabaddi & Agility",
            "category": "Protective Armor",
            "price": 42.00,
            "rating": 4.9,
            "reviews": 195,
            "icon": "fa-solid fa-shield-halved",
            "badge": "Kevlar Anti-Abrasion",
            "specs": ["Multi-Layer EVA Gel Impact Core", "Kevlar Anti-Friction Surface", "Perforated Air-Flow Neoprene Sleeve"],
            "biomechanicalBenefit": "Shields joints and skin from mat burns during explosive low dubki dives and heavy chain tackles.",
            "targetMetric": "Flexibility & Agility",
            "recommendedFor": "Dubki Evasion & Low Dip"
        },
        {
            "id": "kabaddi-3",
            "name": "Polly Quick-Lock Kinetic Ankle & Wrist Support Braces",
            "sport": "kabaddi",
            "sportLabel": "Kabaddi & Agility",
            "category": "Joint Armor",
            "price": 26.00,
            "rating": 4.8,
            "reviews": 140,
            "icon": "fa-solid fa-lock",
            "badge": "Cross-Strap Lock",
            "specs": ["Figure-8 Cross Locking Straps", "Flexible Medial/Lateral Stabilizers", "Breathable Moisture-Wicking Weave"],
            "biomechanicalBenefit": "Reinforces ankle joint against high rotational torque when locked in defender ankle holds.",
            "targetMetric": "Balance & Agility",
            "recommendedFor": "Defender Chain Stance"
        }
    ]

    if sport_filter:
        filtered = [i for i in items if i["sport"] == sport_filter]
        return jsonify({"items": filtered, "total": len(filtered), "sport": sport_filter})

    return jsonify({"items": items, "total": len(items)})

if __name__ == "__main__":
    print("[Flask Server] Starting AI Fitness Assessment API on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
