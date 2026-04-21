"""test_roles_phase5.py — тесты Фазы 5.

Тестирует ProductOwner, BackendDev, FrontendDev, QA, DevOps, TechWriter
через mock LLM-клиент. Реальные API вызовы не делаются.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles.backend_dev import BackendDevPlugin
from agentforge.roles.devops import DevOpsPlugin
from agentforge.roles.frontend_dev import FrontendDevPlugin
from agentforge.roles.product_owner import ProductOwnerPlugin
from agentforge.roles.qa import QAPlugin
from agentforge.roles.tech_writer import TechWriterPlugin


# ── helpers ───────────────────────────────────────────────────────────────── #


def _mock_client(*responses: str):
    client = MagicMock()
    call_count = [0]
    mocks = []
    for text in responses:
        m = MagicMock()
        m.content = [MagicMock(text=text)]
        mocks.append(m)

    async def create(**kwargs):
        idx = min(call_count[0], len(mocks) - 1)
        call_count[0] += 1
        return mocks[idx]

    client.messages.create = create
    return client


def _make_gift(giver: str, receiver: str, content: dict) -> Gift:
    return Gift(giver=giver, receiver=receiver, content=content, telos="тест")


# ── LLM responses ─────────────────────────────────────────────────────────── #

PO_PROCEED = json.dumps({
    "user_value": "пользователь получит CLI для запуска команды",
    "urgency": "HIGH",
    "telos_clear": True,
    "proceed": True,
    "concerns": [],
    "alternative_task": "",
    "refined_telos": "agentforge CLI для запуска пайплайна одной командой",
})

PO_DEFERRED = json.dumps({
    "user_value": "техническая задача без прямой пользы",
    "urgency": "LOW",
    "telos_clear": False,
    "proceed": False,
    "concerns": ["задача не несёт ценности для пользователя"],
    "alternative_task": "Реализовать agentforge status вместо рефакторинга",
    "refined_telos": "",
})

BACKEND_RESPONSE = json.dumps({
    "files_created": ["src/agentforge/cli.py"],
    "files_modified": ["pyproject.toml"],
    "tests_written": ["tests/test_cli.py — покрывает init/run/status"],
    "implementation_notes": "использовал argparse, lazy imports для скорости",
    "deviations_from_plan": "",
    "ready_for_qa": True,
})

FRONTEND_RESPONSE = json.dumps({
    "components_created": ["web/src/views/StatusView.vue"],
    "components_modified": ["web/src/App.vue"],
    "ux_decisions": ["простая таблица без пагинации — задач мало"],
    "reused_from": ["TasksView.vue — похожая структура"],
    "mobile_ok": True,
    "implementation_notes": "PrimeVue DataTable",
    "ready_for_qa": True,
})

QA_PASSED = json.dumps({
    "tests_passed": ["test_cli.py::test_init", "test_cli.py::test_run"],
    "tests_failed": [],
    "regression_ok": True,
    "criteria_met": True,
    "issues_found": [],
    "verdict": "ACCEPTED",
    "deferred_reason": "",
    "qa_notes": "34/34 зелёных",
})

QA_FAILED = json.dumps({
    "tests_passed": ["test_cli.py::test_init"],
    "tests_failed": ["test_cli.py::test_run — AssertionError"],
    "regression_ok": True,
    "criteria_met": False,
    "issues_found": ["test_run падает без API ключа"],
    "verdict": "DEFERRED",
    "deferred_reason": "test_cli.py::test_run красный",
    "qa_notes": "нужно замокать API ключ в тесте",
})

DEVOPS_RESPONSE = json.dumps({
    "deploy_steps": [
        "git add src/agentforge/cli.py tests/test_cli.py",
        "git commit -m 'feat: CLI'",
        "git push",
        "pip install -e . на VPS",
    ],
    "files_to_commit": ["src/agentforge/cli.py", "tests/test_cli.py"],
    "services_to_restart": [],
    "health_check": "agentforge --help",
    "rollback_plan": "git reset --hard HEAD~1 && pip install -e .",
    "deployed": True,
    "deploy_notes": "обычная установка пакета, без перезапуска сервисов",
})

TECHWRITER_RESPONSE = json.dumps({
    "docs_updated": [
        "docs/plan.md — Фаза 4 отмечена ✅",
        "docs/architecture.md — обновлена структура CLI",
    ],
    "plan_tasks_closed": ["Фаза 4 CLI"],
    "architecture_changed": False,
    "memory_updated": True,
    "commit_message": "docs: Фаза 4 завершена — CLI готов",
    "next_task_suggestion": "Фаза 5 — оставшиеся 6 ролей",
    "tech_writer_notes": "CLI работает, следующий шаг — ProductOwner и другие роли",
})


# ── ProductOwner ──────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_product_owner_proceed():
    plugin = ProductOwnerPlugin()
    container = Container()
    container.set("llm_client", _mock_client(PO_PROCEED))
    await plugin.setup(container)

    gift = await plugin.run("Реализовать CLI", None)

    assert gift.giver == "product_owner"
    assert gift.receiver == "scout"
    assert gift.freedom == Freedom.ACCEPTED
    assert gift.content["proceed"] is True
    assert gift.content["urgency"] == "HIGH"


@pytest.mark.asyncio
async def test_product_owner_deferred():
    plugin = ProductOwnerPlugin()
    container = Container()
    container.set("llm_client", _mock_client(PO_DEFERRED))
    await plugin.setup(container)

    gift = await plugin.run("Рефакторинг внутренних утилит", None)

    assert gift.freedom == Freedom.DEFERRED
    assert gift.content["proceed"] is False
    assert gift.content["alternative_task"] != ""


@pytest.mark.asyncio
async def test_product_owner_propagates_no_anamnesis_when_no_gift():
    plugin = ProductOwnerPlugin()
    container = Container()
    container.set("llm_client", _mock_client(PO_PROCEED))
    await plugin.setup(container)

    gift = await plugin.run("задача", None)
    assert "product_owner:value_assessed" in gift.anamnesis


# ── BackendDev ────────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_backend_dev_returns_gift():
    plugin = BackendDevPlugin()
    container = Container()
    container.set("llm_client", _mock_client(BACKEND_RESPONSE))
    await plugin.setup(container)

    prev = _make_gift("security", "backend_dev", {"verdict": "ACCEPTED"})
    gift = await plugin.run("Реализовать CLI", prev)

    assert gift.giver == "backend_dev"
    assert gift.receiver == "qa"
    assert gift.freedom == Freedom.ACCEPTED
    assert "files_created" in gift.content
    assert gift.content["ready_for_qa"] is True


@pytest.mark.asyncio
async def test_backend_dev_propagates_anamnesis():
    plugin = BackendDevPlugin()
    container = Container()
    container.set("llm_client", _mock_client(BACKEND_RESPONSE))
    await plugin.setup(container)

    prev = _make_gift("security", "backend_dev", {})
    prev.anamnesis = ["scout:map", "security:audit"]
    gift = await plugin.run("задача", prev)

    assert "backend_dev:implementation_complete" in gift.anamnesis
    assert "scout:map" in gift.anamnesis
    assert "security:audit" in gift.anamnesis


# ── FrontendDev ───────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_frontend_dev_returns_gift():
    plugin = FrontendDevPlugin()
    container = Container()
    container.set("llm_client", _mock_client(FRONTEND_RESPONSE))
    await plugin.setup(container)

    prev = _make_gift("backend_dev", "frontend_dev", {"files_created": ["src/api.py"]})
    gift = await plugin.run("UI для статуса задач", prev)

    assert gift.giver == "frontend_dev"
    assert gift.receiver == "qa"
    assert gift.freedom == Freedom.ACCEPTED
    assert gift.content["mobile_ok"] is True
    assert "frontend_dev:ui_complete" in gift.anamnesis


# ── QA ────────────────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_qa_accepted_on_green():
    plugin = QAPlugin()
    container = Container()
    container.set("llm_client", _mock_client(QA_PASSED))
    await plugin.setup(container)

    prev = _make_gift("backend_dev", "qa", {"ready_for_qa": True})
    gift = await plugin.run("CLI готов", prev)

    assert gift.giver == "qa"
    assert gift.receiver == "devops"
    assert gift.freedom == Freedom.ACCEPTED
    assert gift.content["verdict"] == "ACCEPTED"
    assert gift.content["tests_failed"] == []


@pytest.mark.asyncio
async def test_qa_deferred_on_red_tests():
    plugin = QAPlugin()
    container = Container()
    container.set("llm_client", _mock_client(QA_FAILED))
    await plugin.setup(container)

    prev = _make_gift("backend_dev", "qa", {"ready_for_qa": True})
    gift = await plugin.run("CLI", prev)

    assert gift.freedom == Freedom.DEFERRED
    assert gift.content["verdict"] == "DEFERRED"
    assert len(gift.content["tests_failed"]) > 0


# ── DevOps ────────────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_devops_returns_gift():
    plugin = DevOpsPlugin()
    container = Container()
    container.set("llm_client", _mock_client(DEVOPS_RESPONSE))
    await plugin.setup(container)

    prev = _make_gift("qa", "devops", {"verdict": "ACCEPTED", "tests_passed": ["test_cli"]})
    gift = await plugin.run("деплой CLI", prev)

    assert gift.giver == "devops"
    assert gift.receiver == "tech_writer"
    assert gift.freedom == Freedom.ACCEPTED
    assert gift.content["deployed"] is True
    assert len(gift.content["deploy_steps"]) > 0
    assert gift.content["rollback_plan"] != ""


# ── TechWriter ────────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_tech_writer_returns_gift():
    plugin = TechWriterPlugin()
    container = Container()
    container.set("llm_client", _mock_client(TECHWRITER_RESPONSE))
    await plugin.setup(container)

    prev = _make_gift("devops", "tech_writer", {"deployed": True})
    gift = await plugin.run("CLI реализован", prev)

    assert gift.giver == "tech_writer"
    assert gift.receiver == "coordinator"
    assert gift.freedom == Freedom.ACCEPTED
    assert len(gift.content["docs_updated"]) > 0
    assert gift.content["next_task_suggestion"] != ""
    assert "tech_writer:docs_updated" in gift.anamnesis
