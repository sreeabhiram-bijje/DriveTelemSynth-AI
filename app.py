"""Flask application for DriveTelemSynth AI – Multi-Vehicle Comparative Driving Simulation & Intelligent Insurance Analytics."""

from collections import OrderedDict
from io import BytesIO
import json
import secrets
from threading import Lock
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request, send_file
import pandas as pd

from analytics.insurance import assess_fleet_insurance, assess_insurance_for_vehicle
from analytics.recommendations import generate_recommendations_for_vehicle
from analytics.summaries import build_summary
from analytics.vehicle_comparison import rank_and_compare_vehicles
from generator.multi_vehicle_generator import (
    DEFAULT_VEHICLE_PRESETS,
    generate_multi_vehicle_dataset,
)
from generator.scenarios import SCENARIO_NAMES
from generator.synthetic_generator import generate_dataset
from generator.validation import validate_multi_vehicle_request, validate_request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

DATASETS = OrderedDict()
COMPARISONS = OrderedDict()
LATEST_MULTI_DATASET: Dict[str, Any] = {}
DATASETS_LOCK = Lock()
MAX_STORED_DATASETS = 32


@app.get("/")
def home():
    return render_template(
        "index.html",
        scenarios=SCENARIO_NAMES,
        default_presets=DEFAULT_VEHICLE_PRESETS,
    )


@app.get("/dashboard")
def dashboard():
    return render_template(
        "index.html",
        scenarios=SCENARIO_NAMES,
        default_presets=DEFAULT_VEHICLE_PRESETS,
    )


@app.get("/health")
def health_check():
    return jsonify({
        "status": "ok",
        "service": "DriveTelemSynth AI",
        "platform": "Multi-Vehicle Driving Simulation and Intelligent Insurance Analytics",
        "version": "2.0.0",
    })


