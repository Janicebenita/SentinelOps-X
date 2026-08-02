from abc import ABC, abstractmethod
from typing import TypeVar
from pydantic import BaseModel
OutputT = TypeVar("OutputT", bound=BaseModel)
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, task:str, output_model:type[OutputT])->OutputT: ...
