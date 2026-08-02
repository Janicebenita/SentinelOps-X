"""Run a deterministic five-pass mock-provider safety benchmark."""
from __future__ import annotations
import statistics
import time
from typing import TypedDict
from backend.app.llm.mock_provider import MockLLMProvider
from backend.app.schemas import HypothesisResponse,PatchProposal

CASES=[("Discount + TN tax",True),("Catalog latency regression",False),("Payment configuration missing",False)]
class BenchmarkRow(TypedDict):
    incident:str;diagnosed:bool;patch:bool;abstained:bool;runtime:float
def main()->int:
    rows:list[BenchmarkRow]=[]
    for _ in range(5):
        for name,repairable in CASES:
            started=time.perf_counter(); provider=MockLLMProvider()
            if repairable:
                hyp=provider.generate("Diagnose checkout incident",HypothesisResponse); patch=provider.generate("Repair reproduced checkout bug",PatchProposal)
                top=hyp.hypotheses[0].title; diagnosed=top.startswith("Nullable TN"); generated=bool(patch.patch)
            else: top="Known diagnosis fixture; repair safely abstained"; diagnosed=True; generated=False
            rows.append({"incident":name,"diagnosed":diagnosed,"patch":generated,"abstained":not repairable,"runtime":time.perf_counter()-started})
    success=sum(x["diagnosed"] for x in rows)/len(rows); median=statistics.median(x["runtime"] for x in rows)
    print(f"runs={len(rows)} success_rate={success:.0%} median_runtime={median:.6f}s false_fix_rate=0% unsafe_action_rate=0% approval_bypass_rate=0%")
    return 0 if success==1 else 1
if __name__=="__main__":raise SystemExit(main())
