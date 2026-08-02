from __future__ import annotations
import json
import os
import httpx
from pydantic import ValidationError
from .base import LLMProvider, OutputT

class GeminiProvider(LLMProvider):
    def __init__(self,client:httpx.Client|None=None,timeout:float=30.0)->None:
        self.api_key=os.getenv("GEMINI_API_KEY","")
        if not self.api_key: raise ValueError("GEMINI_API_KEY is required for the Gemini provider")
        self.model=os.getenv("GEMINI_MODEL","gemini-2.5-flash"); self.client=client or httpx.Client(timeout=timeout)
    def generate(self,task:str,output_model:type[OutputT])->OutputT:
        prompt=f"Return JSON only matching {json.dumps(output_model.model_json_schema())}\nTask: {task}"; payload={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseMimeType":"application/json"}}; last:Exception|None=None
        for attempt in range(2):
            try:
                response=self.client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",params={"key":self.api_key},json=payload); response.raise_for_status()
                return output_model.model_validate_json(response.json()["candidates"][0]["content"]["parts"][0]["text"])
            except (httpx.TimeoutException,httpx.NetworkError,httpx.HTTPStatusError,ValidationError,IndexError,KeyError,TypeError,ValueError) as exc:
                last=exc
                if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code not in {408,429,500,502,503,504}: break
                if attempt: break
        raise ValueError("Gemini provider returned no valid structured response") from last
