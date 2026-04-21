"""test_team_memory.py — тесты TeamMemory (Integram agentforgememory).

Два режима:
  1. Мок-режим (default) — httpx.AsyncMock, без реальной сети.
     Проверяет: remember() сохраняет, recall() находит.

  2. Интеграционный режим — запустить с реальными env-переменными:
     INTEGRAM_DEVTEAM_EMAIL + INTEGRAM_DEVTEAM_PASSWORD (или INTEGRAM_DEVTEAM_TOKEN)
     pytest tests/test_team_memory.py -m integration
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentforge.memory.schema import (
    TABLE_ANTIPATTERNS,
    TABLE_DECISIONS,
    TABLE_LESSONS,
    TABLE_PATTERNS,
    TABLE_TASK_LIFECYCLE,
    TABLE_TASKS,
)
from agentforge.memory.team_memory import TeamMemory, TeamMemoryError


# ── Фикстуры ─────────────────────────────────────────────────────────────────


def _ok_response(data: dict) -> MagicMock:
    """Вернуть httpx.Response-мок с ok:true."""
    mock = MagicMock()
    mock.status_code = 200
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {"ok": True, "data": data}
    return mock


def _login_response() -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {"accessToken": "test-jwt-token"}
    return mock


@pytest.fixture
def mem():
    """TeamMemory с pre-set токеном — не нужен реальный логин."""
    m = TeamMemory(token="test-token")
    m._token_exp = 9999999999  # не истекает в тестах
    return m


# ── remember_pattern ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remember_pattern_returns_id(mem):
    with patch.object(mem, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 42}
        obj_id = await mem.remember_pattern(
            name="RolePlugin вместо AgentBase",
            description="Plugin даёт lifecycle и DI из коробки",
            tags="plugin, lifecycle, DI",
        )
    assert obj_id == 42
    mock_call.assert_called_once()
    call_args = mock_call.call_args[0]
    assert call_args[0] == "create_object"
    assert call_args[1]["typeId"] == TABLE_PATTERNS
    assert call_args[1]["fields"]["name"] == "RolePlugin вместо AgentBase"


@pytest.mark.asyncio
async def test_remember_pattern_sends_all_fields(mem):
    with patch.object(mem, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 1}
        await mem.remember_pattern(
            name="Test",
            description="desc",
            context="ctx",
            example="code",
            tags="a, b",
        )
    fields = mock_call.call_args[0][1]["fields"]
    assert fields["context"] == "ctx"
    assert fields["example"] == "code"
    assert fields["tags"] == "a, b"


# ── remember_decision ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remember_decision(mem):
    with patch.object(mem, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 10}
        obj_id = await mem.remember_decision(
            adr_id="ADR-001",
            title="Role = RolePlugin",
            context="Нужна заменяемость ролей",
            decision="Role = RolePlugin из kernel, не AgentBase напрямую",
            consequences="AgentBase остаётся внутри плагина",
            status="accepted",
        )
    assert obj_id == 10
    fields = mock_call.call_args[0][1]["fields"]
    assert fields["adr_id"] == "ADR-001"
    assert fields["Название"] == "Role = RolePlugin"
    assert fields["status"] == "accepted"
    assert mock_call.call_args[0][1]["typeId"] == TABLE_DECISIONS


# ── remember_antipattern ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remember_antipattern(mem):
    with patch.object(mem, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 5}
        obj_id = await mem.remember_antipattern(
            name="Моки вместо реальной БД в тестах",
            description="Тесты проходят, но prod падает",
            consequence="Расхождение мок/реальность маскирует баги",
            remedy="Использовать реальную БД в интеграционных тестах",
            project="BEEBOT",
        )
    assert obj_id == 5
    assert mock_call.call_args[0][1]["typeId"] == TABLE_ANTIPATTERNS


# ── remember_lesson ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remember_lesson(mem):
    with patch.object(mem, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 7}
        obj_id = await mem.remember_lesson(
            title="Session-log в том же коммите что и код",
            what_happened="Код запушен без лога — контекст потерян",
            what_learned="Лог сессии = часть коммита, не опционально",
            how_to_apply="Обновлять docs/session_*.md перед git push",
            severity="medium",
        )
    assert obj_id == 7
    assert mock_call.call_args[0][1]["typeId"] == TABLE_LESSONS


# ── log_task_step ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task(mem):
    with patch.object(mem, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 55}
        obj_id = await mem.create_task(
            task_id="abc123",
            title="Создать MemoryService",
            project="AgentForge",
        )
    assert obj_id == 55
    args = mock_call.call_args[0][1]
    assert args["typeId"] == TABLE_TASKS
    assert "abc123" in args["fields"]["Название"]
    assert "AgentForge" in args["fields"]["Описание"]


@pytest.mark.asyncio
async def test_log_task_step(mem):
    with patch.object(mem, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 99}
        obj_id = await mem.log_task_step(
            role="Security",
            freedom="DECLINED",
            gift_content="Отклонено: нет валидации входных данных",
            parent_id=55,
        )
    assert obj_id == 99
    args = mock_call.call_args[0][1]
    assert args["typeId"] == TABLE_TASK_LIFECYCLE
    assert args["parentId"] == 55
    assert args["fields"]["freedom"] == "DECLINED"
    assert args["fields"]["role"] == "Security"


@pytest.mark.asyncio
async def test_log_task_step_truncates_long_content(mem):
    long_content = "x" * 5000
    with patch.object(mem, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": 1}
        await mem.log_task_step("Scout", "ACCEPTED", long_content, parent_id=1)
    fields = mock_call.call_args[0][1]["fields"]
    assert len(fields["gift_content"]) <= 2000


# ── recall ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_recall_searches_all_tables(mem):
    """recall() делает semantic_search в 4 таблицах (не TASK_LIFECYCLE)."""
    searched_tables = []

    async def fake_call(tool, args):
        if tool == "semantic_search":
            searched_tables.append(args["typeId"])
            return [{"name": "result", "description": "found", "_source": "test"}]
        return {}

    with patch.object(mem, "_call", side_effect=fake_call):
        results = await mem.recall("plugin lifecycle")

    assert TABLE_PATTERNS in searched_tables
    assert TABLE_ANTIPATTERNS in searched_tables
    assert TABLE_DECISIONS in searched_tables
    assert TABLE_LESSONS in searched_tables
    assert TABLE_TASK_LIFECYCLE not in searched_tables  # lifecycle не в recall
    assert len(results) == 4  # по одному из каждой таблицы


@pytest.mark.asyncio
async def test_recall_adds_table_name(mem):
    async def fake_call(tool, args):
        if tool == "semantic_search" and args["typeId"] == TABLE_PATTERNS:
            return [{"name": "RolePlugin", "description": "..."}]
        return []

    with patch.object(mem, "_call", side_effect=fake_call):
        results = await mem.recall("plugin")

    pattern_results = [r for r in results if r.get("_table") == "PATTERNS"]
    assert len(pattern_results) == 1


@pytest.mark.asyncio
async def test_recall_tolerates_table_errors(mem):
    """Ошибка semantic_search + list_objects в одной таблице не ломает recall остальных."""
    async def fake_call(tool, args):
        # PATTERNS: обе стратегии поиска падают
        if args.get("typeId") == TABLE_PATTERNS:
            raise TeamMemoryError("PATTERNS недоступна")
        # Остальные: semantic_search пустой, list_objects с результатом
        if tool == "semantic_search":
            return {"objects": []}
        return [{"name": "ok"}]

    with patch.object(mem, "_call", side_effect=fake_call):
        results = await mem.recall("anything")

    # 3 из 4 таблиц должны вернуть результат (PATTERNS упала полностью)
    assert len(results) == 3


# ── auth ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_credentials_raises():
    mem = TeamMemory()  # без токена и без email/password
    with pytest.raises(TeamMemoryError, match="токен"):
        await mem._ensure_auth()


@pytest.mark.asyncio
async def test_login_with_email_password():
    mem = TeamMemory(email="test@example.com", password="secret")
    with patch.object(mem._http, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _login_response()
        await mem._ensure_auth()
    assert mem._token == "test-jwt-token"
    assert mem._token_exp > 0


# ── интеграционные (пропускаются без env) ─────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_remember_and_recall():
    """Реальный сохранение + поиск. Требует INTEGRAM_DEVTEAM_EMAIL/PASSWORD."""
    import os
    if not os.getenv("INTEGRAM_DEVTEAM_EMAIL"):
        pytest.skip("INTEGRAM_DEVTEAM_EMAIL не задан")

    async with TeamMemory() as mem:
        obj_id = await mem.remember_pattern(
            name="Integration test pattern",
            description="Создан автотестом test_team_memory",
            tags="test, integration",
        )
        assert obj_id > 0

        results = await mem.recall("integration test pattern")
        names = [r.get("name", "") for r in results]
        assert any("Integration test" in n for n in names)
