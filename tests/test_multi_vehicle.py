"""Comprehensive unit and integration tests for multi-vehicle simulation and insurance analytics."""

import io
import json
import threading
import numpy as np
import pandas as pd
import pytest

from app import app, DATASETS, MAX_STORED_DATASETS
from analytics.insurance import assess_insurance_for_vehicle, assess_fleet_insurance
from analytics.recommendations import generate_recommendations_for_vehicle
from analytics.vehicle_comparison import rank_and_compare_vehicles
from generator.multi_vehicle_generator import (
    DEFAULT_VEHICLE_PRESETS,
    generate_multi_vehicle_dataset,
    generate_single_vehicle_dataset,
)
from generator.validation import validate_multi_vehicle_request


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


# 1. Generating 2, 3, and 5 vehicles
@pytest.mark.parametrize("n_vehicles", [2, 3, 5])
def test_generate_variable_vehicle_counts(n_vehicles):
    res = generate_multi_vehicle_dataset(num_vehicles=n_vehicles, records_per_vehicle=15, seed=101)
    assert len(res["vehicles"]) == n_vehicles
    assert len(res["comparison"]["rankings"]) == n_vehicles
    assert res["fleet_summary"]["total_vehicles"] == n_vehicles
    assert len(res["combined_frame"]) == n_vehicles * 15


# 2. Unique vehicle identifiers
def test_unique_vehicle_identifiers():
    res = generate_multi_vehicle_dataset(num_vehicles=4, records_per_vehicle=10, seed=77)
    v_ids = [v["vehicle_id"] for v in res["vehicles"]]
    assert len(v_ids) == len(set(v_ids))
    assert set(res["combined_frame"]["vehicle_id"].unique()) == set(v_ids)


# 3. Deterministic generation with identical seeds
def test_deterministic_multi_vehicle_generation():
    run1 = generate_multi_vehicle_dataset(num_vehicles=3, records_per_vehicle=20, seed=42)
    run2 = generate_multi_vehicle_dataset(num_vehicles=3, records_per_vehicle=20, seed=42)
    pd.testing.assert_frame_equal(run1["combined_frame"], run2["combined_frame"])
    assert run1["vehicles"] == run2["vehicles"]


# 4. Different speeds for different vehicles
def test_different_speeds_across_categories():
    res = generate_multi_vehicle_dataset(num_vehicles=3, records_per_vehicle=40, seed=99)
    veh_a = next(v for v in res["vehicles"] if v["vehicle_category"] == "Slow")
    veh_b = next(v for v in res["vehicles"] if v["vehicle_category"] == "Medium")
    veh_c = next(v for v in res["vehicles"] if v["vehicle_category"] == "High")
    assert veh_a["average_speed"] < veh_b["average_speed"] < veh_c["average_speed"]


# 5. Physical trip consistency
def test_physical_trip_consistency():
    res = generate_multi_vehicle_dataset(num_vehicles=3, records_per_vehicle=30, seed=55)
    frame = res["combined_frame"]
    assert (frame["distance_km"] > 0).all()
    assert (frame["duration_minutes"] > 0).all()
    assert (frame["average_speed_kmh"] > 0).all()
    assert (frame["maximum_speed_kmh"] >= frame["average_speed_kmh"]).all()
    expected_duration = (frame["distance_km"] / frame["average_speed_kmh"]) * 60.0
    np.testing.assert_allclose(frame["duration_minutes"], expected_duration, atol=0.01)


# 6. Risk score boundaries
def test_risk_score_boundaries():
    res = generate_multi_vehicle_dataset(num_vehicles=4, records_per_vehicle=25, seed=12)
    for v in res["vehicles"]:
        assert 0.0 <= v["risk_score"] <= 100.0
        assert v["risk_classification"] in ("Low", "Medium", "High")


# 7. Insurance classification boundaries and tiers
def test_insurance_classification_boundaries():
    # Test boundary below 35 -> Preferred
    v_low = {"vehicle_id": "V-LOW", "risk_score": 25.0}
    ass_low = assess_insurance_for_vehicle(v_low, base_premium=10000.0)
    assert ass_low["insurance_category"] == "Preferred Safe Driver"
    assert ass_low["discount_percentage"] == 20.0
    assert ass_low["final_simulated_premium"] == 8000.0

    # Test boundary 35 to 64.99 -> Standard
    v_med = {"vehicle_id": "V-MED", "risk_score": 48.0}
    ass_med = assess_insurance_for_vehicle(v_med, base_premium=10000.0)
    assert ass_med["insurance_category"] == "Standard Coverage"
    assert ass_med["discount_percentage"] == 5.0
    assert ass_med["final_simulated_premium"] == 9500.0

    # Test boundary 65 and above -> High Risk
    v_high = {"vehicle_id": "V-HIGH", "risk_score": 75.0}
    ass_high = assess_insurance_for_vehicle(v_high, base_premium=10000.0)
    assert ass_high["insurance_category"] == "High Risk / Surcharge Tier"
    assert ass_high["discount_percentage"] == 0.0
    assert ass_high["final_simulated_premium"] == 10000.0


