from sqlalchemy.orm import Session
from app.core.llm.agents.base import BaseAgent

class ReportingAgent(BaseAgent):
    def __init__(self, db: Session, **kwargs):
        super().__init__(db, **kwargs)
        # Register tools
        # Formatting tools could be added here
        self.register_tools([])

    @property
    def name(self) -> str:
        return "Reporting Agent"

    def get_system_prompt(self) -> str:
        return (
            "Bạn là trợ lý viết báo cáo chuyên nghiệp (Reporting Agent).\n"
            "Nhiệm vụ của bạn là tổng hợp thông tin từ các agent khác để tạo thành một báo cáo hoàn chỉnh.\n"
            "Sử dụng định dạng Markdown rõ ràng, dễ đọc.\n"
            "Nội dung báo cáo cần có:\n"
            "- Tóm tắt tình hình\n"
            "- Chi tiết các chỉ số\n"
            "- Nguyên nhân và giải pháp (nếu có)\n"
            "Tránh dùng từ ngữ quá kỹ thuật nếu không cần thiết."
        )
