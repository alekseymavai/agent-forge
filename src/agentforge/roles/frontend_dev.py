"""frontend_dev.py — Vue/Frontend-разработчик команды AgentForge.

Принцип: «Интерфейс для человека, а не для разработчика.»

FrontendDev получает план и реализует UI-часть:
  - Использует существующие компоненты (не изобретает велосипеды)
  - Фокус на мобильный UX
  - Простота и понятность для пользователя
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Frontend Developer команды AI-агентов AgentForge.

Принцип: «Интерфейс для человека, а не для разработчика.»

Ты строишь UI строго по плану Архитектора. Не изобретаешь велосипеды.
Используешь существующие компоненты проекта. Ориентируешься на мобильный UX.
Пользователь — не программист. Интерфейс должен быть интуитивным.

Паттерн работы: сначала найти похожий компонент, потом адаптировать.

Формат ответа (строго JSON):
{
  "components_created": ["путь — что содержит"],
  "components_modified": ["путь — что изменено"],
  "ux_decisions": ["решение 1 — почему так"],
  "reused_from": ["существующий компонент — что переиспользовали"],
  "mobile_ok": true,
  "implementation_notes": "ключевые решения при реализации",
  "ready_for_qa": true
}

Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class FrontendDevPlugin(LLMRolePlugin):
    """FrontendDev — Vue/frontend-разработчик."""

    role_name = "frontend_dev"
    depends_on: list[str] = ["backend_dev"]
    weight = 1.0

    async def setup(self, container: Container) -> None:
        await super().setup(container)
        self._stack = container.get("frontend_stack") or "Vue 3"

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("FrontendDev: реализую UI для задачи: %s", task[:80])

        backend_result = ""
        if gift:
            backend_result = _format_gift_content(gift.content)

        user_msg = f"""Задача: {task}

Стек: {self._stack}
Результат Backend Dev:
{backend_result or "(нет данных от Backend)"}

Опиши что ты реализовал в UI."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=1500)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("FrontendDev: ошибка LLM вызова: %s", e)
            content = {
                "components_created": [],
                "components_modified": [],
                "ux_decisions": [],
                "reused_from": [],
                "mobile_ok": True,
                "implementation_notes": f"Ошибка: {e}",
                "ready_for_qa": False,
            }

        anamnesis = ["frontend_dev:ui_complete"]
        if gift:
            anamnesis.extend(gift.anamnesis)

        logger.info(
            "FrontendDev: UI готов, компонентов=%d",
            len(content.get("components_created", [])) + len(content.get("components_modified", [])),
        )

        return Gift(
            giver="frontend_dev",
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
