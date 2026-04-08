"""Тесты AgentBus."""

import json
import tempfile
from pathlib import Path

import pytest
from agentforge.agent_bus import AgentBus
from agentforge.gift import Gift


def test_send_and_receive():
    with tempfile.TemporaryDirectory() as tmp:
        bus = AgentBus(task_id="test-001", base_dir=tmp)
        gift = Gift(
            giver="scout",
            receiver="architect",
            content={"files": ["src/bot.py"], "risks": ["монолит"]},
            telos="спроектировать ServiceLayer",
        )
        sent = bus.send(gift)
        assert sent.gift_id != ""

        received = bus.receive("architect", "test-001")
        assert received is not None
        assert received["giver"] == "scout"
        assert received["telos"] == "спроектировать ServiceLayer"


def test_log_written():
    with tempfile.TemporaryDirectory() as tmp:
        bus = AgentBus(task_id="test-002", base_dir=tmp)
        gift = Gift(giver="qa", receiver="devops", content="ok", telos="деплой")
        bus.send(gift)

        log = Path(tmp) / "log" / "test-002.jsonl"
        assert log.exists()
        lines = log.read_text().strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0])["giver"] == "qa"
