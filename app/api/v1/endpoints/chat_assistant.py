import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.llm.agent import ChatAgent

router = APIRouter(tags=["Chat-Assistant"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message in Vietnamese/English")
    session_id: str | None = Field(None, description="Session ID to maintain chat context (optional)")

@router.post("/chat")
def chat_assistant(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint chat với AI Assistant.
    - Tự động quản lý lịch sử chat (File/Redis).
    - Tự động gọi Function Tool (KPI mạng, Weather...).
    """
    try:
        # 1. Manage Session ID
        session_id = payload.session_id
        if not session_id:
            session_id = str(uuid.uuid4())

        # 2. Init Agent
        agent = ChatAgent(session_id=session_id, db=db)
        
        # 3. Process
        answer = agent.chat(payload.message)
        
        # 4. Return
        return {"answer": answer, "session_id": session_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
