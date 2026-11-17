"""Reproducible, scenario-based synthetic driving trip generation."""

import numpy as np
import pandas as pd
from faker import Faker

from generator.risk_scoring import add_risk_scores
from generator.scenarios import SCENARIOS


def _sample_scenario(scenario, records, rng):
    distribution = SCENARIOS[scenario]
    distance = rng.uniform(*distribution["distance_km"], size=records)
    average_speed = rng.uniform(*distribution["average_speed_kmh"], size=records)
    max_speed_offset = rng.uniform(
        *distribution["maximum_speed_offset_kmh"], size=records
    )
    acceleration_rate = rng.uniform(
        *distribution["acceleration_rate_per_10km"], size=records
    )
    braking_rate = rng.uniform(*distribution["braking_rate_per_10km"], size=records)
    speeding_ratio = rng.uniform(*distribution["speeding_ratio"], size=records)
    night_ratio = rng.uniform(*distribution["night_driving_ratio"], size=records)
    return (
        distance,
        average_speed,
        max_speed_offset,
        acceleration_rate,
        braking_rate,
        speeding_ratio,
        night_ratio,
    )


def _sample_custom(settings, records, rng):
    distance = rng.uniform(2.0, 150.0, size=records)
    average_speed = rng.uniform(
        settings["average_speed_min"], settings["average_speed_max"], size=records
    )
    max_speed_offset = rng.uniform(8.0, 48.0, size=records)
    intensity = settings["risk_intensity"]
    acceleration_rate = rng.uniform(0.0, 5.0 * intensity, size=records)
    braking_rate = rng.uniform(0.0, 6.0 * intensity, size=records)
    # The custom intensity shifts the speeding range while preserving variation.
    speeding_ratio = rng.uniform(
        max(0.0, intensity * 0.55 - 0.12),
        min(1.0, intensity * 0.55 + 0.12),
        size=records,
    )
    night_ratio = rng.uniform(
        max(0.0, settings["night_ratio"] - 0.12),
        min(1.0, settings["night_ratio"] + 0.12),
        size=records,
    )
    return (
        distance,
        average_speed,
        max_speed_offset,
        acceleration_rate,
        braking_rate,
        speeding_ratio,
        night_ratio,
    )


def generate_dataset(records, scenario, seed, custom_settings=None):
    """Generate a deterministic DataFrame for a seed and validated options."""
    rng = np.random.default_rng(seed)
    faker = Faker()
    faker.seed_instance(seed)

    sampled = (
        _sample_custom(custom_settings, records, rng)
        if scenario == "Custom Risk"
        else _sample_scenario(scenario, records, rng)
    )
    (
        distance,
        average_speed,
        max_speed_offset,
        acceleration_rate,
        braking_rate,
        speeding_ratio,
        night_ratio,
    ) = sampled

    distance = np.round(distance, 2)
    average_speed = np.round(average_speed, 2)
    driver_pool = [faker.bothify(text="DRV-########") for _ in range(max(1, min(80, records)))]
    driver_indices = rng.integers(0, len(driver_pool), size=records)
    frame = pd.DataFrame(
        {
            "trip_id": [f"TRIP-{seed:010d}-{index + 1:05d}" for index in range(records)],
            "driver_id": [driver_pool[index] for index in driver_indices],
            "distance_km": distance,
            "duration_minutes": np.round(distance / average_speed * 60.0, 4),
            "average_speed_kmh": average_speed,
            "maximum_speed_kmh": np.round(average_speed + max_speed_offset, 2),
            "harsh_acceleration_count": rng.poisson(
                acceleration_rate * distance / 10.0
            ).astype(int),
            "harsh_braking_count": rng.poisson(braking_rate * distance / 10.0).astype(
                int
            ),
            "speeding_ratio": np.round(speeding_ratio, 3),
            "night_driving_ratio": np.round(night_ratio, 3),
        }
    )
    return add_risk_scores(frame)
