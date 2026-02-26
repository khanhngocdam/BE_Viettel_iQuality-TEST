from typing import Any, Dict
from sqlalchemy.orm import Session
from app.services.date_time_parse import parse_time_key
from app.services.get_kpi_data import AggregateLevel

# Reuse existing summary logic
from app.api.v1.endpoints.summary_assistant import summary_internet_kpi
from app.core.llm.tools.base import BaseTool

class NetworkSummaryTool(BaseTool):
    def __init__(self, db: Session):
        self.db = db
    @property
    def is_final_answer(self) -> bool:
        return True
    @property
    def name(self) -> str:
        return "get_network_summary"

    @property
    def description(self) -> str:
        return (
            "Lấy phân tích tình trạng mạng (KPI summary) của 1 nhà mạng (isp) theo ngày/tuần. "
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "isp": {
                    "type": "string",
                    "description": "Tên nhà mạng. Ví dụ: Viettel, VNPT, FPT.",
                },
                "date": {
                    "type": "string",
                    "description": (
                        "Ngày người dùng muốn hỏi. "
                        "KHÔNG ĐƯỢC tự tính toán ngày tháng năm (ví dụ không được tự điền 2026-...). "
                        "Chỉ điền ngày cụ thể nếu người dùng nói rõ (ví dụ 'ngày 5/2')."
                    ),
                },
                "aggregate_level": {
                    "type": "string",
                    "enum": ["daily", "weekly"],
                    "description": "Mức tổng hợp. Nếu hỏi theo ngày thì dùng 'daily'.",
                },
                "kpi_code": {
                    "type": "string",
                    "description": (
                        "Mã KPI cần phân tích."
                        "Ví dụ: internet_latency, internet_jitter, internet_packet_loss_rate."
                    ),
                },
            },
            "required": ["isp"],
        }

    def _normalize_isp(self, isp: str) -> str:
        s = isp.strip()
        low = s.lower()
        if low == "viettel":
            return "Viettel"
        if low == "vnpt":
            return "VNPT"
        if low == "fpt":
            return "FPT"
        return s

    def run(self, isp: str, date: str = "", aggregate_level: str = "daily", kpi_code: str = "internet_latency", **kwargs) -> str:
        isp_norm = self._normalize_isp(isp)
        if not isp_norm:
            return "MISSING_INFO: Thiếu thông tin nhà mạng (isp). Hãy hỏi người dùng cung cấp tên nhà mạng (Ví dụ: Viettel, VNPT, FPT)."
        if not date:
            return "MISSING_INFO: Thiếu thông tin ngày. Hãy hỏi người dùng cung cấp ngày (Ví dụ: ngày 5/2)."

        # Parse AggregateLevel
        agg_level_enum = AggregateLevel(aggregate_level)

        # Parse Date
        date_key = parse_time_key(date if date else None, agg_level_enum)
        # Execute Logic
        try:
            result = summary_internet_kpi(
                aggregate_level=agg_level_enum,
                isp=isp_norm,
                kpi_code=kpi_code,
                date_hour=date_key,
                db=self.db,
            )
            if isinstance(result, dict) and "data" in result:
                return str(result["data"])
            return str(result)
        except Exception as e:
            return f"Error executing tool: {str(e)}"
