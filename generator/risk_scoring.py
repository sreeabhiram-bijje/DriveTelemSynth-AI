"""Transparent heuristic scoring for generated trips; not a pricing model."""

import numpy as np
import pandas as pd


def add_risk_scores(frame):
    """Return a copy with a 0-100 score and its Low/Medium/High label."""
    scored = frame.copy()

    # Each event component measures events per roughly 10 km and is capped at 1.
    # The weights sum to 100: speeding 45, braking 20, acceleration 20, night 15.
    distance_units = np.maximum(scored["distance_km"].to_numpy() / 10.0, 1.0)
    speeding_points = scored["speeding_ratio"].to_numpy() * 45.0
    braking_points = np.minimum(
        scored["harsh_braking_count"].to_numpy() / distance_units, 1.0
    ) * 20.0
    acceleration_points = np.minimum(
        scored["harsh_acceleration_count"].to_numpy() / distance_units, 1.0
    ) * 20.0
    night_points = scored["night_driving_ratio"].to_numpy() * 15.0

    points = np.clip(
        speeding_points + braking_points + acceleration_points + night_points,
        0.0,
        100.0,
    )
    scores = np.floor(points + 0.5).astype(int)
    scored["risk_score"] = scores
    scored["risk_label"] = np.select(
        [scores < 35, scores < 65],
        ["Low", "Medium"],
        default="High",
    )
    return scored
