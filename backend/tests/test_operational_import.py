from __future__ import annotations

import json


def telemetry_document() -> dict[str, object]:
    points = []
    for index, (requests, memory, p95, queue, error) in enumerate([
        (9000, 60, 150, 4, 0.2),
        (10000, 68, 180, 12, 0.5),
        (11000, 76, 240, 28, 1.2),
        (12000, 84, 340, 64, 2.4),
    ]):
        points.append({
            "timestamp": f"2026-08-08T10:{index * 10:02d}:00Z",
            "requests_per_minute": requests,
            "p50_ms": p95 * 0.45,
            "checkout_p95_ms": p95,
            "p99_ms": p95 * 1.4,
            "redis_cpu_pct": 48 + index * 8,
            "redis_saturation": memory,
            "cache_hit_rate_pct": 96 - index * 3,
            "queue_depth": queue,
            "application_replicas": 6,
            "error_rate_pct": error,
        })
    return {"configuration": {"redis_capacity": 16000}, "telemetry": points}


def test_real_telemetry_import_runs_backend_forecast_and_scenarios(client):
    document = telemetry_document()
    response = client.post("/api/v1/workflows/import-json", json={
        "filename": "organization-telemetry.json",
        "content": json.dumps(document),
    })
    assert response.status_code == 200, response.text
    run = response.json()
    assert run["state"] == "AWAITING_HUMAN"
    assert run["inputs_json"]["source_label"] == "manual-upload/organization-telemetry.json"
    assert len(run["inputs_json"]["telemetry_points"]) == 4
    assert run["forecast_json"]["predicted_crossing_minutes"] == 8
    assert "uploaded observations" in run["forecast_json"]["observation_window"]
    assert len(run["scenarios_json"]) == 12
    telemetry = client.get("/api/v1/telemetry", params={"run_id": run["id"]}).json()
    assert [point["redis_memory_pct"] for point in telemetry] == [60, 68, 76, 84]
    evidence = client.get(f"/api/v1/workflows/{run['id']}/evidence").json()
    assert any(row["source"] == "manual-upload/organization-telemetry.json" for row in evidence)
    assert client.get("/api/v1/audit/verify", params={"run_id": run["id"]}).json()["valid"] is True
    assert run["production_action_executed"] is False


def test_control_json_import_calculates_immediately(client):
    response = client.post("/api/v1/workflows/import-json", json={
        "filename": "bounded-controls.json",
        "content": json.dumps({"controls": {
            "traffic_multiplier": 3,
            "redis_capacity": 9000,
            "application_replicas": 3,
            "dependency_latency_ms": 160,
        }}),
    })
    assert response.status_code == 200
    run = response.json()
    assert run["state"] == "AWAITING_HUMAN"
    assert run["inputs_json"]["traffic_multiplier"] == 3
    assert len(run["scenarios_json"]) == 12
    assert "3x traffic" in run["recommendation_json"]["summary"]


def test_incident_feed_is_not_misrepresented_as_capacity_telemetry(client):
    response = client.post("/api/v1/workflows/import-json", json={
        "filename": "status-incidents.json",
        "content": json.dumps({"page": {"name": "Example"}, "incidents": [{"status": "resolved"}]}),
    })
    assert response.status_code == 409
    assert "No supported telemetry series" in response.json()["detail"]
    assert "redis_capacity" in response.json()["detail"]


def test_nested_data_array_and_numeric_strings_are_normalized(client):
    points=telemetry_document()["telemetry"]
    string_points=[{key:(str(value) if isinstance(value,(int,float)) else value) for key,value in point.items()} for point in points]
    response=client.post("/api/v1/workflows/import-json",json={
        "filename":"monitoring-export.json",
        "content":json.dumps({"redis_capacity":"16000","data":string_points}),
    })
    assert response.status_code==200,response.text
    run=response.json()
    assert run["state"]=="AWAITING_HUMAN"
    assert run["forecast_json"]["predicted_crossing_minutes"]==8
    assert len(run["scenarios_json"])==12


def test_top_level_telemetry_array_reads_capacity_from_latest_point(client):
    points=telemetry_document()["telemetry"]
    for point in points:
        point["redis_capacity"]=16000
    response=client.post("/api/v1/workflows/import-json",json={
        "filename":"telemetry-array.json",
        "content":json.dumps(points),
    })
    assert response.status_code==200,response.text
    run=response.json()
    assert run["inputs_json"]["redis_capacity"]==16000
    assert "latest uploaded telemetry point" in run["inputs_json"]["normalization_notes"][0]


def test_import_route_accepts_enterprise_json_larger_than_global_api_limit(client):
    response = client.post("/api/v1/workflows/import-json", json={
        "filename": "large-enterprise-export.json",
        "content": json.dumps({
            "controls": {
                "traffic_multiplier": 2,
                "redis_capacity": 14000,
                "application_replicas": 5,
                "dependency_latency_ms": 80,
            },
            "metadata": "x" * 300000,
        }),
    })
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Imported operational forecast: large-enterprise-export.json"


def test_nested_generic_enterprise_cpu_series_uses_explicit_proxy_notes(client):
    response = client.post("/api/v1/workflows/import-json", json={
        "filename": "enterprise-observability-export.json",
        "content": json.dumps({"export": {"measurements": [
            {"eventTime": f"2026-08-08T10:{index * 10:02d}:00Z", "system": {"cpu": {"utilization": value}}}
            for index, value in enumerate((45, 60, 75, 90))
        ]}}),
    })
    assert response.status_code == 200, response.text
    run = response.json()
    assert [point["redis_memory_pct"] for point in run["inputs_json"]["telemetry_points"]] == [45, 60, 75, 90]
    assert any("CPU utilization" in note for note in run["inputs_json"]["normalization_notes"])
    assert len(run["scenarios_json"]) == 12


def test_cloudwatch_parallel_series_export_is_pivoted_and_calculated(client):
    timestamps = [f"2026-08-08T10:{index * 10:02d}:00Z" for index in range(4)]
    response = client.post("/api/v1/workflows/import-json", json={
        "filename": "cloudwatch-metric-data.json",
        "content": json.dumps({"MetricDataResults": [
            {"Label": "CPUUtilization", "Timestamps": timestamps, "Values": [52, 64, 76, 88]},
            {"Label": "RequestCount", "Timestamps": timestamps, "Values": [7000, 8200, 9500, 10800]},
        ]}),
    })
    assert response.status_code == 200, response.text
    run = response.json()
    assert len(run["inputs_json"]["telemetry_points"]) == 4
    assert len(run["scenarios_json"]) == 12
    assert run["inputs_json"]["source_label"] == "manual-upload/cloudwatch-metric-data.json"
