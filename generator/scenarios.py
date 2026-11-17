"""Scenario distributions used to generate synthetic trips."""

SCENARIOS = {
    "Safe Urban": {
        "distance_km": (1.0, 30.0),
        "average_speed_kmh": (18.0, 52.0),
        "maximum_speed_offset_kmh": (5.0, 28.0),
        "acceleration_rate_per_10km": (0.0, 1.0),
        "braking_rate_per_10km": (0.0, 1.2),
        "speeding_ratio": (0.0, 0.12),
        "night_driving_ratio": (0.0, 0.20),
    },
    "Normal Mixed": {
        "distance_km": (2.0, 180.0),
        "average_speed_kmh": (25.0, 96.0),
        "maximum_speed_offset_kmh": (8.0, 48.0),
        "acceleration_rate_per_10km": (0.2, 2.8),
        "braking_rate_per_10km": (0.3, 3.2),
        "speeding_ratio": (0.02, 0.40),
        "night_driving_ratio": (0.0, 0.45),
    },
    "Aggressive Highway": {
        "distance_km": (8.0, 350.0),
        "average_speed_kmh": (72.0, 138.0),
        "maximum_speed_offset_kmh": (15.0, 58.0),
        "acceleration_rate_per_10km": (1.0, 5.2),
        "braking_rate_per_10km": (1.2, 6.0),
        "speeding_ratio": (0.20, 0.90),
        "night_driving_ratio": (0.05, 0.65),
    },
}

SCENARIO_NAMES = (*SCENARIOS.keys(), "Custom Risk")
