from __future__ import annotations
import json
import subprocess
from pathlib import Path
def read_jsonl(path:Path,limit:int=25)->list[dict]:
    if not path.exists(): return []
    rows=[]
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: continue
    return rows
def git_evidence(repo:Path)->dict:
    def run(*args:str)->str:
        result=subprocess.run(["git",*args],cwd=repo,text=True,capture_output=True,timeout=5,check=False)
        return result.stdout.strip() or result.stderr.strip()
    return {"commits":run("log","-5","--oneline"),"changed_files":run("status","--short"),"diff":run("diff","--","demo_app")}
