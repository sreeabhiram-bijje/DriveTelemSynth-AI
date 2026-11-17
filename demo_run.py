from generator.multi_vehicle_generator import generate_multi_vehicle_dataset
import json

data = generate_multi_vehicle_dataset(
    num_vehicles=3,
    records_per_vehicle=50,
    road_speed_limit=80.0,
    seed=42,
    base_premium=10000.0
)

print("=== FLEET OVERVIEW ===")
print(json.dumps(data["fleet_summary"], indent=2))

print("\n=== VEHICLE COMPARISON & SIMULATED INSURANCE ===")
for v in data["comparison"]["rankings"]:
    print(f"Rank {v['safety_rank']}: {v['vehicle_name']} ({v['vehicle_id']})")
    print(f"  Category: {v['vehicle_category']} | Avg Speed: {v['average_speed']} km/h | Max Speed: {v['maximum_speed']} km/h")
    print(f"  Speeding Ratio: {round(v['speeding_ratio'] * 100, 1)}% | Night Driving: {round(v['night_driving_ratio'] * 100, 1)}%")
    print(f"  Harsh Events: Braking {v['harsh_braking_events']} / trip, Accel {v['harsh_acceleration_events']} / trip")
    print(f"  Risk Score: {v['risk_score']} / 100 ({v['risk_classification']})")
    print(f"  Insurance: {v['insurance_category']} ({v['eligibility_status']})")
    print(f"  Base Premium: Rs.{v['base_premium']} | Safe Driver Discount: {v['discount_percentage']}% (-Rs.{v['discount_amount']})")
    print(f"  Final Simulated Premium: Rs.{v['final_simulated_premium']}")
    print(f"  Decision Explanation: {v['decision_explanation']}")
    print("  Tailored Safety Recommendations:")
    for r in v["recommendations"]:
        print(f"    * [{r['severity'].upper()}] {r['category']}: {r['recommendation']}")
    print()

print("=== SAFEST DRIVER ANALYSIS ===")
print(json.dumps(data["comparison"]["best_driver_analysis"], indent=2))
