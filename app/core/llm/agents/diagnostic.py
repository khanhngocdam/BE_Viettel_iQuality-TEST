from sqlalchemy.orm import Session
from app.core.llm.agents.base import BaseAgent

class NetworkDiagnosticAgent(BaseAgent):
    def __init__(self, db: Session, **kwargs):
        super().__init__(db, **kwargs)
        # Register tools
        # Currently no specific tools, but could add network diagnostic tools later
        self.register_tools([])

    @property
    def name(self) -> str:
        return "Network Diagnostic Agent"

    def get_system_prompt(self) -> str:
        return (
            "Bạn là chuyên gia mạng viễn thông (Network Diagnostic Expert).\n"
            "Nhiệm vụ của bạn là nhận định nguyên nhân gây suy giảm chất lượng mạng dựa trên các số liệu được cung cấp.\n"
            "Hãy phân tích sâu về các nguyên nhân tiềm năng như: nghẽn băng thông quốc tế, sự cố cáp quang biển, thiết bị đầu cuối, routing, v.v.\n"
            "Dựa vào packet loss, latency, jitter để đưa ra chẩn đoán chính xác."
        )
