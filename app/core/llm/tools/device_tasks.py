from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.llm.tools.base import BaseTool


class GetActiveDevicesTool(BaseTool):
    def __init__(self, db: Session):
        self.db = db

    @property
    def is_final_answer(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return "get_active_devices"

    @property
    def description(self) -> str:
        return (
            "Lấy danh sách thiết bị đang hoạt động gần đây. "
            "Thiết bị được xem là đang hoạt động nếu last_seen trong vòng 1 phút gần nhất."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def run(self, **kwargs) -> str:
        try:
            sql = text(
                """
                SELECT username
                FROM account_and_config
                WHERE last_seen::timestamp >= now() - interval '1 minute'
                ORDER BY username ASC
                """
            )
            rows = self.db.execute(sql).mappings().all()
            usernames = [str(r["username"]) for r in rows if r.get("username")]

            if not usernames:
                return "Hiện tại không có thiết bị nào hoạt động trong 1 phút gần nhất."
            return "Danh sách thiết bị đang hoạt động: " + ", ".join(usernames)
        except Exception as e:
            return f"Error executing tool: {str(e)}"


class DeviceCommandTool(BaseTool):
    def __init__(self, db: Session):
        self.db = db

    @property
    def is_final_answer(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return "send_device_command"

    @property
    def description(self) -> str:
        return (
            "Luật điều khiển thiết bị (bắt buộc):"
            "- Mỗi lệnh thiết bị tương ứng đúng 1 cặp (action, username)."
            "- Không bỏ sót, không suy diễn thêm thiết bị."
            "- Chỉ chấp nhận action: reload, restart, update_<version>."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": (
                        "Username thiết bị. Ví dụ: DNG_Speedtest_Viettel_02, "
                        "HNI_Agent_1, HNI_Monitoring_Viettel_01."
                    ),
                },
                "action": {
                    "type": "string",
                    "description": (
                        "Hành động cần gửi tới thiết bị. "
                        "Hỗ trợ: 'reload', 'restart' hoặc 'update_<version>'. "
                        "Ví dụ: update_VQT-Agent-2.6.9554.16557.zip"
                    ),
                },
            },
            "required": ["username", "action"],
        }

    def run(self, username: str, action: str, **kwargs) -> str:
        try:
            username_clean = (username or "").strip()
            action_clean = (action or "").strip()
            action_lower = action_clean.lower()

            if not username_clean:
                return "MISSING_INFO: Thiếu username thiết bị."
            if not (
                action_lower in {"reload", "restart"}
                or action_lower.startswith("update_")
            ):
                return (
                    "MISSING_INFO: Action không hợp lệ. "
                    "Chỉ hỗ trợ reload/restart hoặc update_<version>."
                )
            if action_lower == "update_" or action_clean.endswith("_"):
                return "MISSING_INFO: Thiếu version sau tiền tố update_."

            # Validate username exists in source device table before writing command
            exists_sql = text(
                """
                SELECT 1
                FROM account_and_config
                WHERE username = :username
                LIMIT 1
                """
            )
            exists = self.db.execute(exists_sql, {"username": username_clean}).first()
            if not exists:
                suggest_sql = text(
                    """
                    SELECT username
                    FROM account_and_config
                    WHERE username ILIKE :kw
                    ORDER BY username ASC
                    LIMIT 5
                    """
                )
                suggestions = self.db.execute(
                    suggest_sql,
                    {"kw": f"%{username_clean}%"},
                ).mappings().all()
                suggestion_names = [str(r["username"]) for r in suggestions if r.get("username")]
                if suggestion_names:
                    return (
                        f"MISSING_INFO: Tên thiết bị '{username_clean}' không hợp lệ. "
                        f"Gợi ý: {', '.join(suggestion_names)}."
                    )
                return f"MISSING_INFO: Tên thiết bị '{username_clean}' không hợp lệ hoặc không tồn tại."
            insert_sql = text(
                """
                INSERT INTO device_commands (
                    username, command, created_time, expire_time, executed
                )
                VALUES (
                    :username, :command, now(), now() + interval '3 minute', false
                )
                """
            )
            self.db.execute(insert_sql, {"username": username_clean, "command": action_clean})
            self.db.commit()

            return f"Đã ghi lệnh '{action_clean}' cho thiết bị '{username_clean}'."
        except Exception as e:
            self.db.rollback()
            return f"Error executing tool: {str(e)}"
