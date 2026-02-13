import json
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.core.llm.agents.base import BaseAgent
from app.core.llm.agents.analyst import DataAnalystAgent
from app.core.llm.agents.diagnostic import NetworkDiagnosticAgent
from app.core.llm.agents.reporting import ReportingAgent
from app.core.llm.tools.base import BaseTool

class CallAnalystTool(BaseTool):
    def __init__(self, agent: DataAnalystAgent):
        self.agent = agent

    @property
    def name(self) -> str:
        return "call_data_analyst"

    @property
    def description(self) -> str:
        return "Gọi Data Analyst Agent để lấy dữ liệu mạng, KPI, thống kê từ database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "Câu hỏi cụ thể về dữ liệu cần lấy. Ví dụ: 'Lấy dữ liệu latency của Viettel ngày hôm qua'."
                }
            },
            "required": ["query"]
        }

    def run(self, query: str, **kwargs) -> str:
        return self.agent.run(query)

class CallDiagnosticTool(BaseTool):
    def __init__(self, agent: NetworkDiagnosticAgent):
        self.agent = agent

    @property
    def name(self) -> str:
        return "call_network_diagnostic"

    @property
    def description(self) -> str:
        return "Gọi Network Diagnostic Agent để phân tích nguyên nhân, chẩn đoán vấn đề mạng dựa trên dữ liệu hoặc triệu chứng."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "Vấn đề cần chẩn đoán hoặc câu hỏi về nguyên nhân."
                },
                "context": {
                    "type": "string", 
                    "description": "Dữ liệu hoặc bối cảnh hiện tại (ví dụ: kết quả từ Data Analyst)."
                }
            },
            "required": ["query"]
        }

    def run(self, query: str, context: str = "", **kwargs) -> str:
        full_query = f"{query}\nContext: {context}"
        return self.agent.run(full_query)

class CallReportingTool(BaseTool):
    def __init__(self, agent: ReportingAgent):
        self.agent = agent

    @property
    def name(self) -> str:
        return "call_reporting"

    @property
    def description(self) -> str:
        return "Gọi Reporting Agent để tổng hợp thông tin và viết báo cáo định dạng chuyên nghiệp."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string", 
                    "description": "Nội dung thô cần định dạng thành báo cáo."
                }
            },
            "required": ["content"]
        }

    def run(self, content: str, **kwargs) -> str:
        return self.agent.run(content)


class SupervisorAgent(BaseAgent):
    def __init__(self, db: Session, **kwargs):
        super().__init__(db, **kwargs)
        
        # Initialize sub-agents
        self.analyst_agent = DataAnalystAgent(db, **kwargs)
        self.diagnostic_agent = NetworkDiagnosticAgent(db, **kwargs)
        self.reporting_agent = ReportingAgent(db, **kwargs)
        
        # Register routing tools
        self.register_tools([
            CallAnalystTool(self.analyst_agent),
            CallDiagnosticTool(self.diagnostic_agent),
            CallReportingTool(self.reporting_agent),
        ])

    @property
    def name(self) -> str:
        return "Supervisor Agent"

    def get_system_prompt(self) -> str:
        return (
            "Bạn là Supervisor (Quản lý) của hệ thống hỗ trợ mạng Viettel iQuality.\n"
            "Bạn có các nhân viên (agent) dưới quyền:\n"
            "1. call_data_analyst: Chuyên lấy số liệu, thống kê từ DB.\n"
            "2. call_network_diagnostic: Chuyên chẩn đoán nguyên nhân, phân tích kỹ thuật.\n"
            "3. call_reporting: Chuyên trình bày báo cáo đẹp, dễ đọc.\n\n"
            "Quy trình xử lý:\n"
            "- Bước 1: Phân tích câu hỏi người dùng.\n"
            "- Bước 2: Gọi các agent phù hợp (Analyst -> Diagnostic -> Reporting).\n"
            "- Bước 3: Tổng hợp kết quả cuối cùng để trả lời người dùng.\n\n"
            "Ví dụ: Nếu người dùng hỏi 'Tại sao mạng chậm hôm qua?', bạn cần:\n"
            "1. Gọi Analyst để lấy dữ liệu mạng hôm qua.\n"
            "2. Gọi Diagnostic với dữ liệu vừa lấy được để tìm nguyên nhân.\n"
            "3. Gọi Reporting (hoặc tự tổng hợp) để trả lời người dùng."
        )
