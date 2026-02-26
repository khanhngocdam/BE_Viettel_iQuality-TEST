import json
import os
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.llm.memory import FileChatMemory, BaseChatMemory
from app.core.llm.tools.network_kpi import NetworkSummaryTool

# Setup basic logger
logger = logging.getLogger(__name__)

class ChatAgent:
    def __init__(self, session_id: str, db: Session):
        self.session_id = session_id
        self.db = db
        
        # 1. Init Memory
        self.memory: BaseChatMemory = FileChatMemory(session_id)

        # 2. Init OpenAI Client
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENROUTER_API_KEY")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        # Default model if not set in env
        self.model = os.getenv("OPENROUTER_CHAT_MODEL", "arcee-ai/trinity-large-preview:free")

        # 3. Init Tools
        # Add more tools here in the future
        self.tools = [
            NetworkSummaryTool(db=db),
        ]
        self.tool_map = {t.name: t for t in self.tools}

    def _get_system_prompt(self) -> str:
        return (
            "Bạn là trợ lý hỏi đáp thông minh cho hệ thống Viettel iQuality.\n"
            "Nhiệm vụ của bạn là hỗ trợ người dùng tra cứu thông tin chất lượng mạng (KPI) dựa trên dữ liệu đo kiểm thực tế.\n\n"
        )

    def chat(self, user_message: str) -> str:
        try:
            # 1. Load context history (Last 20 messages)
            full_history = self.memory.load_history()
            context_history = full_history[-20:]

            # 2. Construct messages
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": self._get_system_prompt()},
                *context_history,
                {"role": "user", "content": user_message},
            ]

            # 3. First Call to LLM
            # Cast messages to Any to avoid strict typing issues with OpenAI lib
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages, # type: ignore
                tools=[t.to_openai_schema() for t in self.tools], # type: ignore
                tool_choice="auto",
            )
            
            msg = response.choices[0].message
            final_answer = ""

            # 4. Handle Tool Calls
            if msg.tool_calls:
                # Add Assistant's "intent to call tool" message to history
                # Convert ChatCompletionMessage to dict to match history format
                messages.append(msg.model_dump())
                # Optionally, some tools trả về luôn câu trả lời cuối cùng
                final_answer_from_tool: Optional[str] = None

                for tool_call in msg.tool_calls:
                    # Verify type
                    if tool_call.type != "function":
                        continue
                    fn_name = tool_call.function.name
                    fn_args_str = tool_call.function.arguments or "{}"

                    # Execute Tool
                    tool_result = f"Error: Tool '{fn_name}' not found."
                    if fn_name in self.tool_map:
                        try:
                            args = json.loads(fn_args_str)
                            tool_instance = self.tool_map[fn_name]
                            logger.info(f"[Agent] Calling tool: {fn_name} | Args: {args}")
                            tool_output = tool_instance.run(**args)
                            tool_result = tool_output

                            # Nếu tool được đánh dấu là trả về final answer thì dùng luôn
                            if getattr(tool_instance, "is_final_answer", False):
                                final_answer_from_tool = str(tool_output)
                        except json.JSONDecodeError:
                            tool_result = "Error: Invalid JSON arguments."
                        except Exception as e:
                            tool_result = f"Error executing tool: {str(e)}"
                            logger.error(f"[Agent] Tool execution error: {e}")
                    # Append Tool Output
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result),
                    })

                if final_answer_from_tool is not None:
                    # Một (hoặc nhiều) tool đã trả về luôn câu trả lời cuối cùng
                    final_answer = final_answer_from_tool
                else:
                    # 5. Second Call to LLM (Generate final answer based on tool output)
                    final_res = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages, # type: ignore
                    )
                    final_answer = final_res.choices[0].message.content or ""
            else:
                # No tool called, just direct answer
                final_answer = msg.content or ""

            # 6. Save new turn to memory
            if final_answer:
                self.memory.add_turn(user_message, final_answer)

            return final_answer or "Xin lỗi, tôi không thể trả lời lúc này (Empty response)."

        except Exception as e:
            logger.error(f"[Agent] Chat error: {e}")
            return f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}"
