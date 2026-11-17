"""Intelligent insurance assessment engine for driving telematics.

Calculates illustrative insurance tiers, safe-driving discounts,
and simulated premiums based on heuristic telematics risk scores.
"""

from typing import Any, Dict, List, Optional


def assess_insurance_for_vehicle(
    vehicle: Dict[str, Any],
    base_premium: float = 10000.0,
    preferred_discount: float = 20.0,
    standard_discount: float = 5.0,
) -> Dict[str, Any]:
    """Assess insurance tier, discount percentage, and simulated premium for a vehicle."""
    score = float(vehicle.get("risk_score", 50.0))
    vehicle_id = vehicle.get("vehicle_id", "UNKNOWN")

    if score < 35.0:
        risk_category = "Low Risk"
        insurance_category = "Preferred Safe Driver"
        eligibility_status = "Eligible - Preferred Tier"
        discount_pct = float(preferred_discount)
        status_color = "#10b981"  # Green
        status_tag = "preferred"
        explanation = (
            f"Vehicle {vehicle_id} achieved an exemplary risk score of {score:.1f}/100. "
            "Defensive driving patterns, low speeding ratios, and rare harsh maneuvers qualify "
            f"this vehicle for the maximum safe-driving discount of {discount_pct:.0f}%."
        )
    elif score < 65.0:
        risk_category = "Medium Risk"
        insurance_category = "Standard Coverage"
        eligibility_status = "Eligible - Standard Tier"
        discount_pct = float(standard_discount)
        status_color = "#f59e0b"  # Amber/Yellow
        status_tag = "standard"
        explanation = (
            f"Vehicle {vehicle_id} logged a moderate risk score of {score:.1f}/100. "
            "Driving telemetry exhibits acceptable road safety with occasional harsh events or "
            f"speed variance, earning a baseline discount of {discount_pct:.0f}%."
        )
    else:
        risk_category = "High Risk"
        insurance_category = "High Risk / Surcharge Tier"
        eligibility_status = "Review Required / Surcharge"
        discount_pct = 0.0
        status_color = "#ef4444"  # Red
        status_tag = "high-risk"
        explanation = (
            f"Vehicle {vehicle_id} registered an elevated risk score of {score:.1f}/100. "
            "Telemetry reveals recurrent harsh events, elevated speeding relative to conditions, "
            "or frequent night driving. No safe-driver discount is awarded."
        )

    discount_amount = round(base_premium * (discount_pct / 100.0), 2)
    final_premium = round(base_premium - discount_amount, 2)

    return {
        "insurance_category": insurance_category,
        "insurance_eligibility": eligibility_status,
        "eligibility_status": eligibility_status,
        "risk_category": risk_category,
        "base_premium": round(float(base_premium), 2),
        "insurance_discount": discount_pct,
        "discount_percentage": discount_pct,
        "discount_amount": discount_amount,
        "simulated_premium": final_premium,
        "final_simulated_premium": final_premium,
        "status_color": status_color,
        "status_tag": status_tag,
        "decision_explanation": explanation,
        "disclaimer": (
            "Simulated telematics insurance assessment for model evaluation only; "
            "not a legally binding underwriting commitment or actual quotation."
        ),
    }


def assess_fleet_insurance(
    vehicles: List[Dict[str, Any]],
    base_premium: float = 10000.0,
    preferred_discount: float = 20.0,
    standard_discount: float = 5.0,
) -> List[Dict[str, Any]]:
    """Assess insurance for a list of vehicles and return enriched list."""
    results = []
    for v in vehicles:
        assessment = assess_insurance_for_vehicle(
            v,
            base_premium=base_premium,
            preferred_discount=preferred_discount,
            standard_discount=standard_discount,
        )
        merged = {**v, **assessment}
        results.append(merged)
    return results
