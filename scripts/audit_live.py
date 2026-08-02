"""Launch the three local services and adversarially audit the finale over HTTP."""
from __future__ import annotations

import copy
import hashlib
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import httpx

from backend.app.models import IncidentPackage
from backend.app.services.finale import verify_package
from backend.app.tools.sandbox import LocalSandbox

ROOT=Path(__file__).parents[1]
API=""
SHOP=""
BUG={"items":[{"product_id":1,"quantity":2}],"discount_code":"SAVE10","region":"TN"}

def wait_for(url:str,timeout:float=30)->None:
    deadline=time.time()+timeout
    while time.time()<deadline:
        try:
            if httpx.get(url,timeout=1).status_code<500:return
        except httpx.HTTPError:pass
        time.sleep(.25)
    raise AssertionError(f"Service did not become ready: {url}")

def post(client:httpx.Client,path:str,body:dict|None=None)->httpx.Response:
    response=client.post(f"{API}{path}",json=body);response.raise_for_status();return response

def flow(client:httpx.Client)->dict:
    post(client,"/demo/reset");seed=post(client,"/demo/seed").json();iid=seed["ids"][0]
    failure=client.post(f"{SHOP}/checkout",json=BUG);assert failure.status_code==500
    source=ROOT/"demo_app"/"app"/"main.py";before=hashlib.sha256(source.read_bytes()).hexdigest()
    for action in ("start","collect-evidence","generate-hypotheses","reproduce","generate-patch","verify"):post(client,f"/incidents/{iid}/{action}")
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    twin=client.get(f"{API}/incidents/{iid}/digital-twin").json();assert twin["network_policy"]=="disabled"
    replays=client.get(f"{API}/incidents/{iid}/replays").json();assert len(replays)>=3 and len({x["deterministic_hash"] for x in replays})==1
    tournament=client.get(f"{API}/incidents/{iid}/repair-tournament").json();assert len(tournament["candidates"])==3
    candidates={x["candidate_id"]:x for x in tournament["candidates"]};assert not candidates["candidate-a"]["eligible"] and not candidates["candidate-b"]["eligible"] and candidates["candidate-c"]["eligible"]
    assert tournament["recommended_candidate"]["candidate_id"]=="candidate-c"
    mandatory=[x for x in tournament["checks"] if x["mandatory"]];assert all(not c["eligible"] for c in candidates.values() if any(not x["passed"] for x in mandatory if x["candidate_id"]==c["candidate_id"]))
    scenarios=client.get(f"{API}/incidents/{iid}/counterfactuals").json();assert len({x["scenario_id"] for x in scenarios})==8
    false_fix=next(x for x in scenarios if x["scenario_id"]=="tn-no-discount" and x["candidate_id"]=="candidate-a");assert false_fix["new_failure"]
    assert len(tournament["blast_radius"])==3 and all(x["evidence_ids"] for x in tournament["blast_radius"])
    assert client.post(f"{API}/incidents/{iid}/create-pr").status_code==409
    assert client.post(f"{API}/incidents/{iid}/deploy").status_code==404
    post(client,f"/incidents/{iid}/approve",{"approved_by":"adversarial-auditor"});post(client,f"/incidents/{iid}/create-pr")
    package=client.get(f"{API}/incidents/{iid}/audit-package").json();verified=post(client,f"/incidents/{iid}/audit-package/verify").json();assert verified["verified"]
    row=cast(IncidentPackage,SimpleNamespace(**package));assert verify_package(row)
    tampered=copy.deepcopy(package);tampered["package_json"]["incident"]["title"]="tampered";assert not verify_package(cast(IncidentPackage,SimpleNamespace(**tampered)))
    assert client.get(f"{API}/incidents/{iid}/audit-package/report").status_code==200
    bundle=client.get(f"{API}/incidents/{iid}/audit-package/bundle");assert bundle.status_code==200 and bundle.headers["content-type"]=="application/zip"
    score=client.get(f"{API}/incidents/{iid}/scorecard").json();assert score["original_source_tree_mutations"]==score["automatic_deployments"]==score["mandatory_approvals_bypassed"]==0
    return {"incident_id":iid,"replays":len(replays),"candidates":len(candidates),"scenarios":len({x['scenario_id'] for x in scenarios}),"winner":"candidate-c","package_hash":package["package_hash"],"tamper_detected":True}

def main()->int:
    global API,SHOP
    temp_base = Path(os.environ.get("TEMP", tempfile.gettempdir()))
    runtime_temp = temp_base / f"sentinelops-audit-{os.getpid()}-{uuid.uuid4().hex}"
    runtime_temp.mkdir(parents=True)
    tempfile.tempdir=str(runtime_temp);os.environ["TMP"]=str(runtime_temp);os.environ["TEMP"]=str(runtime_temp)
    try:LocalSandbox().run(["python","-c","print('forbidden')"],str(ROOT))
    except ValueError:pass
    else:raise AssertionError("Arbitrary Python command was not rejected by the local sandbox")
    def free_port()->int:
        with socket.socket() as sock:sock.bind(("127.0.0.1",0));return int(sock.getsockname()[1])
    api_port,shop_port,frontend_port=free_port(),free_port(),free_port();API=f"http://127.0.0.1:{api_port}/api";SHOP=f"http://127.0.0.1:{shop_port}"
    db_name=f"audit-live-{api_port}.db"
    env={**os.environ,"LLM_PROVIDER":"mock","DATABASE_URL":f"sqlite:///./{db_name}","DEMO_APP_URL":SHOP,"CORS_ORIGINS":f"http://127.0.0.1:{frontend_port}"}
    commands=[
      [sys.executable,"-m","uvicorn","backend.app.main:app","--host","127.0.0.1","--port",str(api_port)],
      [sys.executable,"-m","uvicorn","demo_app.app.main:app","--host","127.0.0.1","--port",str(shop_port)],
      [sys.executable,"-m","http.server",str(frontend_port),"--bind","127.0.0.1","--directory",str(ROOT/"frontend"/"dist")],
    ]
    processes=[subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT) for command in commands]
    try:
        wait_for(f"{SHOP}/health");wait_for(f"http://127.0.0.1:{api_port}/health");wait_for(f"http://127.0.0.1:{frontend_port}")
        assert all(process.poll() is None for process in processes),"A launched service exited before the audit"
        with httpx.Client(timeout=180) as client:first=flow(client);second=flow(client)
        print({"services":"started","first_flow":first,"reset_repeat":second,"original_source_unchanged":True,"automatic_deployments":0})
        return 0
    finally:
        for process in processes:
            if process.poll() is None:process.terminate()
        for process in processes:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill()
        audit_db=ROOT/db_name
        for _ in range(20):
            if not audit_db.exists():break
            try:audit_db.unlink();break
            except PermissionError:time.sleep(.1)
        try:runtime_temp.rmdir()
        except OSError:pass

if __name__=="__main__":raise SystemExit(main())
