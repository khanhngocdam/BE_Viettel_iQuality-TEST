import json


import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

# 1. Interface chuẩn (để sau này RedisMemory cũng kế thừa cái này)
class BaseChatMemory(ABC):
    @abstractmethod
    def load_history(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_turn(self, user_msg: str, assistant_msg: str):
        pass

# 2. Implementation hiện tại: File JSON
class FileChatMemory(BaseChatMemory):
    def __init__(self, session_id: str, file_path: str = "chat_sessions.json"):
        self.session_id = session_id
        self.file_path = file_path

    def _load_all(self) -> Dict[str, List[Dict[str, Any]]]:
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_all(self, data: Dict[str, List[Dict[str, Any]]]):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving chat history: {e}")

    def load_history(self) -> List[Dict[str, Any]]:
        all_sessions = self._load_all()
        return all_sessions.get(self.session_id, [])

    def add_turn(self, user_msg: str, assistant_msg: str):
        all_sessions = self._load_all()
        history = all_sessions.get(self.session_id, [])
        
        new_turns = [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg},
        ]
        
        # Append và lưu lại
        all_sessions[self.session_id] = history + new_turns
        self._save_all(all_sessions)

# 3. (Sau này) Redis Implementation - Chỉ cần viết thêm class này
# class RedisChatMemory(BaseChatMemory):
#     def __init__(self, session_id, redis_client): ...
#     def load_history(self): return redis_client.lrange(...)
#     def add_turn(self, ...): redis_client.rpush(...)
