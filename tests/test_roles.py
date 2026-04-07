"""test_roles.py — тест Фазы 2.

Тестирует Scout, Architect, Security через mock LLM-клиент.
Реальные API вызовы не делаются.

Критерии Фазы 2:
  - Scout.run()    → Gift с content (dict с полями карты)
  - Security DECLINED → pipeline стоп (проверяется через Coordinator)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from agentforge.coordinator import Coordinator
from agentforge.gift import Freedom, Gift
from agentforge.kernel.app import AgentForgeApp
from agentforge.kernel.container import Container
from agentforge.roles.architect import ArchitectPlugin
from agentforge.roles.scout import ScoutPlugin
from agentforge.roles.security import SecurityPlugin


# ── mock LLM клиент ───────────────────────────────────────────────────────── #

SCOUT_RESPONSE = json.dumps({
    "files_affected": ["src/agentforge/coordinator.py — основной файл пайплайна"],
    "existing_pattern": "RolePlugin + Container из kernel/",
    "risks": ["изменение coordinator может сломать Фазу 1"],
    "already_done": "kernel/, coordinator.py, gift.py реализованы",
    "tests_found": ["tests/test_coordinator.py — покрывает пайплайн"],
    "fragile_zones": ["src/agentforge/coordinator.py — сердце системы"],
    "ready_for_architect": True,
})

ARCHITECT_RESPONSE = json.dumps({
    "variant_a": {
        "name": "Plugin + DI",
        "approach": "Роли как RolePlugin с DI-контейнером",
        "files_to_create": ["src/agentforge/roles/scout.py"],
        "files_to_modify": ["src/agentforge/__init__.py"],
        "pros": ["заменяемость", "lifecycle"],
        "cons": ["чуть сложнее"],
    },
    "variant_b": {
        "name": "Flat functions",
        "approach": "Просто async функции без классов",
        "files_to_create": ["src/agentforge/roles/functions.py"],
        "files_to_modify": [],
        "pros": ["просто"],
        "cons": ["нет заменяемости", "нет DI"],
    },
    "recommendation": "вариант A — Plugin + DI, соответствует ADR-001",
    "completion_criteria": "все тесты зелёные, Security GREEN",
    "adr_needed": False,
    "adr_text": "",
})

SECURITY_GREEN_RESPONSE = json.dumps({
    "findings": [],
    "secrets_check": "PASS",
    "injection_check": "PASS",
    "validation_check": "PASS",
    "overall_status": "GREEN",
    "verdict": "ACCEPTED",
    "decline_reason": "",
})

SECURITY_RED_RESPONSE = json.dumps({
    "findings": [
        {
            "severity": "HIGH",
            "description": "Hardcoded API key в variant_b/functions.py",
            "location": "src/agentforge/roles/functions.py",
        }
    ],
    "secrets_check": "FAIL",
    "injection_check": "PASS",
    "validation_check": "PASS",
    "overall_status": "RED",
    "verdict": "DECLINED",
    "decline_reason": "Hardcoded API key в variant_b/functions.py",
})


def _make_mock_client(*responses: str):
    """Создать mock AsyncAnthropic клиент с заданными ответами по очереди."""
    client = MagicMock()
    message_mocks = []
    for text in responses:
        msg = MagicMock()
        msg.content = [MagicMock(text=text)]
        message_mocks.append(msg)

    call_count = [0]

    async def create(**kwargs):
        idx = min(call_count[0], len(message_mocks) - 1)
        call_count[0] += 1
        return message_mocks[idx]

    client.messages.create = create
    return client


def _make_app_with_mock(mock_client, *, security_red: bool = False) -> AgentForgeApp:
    """Создать AgentForgeApp с mock LLM клиентом."""
    app = AgentForgeApp()
    app.container.set(
        "llm_client",
        _make_mock_client(
            SCOUT_RESPONSE,
            ARCHITECT_RESPONSE,
            SECURITY_RED_RESPONSE if security_red else SECURITY_GREEN_RESPONSE,
        ),
    )
    app.register(ScoutPlugin())
    app.register(ArchitectPlugin())
    app.register(SecurityPlugin())
    return app


# ── тесты ─────────────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_scout_returns_gift_with_content():
    """Scout.run() → Gift с content (dict с полями карты)."""
    plugin = ScoutPlugin()
    container = Container()
    container.set("llm_client", _make_mock_client(SCOUT_RESPONSE))
    await plugin.setup(container)

    gift = await plugin.run("Реализовать roles/scout.py", None)

    assert isinstance(gift, Gift)
    assert gift.giver == "scout"
    assert gift.receiver == "architect"
    assert gift.freedom == Freedom.ACCEPTED
    assert isinstance(gift.content, dict)
    assert "files_affected" in gift.content
    assert "existing_pattern" in gift.content
    assert gift.content["ready_for_architect"] is True


@pytest.mark.asyncio
async def test_architect_returns_two_variants():
    """Architect.run() → Gift с двумя вариантами от Scout."""
    scout_gift = Gift(
        giver="scout",
        receiver="architect",
        content={"files_affected": ["src/x.py"], "existing_pattern": "Plugin", "risks": [], "already_done": "", "tests_found": [], "fragile_zones": [], "ready_for_architect": True},
        telos="тест",
    )

    plugin = ArchitectPlugin()
    container = Container()
    container.set("llm_client", _make_mock_client(ARCHITECT_RESPONSE))
    await plugin.setup(container)

    gift = await plugin.run("Реализовать roles/", scout_gift)

    assert gift.giver == "architect"
    assert gift.receiver == "security"
    assert gift.freedom == Freedom.ACCEPTED
    assert "variant_a" in gift.content
    assert "variant_b" in gift.content
    assert gift.content["recommendation"] != ""


@pytest.mark.asyncio
async def test_security_accepted_on_green():
    """Security GREEN → ACCEPTED, gift не DECLINED."""
    architect_gift = Gift(
        giver="architect",
        receiver="security",
        content={"variant_a": {"name": "A", "approach": "safe"}, "recommendation": "A лучше"},
        telos="тест",
    )

    plugin = SecurityPlugin()
    container = Container()
    container.set("llm_client", _make_mock_client(SECURITY_GREEN_RESPONSE))
    await plugin.setup(container)

    gift = await plugin.run("тест", architect_gift)

    assert gift.freedom == Freedom.ACCEPTED
    assert gift.content["overall_status"] == "GREEN"
    assert len(gift.content["findings"]) == 0


@pytest.mark.asyncio
async def test_security_declined_on_high():
    """Security HIGH → DECLINED, gift.freedom == DECLINED."""
    architect_gift = Gift(
        giver="architect",
        receiver="security",
        content={"variant_a": {"name": "A"}, "variant_b": {"name": "B с hardcoded key"}},
        telos="тест",
    )

    plugin = SecurityPlugin()
    container = Container()
    container.set("llm_client", _make_mock_client(SECURITY_RED_RESPONSE))
    await plugin.setup(container)

    gift = await plugin.run("тест", architect_gift)

    assert gift.freedom == Freedom.DECLINED
    assert gift.content["overall_status"] == "RED"
    assert any(f["severity"] == "HIGH" for f in gift.content["findings"])


@pytest.mark.asyncio
async def test_full_pipeline_scout_architect_security_green():
    """Полный прогон Scout → Architect → Security GREEN → ConsensusReport."""
    app = _make_app_with_mock(None, security_red=False)
    coordinator = Coordinator(app, telos="реализовать roles/")
    report = await coordinator.run("Создай Scout, Architect, Security роли")

    assert report.blocked is False
    assert report.security_status == "GREEN"
    assert len(report.gifts) == 3
    assert report.gifts[0].giver == "scout"
    assert report.gifts[1].giver == "architect"
    assert report.gifts[2].giver == "security"
    assert report.human_decision_required is True


@pytest.mark.asyncio
async def test_full_pipeline_security_blocks_on_high():
    """Полный прогон: Security DECLINED → pipeline стоп, blocked=True."""
    app = _make_app_with_mock(None, security_red=True)
    coordinator = Coordinator(app, telos="тест блокировки")
    report = await coordinator.run("Задача с небезопасным вариантом")

    assert report.blocked is True
    assert report.security_status == "RED"
    assert report.gifts[-1].freedom == Freedom.DECLINED
    assert report.human_decision_required is True
