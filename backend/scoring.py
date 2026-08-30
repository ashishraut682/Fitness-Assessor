class FitnessScorer:
    """
    Computes overall weighted Fitness Score (0-100) based on sub-metrics:
      - Strength Score (30%)
      - Flexibility Score (25%)
      - Balance Score (20%)
      - Posture Score (25%)
    """
    STRENGTH_WEIGHT = 0.30
    FLEXIBILITY_WEIGHT = 0.25
    BALANCE_WEIGHT = 0.20
    POSTURE_WEIGHT = 0.25

    @classmethod
    def calculate_fitness_score(cls, strength, flexibility, balance, posture):
        """
        Calculates composite fitness score and sub-score breakdown.
        `strength`, `flexibility`, `balance`, `posture` are floats between 0 and 100.
        """
        strength = max(0.0, min(100.0, float(strength)))
        flexibility = max(0.0, min(100.0, float(flexibility)))
        balance = max(0.0, min(100.0, float(balance)))
        posture = max(0.0, min(100.0, float(posture)))

        weighted_score = (
            (strength * cls.STRENGTH_WEIGHT) +
            (flexibility * cls.FLEXIBILITY_WEIGHT) +
            (balance * cls.BALANCE_WEIGHT) +
            (posture * cls.POSTURE_WEIGHT)
        )

        fitness_score = round(weighted_score, 1)

        # Rating Category
        if fitness_score >= 85.0:
            tier = "Excellent (Athlete Level)"
        elif fitness_score >= 70.0:
            tier = "Good (Fit)"
        elif fitness_score >= 50.0:
            tier = "Moderate (Needs Work)"
        else:
            tier = "Novice / Attention Required"

        return {
            "fitness_score": fitness_score,
            "tier": tier,
            "breakdown": {
                "strength": round(strength, 1),
                "flexibility": round(flexibility, 1),
                "balance": round(balance, 1),
                "posture": round(posture, 1)
            }
        }

    @classmethod
    def compute_strength_from_reps(cls, squats, pushups):
        """Estimate strength score (0-100) based on rep counts."""
        # Baseline benchmarks: 25 squats and 25 pushups = 100% strength score
        squat_score = min(100.0, (squats / 25.0) * 100.0)
        pushup_score = min(100.0, (pushups / 25.0) * 100.0)
        return round((squat_score * 0.5) + (pushup_score * 0.5), 1)
