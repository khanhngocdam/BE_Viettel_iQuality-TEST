from sqlalchemy.orm import Session
from app.core.llm.agents.base import BaseAgent
from app.core.llm.tools.network_kpi import NetworkSummaryTool

class DataAnalystAgent(BaseAgent):
    def __init__(self, db: Session, **kwargs):
        super().__init__(db, **kwargs)
        # Register tools
        self.register_tools([
            NetworkSummaryTool(db=db),
            # Add more data analysis tools here
        ])

    @property
    def name(self) -> str:
        return "Data Analyst Agent"

    def get_system_prompt(self) -> str:
        return (
            "Bạn là Data Analyst chuyên về dữ liệu mạng viễn thông.\n"
            "Nhiệm vụ của bạn là truy xuất dữ liệu từ database, phân tích các chỉ số KPI như latency, packet loss, jitter.\n"
            "Khi được hỏi về số liệu, hãy dùng tool để lấy dữ liệu chính xác.\n"
            "Luôn trả về kết quả dưới dạng tóm tắt các con số quan trọng."
        )
