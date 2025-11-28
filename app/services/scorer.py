# app/services/scorer.py
from typing import List, Dict
from app.utils.calibration import calculate_tattva_score, calculate_reality_distance

class Scorer:
    @staticmethod
    def calculate_scores(claims: List[Dict], beliefs: List[Dict]) -> Dict:
        """Calculate Tattva Score and Reality Distance."""
        tattva_score = calculate_tattva_score(claims)
        reality_distance = calculate_reality_distance(claims, beliefs)
        
        return {
            "tattva_score": tattva_score,
            "reality_distance": reality_distance
        }