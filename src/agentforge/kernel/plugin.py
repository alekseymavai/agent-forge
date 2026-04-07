"""RolePlugin — абстрактный плагин роли AgentForge.

Каждая роль — плагин с призванием, lifecycle и зависимостями.
Ядро (AgentForgeApp) выстраивает граф зависимостей и запускает роли
в правильном порядке.

Lifecycle роли:
  setup(container)   → инициализация, регистрация сервисов в контейнере
  run(task, gift)    → выполнить призвание, вернуть дар следующей роли
  teardown()         → graceful shutdown
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentforge.kernel.container import Container
    from agentforge.gift import Gift


class RolePlugin(ABC):
    """Абстрактный плагин роли AgentForge.

    Подкласс объявляет:
      - role_name: str  — уникальное имя роли (ключ в реестре)
      - depends_on: list[str] — роли, которые должны отработать раньше
      - weight: float  — вес в консенсусе (Security=1.3, QA=1.2, остальные=1.0)
    """

    role_name: str = ""
    depends_on: list[str] = []
    weight: float = 1.0

    @abstractmethod
    async def setup(self, container: "Container") -> None:
        """Инициализировать роль и зарегистрировать сервисы в контейнере."""

    @abstractmethod
    async def run(self, task: str, gift: "Gift | None") -> "Gift":
        """
        Выполнить призвание роли.
        Принять дар от предыдущей роли → выполнить работу → подарить следующей.
        """

    async def teardown(self) -> None:
        """Graceful shutdown ресурсов роли."""
