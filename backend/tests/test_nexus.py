from backend.app.services.nexus import build_operational_twin


def test_prediction_and_impact_are_derived():
    twin=build_operational_twin()
    assert twin["prediction"]["time_to_impact_minutes"] > 0
    assert 0 <= twin["prediction"]["confidence_score"] <= 100
    assert twin["business_impact"]["revenue_risk_inr"] > 0
    assert twin["business_impact"]["assumptions"]["average_order_value_inr"] == 3200


def test_false_fix_is_rejected_and_human_remains_in_control():
    twin=build_operational_twin()
    fast=next(x for x in twin["strategies"] if x["id"]=="fast")
    assert not fast["eligible"] and not fast["gates"]["failover"]
    assert twin["recommended_strategy"]["id"]=="optimal"
    assert twin["approval"]["required"] and not twin["approval"]["automatic_execution"]


def test_capacity_counterfactual_changes_forecast():
    baseline=build_operational_twin()
    expanded=build_operational_twin(redis_capacity=24000)
    assert expanded["reliability_score"] > baseline["reliability_score"]
    assert expanded["prediction"]["confidence_score"] < baseline["prediction"]["confidence_score"]


def test_nexus_api(client):
    assert client.get("/api/nexus/operational-twin").json()["product"]=="SentinelOps Nexus"
    assert client.get("/api/nexus/operational-twin?load_multiplier=9").status_code==422
