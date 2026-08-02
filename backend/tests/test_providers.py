import json
import httpx
import pytest
from backend.app.llm import get_provider
from backend.app.llm.gemini_provider import GeminiProvider
from backend.app.llm.mock_provider import MockLLMProvider
from backend.app.llm.openai_provider import OpenAIProvider
from backend.app.schemas import PatchProposal

VALID={"summary":"safe","target_files":["demo_app/app/main.py"],"patch":"--- a\n+++ b","expected_effect":"works","risks":[],"verification_plan":["pytest"]}

def client(handler): return httpx.Client(transport=httpx.MockTransport(handler),timeout=0.1)
def test_openai_structured_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","secret")
    provider=OpenAIProvider(client=client(lambda request:httpx.Response(200,json={"choices":[{"message":{"content":json.dumps(VALID)}}]})))
    assert provider.generate("task",PatchProposal).summary=="safe"
def test_openai_retries_rate_limit_once(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","secret"); calls=0
    def handler(request):
        nonlocal calls; calls+=1
        if calls==1:return httpx.Response(429,request=request)
        return httpx.Response(200,json={"choices":[{"message":{"content":json.dumps(VALID)}}]},request=request)
    assert OpenAIProvider(client=client(handler)).generate("task",PatchProposal).summary=="safe"; assert calls==2
def test_openai_rejects_malformed_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","secret")
    with pytest.raises(ValueError,match="structured"):
        OpenAIProvider(client=client(lambda request:httpx.Response(200,json={"choices":[]}))).generate("task",PatchProposal)
def test_openai_retries_timeout_once(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","secret"); calls=0
    def handler(request):
        nonlocal calls; calls+=1; raise httpx.ReadTimeout("timeout",request=request)
    with pytest.raises(ValueError):OpenAIProvider(client=client(handler)).generate("task",PatchProposal)
    assert calls==2
def test_gemini_structured_response(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY","secret")
    body={"candidates":[{"content":{"parts":[{"text":json.dumps(VALID)}]}}]}
    assert GeminiProvider(client=client(lambda request:httpx.Response(200,json=body))).generate("task",PatchProposal).summary=="safe"
def test_gemini_retries_rate_limit_and_rejects_malformed(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY","secret"); calls=0
    def handler(request):
        nonlocal calls; calls+=1
        if calls==1:return httpx.Response(429,request=request)
        return httpx.Response(200,json={"candidates":[]},request=request)
    with pytest.raises(ValueError,match="structured"):
        GeminiProvider(client=client(handler)).generate("task",PatchProposal)
    assert calls==2
def test_gemini_retries_timeout_once(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY","secret"); calls=0
    def handler(request):
        nonlocal calls; calls+=1; raise httpx.ReadTimeout("timeout",request=request)
    with pytest.raises(ValueError):GeminiProvider(client=client(handler)).generate("task",PatchProposal)
    assert calls==2
def test_missing_credentials_fall_back_without_secret(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY",raising=False)
    with pytest.warns(RuntimeWarning,match="deterministic mock"):
        assert isinstance(get_provider("openai"),MockLLMProvider)
