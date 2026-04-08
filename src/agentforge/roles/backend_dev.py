"""backend_dev.py — Python-разработчик команды AgentForge.

Принцип: «Минимальный код, который проходит тест.»

BackendDev получает план Архитектора и реализует его строго по плану:
  - Read → Edit (никогда Edit без Read)
  - Test-first: сначала тест, потом реализация
  - Не расширяет scope
  - Не исправляет "заодно" чужой код
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Backend Developer команды AI-агентов AgentForge.

Принцип: «Минимальный код, который проходит тест.»

Ты реализуешь задачу строго по плану Архитектора.
Ты НЕ придумываешь новые фичи. Не расширяешь scope.
Не исправляешь "заодно" чужой код. Делаешь ровно то что написано в плане.

Паттерн работы: Read → Edit. Никогда Edit без чтения файла.
Test-first: сначала тест (красный), потом реализация (зелёный).

Формат ответа (строго JSON):
{
  "files_created": ["путь — что содержит"],
  "files_modified": ["путь — что изменено"],
  "tests_written": ["tests/test_X.py — что покрывает"],
  "implementation_notes": "ключевые решения при реализации",
  "deviations_from_plan": "отклонения от плана Архитектора если есть, иначе пустая строка",
  "ready_for_qa": true
}

Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class BackendDevPlugin(LLMRolePlugin):
    """BackendDev — Python-разработчик, реализует план Архитектора."""

    role_name = "backend_dev"
    depends_on: list[str] = ["security"]
    weight = 1.0

    async def setup(self, container: Container) -> None:
        await super().setup(container)

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("BackendDev: реализую задачу: %s", task[:80])

        architect_plan = ""
        if gift:
            architect_plan = _format_gift_content(gift.content)

        user_msg = f"""Задача: {task}

План (от Архитектора через Security):
{architect_plan or "(план недоступен)"}

Опиши что ты реализовал (без написания кода — только план действий)."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=1500)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("BackendDev: ошибка LLM вызова: %s", e)
            content = {
                "files_created": [],
                "files_modified": [],
                "tests_written": [],
                "implementation_notes": f"Ошибка: {e}",
                "deviations_from_plan": "",
                "ready_for_qa": False,
            }

        anamnesis = ["backend_dev:implementation_complete"]
        if gift:
            anamnesis.extend(gift.anamnesis)

        logger.info(
            "BackendDev: реализовано, файлов=%d, тестов=%d",
            len(content.get("files_modified", [])) + len(content.get("files_created", [])),
            len(content.get("tests_written", [])),
        )

        return Gift(
            giver="backend_dev",
            receiver="qa",
            content=content,
            telos=task,
            anamnesis=anamnesis,
        )


def _format_gift_content(content: object) -> str:
    if isinstance(content, dict):
        import json
        return json.dumps(content, ensure_ascii=False, indent=2)[:2000]
    return str(content)[:2000]


def _parse_json(text: str) -> dict:
    import json
    import re
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(cleaned)
