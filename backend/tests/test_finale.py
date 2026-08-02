import copy
import hashlib

from backend.app.models import EvidenceItem, Hypothesis, Incident
from backend.app.services import finale


def seeded_incident(db):
    incident=Incident(title="Discount + TN tax causes checkout 500",description="demo",severity="SEV1")
    db.add(incident);db.commit()
    evidence=EvidenceItem(incident_id=incident.id,evidence_type="trace",source="fixture",content="TypeError",summary="Decimal multiplied by null rate",relevance_score=.99,metadata_json={})
    db.add(evidence);db.commit()
    hypothesis=Hypothesis(incident_id=incident.id,title="Nullable tax rate",explanation="TN rate is null",evidence_for=["trace"],evidence_against=["other regions pass"],confidence=.94,rank=1)
    db.add(hypothesis);db.commit();return incident


def test_twin_manifest_hash_is_stable_and_network_disabled(db):
    incident=seeded_incident(db);first=finale.create_twin(db,incident);second=finale.create_twin(db,incident)
    assert first.manifest_hash==second.manifest_hash
    assert first.twin_id==second.twin_id and first.network_policy=="disabled"
    assert first.random_seed==finale.SEED and "pytest" in first.command_allowlist


def test_replay_is_deterministic_three_times(db):
    incident=seeded_incident(db);rows=finale.replay_incident(db,incident,attempts=3)
    assert len(rows)==3 and len({x.deterministic_hash for x in rows})==1
    assert all(x.exit_status==1 and x.reproduced for x in rows)


def test_tournament_disqualifies_failed_mandatory_gate_and_bounds_scores(db):
    incident=seeded_incident(db);result=finale.run_tournament(db,incident)
    leaderboard={x["candidate_id"]:x for x in result["leaderboard"]}
    assert not leaderboard["candidate-a"]["eligible"]
    assert not leaderboard["candidate-b"]["eligible"]
    assert result["recommended_candidate"]["candidate_id"]=="candidate-c"
    assert all(0<=x["score"]<=100 and 0<=x["blast_radius"]<=100 for x in leaderboard.values())


def test_counterfactuals_detect_false_fix_and_validate_matrix(db):
    incident=seeded_incident(db);finale.run_tournament(db,incident)
    rows=finale.run_counterfactuals(db,incident)
    assert len(rows)==8*4
    false_fix=next(x for x in rows if x.scenario_id=="tn-no-discount" and x.candidate_id=="candidate-a")
    assert false_fix.outcome=="fail" and false_fix.new_failure
    winner=[x for x in rows if x.candidate_id=="candidate-c" and x.scenario_id not in {"database-outage","slow-dependency","compound"}]
    assert winner and all(x.outcome=="pass" for x in winner)


def test_major_claims_have_evidence_links(db):
    incident=seeded_incident(db);links=finale.create_evidence_links(db,incident)
    assert {x.claim_type for x in links}>={"root-cause","reproduction","recommendation","deployment"}
    assert all(x.evidence_ids and x.confidence_label in {"Low","Moderate","High"} for x in links)


def test_audit_chain_verifies_and_detects_tampering(db):
    incident=seeded_incident(db);finale.replay_incident(db,incident);finale.run_tournament(db,incident)
    package=finale.export_package(db,incident);assert finale.verify_package(package)
    package.package_json=copy.deepcopy(package.package_json);package.package_json["incident"]["title"]="tampered"
    assert not finale.verify_package(package)


def test_candidate_evaluation_never_mutates_source_tree(db,tmp_path,monkeypatch):
    source=tmp_path/"service.py";source.write_text("ORIGINAL",encoding="utf-8")
    before=hashlib.sha256(source.read_bytes()).hexdigest();incident=seeded_incident(db)
    finale.generate_candidates(db,incident);finale.run_tournament(db,incident)
    after=hashlib.sha256(source.read_bytes()).hexdigest();assert before==after


def test_scorecard_safety_values_are_event_derived_zeroes(db):
    incident=seeded_incident(db);finale.replay_incident(db,incident);finale.run_tournament(db,incident)
    result=finale.scorecard(db,incident)
    assert result["original_source_tree_mutations"]==0
    assert result["automatic_deployments"]==0
    assert result["mandatory_approvals_bypassed"]==0
    assert result["arbitrary_generated_shell_commands_executed"]==0
