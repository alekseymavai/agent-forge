"""
agent_core.py — базовый класс агента-лица

Каждая роль — лицо с призванием (логосом), весом и ответственностью.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .gift import Gift
from .project_context import ProjectContext


# Веса ролей (иерархия телоса)
ROLE_WEIGHTS: dict[str, float] = {
    "security":    1.3,  # блокирующая — P0 стопит деплой
    "qa":          1.2,  # зелёные тесты обязательны
    "architect":   1.0,
    "backend_dev": 1.0,
    "frontend_dev": 1.0,
    "scout":       0.9,  # информирует, не решает
    "devops":      0.9,
    "tech_writer": 0.7,
}


@dataclass
class RoleManifest:
    """Призвание роли — логос и телос."""
    role: str
    calling: str    # краткое описание призвания
    gifts: str      # что дарит
    weight: float   # вес в консенсусе


class AgentBase(ABC):
    """
    Базовый класс агента-лица AgentForge.

    Подкласс обязан реализовать:
      - manifest — призвание роли
      - run(task, context, anamnesis) → Gift
    """

    @property
    @abstractmethod
    def manifest(self) -> RoleManifest:
        ...

    @abstractmethod
    async def run(
        self,
        task: str,
        context: ProjectContext,
        anamnesis: list[Gift],
    ) -> Gift:
        """
        Выполнить призвание.

        Args:
            task:      описание задачи
            context:   контекст проекта (context.yaml)
            anamnesis: предыдущие дары (со-присутствие прошлого)

        Returns:
            Gift — дар следующей роли
        """
        ...

    def _make_gift(
        self,
        receiver: str,
        content: Any,
        telos: str,
        task_id: str = "",
        anamnesis: list[str] | None = None,
    ) -> Gift:
        """Создать дар от этой роли."""
        return Gift(
            giver=self.manifest.role,
            receiver=receiver,
            content=content,
            telos=telos,
            task_id=task_id,
            anamnesis=anamnesis or [],
        )
