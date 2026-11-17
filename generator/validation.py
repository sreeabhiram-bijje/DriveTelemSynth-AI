"""Input validation shared by the Flask routes and tests."""

import math

from generator.scenarios import SCENARIO_NAMES

MAX_RECORDS = 10_000
MAX_SEED = 4_294_967_295


def validate_request(payload):
    """Return normalized generation options or raise ValueError."""
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    records = payload.get("records", 500)
    if isinstance(records, bool) or not isinstance(records, int):
        raise ValueError("Record count must be a whole number.")
    if not 1 <= records <= MAX_RECORDS:
        raise ValueError(f"Record count must be between 1 and {MAX_RECORDS:,}.")

    scenario = payload.get("scenario", "Normal Mixed")
    if not isinstance(scenario, str) or scenario not in SCENARIO_NAMES:
        raise ValueError("Choose one of the available driving scenarios.")

    seed = payload.get("seed", 42)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("Random seed must be a whole number.")
    if not 0 <= seed <= MAX_SEED:
        raise ValueError(f"Random seed must be between 0 and {MAX_SEED:,}.")

    options = {
        "records": records,
        "scenario": scenario,
        "seed": seed,
        "custom_settings": None,
    }
    if scenario == "Custom Risk":
        options["custom_settings"] = validate_custom_settings(
            payload.get("custom_settings")
        )
    return options


def validate_custom_settings(settings):
    """Validate the bounded controls exposed for the custom scenario."""
    if not isinstance(settings, dict):
        raise ValueError("Custom Risk settings are required.")

    validated = {}
    ranges = {
        "average_speed_min": (10.0, 150.0),
        "average_speed_max": (10.0, 180.0),
        "risk_intensity": (0.0, 1.0),
        "night_ratio": (0.0, 1.0),
    }
    for key, (minimum, maximum) in ranges.items():
        value = settings.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key.replace('_', ' ').capitalize()} must be a number.")
        if not math.isfinite(value) or not minimum <= value <= maximum:
            raise ValueError(
                f"{key.replace('_', ' ').capitalize()} must be between "
                f"{minimum:g} and {maximum:g}."
            )
        validated[key] = float(value)

    if validated["average_speed_min"] >= validated["average_speed_max"]:
        raise ValueError("Minimum average speed must be lower than maximum speed.")
    return validated


def validate_multi_vehicle_request(payload):
    """Validate options for multi-vehicle comparative generation."""
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    num_vehicles = payload.get("num_vehicles", 3)
    if isinstance(num_vehicles, bool) or not isinstance(num_vehicles, int):
        raise ValueError("Number of vehicles must be a whole number.")
    if not 2 <= num_vehicles <= 5:
        raise ValueError("Number of vehicles must be between 2 and 5.")

    records_per_vehicle = payload.get("records_per_vehicle", 50)
    if isinstance(records_per_vehicle, bool) or not isinstance(records_per_vehicle, int):
        raise ValueError("Records per vehicle must be a whole number.")
    if not 5 <= records_per_vehicle <= 2000:
        raise ValueError("Records per vehicle must be between 5 and 2,000.")

    road_speed_limit = payload.get("road_speed_limit", 80.0)
    if isinstance(road_speed_limit, bool) or not isinstance(road_speed_limit, (int, float)):
        raise ValueError("Road speed limit must be a number.")
    if not 30.0 <= road_speed_limit <= 150.0:
        raise ValueError("Road speed limit must be between 30 and 150 km/h.")

    seed = payload.get("seed", 42)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("Random seed must be a whole number.")
    if not 0 <= seed <= MAX_SEED:
        raise ValueError(f"Random seed must be between 0 and {MAX_SEED:,}.")

    base_premium = payload.get("base_premium", 10000.0)
    if isinstance(base_premium, bool) or not isinstance(base_premium, (int, float)):
        raise ValueError("Base premium must be a number.")
    if not 1000.0 <= base_premium <= 500000.0:
        raise ValueError("Base premium must be between 1,000 and 500,000.")

    validated_vehicles = None
    raw_vehicles = payload.get("vehicles")
    if raw_vehicles is not None:
        if not isinstance(raw_vehicles, list):
            raise ValueError("Vehicles must be an array of vehicle configurations.")
        if len(raw_vehicles) < num_vehicles:
            raise ValueError(f"Provide at least {num_vehicles} vehicle configurations.")

        validated_vehicles = []
        seen_ids = set()
        for idx, v in enumerate(raw_vehicles[:num_vehicles]):
            if not isinstance(v, dict):
                raise ValueError(f"Vehicle at index {idx} must be a JSON object.")
            v_id = str(v.get("vehicle_id", f"VEH-{idx + 1:03d}")).strip()
            if not v_id:
                raise ValueError("Vehicle ID cannot be empty.")
            if v_id in seen_ids:
                raise ValueError(f"Duplicate vehicle ID '{v_id}' detected. IDs must be unique.")
            seen_ids.add(v_id)

            target_speed = v.get("target_speed", 50.0)
            if isinstance(target_speed, bool) or not isinstance(target_speed, (int, float)):
                raise ValueError(f"Target speed for {v_id} must be a number.")
            if not 10.0 <= target_speed <= 180.0:
                raise ValueError(f"Target speed for {v_id} must be between 10 and 180 km/h.")

            behaviour = str(v.get("driving_behaviour", "Moderate"))
            if behaviour not in ("Safe", "Moderate", "Aggressive"):
                raise ValueError(f"Driving behaviour for {v_id} must be Safe, Moderate, or Aggressive.")

            category = str(v.get("vehicle_category", "Medium"))
            if category not in ("Slow", "Medium", "High"):
                raise ValueError(f"Vehicle category for {v_id} must be Slow, Medium, or High.")

            validated_vehicles.append(
                {
                    "vehicle_id": v_id,
                    "vehicle_name": str(v.get("vehicle_name", v_id)).strip(),
                    "vehicle_category": category,
                    "target_speed": float(target_speed),
                    "driving_behaviour": behaviour,
                    "color": str(v.get("color", "#0ea5e9")),
                }
            )

    return {
        "num_vehicles": num_vehicles,
        "vehicles": validated_vehicles,
        "records_per_vehicle": records_per_vehicle,
        "road_speed_limit": float(road_speed_limit),
        "seed": seed,
        "base_premium": float(base_premium),
    }