# 8. Premium calculations with custom base premium
def test_custom_premium_calculations():
    v = {"vehicle_id": "V-PREM", "risk_score": 30.0}
    res = assess_insurance_for_vehicle(v, base_premium=25000.0, preferred_discount=25.0)
    assert res["base_premium"] == 25000.0
    assert res["discount_percentage"] == 25.0
    assert res["discount_amount"] == 6250.0
    assert res["final_simulated_premium"] == 18750.0


# 9. Vehicle ranking logic
def test_vehicle_ranking_logic():
    v1 = {"vehicle_id": "V1", "risk_score": 20.0, "speeding_ratio": 0.02, "harsh_braking_events": 0.5, "harsh_acceleration_events": 0.5, "average_speed": 40.0}
    v2 = {"vehicle_id": "V2", "risk_score": 50.0, "speeding_ratio": 0.15, "harsh_braking_events": 1.5, "harsh_acceleration_events": 1.2, "average_speed": 65.0}
    v3 = {"vehicle_id": "V3", "risk_score": 75.0, "speeding_ratio": 0.45, "harsh_braking_events": 3.0, "harsh_acceleration_events": 2.8, "average_speed": 110.0}
    comp = rank_and_compare_vehicles([v2, v3, v1])
    assert comp["rankings"][0]["vehicle_id"] == "V1"
    assert comp["rankings"][0]["safety_rank"] == 1
    assert comp["safest_vehicle"]["vehicle_id"] == "V1"
    assert comp["highest_risk_vehicle"]["vehicle_id"] == "V3"


# 10. Individualized safety recommendations
def test_safety_recommendations_individualized():
    safe_v = {
        "vehicle_id": "V-SAFE",
        "speeding_ratio": 0.02,
        "average_speed": 35.0,
        "harsh_braking_events": 0.2,
        "harsh_acceleration_events": 0.3,
        "night_driving_ratio": 0.05,
        "risk_score": 18.0,
    }
    recs_safe = generate_recommendations_for_vehicle(safe_v, road_speed_limit=80.0)
    assert any("Exemplary" in r["category"] or "Preferred" in r["category"] for r in recs_safe)

    risky_v = {
        "vehicle_id": "V-RISKY",
        "speeding_ratio": 0.60,
        "average_speed": 115.0,
        "harsh_braking_events": 3.8,
        "harsh_acceleration_events": 3.2,
        "night_driving_ratio": 0.45,
        "risk_score": 82.0,
    }
    recs_risky = generate_recommendations_for_vehicle(risky_v, road_speed_limit=80.0)
    categories = [r["category"] for r in recs_risky]
    assert "Speed Compliance" in categories
    assert "Following Distance & Deceleration" in categories
    assert "Throttle Control" in categories


# 11. Multi-vehicle API endpoint (POST /api/generate-multiple)
def test_api_generate_multiple(client):
    payload = {
        "num_vehicles": 3,
        "records_per_vehicle": 20,
        "road_speed_limit": 90.0,
        "seed": 42,
        "base_premium": 12000.0,
    }
    response = client.post("/api/generate-multiple", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["vehicles"]) == 3
    assert data["fleet_summary"]["total_vehicles"] == 3
    assert "download_url" in data
    assert "download_json_url" in data
    assert "comparison_id" in data


# 12. Simulation API endpoint (POST /api/simulate)
def test_api_simulate(client):
    payload = {"num_vehicles": 4, "road_speed_limit": 100.0}
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ready"
    assert data["num_vehicles"] == 4
    assert len(data["vehicles"]) == 4


# 13. Comparison API endpoint (POST /api/compare & GET /api/comparison/<id>)
def test_api_compare_and_cached_lookup(client):
    gen_resp = client.post(
        "/api/generate-multiple",
        json={"num_vehicles": 3, "records_per_vehicle": 10, "seed": 123},
    )
    comp_id = gen_resp.get_json()["comparison_id"]

    # Test GET cached comparison
    comp_resp = client.get(f"/api/comparison/{comp_id}")
    assert comp_resp.status_code == 200
    comp_data = comp_resp.get_json()
    assert "safest_vehicle" in comp_data

    # Test POST /api/compare
    direct_compare = client.post("/api/compare", json={"vehicles": gen_resp.get_json()["vehicles"]})
    assert direct_compare.status_code == 200
    assert len(direct_compare.get_json()["rankings"]) == 3


