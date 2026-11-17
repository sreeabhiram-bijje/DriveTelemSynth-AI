"""JSON-friendly dashboard aggregations."""


import pandas as pd


def build_summary(frame):
    risk_counts = (
        frame["risk_label"]
        .value_counts()
        .reindex(["Low", "Medium", "High"], fill_value=0)
    )
    speed_by_risk = (
        frame.groupby("risk_label")["average_speed_kmh"]
        .mean()
        .reindex(["Low", "Medium", "High"])
    )
    return {
        "kpis": {
            "records": int(len(frame)),
            "drivers": int(frame["driver_id"].nunique()),
            "average_risk": round(float(frame["risk_score"].mean()), 1),
            "high_risk_percent": round(
                float((frame["risk_label"] == "High").mean() * 100.0), 1
            ),
            "average_speed": round(float(frame["average_speed_kmh"].mean()), 1),
        },
        "risk_distribution": {
            label: int(count) for label, count in risk_counts.items()
        },
        "average_speed_by_risk": {
            label: round(float(speed_by_risk[label]), 1)
            if label in speed_by_risk.index and not pd.isna(speed_by_risk[label])
            else 0
            for label in ("Low", "Medium", "High")
        },
        "driving_events": {
            "Harsh acceleration": round(
                float(frame["harsh_acceleration_count"].mean()), 2
            ),
            "Harsh braking": round(float(frame["harsh_braking_count"].mean()), 2),
        },
    }
