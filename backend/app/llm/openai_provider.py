from __future__ import annotations
import json
import os
import httpx
from pydantic import ValidationError
from .base import LLMProvider, OutputT

class OpenAIProvider(LLMProvider):
    def __init__(self,client:httpx.Client|None=None,timeout:float=30.0)->None:
        self.api_key=os.getenv("OPENAI_API_KEY","")
        if not self.api_key: raise ValueError("OPENAI_API_KEY is required for the OpenAI provider")
        self.base_url=os.getenv("OPENAI_BASE_URL","https://api.openai.com/v1").rstrip("/")
        self.model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"); self.client=client or httpx.Client(timeout=timeout)
    def generate(self,task:str,output_model:type[OutputT])->OutputT:
        payload={"model":self.model,"messages":[{"role":"system","content":"Return JSON only matching: "+json.dumps(output_model.model_json_schema())},{"role":"user","content":task}],"response_format":{"type":"json_object"}}; last:Exception|None=None
        for attempt in range(2):
            try:
                response=self.client.post(f"{self.base_url}/chat/completions",json=payload,headers={"Authorization":f"Bearer {self.api_key}"}); response.raise_for_status()
                return output_model.model_validate_json(response.json()["choices"][0]["message"]["content"])
            except (httpx.TimeoutException,httpx.NetworkError,httpx.HTTPStatusError,ValidationError,IndexError,KeyError,TypeError,ValueError) as exc:
                last=exc
                if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code not in {408,429,500,502,503,504}: break
                if attempt: break
        raise ValueError("OpenAI provider returned no valid structured response") from last
