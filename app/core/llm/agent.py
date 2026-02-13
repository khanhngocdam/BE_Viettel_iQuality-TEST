import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from app.core.llm.memory import FileChatMemory, BaseChatMemory
from app.core.llm.agents.supervisor import SupervisorAgent

# Setup basic logger
logger = logging.getLogger(__name__)

class ChatAgent:
    """
    Main entry point for the chat system.
    This class manages the session, memory, and delegates the actual processing to the Supervisor Agent.
    """
    def __init__(self, session_id: str, db: Session):
        self.session_id = session_id
        self.db = db
        
        # 1. Init Memory
        self.memory: BaseChatMemory = FileChatMemory(session_id)

        # 2. Init Supervisor Agent (The main orchestrator)
        self.supervisor = SupervisorAgent(db=db)

    def chat(self, user_message: str) -> str:
        try:
            # 1. Load context history (Last 20 messages)
            full_history = self.memory.load_history()
            context_history = full_history[-20:]

            # 2. Delegate to Supervisor Agent
            # The Supervisor will coordinate with Analyst, Diagnostic, Reporting agents
            final_answer = self.supervisor.run(
                input_message=user_message, 
                context_history=context_history
            )

            # 3. Save new turn to memory
            if final_answer:
                self.memory.add_turn(user_message, final_answer)

            return final_answer or "Xin lỗi, tôi không thể trả lời lúc này (Empty response)."

        except Exception as e:
            logger.error(f"[ChatAgent] Error: {e}")
            return f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}"
