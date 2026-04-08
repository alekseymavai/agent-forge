"""Тесты Gift Protocol."""

import pytest
from agentforge.gift import Gift, Freedom


def test_gift_created():
    g = Gift(
        giver="scout",
        receiver="architect",
        content={"files": ["src/bot.py"]},
        telos="спроектировать MemoryService",
        anamnesis=["task:M4"],
    )
    assert g.giver == "scout"
    assert g.freedom == Freedom.ACCEPTED


def test_gift_defer():
    g = Gift(giver="qa", receiver="devops", content="report", telos="деплой")
    g.defer("тесты не зелёные")
    assert g.freedom == Freedom.DEFERRED
    assert any("deferred_reason" in a for a in g.anamnesis)


def test_gift_to_dict():
    g = Gift(giver="architect", receiver="backend_dev", content="plan", telos="M.6")
    d = g.to_dict()
    assert d["giver"] == "architect"
    assert d["freedom"] == "ACCEPTED"
    assert "timestamp" in d
