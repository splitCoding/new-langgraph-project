from enum import Enum
from typing import TypedDict


class LLMModel:
    def __init__(self, model: str, temperature: float | None = 0):
        self.name = model
        self.temperature = temperature


class LLMModels(TypedDict):
    gpt_3_5_turbo: LLMModel
    gpt_4_1_nano: LLMModel
    gpt_4_1_mini: LLMModel
    gpt_o_4_mini: LLMModel


models: LLMModels = {
    "gpt_3_5_turbo": LLMModel("gpt-3.5-turbo", 0),
    "gpt_4_1_nano": LLMModel("gpt-4.1-nano", 0),
    "gpt_4_1_mini": LLMModel("gpt-4.1-mini", 0),
    "gpt_o_4_mini": LLMModel("o4-mini", None),  # temperature 없음
}

__all__ = ["models", "LLMModel"]
