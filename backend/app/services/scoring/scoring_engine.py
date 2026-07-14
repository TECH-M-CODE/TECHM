import yaml
import os
from pathlib import Path

class ScoringEngine:
    """Deterministic mathematical risk engine.
    Computes risk score modifications and limits based on strict rules.
    """
    def __init__(self, policy_path: str = "risk_policy.yaml"):
        # For simplicity, we just define a default static policy here if the file is missing
        self.policy = {
            "bands": {
                "low": {"min": 0, "max": 25},
                "medium": {"min": 26, "max": 60},
                "high": {"min": 61, "max": 85},
                "critical": {"min": 86, "max": 100}
            },
            "events": {
                "transaction": {"low": 1, "medium": 5, "high": 15, "critical": 25},
                "sanction": {"low": 10, "medium": 20, "high": 50, "critical": 100},
                "news": {"low": 0, "medium": 5, "high": 10, "critical": 15},
                "kyc_update": {"low": -5, "medium": -2, "high": 5, "critical": 15}
            },
            "velocity": {
                "threshold_points": 30,
                "window_days": 7
            }
        }
        
        path = Path(policy_path)
        if path.exists():
            with open(path, "r") as f:
                self.policy = yaml.safe_load(f)

    def compute_delta(self, event_type: str, severity: str) -> float:
        """Returns the fixed score modifier for an event type and severity."""
        event_rules = self.policy.get("events", {})
        type_rules = event_rules.get(event_type.lower(), {})
        
        # Default to 0 if unknown event type or severity
        delta = type_rules.get(severity.lower(), 0)
        return float(delta)

    def get_band(self, score: float) -> str:
        """Maps a 0-100 score to its risk band."""
        # Clamp score between 0 and 100
        clamped_score = max(0.0, min(100.0, score))
        
        for band_name, limits in self.policy.get("bands", {}).items():
            if limits["min"] <= clamped_score <= limits["max"]:
                return band_name
                
        return "low"  # Fallback

    def compute_velocity(self, recent_deltas: list[float]) -> bool:
        """Determines if the cumulative score change exceeds the velocity threshold."""
        total_change = sum(d for d in recent_deltas if d > 0) # Only consider positive increases as risk
        threshold = self.policy.get("velocity", {}).get("threshold_points", 30)
        return total_change >= threshold
