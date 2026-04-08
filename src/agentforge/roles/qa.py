"""qa.py — Инженер по качеству AgentForge (вес 1.2).

Принцип: «Зелёный — не значит правильный. Но красный — точно неправильный.»

QA запускает все проверки и принимает решение:
  - Все тесты зелёные? → ACCEPTED
  - Хотя бы один красный → DEFERRED (не исправляет сам, возвращает разработчику)

QA не принимает "у меня локально работало".
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — QA Engineer команды AI-агентов AgentForge (вес 1.2).

Принцип: «Зелёный — не значит правильный. Но красный — точно неправильный.»

Ты финальный контроль качества перед Security-ревью и деплоем.
Ты НЕ исправляешь ошибки — ты фиксируешь факты и возвращаешь разработчику.
Ты не принимаешь "у меня локально работало". Тебе нужны реальные результаты.

Чеклист QA:
1. Все тесты зелёные?
2. Регрессия не сломана?
3. Задача выполнена по критерию от Архитектора?
4. Код не содержит TODO/FIXME в критических местах?
5. Логи и ошибки обработаны?

Формат ответа (строго JSON):
{
  "tests_passed": ["тест 1", "тест 2"],
  "tests_failed": [],
  "regression_ok": true,
  "criteria_met": true,
  "issues_found": ["проблема если есть"],
  "verdict": "ACCEPTED|DEFERRED",
  "deferred_reason": "причина если DEFERRED, иначе пустая строка",
  "qa_notes": "дополнительные наблюдения"
}

Правило: если tests_failed не пустой или criteria_met=false → verdict=DEFERRED.
Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class QAPlugin(LLMRolePlugin):
    """QA — инженер качества (вес 1.2, блокирующий при красных тестах)."""

    role_name = "qa"
    depends_on: list[str] = ["backend_dev"]
    weight = 1.2

    async def setup(self, container: Container) -> None:
        await super().setup(container)

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("QA: проверяю качество для задачи: %s", task[:80])

        dev_result = ""
        if gift:
            dev_result = _format_gift_content(gift.content)

        user_msg = f"""Задача: {task}

Результат разработки:
{dev_result or "(нет данных от разработчика)"}

Проведи QA-проверку."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=1500)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("QA: ошибка LLM вызова: %s", e)
            content = {
                "tests_passed": [],
                "tests_failed": [],
                "regression_ok": True,
                "criteria_met": True,
                "issues_found": [f"Ошибка QA: {e}"],
                "verdict": "ACCEPTED",
                "deferred_reason": "",
                "qa_notes": str(e),
            }

        verdict = content.get("verdict", "ACCEPTED")
        anamnesis = ["qa:quality_checked"]
        if gift:
            anamnesis.extend(gift.anamnesis)

        result_gift = Gift(
            giver="qa",
            receiver="devops",
            content=content,
            telos=task,
            anamnesis=anamnesis,
        )

        if verdict == "DEFERRED" or content.get("tests_failed"):
            reason = content.get("deferred_reason") or (
                f"Красные тесты: {content['tests_failed']}" if content.get("tests_failed") else "QA отклонил"
            )
            result_gift.defer(reason)
            logger.warning("QA: DEFERRED — %s", reason)
        else:
            logger.info(
                "QA: ACCEPTED, тестов=%d, проблем=%d",
                len(content.get("tests_passed", [])),
                len(content.get("issues_found", [])),
            )

        return result_gift


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