# 14. Single vehicle lookup (GET /api/vehicle/<vehicle_id>)
def test_api_get_single_vehicle(client):
    client.post("/api/generate-multiple", json={"num_vehicles": 3, "records_per_vehicle": 10, "seed": 7})
    res = client.get("/api/vehicle/VEH-001")
    assert res.status_code == 200
    data = res.get_json()
    assert data["vehicle"]["vehicle_id"] == "VEH-001"
    assert "trips_sample" in data

    # Non-existent vehicle
    assert client.get("/api/vehicle/VEH-999").status_code == 404


# 15. CSV Export with multi-vehicle columns
def test_csv_export_multi_vehicle(client):
    gen = client.post("/api/generate-multiple", json={"num_vehicles": 2, "records_per_vehicle": 15, "seed": 88})
    dl_url = gen.get_json()["download_url"]
    csv_resp = client.get(dl_url)
    assert csv_resp.status_code == 200
    assert csv_resp.mimetype == "text/csv"
    df = pd.read_csv(io.BytesIO(csv_resp.data))
    assert len(df) == 30
    assert "vehicle_id" in df.columns
    assert "vehicle_name" in df.columns
    assert "vehicle_category" in df.columns
    assert set(df["vehicle_id"].unique()) == {"VEH-001", "VEH-002"}


# 16. JSON Export endpoint
def test_json_export_multi_vehicle(client):
    gen = client.post("/api/generate-multiple", json={"num_vehicles": 3, "records_per_vehicle": 10, "seed": 33})
    json_url = gen.get_json()["download_json_url"]
    resp = client.get(json_url)
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    data = json.loads(resp.data.decode("utf-8"))
    assert "fleet_summary" in data
    assert "vehicles" in data
    assert "comparison" in data


# 17. Invalid multi-vehicle configuration rejection
@pytest.mark.parametrize(
    ("bad_payload", "expected_err"),
    [
        ({"num_vehicles": 1}, "between 2 and 5"),
        ({"num_vehicles": 6}, "between 2 and 5"),
        ({"num_vehicles": 3, "road_speed_limit": 20}, "between 30 and 150"),
        ({"num_vehicles": 3, "records_per_vehicle": 3}, "between 5 and 2,000"),
        (
            {
                "num_vehicles": 2,
                "vehicles": [
                    {"vehicle_id": "V1", "target_speed": 40},
                    {"vehicle_id": "V1", "target_speed": 60},  # duplicate ID
                ],
            },
            "Duplicate vehicle ID",
        ),
        (
            {
                "num_vehicles": 2,
                "vehicles": [
                    {"vehicle_id": "V1", "target_speed": 250},  # speed > 180
                    {"vehicle_id": "V2", "target_speed": 60},
                ],
            },
            "between 10 and 180",
        ),
    ],
)
def test_multi_vehicle_validation_rejections(client, bad_payload, expected_err):
    with pytest.raises(ValueError, match=expected_err):
        validate_multi_vehicle_request(bad_payload)
    resp = client.post("/api/generate-multiple", json=bad_payload)
    assert resp.status_code == 400


# 18. Multi-vehicle cache capacity & FIFO eviction
def test_multi_vehicle_cache_eviction(client, monkeypatch):
    import app as app_mod
    DATASETS.clear()
    monkeypatch.setattr(app_mod, "MAX_STORED_DATASETS", 2)
    resp1 = client.post("/api/generate-multiple", json={"num_vehicles": 2, "records_per_vehicle": 5, "seed": 1})
    dl1 = resp1.get_json()["download_url"]

    for s in (2, 3):
        client.post("/api/generate-multiple", json={"num_vehicles": 2, "records_per_vehicle": 5, "seed": s})

    assert len(DATASETS) == 2
    assert client.get(dl1).status_code == 404
    DATASETS.clear()


# 19. Concurrent cache access safety
def test_concurrent_multi_vehicle_generation():
    errors = []

    def make_request(s):
        try:
            with app.test_client() as thread_client:
                res = thread_client.post(
                    "/api/generate-multiple",
                    json={"num_vehicles": 2, "records_per_vehicle": 10, "seed": s},
                )
                if res.status_code != 200:
                    errors.append(f"Status {res.status_code}")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=make_request, args=(seed,)) for seed in range(10, 16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


# 20. Direct insurance assessment endpoint
def test_insurance_assessment_endpoint(client):
    vehicles = [
        {"vehicle_id": "V-10", "risk_score": 20.0},
        {"vehicle_id": "V-20", "risk_score": 55.0},
    ]
    resp = client.post("/api/insurance-assessment", json={"vehicles": vehicles, "base_premium": 15000.0})
    assert resp.status_code == 200
    enriched = resp.get_json()["vehicles"]
    assert len(enriched) == 2
    assert enriched[0]["final_simulated_premium"] == 12000.0  # 20% discount on 15,000
    assert enriched[1]["final_simulated_premium"] == 14250.0  # 5% discount on 15,000
