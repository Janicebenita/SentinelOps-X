from .base import LLMProvider, OutputT
from ..schemas import HypothesisResponse, PatchProposal
PATCH='''--- a/demo_app/app/main.py
+++ b/demo_app/app/main.py
@@ -70,1 +70,1 @@
-        tax = taxable * cast(Decimal, rate) if order.discount_code else taxable * (rate or Decimal("0"))
+        tax = taxable * (rate or Decimal("0"))'''
class MockLLMProvider(LLMProvider):
    def generate(self,task:str,output_model:type[OutputT])->OutputT:
        if output_model is HypothesisResponse:
            return output_model.model_validate({"hypotheses":[
              {"title":"Nullable TN tax rate in discounted checkout","explanation":"The discounted branch multiplies Decimal by the legacy null TN rate.","evidence_for":["log: TypeError at checkout tax calculation","trace: checkout.calculate failed only for TN + SAVE10","source: TN rate is None"],"evidence_against":["Non-discounted TN checkout succeeds"],"confidence":0.94,"relevant_files":["demo_app/app/main.py"]},
              {"title":"Malformed discount code handling","explanation":"The discount path may supply an unexpected value.","evidence_for":["Failure requires SAVE10"],"evidence_against":["SAVE10 succeeds in CA","validated request schema"],"confidence":0.31,"relevant_files":["demo_app/app/main.py"]},
              {"title":"Product price corruption","explanation":"A price type mismatch could break arithmetic.","evidence_for":["Arithmetic stack frame"],"evidence_against":["Same products succeed in all control requests"],"confidence":0.08,"relevant_files":["demo_app/app/main.py"]}]})
        if output_model is PatchProposal:
            return output_model.model_validate(PatchProposal(summary="Normalize nullable regional tax rate",target_files=["demo_app/app/main.py","demo_app/tests/test_regression_checkout.py"],patch=PATCH,expected_effect="TN discounted checkout returns a valid total",risks=["Tax policy may require a non-zero TN rate later"],verification_plan=["Fail regression before patch","Pass regression after patch","Run full suite, Ruff, MyPy, Bandit"]).model_dump())
        raise ValueError(f"Unsupported contract {output_model}")
