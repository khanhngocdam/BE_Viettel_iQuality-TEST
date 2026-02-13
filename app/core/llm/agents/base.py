import json
import os
import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.llm.memory import BaseChatMemory
from app.core.llm.tools.base import BaseTool

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, db: Session, client: OpenAI = None, model: str = None):
        self.db = db
        
        # Init OpenAI Client if not provided
        if client:
            self.client = client
        else:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise RuntimeError("Missing OPENROUTER_API_KEY")
            
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            
        self.model = model or os.getenv("OPENROUTER_CHAT_MODEL", "arcee-ai/trinity-large-preview:free")
        self.tools: List[BaseTool] = []
        self.tool_map: Dict[str, BaseTool] = {}

    def register_tools(self, tools: List[BaseTool]):
        self.tools = tools
        self.tool_map = {t.name: t for t in self.tools}

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def run(self, input_message: str, context_history: List[Dict[str, Any]] = None) -> str:
        """
        Main execution method for the agent.
        """
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
            ]
            
            if context_history:
                messages.extend(context_history)
                
            messages.append({"role": "user", "content": input_message})

            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages, # type: ignore
                tools=[t.to_openai_schema() for t in self.tools] if self.tools else None, # type: ignore
                tool_choice="auto" if self.tools else None,
            )
            
            msg = response.choices[0].message
            final_answer = ""

            # Handle Tool Calls
            if msg.tool_calls:
                messages.append(msg.model_dump())
                
                for tool_call in msg.tool_calls:
                    if tool_call.type != "function":
                        continue

                    fn_name = tool_call.function.name
                    fn_args_str = tool_call.function.arguments or "{}"
                    
                    tool_result = f"Error: Tool '{fn_name}' not found."
                    if fn_name in self.tool_map:
                        try:
                            args = json.loads(fn_args_str)
                            logger.info(f"[{self.name}] Calling tool: {fn_name} | Args: {args}")
                            tool_result = self.tool_map[fn_name].run(**args)
                        except Exception as e:
                            tool_result = f"Error executing tool: {str(e)}"
                            logger.error(f"[{self.name}] Tool execution error: {e}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result),
                    })

                # Second Call to LLM
                final_res = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages, # type: ignore
                )
                final_answer = final_res.choices[0].message.content or ""
            else:
                final_answer = msg.content or ""

            return final_answer

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}")
            return f"Error in {self.name}: {str(e)}"
