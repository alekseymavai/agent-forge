"""
gift.py — Gift Protocol

Каждая передача эстафеты между ролями — дар.
Основан на PLM-GIFT онтологии (unidel2035/plm, Гаврилов Денис, 2026).

Пять аксиом:
  A1. Лицо     — роль с призванием, не функция
  A2. Кеносис  — каждый дар стоит (токены, время)
  A3. Анамнезис — прошлые дары со-присутствуют в новом
  A4. Телос    — каждая задача имеет цель выше себя
  A5. Свобода  — DEFERRED не ошибка, условие дара
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Freedom(str, Enum):
    ACCEPTED  = "ACCEPTED"   # дар принят, работа начата
    DEFERRED  = "DEFERRED"   # дар отложен (A5 — не ошибка)
    DECLINED  = "DECLINED"   # дар отклонён с обратной связью


@dataclass
class Gift:
    """
    Дар между ролями — первичный примитив AgentForge.

    Пример:
        gift = Gift(
            giver="scout",
            receiver="architect",
            content=scout_report,
            telos="спроектировать MemoryService без N+1",
            anamnesis=["task:M4", "adr:ADR-002"],
        )
    """
    giver:     str           # роль-отправитель
    receiver:  str           # роль-получатель
    content:   Any           # содержание дара
    telos:     str           # зачем — связь с телосом задачи
    task_id:   str = ""      # ID задачи из плана
    anamnesis: list[str] = field(default_factory=list)  # что помним
    freedom:   Freedom = Freedom.ACCEPTED
    cost:      int = 0       # кеносис — стоимость (токены LLM)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    gift_id:   str = ""      # заполняется GiftBus при отправке

    def to_dict(self) -> dict:
        return {
            "gift_id":   self.gift_id,
            "task_id":   self.task_id,
            "giver":     self.giver,
            "receiver":  self.receiver,
            "telos":     self.telos,
            "anamnesis": self.anamnesis,
            "freedom":   self.freedom.value,
            "cost":      self.cost,
            "timestamp": self.timestamp,
            # content сериализуется отдельно (может быть сложным объектом)
        }

    def accept(self) -> "Gift":
        self.freedom = Freedom.ACCEPTED
        return self

    def defer(self, reason: str = "") -> "Gift":
        """A5 — свобода. DEFERRED не ошибка."""
        self.freedom = Freedom.DEFERRED
        if reason:
            self.anamnesis.append(f"deferred_reason: {reason}")
        return self

    def decline(self, reason: str = "") -> "Gift":
        self.freedom = Freedom.DECLINED
        if reason:
            self.anamnesis.append(f"declined_reason: {reason}")
        return self
