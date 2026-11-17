"""Intelligent rule-based safety recommendation engine."""

from typing import Any, Dict, List


def generate_recommendations_for_vehicle(
    vehicle: Dict[str, Any], road_speed_limit: float = 80.0
) -> List[Dict[str, str]]:
    """Produce tailored, factor-specific safety recommendations for a vehicle."""
    recommendations = []

    speeding_ratio = float(vehicle.get("speeding_ratio", 0.0))
    avg_speed = float(vehicle.get("average_speed", 0.0))
    harsh_braking = float(vehicle.get("harsh_braking_events", 0.0))
    harsh_accel = float(vehicle.get("harsh_acceleration_events", 0.0))
    night_ratio = float(vehicle.get("night_driving_ratio", 0.0))
    risk_score = float(vehicle.get("risk_score", 0.0))

    # 1. Speeding Evaluation
    if speeding_ratio >= 0.35 or avg_speed > road_speed_limit:
        recommendations.append(
            {
                "category": "Speed Compliance",
                "severity": "critical" if speeding_ratio >= 0.50 else "warning",
                "recommendation": (
                    f"Maintain speed within the posted road speed limit ({road_speed_limit:.0f} km/h). "
                    f"Vehicle recorded {speeding_ratio * 100:.1f}% time speeding, significantly inflating risk points."
                ),
            }
        )
    elif speeding_ratio >= 0.15:
        recommendations.append(
            {
                "category": "Speed Compliance",
                "severity": "advisory",
                "recommendation": (
                    "Monitor speedometer during highway transitions; minor speeding was observed on some trip segments."
                ),
            }
        )

    # 2. Harsh Braking Evaluation
    if harsh_braking >= 2.5:
        recommendations.append(
            {
                "category": "Following Distance & Deceleration",
                "severity": "critical",
                "recommendation": (
                    "Maintain a safe 3-to-4 second following distance and anticipate traffic flow early "
                    f"to avoid high deceleration incidents ({harsh_braking:.1f} events/trip)."
                ),
            }
        )
    elif harsh_braking >= 1.0:
        recommendations.append(
            {
                "category": "Following Distance & Deceleration",
                "severity": "advisory",
                "recommendation": (
                    "Gentle, progressive brake application will reduce brake pad wear and lower telematics risk."
                ),
            }
        )

    # 3. Harsh Acceleration Evaluation
    if harsh_accel >= 2.0:
        recommendations.append(
            {
                "category": "Throttle Control",
                "severity": "warning",
                "recommendation": (
                    "Use gradual acceleration from stops and avoid sudden speed surges. "
                    f"Frequent rapid accelerations ({harsh_accel:.1f} events/trip) degrade fuel economy."
                ),
            }
        )

    # 4. Night Driving Evaluation
    if night_ratio >= 0.25:
        recommendations.append(
            {
                "category": "Visibility & Fatigue",
                "severity": "warning" if night_ratio >= 0.40 else "advisory",
                "recommendation": (
                    "Take additional precautions during night driving (accounting for "
                    f"{night_ratio * 100:.1f}% of travel). Ensure headlamp clarity and take breaks to manage driver fatigue."
                ),
            }
        )

    # 5. Overall Risk & Positive Reinforcement
    if risk_score >= 65.0:
        recommendations.append(
            {
                "category": "Comprehensive Telematics Coaching",
                "severity": "critical",
                "recommendation": (
                    "Overall driving behaviour places this vehicle in the High Risk tier. "
                    "Enroll in a telematics defensive driving module to qualify for insurance discounts."
                ),
            }
        )
    elif risk_score < 35.0 and len(recommendations) == 0:
        recommendations.append(
            {
                "category": "Exemplary Driving",
                "severity": "success",
                "recommendation": (
                    "Exceptional driving discipline observed across all telematics indicators. "
                    "Maintain current habits to retain maximum safe-driver insurance rewards."
                ),
            }
        )
    elif risk_score < 35.0:
        recommendations.append(
            {
                "category": "Preferred Tier Maintenance",
                "severity": "success",
                "recommendation": (
                    "Qualifies for preferred insurance rating. Continue defensive driving discipline."
                ),
            }
        )

    return recommendations
