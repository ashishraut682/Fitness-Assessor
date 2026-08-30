from metrics import calculate_angle, calculate_body_stability, calculate_arm_horizon, calculate_spine_lean

class MultiSportAnalyzer:
    """
    Comprehensive multi-sport pose analyzer for Gym, Yoga, Basketball, Cricket, and Athletics.
    """
    def __init__(self):
        # Repetition State Counters
        self.rep_counters = {
            "squat": 0, "pushup": 0, "lunge": 0, "deadlift": 0,
            "shooting_form": 0, "bowling_action": 0, "sprint_stride": 0
        }
        self.stages = {
            "squat": "UP", "pushup": "UP", "lunge": "UP", "deadlift": "UP",
            "shooting_form": "SET", "bowling_action": "START", "sprint_stride": "DRIVE"
        }
        self.min_angles = {"squat": 180.0, "pushup": 180.0}

    def analyze_frame(self, landmarks, category="gym", exercise="squat"):
        if not landmarks or len(landmarks) < 12:
            return {
                "status": "No landmarks detected",
                "rep_count": 0,
                "stage": "UNKNOWN",
                "feedback": "Position full body in camera frame",
                "angles": {}
            }

        def get_pt(idx):
            lm = landmarks.get(idx, {})
            return (lm.get("x", 0.0), lm.get("y", 0.0), lm.get("z", 0.0))

        # Key Landmarks Map
        l_ear, r_ear = get_pt(7), get_pt(8)
        l_shoulder, r_shoulder = get_pt(11), get_pt(12)
        l_elbow, r_elbow = get_pt(13), get_pt(14)
        l_wrist, r_wrist = get_pt(15), get_pt(16)
        l_hip, r_hip = get_pt(23), get_pt(24)
        l_knee, r_knee = get_pt(25), get_pt(26)
        l_ankle, r_ankle = get_pt(27), get_pt(28)

        stability = calculate_body_stability(l_shoulder, r_shoulder, l_hip, r_hip)
        cat = category.lower()
        ex = exercise.lower()

        # ==========================================
        # 1. GYM MODULE
        # ==========================================
        if cat == "gym":
            if ex == "squat":
                l_knee_angle = calculate_angle(l_hip, l_knee, l_ankle)
                r_knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
                knee_angle = round((l_knee_angle + r_knee_angle) / 2.0, 1)

                if knee_angle < self.min_angles["squat"]:
                    self.min_angles["squat"] = knee_angle

                if knee_angle > 160:
                    if self.stages["squat"] == "DOWN":
                        self.rep_counters["squat"] += 1
                        feedback = "Great Squat Rep! Full depth (<90°) achieved." if self.min_angles["squat"] <= 90 else "Rep counted, but squat deeper."
                        self.min_angles["squat"] = 180.0
                    else:
                        feedback = "Descent into squat position..."
                    self.stages["squat"] = "UP"
                elif knee_angle <= 95 and self.stages["squat"] == "UP":
                    self.stages["squat"] = "DOWN"
                    feedback = "Push up through heels!"
                else:
                    feedback = "Maintain knee alignment over toes..."

                return {
                    "category": "Gym", "exercise": "Squat",
                    "rep_count": self.rep_counters["squat"], "stage": self.stages["squat"],
                    "feedback": feedback, "stability_score": stability,
                    "angles": {"knee_angle": knee_angle, "left_knee": l_knee_angle, "right_knee": r_knee_angle}
                }

            elif ex == "pushup":
                l_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                r_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                elbow_angle = round((l_elbow_angle + r_elbow_angle) / 2.0, 1)
                plank_line = calculate_angle(l_shoulder, l_hip, l_ankle)

                if elbow_angle < self.min_angles["pushup"]:
                    self.min_angles["pushup"] = elbow_angle

                if elbow_angle > 160:
                    if self.stages["pushup"] == "DOWN":
                        self.rep_counters["pushup"] += 1
                        feedback = "Excellent Pushup Form!" if self.min_angles["pushup"] <= 90 and plank_line >= 160 else "Keep core tight & lower chest."
                        self.min_angles["pushup"] = 180.0
                    else:
                        feedback = "Lower chest to ground..."
                    self.stages["pushup"] = "UP"
                elif elbow_angle <= 95 and self.stages["pushup"] == "UP":
                    self.stages["pushup"] = "DOWN"
                    feedback = "Press firmly back up!"
                else:
                    feedback = "Maintain rigid plank line..."

                return {
                    "category": "Gym", "exercise": "Pushup",
                    "rep_count": self.rep_counters["pushup"], "stage": self.stages["pushup"],
                    "feedback": feedback, "stability_score": stability,
                    "angles": {"elbow_angle": elbow_angle, "plank_alignment": plank_line}
                }

            elif ex == "plank":
                plank_angle = calculate_angle(l_shoulder, l_hip, l_ankle)
                feedback = "Perfect Core Plank Line!" if plank_angle >= 165 else "Adjust hips - don't sag lower back."
                return {
                    "category": "Gym", "exercise": "Plank",
                    "rep_count": 1, "stage": "HOLDING",
                    "feedback": feedback, "stability_score": stability,
                    "angles": {"plank_line_angle": plank_angle}
                }

            elif ex == "lunge":
                front_knee = calculate_angle(l_hip, l_knee, l_ankle)
                if front_knee < 100 and self.stages["lunge"] == "UP":
                    self.stages["lunge"] = "DOWN"
                    self.rep_counters["lunge"] += 1
                    feedback = "Great Lunge Stride! Push back up."
                else:
                    self.stages["lunge"] = "UP"
                    feedback = "Step forward into 90° lunge stance."
                return {
                    "category": "Gym", "exercise": "Lunge",
                    "rep_count": self.rep_counters["lunge"], "stage": self.stages["lunge"],
                    "feedback": feedback, "stability_score": stability,
                    "angles": {"front_knee_angle": front_knee}
                }

        # ==========================================
        # 2. YOGA MODULE
        # ==========================================
        elif cat == "yoga":
            if ex == "tree_pose":
                lifted_knee = calculate_angle(r_hip, r_knee, r_ankle)
                spine_vert = calculate_spine_lean(l_ear, l_hip, l_ankle)
                feedback = "Excellent Vrksasana Balance & Alignment!" if stability > 80 and spine_vert < 8 else "Focus gaze on static point & align spine."
                return {
                    "category": "Yoga", "exercise": "Tree Pose (Vrksasana)",
                    "stage": "BALANCING", "feedback": feedback, "stability_score": stability,
                    "angles": {"lifted_knee_angle": lifted_knee, "spine_lean": spine_vert}
                }

            elif ex == "warrior_ii":
                front_knee = calculate_angle(l_hip, l_knee, l_ankle)
                arm_horizon = calculate_arm_horizon(l_shoulder, l_wrist, r_shoulder, r_wrist)
                feedback = "Strong Virabhadrasana II Pose! Front leg at 90°." if front_knee <= 95 and arm_horizon > 85 else "Extend arms parallel to horizon and sink hips."
                return {
                    "category": "Yoga", "exercise": "Warrior II (Virabhadrasana II)",
                    "stage": "HOLDING", "feedback": feedback, "stability_score": stability,
                    "angles": {"front_knee_angle": front_knee, "arm_horizon_score": arm_horizon}
                }

            elif ex == "cobra_pose":
                torso_ext = calculate_angle(l_ear, l_shoulder, l_hip)
                feedback = "Good Bhujangasana Extension! Open chest." if torso_ext > 140 else "Gently extend chest up while pressing palms."
                return {
                    "category": "Yoga", "exercise": "Cobra Pose (Bhujangasana)",
                    "stage": "EXTENDING", "feedback": feedback, "stability_score": stability,
                    "angles": {"lumbar_extension": torso_ext}
                }

        # ==========================================
        # 3. BASKETBALL MODULE
        # ==========================================
        elif cat == "basketball":
            if ex == "shooting_form":
                shooting_elbow = calculate_angle(r_shoulder, r_elbow, r_wrist)
                knee_dip = calculate_angle(r_hip, r_knee, r_ankle)

                if shooting_elbow <= 100:
                    self.stages["shooting_form"] = "SET"
                    feedback = "Good L-Shape Set Point (90° elbow). Jump & extend!"
                elif shooting_elbow >= 155 and self.stages["shooting_form"] == "SET":
                    self.stages["shooting_form"] = "RELEASE"
                    self.rep_counters["shooting_form"] += 1
                    feedback = "High Release & Follow-Through Wrist Snap!"
                else:
                    feedback = "Load knees into shooting stance..."

                return {
                    "category": "Basketball", "exercise": "Shooting Form Check",
                    "rep_count": self.rep_counters["shooting_form"], "stage": self.stages["shooting_form"],
                    "feedback": feedback, "stability_score": stability,
                    "angles": {"shooting_elbow_angle": shooting_elbow, "knee_dip_angle": knee_dip}
                }

            elif ex == "defensive_stance":
                stance_knee = calculate_angle(l_hip, l_knee, l_ankle)
                arm_span = calculate_arm_horizon(l_shoulder, l_wrist, r_shoulder, r_wrist)
                feedback = "Low Center of Gravity Defensive Stance!" if stance_knee <= 110 else "Bend knees deeper and widen arm contest."
                return {
                    "category": "Basketball", "exercise": "Defensive Stance",
                    "stage": "STANCE", "feedback": feedback, "stability_score": stability,
                    "angles": {"stance_knee_flex": stance_knee, "arm_span_reach": arm_span}
                }

        # ==========================================
        # 4. CRICKET MODULE
        # ==========================================
        elif cat == "cricket":
            if ex == "batting_stance":
                backlift_elbow = calculate_angle(r_shoulder, r_elbow, r_wrist)
                head_align = abs(l_ear[0] - l_knee[0]) * 100
                feedback = "Balanced Batting Stance & High Backlift!" if backlift_elbow <= 110 else "Raise high backlift elbow and keep head still."
                return {
                    "category": "Cricket", "exercise": "Batting Stance Check",
                    "stage": "STANCE", "feedback": feedback, "stability_score": stability,
                    "angles": {"backlift_elbow_angle": backlift_elbow, "head_knee_offset": round(head_align, 1)}
                }

            elif ex == "bowling_action":
                bowling_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
                is_legal = bowling_arm >= 165  # Straight arm rule check (<15° flex)
                feedback = "Legal Straight Bowling Arm Delivery!" if is_legal else "Warning: Elbow flex > 15° detected during release."
                return {
                    "category": "Cricket", "exercise": "Bowling Action Straightness Check",
                    "stage": "DELIVERY", "feedback": feedback, "stability_score": stability,
                    "angles": {"bowling_arm_straightness": bowling_arm, "legal_compliance": is_legal}
                }

        # ==========================================
        # 5. ATHLETICS MODULE
        # ==========================================
        elif cat == "athletics":
            if ex == "running_gait":
                knee_drive = calculate_angle(l_hip, l_knee, l_ankle)
                torso_lean = calculate_spine_lean(l_ear, l_hip, l_ankle)
                feedback = "High Knee Drive & Optimal Torso Lean!" if knee_drive <= 85 else "Drive lead knee higher and maintain 5°-10° forward lean."
                return {
                    "category": "Athletics", "exercise": "Running Gait & Posture",
                    "stage": "STRIDE", "feedback": feedback, "stability_score": stability,
                    "angles": {"knee_drive_angle": knee_drive, "torso_forward_lean": torso_lean}
                }

            elif ex == "sprint_start":
                front_knee = calculate_angle(l_hip, l_knee, l_ankle)
                rear_knee = calculate_angle(r_hip, r_knee, r_ankle)
                feedback = "Optimal Set Stance Angles (Front 90°, Rear 120°)!" if 80 <= front_knee <= 100 else "Adjust block angles for maximum explosive acceleration."
                return {
                    "category": "Athletics", "exercise": "Sprint Block Stance",
                    "stage": "SET", "feedback": feedback, "stability_score": stability,
                    "angles": {"front_knee_angle": front_knee, "rear_knee_angle": rear_knee}
                }

        # Fallback default
        return {
            "category": category.capitalize(), "exercise": exercise.capitalize(),
            "stage": "ACTIVE", "feedback": "Monitoring pose kinematics",
            "stability_score": stability, "angles": {}
        }
