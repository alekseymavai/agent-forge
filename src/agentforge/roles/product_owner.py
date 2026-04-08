"""product_owner.py — Голос пользователя в команде AgentForge.

Принцип: «А кому это нужно — и нужно ли прямо сейчас?»

ProductOwner стоит первым в пайплайне. Он проверяет:
  - реальную ценность задачи для пользователя
  - приоритет относительно других задач
  - ясность телоса

Если задача не несёт ценности для пользователя — DEFERRED с предложением альтернативы.
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Product Owner команды AI-агентов AgentForge.

Твоё призвание: защищать пользователя от бесполезной работы команды.
Принцип: «А кому это нужно — и нужно ли прямо сейчас?»

Ты задаёшь неудобные вопросы, но не блокируешь без веской причины.
Оцени задачу с точки зрения ценности для конечного пользователя.

Формат ответа (строго JSON):
{
  "user_value": "что получит пользователь после выполнения этой задачи",
  "urgency": "HIGH|MEDIUM|LOW — почему сейчас, а не позже",
  "telos_clear": true,
  "proceed": true,
  "concerns": ["беспокойство 1 если есть"],
  "alternative_task": "предложение альтернативы если proceed=false, иначе пустая строка",
  "refined_telos": "уточнённый телос задачи с фокусом на пользователя"
}

Правило: proceed=false только если задача явно не несёт пользы пользователю
или противоречит телосу проекта. В сомнении — proceed=true с concerns.
Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class ProductOwnerPlugin(LLMRolePlugin):
    """ProductOwner — голос пользователя, первая роль в пайплайне."""

    role_name = "product_owner"
    depends_on: list[str] = []
    weight = 1.0

    async def setup(self, container: Container) -> None:
        await super().setup(container)
        self._project_telos = container.get("project_telos") or ""

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("ProductOwner: оцениваю ценность задачи: %s", task[:80])

        user_msg = f"""Задача: {task}

Телос проекта: {self._project_telos or "(не задан)"}

Оцени ценность для пользователя."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=1000)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("ProductOwner: ошибка LLM вызова: %s", e)
            content = {
                "user_value": f"Ошибка оценки: {e}",
                "urgency": "MEDIUM",
                "telos_clear": True,
                "proceed": True,
                "concerns": [str(e)],
                "alternative_task": "",
                "refined_telos": task,
            }

        result_gift = Gift(
            giver="product_owner",
            receiver="scout",
            content=content,
            telos=content.get("refined_telos") or task,
            anamnesis=["product_owner:value_assessed"],
        )

        if not content.get("proceed", True):
            alternative = content.get("alternative_task", "")
            result_gift.defer(f"Задача отложена PO. Альтернатива: {alternative}")
            logger.info("ProductOwner: DEFERRED — %s", alternative)
        else:
            logger.info(
                "ProductOwner: PROCEED, ценность=%s, срочность=%s",
                content.get("user_value", "?")[:60],
                content.get("urgency"),
            )

        return result_gift


def _parse_json(text: str) -> dict:
    import json
    import re
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(cleaned)
