"""scout.py — Разведчик кодовой базы.

Принцип: «Прежде чем трогать — понять.»

Роль Scout получает задачу, изучает кодовую базу проекта
и составляет карту для Архитектора:
  - файлы которые будут затронуты
  - существующий паттерн
  - риски и зависимости
  - что уже есть по теме

Scout никогда не предлагает решений — только карту.
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Разведчик (Scout) команды AI-агентов AgentForge.

Твоё призвание: понять что уже есть в проекте, прежде чем кто-то начнёт что-то менять.
Принцип: «Прежде чем трогать — понять.»

Ты НИКОГДА не пишешь код и не предлагаешь решений. Только читаешь, ищешь, анализируешь.
Твоя работа — дать Архитектору полную картину.

Формат ответа (строго JSON):
{
  "files_affected": ["путь/к/файлу — почему затронут"],
  "existing_pattern": "как похожее уже сделано в проекте",
  "risks": ["риск 1", "риск 2"],
  "already_done": "что уже реализовано по этой теме",
  "tests_found": ["tests/test_X.py — что покрывает"],
  "fragile_zones": ["файл — почему хрупкий"],
  "ready_for_architect": true
}

Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class ScoutPlugin(LLMRolePlugin):
    """Scout — разведчик кодовой базы."""

    role_name = "scout"
    depends_on = []
    weight = 0.9

    async def setup(self, container: Container) -> None:
        await super().setup(container)
        # Контекст проекта для Scout — структура кода
        self._project_structure = container.get("project_structure") or ""

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("Scout: начинаю разведку для задачи: %s", task[:80])

        user_msg = f"""Задача: {task}

Структура проекта:
{self._project_structure}

Составь карту задачи для Архитектора."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=3000)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("Scout: ошибка LLM вызова: %s", e)
            content = {
                "files_affected": [],
                "existing_pattern": f"Ошибка разведки: {e}",
                "risks": [str(e)],
                "already_done": "",
                "tests_found": [],
                "fragile_zones": [],
                "ready_for_architect": False,
            }

        logger.info("Scout: карта составлена, %d файлов", len(content.get("files_affected", [])))

        return Gift(
            giver="scout",
            receiver="architect",
            content=content,
            telos=task,
            anamnesis=["scout:code_map"],
        )


def _parse_json(text: str) -> dict:
    """Парсить JSON из ответа LLM (устойчиво к markdown-обёрткам)."""
    import json
    import re

    # Убрать ```json ... ``` если есть
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(cleaned)
