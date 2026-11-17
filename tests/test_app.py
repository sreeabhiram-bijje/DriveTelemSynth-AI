import numpy as np
import pandas as pd
import pytest

import app as app_module
from app import app, DATASETS
from generator.risk_scoring import add_risk_scores
from generator.scenarios import SCENARIO_NAMES
from generator.synthetic_generator import generate_dataset
from generator.validation import validate_request


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


@pytest.mark.parametrize("scenario", SCENARIO_NAMES)
def test_all_scenarios_generate_valid_records(scenario):
    custom_settings = {
        "average_speed_min": 25,
        "average_speed_max": 90,
        "risk_intensity": 0.6,
        "night_ratio": 0.2,
    } if scenario == "Custom Risk" else None
    frame = generate_dataset(40, scenario, 13, custom_settings)
    assert len(frame) == 40
    assert frame.isna().sum().sum() == 0
    assert frame["distance_km"].gt(0).all()
    assert frame["duration_minutes"].gt(0).all()
    assert frame["average_speed_kmh"].gt(0).all()
    assert frame["maximum_speed_kmh"].ge(frame["average_speed_kmh"]).all()
    assert frame["speeding_ratio"].between(0, 1).all()
    assert frame["night_driving_ratio"].between(0, 1).all()
    assert frame["risk_score"].between(0, 100).all()
    assert set(frame["risk_label"]).issubset({"Low", "Medium", "High"})
    assert frame["trip_id"].is_unique
    measured_speed = frame["distance_km"] / (frame["duration_minutes"] / 60)
    np.testing.assert_allclose(
        measured_speed, frame["average_speed_kmh"], atol=0.01, rtol=0
    )


def test_generation_is_reproducible():
    first = generate_dataset(50, "Normal Mixed", 777)
    second = generate_dataset(50, "Normal Mixed", 777)
    pd.testing.assert_frame_equal(first, second)


def test_scenario_distributions_match_expected_profile():
    safe = generate_dataset(500, "Safe Urban", 91)
    aggressive = generate_dataset(500, "Aggressive Highway", 91)
    assert safe["average_speed_kmh"].mean() < aggressive["average_speed_kmh"].mean()
    assert safe["speeding_ratio"].mean() < aggressive["speeding_ratio"].mean()
    assert (
        safe["harsh_acceleration_count"].mean()
        < aggressive["harsh_acceleration_count"].mean()
    )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"records": 0}, "Record count"),
        ({"records": 10_001}, "Record count"),
        ({"records": 2.5}, "whole number"),
        ({"scenario": "Unknown"}, "scenario"),
        ({"seed": -1}, "Random seed"),
        ({"seed": True}, "whole number"),
        (
            {
                "scenario": "Custom Risk",
                "custom_settings": {
                    "average_speed_min": 90,
                    "average_speed_max": 20,
                    "risk_intensity": 0.5,
                    "night_ratio": 0.2,
                },
            },
            "lower than",
        ),
    ],
)
def test_invalid_inputs_are_rejected(payload, message):
    with pytest.raises(ValueError, match=message):
        validate_request(payload)


def test_risk_scoring_rules_and_thresholds():
    frame = pd.DataFrame(
        {
            "distance_km": [10.0, 10.0, 10.0],
            "speeding_ratio": [0.0, 0.5, 1.0],
            "harsh_braking_count": [0, 1, 1],
            "harsh_acceleration_count": [0, 1, 1],
            "night_driving_ratio": [0.0, 0.0, 1.0],
        }
    )
    scored = add_risk_scores(frame)
    assert scored["risk_score"].tolist() == [0, 63, 100]
    assert scored["risk_label"].tolist() == ["Low", "Medium", "High"]


def test_generate_endpoint_validates_and_returns_requested_count(client):
    response = client.post(
        "/api/generate",
        json={"records": 7, "scenario": "Safe Urban", "seed": 9},
    )
    assert response.status_code == 200
    result = response.get_json()
    assert result["summary"]["kpis"]["records"] == 7
    assert len(result["preview"]) == 7
    assert result["synthetic"] is True


def test_generate_endpoint_rejects_bad_request_and_non_json(client):
    assert client.post("/api/generate", json={"records": 0}).status_code == 400
    assert client.post("/api/generate", data="not json").status_code == 400


def test_csv_export_contains_complete_dataset(client):
    response = client.post(
        "/api/generate",
        json={"records": 30, "scenario": "Normal Mixed", "seed": 42},
    )
    download_url = response.get_json()["download_url"]
    csv_response = client.get(download_url)
    assert csv_response.status_code == 200
    assert csv_response.mimetype == "text/csv"
    exported = pd.read_csv(pd.io.common.BytesIO(csv_response.data))
    assert len(exported) == 30
    assert "risk_label" in exported.columns
    assert "trip_id" in exported.columns


def test_csv_unknown_token_returns_friendly_404(client):
    assert client.get("/download/not-a-valid-token").status_code == 404


def test_health_and_home_routes(client):
    assert client.get("/health").get_json()["status"] == "ok"
    assert client.get("/").status_code == 200
    assert client.get("/dashboard").status_code == 200


def test_download_cache_is_bounded(client, monkeypatch):
    DATASETS.clear()
    monkeypatch.setattr(app_module, "MAX_STORED_DATASETS", 2)
    first_response = client.post(
        "/api/generate", json={"records": 1, "scenario": "Safe Urban", "seed": 1}
    )
    first_url = first_response.get_json()["download_url"]
    for seed in (2, 3):
        response = client.post(
            "/api/generate",
            json={"records": 1, "scenario": "Safe Urban", "seed": seed},
        )
        assert response.status_code == 200
    assert len(DATASETS) == 2
    assert client.get(first_url).status_code == 404
    DATASETS.clear()