# -------------------------------------------------------------
# Existing Single Dataset Generation Route (100% Backwards Compatible)
# -------------------------------------------------------------
@app.post("/api/generate")
def generate():
    if not request.is_json:
        return jsonify({"error": "Send generation settings as a JSON object."}), 400
    try:
        options = validate_request(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    frame = generate_dataset(**options)
    download_id = secrets.token_urlsafe(24)
    with DATASETS_LOCK:
        DATASETS[download_id] = frame
        DATASETS.move_to_end(download_id)
        while len(DATASETS) > MAX_STORED_DATASETS:
            DATASETS.popitem(last=False)

    return jsonify(
        {
            "scenario": options["scenario"],
            "seed": options["seed"],
            "synthetic": True,
            "summary": build_summary(frame),
            "preview": frame.head(25).to_dict(orient="records"),
            "download_url": f"/download/{download_id}",
        }
    )


# -------------------------------------------------------------
# Multi-Vehicle Comparative Generation Route
# -------------------------------------------------------------
@app.post("/api/generate-multiple")
def generate_multiple():
    if not request.is_json:
        return jsonify({"error": "Send multi-vehicle configuration as a JSON object."}), 400
    try:
        options = validate_multi_vehicle_request(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    result = generate_multi_vehicle_dataset(
        num_vehicles=options["num_vehicles"],
        vehicle_configs=options["vehicles"],
        records_per_vehicle=options["records_per_vehicle"],
        road_speed_limit=options["road_speed_limit"],
        seed=options["seed"],
        base_premium=options["base_premium"],
    )

    combined_frame = result["combined_frame"]
    download_id = secrets.token_urlsafe(24)
    comparison_id = secrets.token_urlsafe(24)

    json_export_data = {
        "metadata": {
            "platform": "DriveTelemSynth AI",
            "seed": options["seed"],
            "road_speed_limit": options["road_speed_limit"],
            "num_vehicles": options["num_vehicles"],
            "records_per_vehicle": options["records_per_vehicle"],
            "base_premium": options["base_premium"],
        },
        "fleet_summary": result["fleet_summary"],
        "vehicles": result["vehicles"],
        "comparison": result["comparison"],
        "sample_trips": combined_frame.head(50).to_dict(orient="records"),
    }

    with DATASETS_LOCK:
        DATASETS[download_id] = {
            "frame": combined_frame,
            "json": json_export_data,
        }
        DATASETS.move_to_end(download_id)
        while len(DATASETS) > MAX_STORED_DATASETS:
            DATASETS.popitem(last=False)

        COMPARISONS[comparison_id] = result["comparison"]
        COMPARISONS.move_to_end(comparison_id)
        while len(COMPARISONS) > MAX_STORED_DATASETS:
            COMPARISONS.popitem(last=False)

        global LATEST_MULTI_DATASET
        LATEST_MULTI_DATASET = {
            "vehicles": {v["vehicle_id"]: v for v in result["vehicles"]},
            "frame": combined_frame,
            "comparison": result["comparison"],
            "fleet_summary": result["fleet_summary"],
            "download_id": download_id,
            "comparison_id": comparison_id,
        }

    return jsonify(
        {
            "success": True,
            "synthetic": True,
            "seed": options["seed"],
            "road_speed_limit": options["road_speed_limit"],
            "fleet_summary": result["fleet_summary"],
            "vehicles": result["vehicles"],
            "comparison": result["comparison"],
            "preview": combined_frame.head(30).to_dict(orient="records"),
            "download_url": f"/download/{download_id}",
            "download_json_url": f"/download-json/{download_id}",
            "comparison_id": comparison_id,
        }
    )


# -------------------------------------------------------------
# Simulation Configuration & State Route
# -------------------------------------------------------------
@app.post("/api/simulate")
def simulate():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    num_vehicles = payload.get("num_vehicles", 3)
    if isinstance(num_vehicles, bool) or not isinstance(num_vehicles, int) or not 2 <= num_vehicles <= 5:
        num_vehicles = 3

    road_speed_limit = float(payload.get("road_speed_limit", 80.0))
    road_speed_limit = max(30.0, min(150.0, road_speed_limit))

    custom_speeds = payload.get("speeds")
    vehicles = []
    presets = DEFAULT_VEHICLE_PRESETS[:num_vehicles]

    for idx, preset in enumerate(presets):
        speed = preset["target_speed"]
        if isinstance(custom_speeds, dict) and preset["vehicle_id"] in custom_speeds:
            try:
                speed = float(custom_speeds[preset["vehicle_id"]])
            except (ValueError, TypeError):
                pass
        vehicles.append(
            {
                "vehicle_id": preset["vehicle_id"],
                "vehicle_name": preset["vehicle_name"],
                "vehicle_category": preset["vehicle_category"],
                "driving_behaviour": preset["driving_behaviour"],
                "speed_kmh": round(speed, 1),
                "lane_index": idx,
                "color": preset["color"],
            }
        )

    return jsonify(
        {
            "status": "ready",
            "road_speed_limit": road_speed_limit,
            "num_vehicles": num_vehicles,
            "vehicles": vehicles,
            "time_scale": 1.0,
            "lanes": num_vehicles,
            "instructions": (
                "Simulation ready. Use Start, Pause, Resume, Reset controls in the Canvas studio."
            ),
        }
    )


# -------------------------------------------------------------
# Comparison Route
# -------------------------------------------------------------
@app.post("/api/compare")
def compare_vehicles_endpoint():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    vehicles = payload.get("vehicles")
    if not vehicles or not isinstance(vehicles, list):
        with DATASETS_LOCK:
            if LATEST_MULTI_DATASET and "vehicles" in LATEST_MULTI_DATASET:
                vehicles = list(LATEST_MULTI_DATASET["vehicles"].values())
            else:
                return jsonify({"error": "No vehicles provided and no active multi-vehicle dataset found."}), 400

    comparison_results = rank_and_compare_vehicles(vehicles)
    return jsonify(comparison_results)


@app.get("/api/comparison/<comparison_id>")
def get_cached_comparison(comparison_id):
    with DATASETS_LOCK:
        comp = COMPARISONS.get(comparison_id)
    if comp is None:
        return jsonify({"error": "Comparison not found or expired."}), 404
    return jsonify(comp)


# -------------------------------------------------------------
# Insurance Assessment Route
# -------------------------------------------------------------
@app.post("/api/insurance-assessment")
def insurance_assessment_endpoint():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    base_premium = float(payload.get("base_premium", 10000.0))
    vehicles = payload.get("vehicles")
    if isinstance(vehicles, list):
        enriched = assess_fleet_insurance(vehicles, base_premium=base_premium)
        return jsonify({"vehicles": enriched, "base_premium": base_premium})
    elif isinstance(payload.get("vehicle"), dict):
        assessed = assess_insurance_for_vehicle(payload["vehicle"], base_premium=base_premium)
        return jsonify(assessed)
    else:
        with DATASETS_LOCK:
            if LATEST_MULTI_DATASET and "vehicles" in LATEST_MULTI_DATASET:
                v_list = list(LATEST_MULTI_DATASET["vehicles"].values())
                enriched = assess_fleet_insurance(v_list, base_premium=base_premium)
                return jsonify({"vehicles": enriched, "base_premium": base_premium})
        return jsonify({"error": "Provide a 'vehicles' list or 'vehicle' object."}), 400


# -------------------------------------------------------------
# Individual Vehicle Lookup Route
# -------------------------------------------------------------
@app.get("/api/vehicle/<vehicle_id>")
def get_single_vehicle(vehicle_id):
    with DATASETS_LOCK:
        if not LATEST_MULTI_DATASET or "vehicles" not in LATEST_MULTI_DATASET:
            return jsonify({"error": "No multi-vehicle dataset has been generated yet."}), 404
        vehicle = LATEST_MULTI_DATASET["vehicles"].get(vehicle_id)
        if not vehicle:
            return jsonify({"error": f"Vehicle '{vehicle_id}' not found in active dataset."}), 404
        frame = LATEST_MULTI_DATASET.get("frame")

    trips_preview = []
    if frame is not None and "vehicle_id" in frame.columns:
        sub = frame[frame["vehicle_id"] == vehicle_id]
        trips_preview = sub.head(10).to_dict(orient="records")

    return jsonify({
        "vehicle": vehicle,
        "trips_sample": trips_preview,
    })


# -------------------------------------------------------------
# Download Routes (CSV & JSON)
# -------------------------------------------------------------
@app.get("/download/<download_id>")
def download_csv(download_id):
    with DATASETS_LOCK:
        stored = DATASETS.get(download_id)
    if stored is None:
        return jsonify({"error": "This download has expired. Generate a new dataset."}), 404

    if isinstance(stored, dict):
        frame = stored["frame"]
    else:
        frame = stored

    csv_bytes = BytesIO(frame.to_csv(index=False).encode("utf-8"))
    csv_bytes.seek(0)
    return send_file(
        csv_bytes,
        mimetype="text/csv",
        as_attachment=True,
        download_name="drivetelemsynth_synthetic_trips.csv",
    )


@app.get("/download-json/<download_id>")
def download_json(download_id):
    with DATASETS_LOCK:
        stored = DATASETS.get(download_id)
    if stored is None:
        return jsonify({"error": "This download has expired. Generate a new dataset."}), 404

    if isinstance(stored, dict) and "json" in stored:
        json_content = json.dumps(stored["json"], indent=2).encode("utf-8")
    else:
        # Fallback if single dataset frame was stored
        frame = stored if isinstance(stored, pd.DataFrame) else stored.get("frame")
        json_content = frame.to_json(orient="records", indent=2).encode("utf-8")

    json_bytes = BytesIO(json_content)
    json_bytes.seek(0)
    return send_file(
        json_bytes,
        mimetype="application/json",
        as_attachment=True,
        download_name="drivetelemsynth_analytics_export.json",
    )


if __name__ == "__main__":
    app.run(debug=False)
