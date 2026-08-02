from __future__ import annotations
PROTECTED=(".env",".github/","policies/","sandbox/","deployment/","secrets/","migrations/")
class PatchPolicyError(ValueError): pass
def inspect_patch(diff:str,files:list[str],has_regression_test:bool)->dict:
    normalized=[f.replace("\\","/").lstrip("./") for f in files]
    if any(any(f==p or f.startswith(p) for p in PROTECTED) for f in normalized): raise PatchPolicyError("Protected path modified")
    if len(files)>5: raise PatchPolicyError("Patch changes more than 5 files")
    changed=sum(1 for line in diff.splitlines() if line.startswith(("+","-")) and not line.startswith(("+++","---")))
    if changed>150: raise PatchPolicyError("Patch changes more than 150 lines")
    if not has_regression_test: raise PatchPolicyError("Regression test required")
    forbidden=("@pytest.mark.skip","# noqa: S","nosec","http://","https://","API_KEY=")
    if any(token in diff for token in forbidden): raise PatchPolicyError("Patch weakens safety or adds network/secret material")
    deleted_assertions=[line for line in diff.splitlines() if line.startswith("-") and "assert" in line]
    if deleted_assertions: raise PatchPolicyError("Patch weakens assertions")
    return {"files":len(files),"changed_lines":changed,"within_policy":True}
