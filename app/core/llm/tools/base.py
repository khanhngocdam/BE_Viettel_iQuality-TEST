from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Tên gọi function cho LLM"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Mô tả công dụng"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Schema (Pydantic-like JSON) cho tham số"""
        pass

    @abstractmethod
    def run(self, **kwargs) -> str:
        """Logic thực thi tool"""
        pass

    def to_openai_schema(self) -> Dict[str, Any]:
        """Tự động sinh schema cho OpenAI API"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
