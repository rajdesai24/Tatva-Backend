# app/utils/calibration.py
import numpy as np
from typing import List  # Add this line

def calibrate_probability(prob: float, temperature: float = 1.45) -> float:
    """
    Apply temperature scaling to calibrate probability.
    """
    # Avoid division by zero and log of zero
    prob = np.clip(prob, 0.005, 0.995)
    
    # Apply temperature scaling via logit transformation
    logit = np.log(prob / (1 - prob))
    calibrated_logit = logit / temperature
    calibrated_prob = 1 / (1 + np.exp(-calibrated_logit))
    
    # Clamp to valid range
    return float(np.clip(calibrated_prob, 0.005, 0.995))

def calculate_evidence_strength(
    credibility: float,
    specificity: float,
    recency: float,
    diversity: float,
    modality_align: float,
    primary_source_bonus: float
) -> float:
    """
    Calculate evidence strength score.
    E = 0.35*Cred + 0.20*Spec + 0.15*Rec + 0.15*Div + 0.10*Mod + 0.05*Primary
    """
    return (
        0.35 * credibility +
        0.20 * specificity +
        0.15 * recency +
        0.15 * diversity +
        0.10 * modality_align +
        0.05 * primary_source_bonus
    )

def calculate_tattva_score(
    claims: List,
    calibration_temp: float = 1.45
) -> float:
    """
    Calculate overall Tattva Score.
    """
    if not claims:
        return 0.0
    
    # Calculate normalized weights
    weights = []
    for claim in claims:
        prominence = claim.get('prominence', 0.5)
        evidence_strength = claim.get('evidence_strength', 0.5)
        weight = prominence * (0.5 + 0.5 * evidence_strength)
        weights.append(weight)
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        alpha = [1.0 / len(claims)] * len(claims)
    else:
        alpha = [w / total_weight for w in weights]
    
    # Calculate base score
    base_score = 0.0
    for i, claim in enumerate(claims):
        truth_prob_cal = claim['verdict']['truth_prob_cal']
        base_score += alpha[i] * truth_prob_cal
    base_score *= 100
    
    # Calculate penalties
    conflict_rate = sum(
        1 for claim in claims 
        if claim['verdict']['label'] == 'mixed'
    ) / len(claims)
    
    thin_evidence_rate = sum(
        1 for claim in claims 
        if claim.get('evidence_strength', 1.0) < 0.35
    ) / len(claims)
    
    penalty = 100 * (0.4 * conflict_rate + 0.3 * thin_evidence_rate)
    
    # Final score
    tattva_score = base_score - penalty
    return float(np.clip(tattva_score, 0.0, 100.0))

def calculate_reality_distance(
    claims: List,
    beliefs: List
) -> dict:
    """
    Calculate Reality Distance if beliefs are provided.
    """
    if not beliefs:
        return {
            "status": "needs_user_input",
            "value": 0.0,
            "notes": "No user beliefs provided. Create belief sliders to measure Reality Distance."
        }
    
    # Create belief map
    belief_map = {b['claim_id']: b['p'] for b in beliefs}
    
    # Calculate weights
    weights = []
    for claim in claims:
        prominence = claim.get('prominence', 0.5)
        evidence_strength = claim.get('evidence_strength', 0.5)
        weight = prominence * (0.5 + 0.5 * evidence_strength)
        weights.append(weight)
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        alpha = [1.0 / len(claims)] * len(claims)
    else:
        alpha = [w / total_weight for w in weights]
    
    # Calculate weighted mean absolute deviation
    reality_distance = 0.0
    matched_claims = 0
    
    for i, claim in enumerate(claims):
        claim_id = claim['id']
        if claim_id in belief_map:
            user_belief = belief_map[claim_id]
            truth_prob_cal = claim['verdict']['truth_prob_cal']
            reality_distance += alpha[i] * abs(user_belief - truth_prob_cal)
            matched_claims += 1
    
    reality_distance *= 100
    
    return {
        "status": "ok",
        "value": float(np.clip(reality_distance, 0.0, 100.0)),
        "notes": f"Based on {matched_claims} matched beliefs out of {len(claims)} claims."
    }