"""tests/test_cli.py — тесты CLI AgentForge.

Покрывают:
  - init: создаёт папку, context.yaml с именем проекта, .gitignore с .agent_bus/
  - run: ошибка если нет API-ключа; запуск с моком Coordinator
  - status: вывод задач через мок TeamMemory
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── init ──────────────────────────────────────────────────────────────────────


def test_init_creates_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from agentforge.cli import _init

    _init("TestProj")

    project = tmp_path / "TestProj"
    assert project.is_dir()

    ctx = (project / "context.yaml").read_text()
    assert "TestProj" in ctx
    assert "MyProject" not in ctx

    gitignore = (project / ".gitignore").read_text()
    assert ".agent_bus/" in gitignore


def test_init_fails_if_dir_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Existing").mkdir()

    from agentforge.cli import _init

    with pytest.raises(SystemExit):
        _init("Existing")


# ── run ───────────────────────────────────────────────────────────────────────


def test_run_exits_without_api_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    monkeypatch.delenv("POLZA_API_KEY", raising=False)

    from agentforge.cli import _run

    with pytest.raises(SystemExit):
        _run("задача X", "context.yaml")


def test_run_with_mock_coordinator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake")

    mock_report = MagicMock()
    mock_report.summary.return_value = "ConsensusReport [test] — OK"

    mock_coordinator = MagicMock()
    mock_coordinator.run = AsyncMock(return_value=mock_report)

    with patch("agentforge.kernel.app.AgentForgeApp"), \
         patch("agentforge.roles.scout.ScoutPlugin"), \
         patch("agentforge.roles.architect.ArchitectPlugin"), \
         patch("agentforge.roles.security.SecurityPlugin"), \
         patch("agentforge.coordinator.Coordinator", return_value=mock_coordinator):
        from agentforge.cli import _run
        _run("задача X", "context.yaml")

    mock_coordinator.run.assert_called_once_with("задача X")


# ── status ────────────────────────────────────────────────────────────────────


def test_status_prints_tasks(monkeypatch, capsys):
    fake_tasks = [
        {"task_id": "abc-001", "project": "AgentForge", "status": "in_progress", "title": "Фаза 4 CLI"},
        {"task_id": "abc-002", "project": "BEECRM", "status": "done", "title": "Спроектируй модель данных"},
    ]

    mock_mem = AsyncMock()
    mock_mem.__aenter__ = AsyncMock(return_value=mock_mem)
    mock_mem.__aexit__ = AsyncMock(return_value=False)
    mock_mem.list_tasks = AsyncMock(return_value=fake_tasks)

    with patch("agentforge.memory.team_memory.TeamMemory", return_value=mock_mem):
        from agentforge.cli import _status
        _status()

    out = capsys.readouterr().out
    assert "abc-001" in out
    assert "AgentForge" in out
    assert "Фаза 4 CLI" in out


def test_status_empty(monkeypatch, capsys):
    mock_mem = AsyncMock()
    mock_mem.__aenter__ = AsyncMock(return_value=mock_mem)
    mock_mem.__aexit__ = AsyncMock(return_value=False)
    mock_mem.list_tasks = AsyncMock(return_value=[])

    with patch("agentforge.memory.team_memory.TeamMemory", return_value=mock_mem):
        from agentforge.cli import _status
        _status()

    out = capsys.readouterr().out
    assert "Нет задач" in out
