"""
agent_bus.py — AgentBus (файловая шина + лог)

Транспортный слой для Gift Protocol.
Фаза 1: файловая шина (.agent_bus/)
Фаза 3+: Redis транспорт (замена без изменения интерфейса)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from .gift import Gift, Freedom


class AgentBus:
    """
    Файловая шина передачи даров между ролями.

    Использование:
        bus = AgentBus(task_id="M.6", base_dir=".agent_bus")
        await bus.send(gift)
        gift = await bus.receive("architect")
    """

    def __init__(self, task_id: str, base_dir: str = ".agent_bus"):
        self.task_id = task_id
        self.base = Path(base_dir)
        self._init_dirs()

    def _init_dirs(self) -> None:
        for d in ["inbox", "outbox", "consensus", "log"]:
            (self.base / d).mkdir(parents=True, exist_ok=True)

    def send(self, gift: Gift) -> Gift:
        """Положить дар в inbox получателя."""
        gift.gift_id = str(uuid.uuid4())[:8]
        gift.task_id = gift.task_id or self.task_id

        path = self.base / "inbox" / f"{gift.receiver}_{gift.task_id}.json"
        payload = gift.to_dict()
        # content сериализуем как строку если не dict/list
        if hasattr(gift.content, "__dict__"):
            payload["content"] = vars(gift.content)
        elif isinstance(gift.content, (dict, list)):
            payload["content"] = gift.content
        else:
            payload["content"] = str(gift.content)

        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        self._log(gift)
        return gift

    def receive(self, role: str, task_id: Optional[str] = None) -> Optional[dict]:
        """Прочитать дар из inbox для роли."""
        tid = task_id or self.task_id
        path = self.base / "inbox" / f"{role}_{tid}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def save_consensus(self, report: dict) -> None:
        """Сохранить итог совещания."""
        path = self.base / "consensus" / f"{self.task_id}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    def _log(self, gift: Gift) -> None:
        """Дописать в лог шины."""
        log_path = self.base / "log" / f"{self.task_id}.jsonl"
        with log_path.open("a") as f:
            f.write(json.dumps(gift.to_dict(), ensure_ascii=False) + "\n")
