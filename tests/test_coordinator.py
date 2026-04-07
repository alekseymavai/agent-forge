"""test_coordinator.py — тест Фазы 1.

Критерий готовности:
  Coordinator.run(task) → ConsensusReport, human_decision_required=True

Тест использует mock-роли, чтобы не зависеть от реальных LLM.
"""

import pytest

from agentforge.coordinator import ConsensusReport, Coordinator
from agentforge.gift import Freedom, Gift
from agentforge.kernel.app import AgentForgeApp
from agentforge.kernel.container import Container
from agentforge.kernel.plugin import RolePlugin


# ── mock-роли ─────────────────────────────────────────────────────────────── #


class MockScout(RolePlugin):
    role_name = "scout"
    depends_on = []
    weight = 0.9

    async def setup(self, container: Container) -> None:
        container.set("scout", self)

    async def run(self, task: str, gift: Gift | None) -> Gift:
        return Gift(
            giver="scout",
            receiver="architect",
            content={"code_map": "src/agentforge/**, tests/**", "risks": []},
            telos=task,
        )


class MockArchitect(RolePlugin):
    role_name = "architect"
    depends_on = ["scout"]
    weight = 1.0

    async def setup(self, container: Container) -> None:
        container.set("architect", self)

    async def run(self, task: str, gift: Gift | None) -> Gift:
        return Gift(
            giver="architect",
            receiver="security",
            content={"variant_a": "Plugin + DI", "variant_b": "Flat functions"},
            telos=task,
        )


class MockSecurity(RolePlugin):
    role_name = "security"
    depends_on = ["architect"]
    weight = 1.3

    def __init__(self, should_decline: bool = False) -> None:
        self.should_decline = should_decline

    async def setup(self, container: Container) -> None:
        container.set("security", self)

    async def run(self, task: str, gift: Gift | None) -> Gift:
        g = Gift(
            giver="security",
            receiver="coordinator",
            content={"vulnerabilities": []},
            telos=task,
        )
        if self.should_decline:
            g.decline("HIGH уязвимость: SQL injection в variant_b")
        return g


# ── тесты ─────────────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_coordinator_returns_consensus_report():
    """Базовый прогон: Scout → Architect → Security → ConsensusReport."""
    app = AgentForgeApp()
    app.register(MockScout())
    app.register(MockArchitect())
    app.register(MockSecurity())

    coordinator = Coordinator(app, telos="спроектировать ядро AgentForge")
    report = await coordinator.run("Создай kernel/ с RolePlugin и Container")

    assert isinstance(report, ConsensusReport)
    assert report.human_decision_required is True
    assert report.recommendation != ""
    assert report.telos == "спроектировать ядро AgentForge"
    assert len(report.gifts) == 3


@pytest.mark.asyncio
async def test_coordinator_security_declined_blocks_pipeline():
    """Security DECLINED → pipeline стоп, blocked=True, security_status=RED."""
    app = AgentForgeApp()
    app.register(MockScout())
    app.register(MockArchitect())
    app.register(MockSecurity(should_decline=True))

    coordinator = Coordinator(app, telos="тест блокировки")
    report = await coordinator.run("Задача с уязвимостью")

    assert report.blocked is True
    assert report.security_status == "RED"
    assert report.human_decision_required is True
    # пайплайн остановился на security — gifts содержат все 3 (scout, arch, security)
    assert len(report.gifts) == 3
    assert report.gifts[-1].freedom == Freedom.DECLINED


@pytest.mark.asyncio
async def test_coordinator_empty_app_returns_empty_report():
    """Пустой AgentForgeApp → report без gifts, recommendation об этом."""
    app = AgentForgeApp()
    coordinator = Coordinator(app, telos="тест пустого пайплайна")
    report = await coordinator.run("задача")

    assert report.human_decision_required is True
    assert report.blocked is False
    assert len(report.gifts) == 0
    assert "Ни одна роль" in report.recommendation


@pytest.mark.asyncio
async def test_consensus_report_summary():
    """ConsensusReport.summary() возвращает читаемую строку."""
    app = AgentForgeApp()
    app.register(MockScout())

    coordinator = Coordinator(app, telos="тест summary")
    report = await coordinator.run("задача")

    summary = report.summary()
    assert "ConsensusReport" in summary
    assert "human_decision_required: True" in summary
