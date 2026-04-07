"""Coordinator — запуск пайплайна ролей и формирование ConsensusReport.

Coordinator знает о пайплайне (порядке ролей) и Gift Protocol.
Ядро (AgentForgeApp) знает о lifecycle. Coordinator использует оба.

Пайплайн:
  task → Role1 → Gift1 → Role2 → Gift2 → ... → ConsensusReport

Правила:
  - Если роль вернула Freedom.DECLINED → pipeline стоп, blocked=True
  - security_status = RED если любая роль c weight >= 1.3 вернула DECLINED
  - human_decision_required ВСЕГДА True
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field

from agentforge.gift import Freedom, Gift
from agentforge.kernel.app import AgentForgeApp

logger = logging.getLogger(__name__)


@dataclass
class ConsensusReport:
    """Итоговый отчёт команды — выход к человеку."""

    task_id: str
    telos: str
    gifts: list[Gift]
    recommendation: str
    variants: list[dict]
    security_status: str          # GREEN | YELLOW | RED
    blocked: bool
    human_decision_required: bool = True  # ВСЕГДА True
    anamnesis_used: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"ConsensusReport [{self.task_id}]",
            f"  Телос:    {self.telos}",
            f"  Security: {self.security_status}",
            f"  Blocked:  {self.blocked}",
            f"  Ролей:    {len(self.gifts)}",
            f"  Решение:  {self.recommendation}",
            f"  → human_decision_required: {self.human_decision_required}",
        ]
        return "\n".join(lines)


class Coordinator:
    """Запускает пайплайн ролей AgentForge и собирает ConsensusReport.

    Использование:
        app = AgentForgeApp()
        app.register(ScoutPlugin())
        app.register(ArchitectPlugin())
        app.register(SecurityPlugin())

        coordinator = Coordinator(app, telos="спроектировать X")
        report = await coordinator.run("Создай модель данных клиента")
    """

    def __init__(self, app: AgentForgeApp, telos: str = "") -> None:
        self.app = app
        self.telos = telos

    async def run(self, task: str, anamnesis_used: list[str] | None = None) -> ConsensusReport:
        """Запустить пайплайн ролей → ConsensusReport.

        Args:
            task: описание задачи
            anamnesis_used: ссылки на паттерны/решения из TeamMemory

        Returns:
            ConsensusReport с human_decision_required=True
        """
        task_id = str(uuid.uuid4())[:8]
        logger.info("Coordinator: task_id=%s, telos=%s", task_id, self.telos)

        await self.app.setup()

        gifts: list[Gift] = []
        current_gift: Gift | None = None
        blocked = False
        security_status = "GREEN"

        try:
            for role in self.app.sorted_roles:
                logger.info("  → роль: %s", role.role_name)
                gift = await role.run(task, current_gift)
                gift.task_id = task_id
                gifts.append(gift)

                if gift.freedom == Freedom.DECLINED:
                    logger.warning(
                        "  ✗ роль '%s' DECLINED — pipeline стоп", role.role_name
                    )
                    blocked = True
                    if role.weight >= 1.3:
                        security_status = "RED"
                    elif role.weight >= 1.2:
                        security_status = "YELLOW"
                    break

                current_gift = gift

        finally:
            await self.app.teardown()

        recommendation = self._build_recommendation(gifts, blocked, security_status)

        return ConsensusReport(
            task_id=task_id,
            telos=self.telos or task,
            gifts=gifts,
            recommendation=recommendation,
            variants=[],
            security_status=security_status,
            blocked=blocked,
            human_decision_required=True,
            anamnesis_used=anamnesis_used or [],
        )

    def _build_recommendation(
        self, gifts: list[Gift], blocked: bool, security_status: str
    ) -> str:
        if blocked:
            blocking_gift = gifts[-1]
            reasons = [a for a in blocking_gift.anamnesis if "declined_reason" in a]
            reason_str = reasons[0].replace("declined_reason: ", "") if reasons else "причина не указана"
            return (
                f"Пайплайн остановлен ролью '{blocking_gift.giver}': {reason_str}. "
                f"Требуется решение человека."
            )

        if not gifts:
            return "Ни одна роль не выполнена. Проверьте регистрацию ролей."

        last = gifts[-1]
        roles_str = " → ".join(g.giver for g in gifts)
        return (
            f"Пайплайн завершён: {roles_str}. "
            f"Security: {security_status}. "
            f"Последний дар от '{last.giver}': {str(last.content)[:120]}. "
            f"Решение за вами."
        )
