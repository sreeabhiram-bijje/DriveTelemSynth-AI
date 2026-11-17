"""Vehicle comparison engine and safety ranking module."""

from typing import Any, Dict, List


def rank_and_compare_vehicles(vehicles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rank vehicles according to telematics safety criteria and compute comparisons."""
    if not vehicles:
        return {
            "rankings": [],
            "comparisons": {},
            "safest_vehicle": None,
            "highest_risk_vehicle": None,
            "best_driver_analysis": {},
        }

    # Sorting with primary: risk_score ascending (lower is safer)
    # Secondary tie-breakers: speeding_ratio ascending, total harsh events ascending
    def sort_key(v):
        risk = float(v.get("risk_score", 100.0))
        speeding = float(v.get("speeding_ratio", 1.0))
        events = float(v.get("harsh_braking_events", 10.0)) + float(v.get("harsh_acceleration_events", 10.0))
        return (risk, speeding, events)

    sorted_vehicles = sorted(vehicles, key=sort_key)

    # Assign safety ranks (1 = Safest)
    for rank_idx, v in enumerate(sorted_vehicles, start=1):
        v["safety_rank"] = rank_idx

    safest = sorted_vehicles[0]
    highest_risk = sorted_vehicles[-1]

    # Generate explanation for the safest vehicle
    safest_id = safest.get("vehicle_id", "VEH-001")
    safest_name = safest.get("vehicle_name", safest_id)
    safest_score = safest.get("risk_score", 0.0)
    safest_speed = safest.get("average_speed", 0.0)
    safest_speeding = safest.get("speeding_ratio", 0.0) * 100.0
    safest_braking = safest.get("harsh_braking_events", 0.0)

    # Clear check: does lowest risk necessarily equal slowest vehicle?
    slowest_vehicle = min(vehicles, key=lambda v: float(v.get("average_speed", 999.0)))
    slowest_id = slowest_vehicle.get("vehicle_id")

    if safest_id == slowest_id:
        speed_insight = (
            f"While {safest_name} operated at a cautious average speed of {safest_speed} km/h, "
            f"its top ranking is directly driven by minimal speeding ({safest_speeding:.1f}%) and "
            f"low harsh braking ({safest_braking} events/trip), not simply by traveling slowly."
        )
    else:
        speed_insight = (
            f"Notably, {safest_name} achieved Rank #1 despite not being the slowest vehicle in the fleet, "
            f"demonstrating that smooth throttle control, adherence to posted limits ({safest_speeding:.1f}% speeding), "
            f"and defensive braking ({safest_braking} events/trip) outweigh pure crawl speed."
        )

    best_driver_analysis = {
        "safest_vehicle_id": safest_id,
        "safest_vehicle_name": safest_name,
        "safest_risk_score": safest_score,
        "highest_risk_vehicle_id": highest_risk.get("vehicle_id"),
        "highest_risk_vehicle_name": highest_risk.get("vehicle_name"),
        "highest_risk_score": highest_risk.get("risk_score"),
        "lowest_risk_score": safest_score,
        "best_insurance_category": safest.get("insurance_category", "Preferred Safe Driver"),
        "safety_reason": speed_insight,
    }

    # Comparative metric lists for UI rendering and charts
    comparisons = {
        "vehicle_ids": [v.get("vehicle_id", f"VEH-{i+1}") for i, v in enumerate(vehicles)],
        "vehicle_names": [v.get("vehicle_name", v.get("vehicle_id", f"VEH-{i+1}")) for i, v in enumerate(vehicles)],
        "average_speed": {v.get("vehicle_id"): v.get("average_speed", 0.0) for v in vehicles},
        "maximum_speed": {v.get("vehicle_id"): v.get("maximum_speed", 0.0) for v in vehicles},
        "total_distance": {v.get("vehicle_id"): v.get("total_distance", 0.0) for v in vehicles},
        "harsh_braking": {v.get("vehicle_id"): v.get("harsh_braking_events", 0.0) for v in vehicles},
        "harsh_acceleration": {v.get("vehicle_id"): v.get("harsh_acceleration_events", 0.0) for v in vehicles},
        "night_driving_ratio": {v.get("vehicle_id"): round(float(v.get("night_driving_ratio", 0.0)) * 100.0, 1) for v in vehicles},
        "speeding_ratio": {v.get("vehicle_id"): round(float(v.get("speeding_ratio", 0.0)) * 100.0, 1) for v in vehicles},
        "risk_scores": {v.get("vehicle_id"): v.get("risk_score", 0.0) for v in vehicles},
        "insurance_eligibility": {v.get("vehicle_id"): v.get("insurance_eligibility", "Standard") for v in vehicles},
        "simulated_premiums": {v.get("vehicle_id"): v.get("final_simulated_premium", 10000.0) for v in vehicles},
    }

    return {
        "rankings": sorted_vehicles,
        "comparisons": comparisons,
        "safest_vehicle": safest,
        "highest_risk_vehicle": highest_risk,
        "best_driver_analysis": best_driver_analysis,
    }
