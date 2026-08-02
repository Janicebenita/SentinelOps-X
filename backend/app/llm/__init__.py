import warnings
from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .mock_provider import MockLLMProvider
from .openai_provider import OpenAIProvider

provider_warning: str | None = None

def get_provider(name:str)->LLMProvider:
    global provider_warning
    provider_warning=None
    try:
        if name=="openai": return OpenAIProvider()
        if name=="gemini": return GeminiProvider()
        return MockLLMProvider()
    except ValueError:
        provider_warning=f"{name} is unavailable; using deterministic mock provider"
        warnings.warn(provider_warning,RuntimeWarning,stacklevel=2)
        return MockLLMProvider()
