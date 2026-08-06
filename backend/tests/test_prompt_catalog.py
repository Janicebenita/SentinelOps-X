import json
from pathlib import Path

import yaml  # type: ignore[import-untyped]


def test_task_prompt_catalogs_are_complete_unique_and_safe() -> None:
    required = {"prompt_id", "version", "model_family", "capacity_and_role", "request",
        "insight_and_context", "scope_and_constraints", "personality_and_tone", "expected_output",
        "evidence_input_schema", "allowed_tools", "prohibited_actions", "refusal_conditions",
        "safety_boundary", "timeout_behavior", "fallback_behavior", "evaluation_cases",
        "expected_pass_example", "expected_fail_example"}
    prompts = []
    for path in (Path("prompts/gemini/task-prompts-v1.yaml"), Path("prompts/gemma/task-prompts-v1.yaml")):
        prompts.extend(yaml.safe_load(path.read_text(encoding="utf-8"))["prompts"])
    assert len(prompts) == 13
    assert all(required <= item.keys() for item in prompts)
    ids = [item["prompt_id"] for item in prompts]
    assert len(ids) == len(set(ids))
    assert all(item["version"].count(".") == 2 for item in prompts)
    assert all(item["refusal_conditions"] and item["prohibited_actions"] for item in prompts)
    assert all(item["safety_boundary"] == "PRODUCTION ACTION: NOT EXECUTED" for item in prompts)
    serialized = json.dumps(prompts).lower()
    assert "chain-of-thought" in serialized and "reveal hidden chain-of-thought" in serialized
    assert all("approve" in item["prohibited_actions"] for item in prompts)


def test_advisory_json_schema_compiles_and_denies_authority() -> None:
    schema = json.loads(Path("prompts/schemas/advisory-output-v1.json").read_text(encoding="utf-8"))
    assert schema["type"] == "object" and schema["additionalProperties"] is False
    assert schema["properties"]["authoritative"]["const"] is False
    assert schema["properties"]["production_action"]["const"] == "NOT_EXECUTED"
