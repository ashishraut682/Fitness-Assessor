from ml_model import MLRecommendationModel

class RecommendationEngine:
    def __init__(self):
        self.ml_model = MLRecommendationModel()

    def generate_recommendations(self, strength, flexibility, balance, posture):
        """
        Generates hybrid recommendations combining rule-based heuristics 
        and RandomForest ML predictions.
        """
        rules_recommendations = []

        # Rule 1: Strength Check
        if strength < 60:
            rules_recommendations.append({
                "exercise": "Bodyweight Squats & Standard Pushups",
                "duration": "20 mins",
                "frequency": "3x / week",
                "reason": "Strength score is below 60. Focus on progressive compound resistance movements.",
                "source": "RuleEngine"
            })

        # Rule 2: Flexibility Check
        if flexibility < 60:
            rules_recommendations.append({
                "exercise": "Hamstring Stretch, Cobra Pose & Hip Openers",
                "duration": "15 mins",
                "frequency": "Daily",
                "reason": "Flexibility score is below 60. Daily mobility drills recommended to improve squat depth.",
                "source": "RuleEngine"
            })

        # Rule 3: Balance Check
        if balance < 60:
            rules_recommendations.append({
                "exercise": "Single-Leg Stance & Plank Holds",
                "duration": "15 mins",
                "frequency": "4x / week",
                "reason": "Balance/Stability score is below 60. Core stabilization exercises recommended.",
                "source": "RuleEngine"
            })

        # Rule 4: Posture Check
        if posture < 60:
            rules_recommendations.append({
                "exercise": "Wall Slides & Scapular Retraction Drills",
                "duration": "10 mins",
                "frequency": "Daily",
                "reason": "Posture alignment score is below 60. Scapular and spinal alignment needed.",
                "source": "RuleEngine"
            })

        # ML Model Prediction
        ml_prediction, ml_confidence = self.ml_model.predict(strength, flexibility, balance, posture)
        ml_rec = {
            "exercise": ml_prediction,
            "duration": "25 mins",
            "frequency": "3x / week",
            "reason": f"AI Machine Learning model prediction based on overall metric pattern ({ml_confidence}% confidence).",
            "source": "RandomForestML"
        }

        # Combine results
        all_recs = [ml_rec] + rules_recommendations
        return all_recs

    def generate_workout_plan(self, user_id, fitness_score):
        """Generates a 4-week structured workout plan matching user level."""
        if fitness_score >= 80:
            intensity = "Advanced"
            plan = [
                {"week": 1, "exercise": "Jump Squats & Diamond Pushups", "sets": 4, "reps": 15},
                {"week": 2, "exercise": "Bulgarian Split Squats & Decline Pushups", "sets": 4, "reps": 12},
                {"week": 3, "exercise": "Pistol Squats & Archer Pushups", "sets": 3, "reps": 8},
                {"week": 4, "exercise": "Plyometric Circuit & Plank Hold (90s)", "sets": 4, "reps": 20}
            ]
        elif fitness_score >= 60:
            intensity = "Intermediate"
            plan = [
                {"week": 1, "exercise": "Bodyweight Squats & Pushups", "sets": 3, "reps": 12},
                {"week": 2, "exercise": "Goblet Squats & Incline Pushups", "sets": 3, "reps": 15},
                {"week": 3, "exercise": "Walking Lunges & Standard Pushups", "sets": 3, "reps": 12},
                {"week": 4, "exercise": "Sumo Squats & Plank Hold (60s)", "sets": 4, "reps": 15}
            ]
        else:
            intensity = "Beginner / Remedial"
            plan = [
                {"week": 1, "exercise": "Box Squats & Wall Pushups", "sets": 3, "reps": 10},
                {"week": 2, "exercise": "Supported Squats & Knee Pushups", "sets": 3, "reps": 12},
                {"week": 3, "exercise": "Bodyweight Squats & Knee Pushups", "sets": 3, "reps": 15},
                {"week": 4, "exercise": "Standard Squats & Countertop Pushups", "sets": 3, "reps": 12}
            ]

        return {"intensity": intensity, "schedule": plan}
