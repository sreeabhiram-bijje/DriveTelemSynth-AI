"""Multi-vehicle synthetic driving telematics generation module.

Generates comparative synthetic telematics for 2 to 5 vehicles with
configurable driving speeds, behaviours, and road conditions.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from faker import Faker

from analytics.insurance import assess_insurance_for_vehicle
from analytics.recommendations import generate_recommendations_for_vehicle
from analytics.vehicle_comparison import rank_and_compare_vehicles
from generator.risk_scoring import add_risk_scores

DEFAULT_VEHICLE_PRESETS: List[Dict[str, Any]] = [
    {
        "vehicle_id": "VEH-001",
        "vehicle_name": "Vehicle A (Eco Commuter)",
        "vehicle_category": "Slow",
        "target_speed": 35.0,
        "driving_behaviour": "Safe",
        "color": "#10b981",  # Emerald
    },
    {
        "vehicle_id": "VEH-002",
        "vehicle_name": "Vehicle B (Family SUV)",
        "vehicle_category": "Medium",
        "target_speed": 65.0,
        "driving_behaviour": "Moderate",
        "color": "#0ea5e9",  # Sky Blue
    },
    {
        "vehicle_id": "VEH-003",
        "vehicle_name": "Vehicle C (Express Coupe)",
        "vehicle_category": "High",
        "target_speed": 110.0,
        "driving_behaviour": "Aggressive",
        "color": "#f43f5e",  # Rose Red
    },
    {
        "vehicle_id": "VEH-004",
        "vehicle_name": "Vehicle D (City Hatchback)",
        "vehicle_category": "Slow",
        "target_speed": 40.0,
        "driving_behaviour": "Safe",
        "color": "#a855f7",  # Purple
    },
    {
        "vehicle_id": "VEH-005",
        "vehicle_name": "Vehicle E (Commercial Van)",
        "vehicle_category": "Medium",
        "target_speed": 75.0,
        "driving_behaviour": "Moderate",
        "color": "#f59e0b",  # Amber
    },
]


def _build_vehicle_trip_samples(
    config: Dict[str, Any],
    records: int,
    road_speed_limit: float,
    rng: np.random.Generator,
) -> tuple:
    target_speed = float(config.get("target_speed", 50.0))
    behaviour = str(config.get("driving_behaviour", "Moderate"))

    # Behaviour-based distributions
    if behaviour == "Safe":
        distance_min, distance_max = 3.0, 45.0
        speed_delta = 7.0
        accel_min, accel_max = 0.0, 0.8
        brake_min, brake_max = 0.0, 1.0
        night_min, night_max = 0.0, 0.15
        base_speeding_min, base_speeding_max = 0.0, 0.06
    elif behaviour == "Aggressive":
        distance_min, distance_max = 12.0, 160.0
        speed_delta = 16.0
        accel_min, accel_max = 1.8, 5.5
        brake_min, brake_max = 2.0, 6.2
        night_min, night_max = 0.10, 0.60
        base_speeding_min, base_speeding_max = 0.30, 0.85
    else:  # Moderate
        distance_min, distance_max = 5.0, 95.0
        speed_delta = 11.0
        accel_min, accel_max = 0.4, 2.4
        brake_min, brake_max = 0.5, 2.8
        night_min, night_max = 0.02, 0.35
        base_speeding_min, base_speeding_max = 0.04, 0.30

    distance = rng.uniform(distance_min, distance_max, size=records)
    speed_min = max(12.0, target_speed - speed_delta)
    speed_max = target_speed + speed_delta
    average_speed = rng.uniform(speed_min, speed_max, size=records)

    max_speed_offset = rng.uniform(6.0, 28.0 if behaviour == "Safe" else 48.0, size=records)
    accel_rate = rng.uniform(accel_min, accel_max, size=records)
    brake_rate = rng.uniform(brake_min, brake_max, size=records)
    night_ratio = rng.uniform(night_min, night_max, size=records)

    # Calculate speeding ratio relative to road_speed_limit
    # Speed risk depends on speeding relative to configured road speed limit!
    # If vehicle target_speed is well below road_speed_limit, speeding ratio is minimal.
    # If vehicle average_speed exceeds road_speed_limit, speeding is substantial.
    speed_ratio_factor = np.clip((average_speed - (road_speed_limit * 0.9)) / max(road_speed_limit * 0.3, 10.0), 0.0, 1.0)
    speeding_ratio = np.clip(
        rng.uniform(base_speeding_min, base_speeding_max, size=records) * 0.5 + speed_ratio_factor * 0.5,
        0.0,
        1.0,
    )

    return (
        distance,
        average_speed,
        max_speed_offset,
        accel_rate,
        brake_rate,
        speeding_ratio,
        night_ratio,
    )


def generate_single_vehicle_dataset(
    config: Dict[str, Any],
    records: int,
    road_speed_limit: float,
    seed: int,
    faker: Faker,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    (
        distance,
        average_speed,
        max_speed_offset,
        accel_rate,
        brake_rate,
        speeding_ratio,
        night_ratio,
    ) = _build_vehicle_trip_samples(config, records, road_speed_limit, rng)

    distance = np.round(distance, 2)
    average_speed = np.round(average_speed, 2)
    vehicle_id = config["vehicle_id"]
    vehicle_name = config.get("vehicle_name", vehicle_id)
    vehicle_category = config.get("vehicle_category", "Medium")

    driver_pool = [faker.bothify(text="DRV-########") for _ in range(max(1, min(20, records)))]
    driver_indices = rng.integers(0, len(driver_pool), size=records)

    frame = pd.DataFrame(
        {
            "vehicle_id": [vehicle_id] * records,
            "vehicle_name": [vehicle_name] * records,
            "vehicle_category": [vehicle_category] * records,
            "trip_id": [f"TRIP-{vehicle_id}-{seed:08d}-{i + 1:04d}" for i in range(records)],
            "driver_id": [driver_pool[idx] for idx in driver_indices],
            "distance_km": distance,
            "duration_minutes": np.round((distance / average_speed) * 60.0, 4),
            "average_speed_kmh": average_speed,
            "maximum_speed_kmh": np.round(average_speed + max_speed_offset, 2),
            "harsh_acceleration_count": rng.poisson(accel_rate * distance / 10.0).astype(int),
            "harsh_braking_count": rng.poisson(brake_rate * distance / 10.0).astype(int),
            "speeding_ratio": np.round(speeding_ratio, 3),
            "night_driving_ratio": np.round(night_ratio, 3),
        }
    )

    return add_risk_scores(frame)


def summarize_vehicle(
    config: Dict[str, Any],
    frame: pd.DataFrame,
    road_speed_limit: float,
    base_premium: float = 10000.0,
) -> Dict[str, Any]:
    """Calculate aggregate metrics, insurance status, and recommendations for a vehicle."""
    vehicle_id = config["vehicle_id"]
    avg_speed = round(float(frame["average_speed_kmh"].mean()), 1)
    max_speed = round(float(frame["maximum_speed_kmh"].max()), 1)
    total_distance = round(float(frame["distance_km"].sum()), 1)
    total_duration = round(float(frame["duration_minutes"].sum()), 1)
    avg_braking = round(float(frame["harsh_braking_count"].mean()), 2)
    avg_acceleration = round(float(frame["harsh_acceleration_count"].mean()), 2)
    avg_speeding = round(float(frame["speeding_ratio"].mean()), 3)
    avg_night = round(float(frame["night_driving_ratio"].mean()), 3)
    avg_risk = round(float(frame["risk_score"].mean()), 1)

    # Classification matching project specifications
    if avg_risk < 35.0:
        risk_class = "Low"
    elif avg_risk < 65.0:
        risk_class = "Medium"
    else:
        risk_class = "High"

    vehicle_data = {
        "vehicle_id": vehicle_id,
        "vehicle_name": config.get("vehicle_name", vehicle_id),
        "vehicle_category": config.get("vehicle_category", "Medium"),
        "driving_behaviour": config.get("driving_behaviour", "Moderate"),
        "target_speed": float(config.get("target_speed", avg_speed)),
        "color": config.get("color", "#0ea5e9"),
        "average_speed": avg_speed,
        "maximum_speed": max_speed,
        "total_distance": total_distance,
        "trip_duration": total_duration,
        "harsh_braking_events": avg_braking,
        "harsh_acceleration_events": avg_acceleration,
        "speeding_ratio": avg_speeding,
        "night_driving_ratio": avg_night,
        "risk_score": avg_risk,
        "risk_classification": risk_class,
        "trips_count": len(frame),
        "road_speed_limit": road_speed_limit,
    }

    # Assess Insurance
    insurance_data = assess_insurance_for_vehicle(vehicle_data, base_premium=base_premium)
    vehicle_data.update(insurance_data)

    # Generate tailored safety recommendations
    vehicle_data["recommendations"] = generate_recommendations_for_vehicle(
        vehicle_data, road_speed_limit=road_speed_limit
    )

    return vehicle_data


def generate_multi_vehicle_dataset(
    num_vehicles: int = 3,
    vehicle_configs: Optional[List[Dict[str, Any]]] = None,
    records_per_vehicle: int = 50,
    road_speed_limit: float = 80.0,
    seed: int = 42,
    base_premium: float = 10000.0,
) -> Dict[str, Any]:
    """Generate multi-vehicle synthetic telematics datasets and comparative analytics."""
    faker = Faker()
    faker.seed_instance(seed)

    if not vehicle_configs:
        vehicle_configs = DEFAULT_VEHICLE_PRESETS[:num_vehicles]
    else:
        # Merge preset metadata if missing
        configs = []
        for idx, cfg in enumerate(vehicle_configs[:num_vehicles]):
            preset = DEFAULT_VEHICLE_PRESETS[idx % len(DEFAULT_VEHICLE_PRESETS)]
            merged = {**preset, **cfg}
            configs.append(merged)
        vehicle_configs = configs

    vehicle_frames = []
    vehicle_summaries = []

    for idx, cfg in enumerate(vehicle_configs):
        v_seed = (seed + (idx + 1) * 7919) % (2**32)
        v_frame = generate_single_vehicle_dataset(
            config=cfg,
            records=records_per_vehicle,
            road_speed_limit=road_speed_limit,
            seed=v_seed,
            faker=faker,
        )
        vehicle_frames.append(v_frame)
        v_summary = summarize_vehicle(
            config=cfg,
            frame=v_frame,
            road_speed_limit=road_speed_limit,
            base_premium=base_premium,
        )
        vehicle_summaries.append(v_summary)

    combined_frame = pd.concat(vehicle_frames, ignore_index=True)

    # Rank and compare vehicles
    comparison_results = rank_and_compare_vehicles(vehicle_summaries)

    # Fleet-level aggregates
    total_vehicles = len(vehicle_summaries)
    fleet_risk = round(float(np.mean([v["risk_score"] for v in vehicle_summaries])), 1)
    low_count = sum(1 for v in vehicle_summaries if v["risk_classification"] == "Low")
    medium_count = sum(1 for v in vehicle_summaries if v["risk_classification"] == "Medium")
    high_count = sum(1 for v in vehicle_summaries if v["risk_classification"] == "High")
    preferred_count = sum(
        1 for v in vehicle_summaries if v.get("insurance_category") == "Preferred Safe Driver"
    )

    fleet_summary = {
        "total_vehicles": total_vehicles,
        "total_records": len(combined_frame),
        "fleet_average_risk": fleet_risk,
        "low_risk_vehicles": low_count,
        "medium_risk_vehicles": medium_count,
        "high_risk_vehicles": high_count,
        "preferred_insurance_count": preferred_count,
        "road_speed_limit": road_speed_limit,
        "base_premium": base_premium,
    }

    return {
        "vehicles": vehicle_summaries,
        "combined_frame": combined_frame,
        "comparison": comparison_results,
        "fleet_summary": fleet_summary,
        "seed": seed,
    }
