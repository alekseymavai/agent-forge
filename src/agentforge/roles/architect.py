"""architect.py — Архитектор команды AgentForge.

Принцип: «Как это должно быть устроено — и почему именно так.»

Архитектор получает карту от Scout и превращает её в конкретный план:
  - Два варианта решения (A и B) для ConsensusReport
  - Какие файлы создать/изменить
  - Паттерн реализации
  - Критерий завершения для QA

Не пишет production-код, но может написать скелет для иллюстрации.
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Архитектор команды AI-агентов AgentForge.

Твоё призвание: спроектировать решение прежде чем начнётся разработка.
Принцип: «Как это должно быть устроено — и почему именно так.»

Ты получаешь карту от Scout и превращаешь её в план.
ВСЕГДА предлагай ДВА варианта решения (A и B) — разных подхода.
Не нарушай принятые ADR без явного обоснования.
Предпочитай простоту. Не расширяй scope задачи.

Формат ответа (строго JSON):
{
  "variant_a": {
    "name": "название варианта A",
    "approach": "описание подхода",
    "files_to_create": ["путь — что содержит"],
    "files_to_modify": ["путь — что меняем"],
    "pros": ["плюс 1", "плюс 2"],
    "cons": ["минус 1"]
  },
  "variant_b": {
    "name": "название варианта B",
    "approach": "описание подхода",
    "files_to_create": ["путь — что содержит"],
    "files_to_modify": ["путь — что меняем"],
    "pros": ["плюс 1"],
    "cons": ["минус 1", "минус 2"]
  },
  "recommendation": "вариант A / вариант B — краткое обоснование",
  "completion_criteria": "как QA поймёт что задача выполнена",
  "adr_needed": false,
  "adr_text": ""
}

Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class ArchitectPlugin(LLMRolePlugin):
    """Architect — проектировщик решений."""

    role_name = "architect"
    depends_on = ["scout"]
    weight = 1.0

    async def setup(self, container: Container) -> None:
        await super().setup(container)
        self._decisions = container.get("decisions") or ""

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("Architect: проектирую решение для задачи: %s", task[:80])

        scout_map = ""
        if gift and gift.giver == "scout":
            scout_map = _format_scout_map(gift.content)

        user_msg = f"""Задача: {task}

Карта от Scout:
{scout_map or "(карта недоступна — Scout не запускался)"}

Принятые решения (ADR):
{self._decisions or "(нет)"}

Предложи два варианта решения."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=2000)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("Architect: ошибка LLM вызова: %s", e)
            content = {
                "variant_a": {"name": "Ошибка", "approach": str(e), "files_to_create": [], "files_to_modify": [], "pros": [], "cons": []},
                "variant_b": {"name": "Ошибка", "approach": str(e), "files_to_create": [], "files_to_modify": [], "pros": [], "cons": []},
                "recommendation": f"Ошибка архитектора: {e}",
                "completion_criteria": "",
                "adr_needed": False,
                "adr_text": "",
            }

        anamnesis = ["architect:variants_proposed"]
        if gift:
            anamnesis.extend(gift.anamnesis)

        logger.info(
            "Architect: предложены варианты: '%s' и '%s'",
            content.get("variant_a", {}).get("name", "?"),
            content.get("variant_b", {}).get("name", "?"),
        )

        return Gift(
            giver="architect",
            receiver="security",
            content=content,
            telos=task,
            anamnesis=anamnesis,
        )


def _format_scout_map(content: dict) -> str:
    if not isinstance(content, dict):
        return str(content)
    lines = []
    if content.get("files_affected"):
        lines.append("Файлы: " + ", ".join(content["files_affected"]))
    if content.get("existing_pattern"):
        lines.append("Паттерн: " + content["existing_pattern"])
    if content.get("risks"):
        lines.append("Риски: " + "; ".join(content["risks"]))
    if content.get("already_done"):
        lines.append("Уже сделано: " + content["already_done"])
    return "\n".join(lines)


def _parse_json(text: str) -> dict:
    import json
    import re

    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(cleaned)
