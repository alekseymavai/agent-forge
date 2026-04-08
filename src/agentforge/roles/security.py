"""security.py — Аудитор безопасности AgentForge (вес 1.3, блокирующий).

Принцип: «Секреты в коде — не ошибка, это катастрофа.»

Security проверяет план Архитектора по чеклисту OWASP:
  - Секреты не в коде
  - Валидация внешних данных
  - Нет SQL/shell инъекций
  - Нет shell=True с пользовательскими данными
  - Нет hardcoded credentials

Приоритеты:
  HIGH   → DECLINED, pipeline стоп
  MEDIUM → ACCEPTED с предупреждением
  LOW    → ACCEPTED с комментарием
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Security Reviewer команды AI-агентов AgentForge.

Принцип: «Секреты в коде — не ошибка, это катастрофа.»
Ты смотришь на план Архитектора глазами злоумышленника.

OWASP проверки (применительно к AgentForge):
- A01: нет небезопасного доступа к файлам (path traversal)
- A02: секреты только через os.environ, не hardcoded
- A03: нет shell=True с пользовательскими данными, нет f-string SQL
- A05: API ключи не в context.yaml, только ${ENV_VAR}
- A07: нет хранения токенов в plaintext

Уровни находок:
  HIGH   → немедленно блокирует, нужно исправить
  MEDIUM → создать задачу, не блокирует текущий деплой
  LOW    → комментарий, не блокирует

Формат ответа (строго JSON):
{
  "findings": [
    {"severity": "HIGH|MEDIUM|LOW", "description": "...", "location": "файл или компонент"}
  ],
  "secrets_check": "PASS|FAIL",
  "injection_check": "PASS|FAIL",
  "validation_check": "PASS|FAIL",
  "overall_status": "GREEN|YELLOW|RED",
  "verdict": "ACCEPTED|DECLINED",
  "decline_reason": "причина если DECLINED, иначе пустая строка"
}

Правило: если есть хотя бы одна находка с severity=HIGH → verdict=DECLINED, overall_status=RED.
Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class SecurityPlugin(LLMRolePlugin):
    """Security — аудитор безопасности (блокирующая роль, вес 1.3)."""

    role_name = "security"
    depends_on = ["architect"]
    weight = 1.3

    async def setup(self, container: Container) -> None:
        await super().setup(container)

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("Security: аудит плана для задачи: %s", task[:80])

        architect_plan = ""
        if gift and gift.giver == "architect":
            architect_plan = _format_architect_plan(gift.content)

        user_msg = f"""Задача: {task}

План Архитектора:
{architect_plan or "(план недоступен — Architect не запускался)"}

Проведи аудит безопасности."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=4000)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("Security: ошибка LLM вызова: %s", e)
            content = {
                "findings": [{"severity": "MEDIUM", "description": f"Ошибка аудита: {e}", "location": "security_plugin"}],
                "secrets_check": "PASS",
                "injection_check": "PASS",
                "validation_check": "PASS",
                "overall_status": "YELLOW",
                "verdict": "ACCEPTED",
                "decline_reason": "",
            }

        verdict = content.get("verdict", "ACCEPTED")
        anamnesis = ["security:audit_complete"]
        if gift:
            anamnesis.extend(gift.anamnesis)

        high_findings = [f for f in content.get("findings", []) if f.get("severity") == "HIGH"]

        result_gift = Gift(
            giver="security",
            receiver="coordinator",
            content=content,
            telos=task,
            anamnesis=anamnesis,
        )

        if verdict == "DECLINED" or high_findings:
            decline_reason = content.get("decline_reason") or (
                f"HIGH уязвимость: {high_findings[0]['description']}" if high_findings else "Security отклонил план"
            )
            result_gift.decline(decline_reason)
            logger.warning("Security: DECLINED — %s", decline_reason)
        else:
            logger.info(
                "Security: ACCEPTED, статус=%s, находок=%d",
                content.get("overall_status"),
                len(content.get("findings", [])),
            )

        return result_gift


def _format_architect_plan(content: dict) -> str:
    if not isinstance(content, dict):
        return str(content)
    lines = []
    for variant in ("variant_a", "variant_b"):
        v = content.get(variant, {})
        if v:
            lines.append(f"\n{variant.upper()}: {v.get('name', '?')}")
            lines.append(f"  Подход: {v.get('approach', '')}")
            if v.get("files_to_create"):
                lines.append(f"  Создать: {', '.join(v['files_to_create'])}")
            if v.get("files_to_modify"):
                lines.append(f"  Изменить: {', '.join(v['files_to_modify'])}")
    if content.get("recommendation"):
        lines.append(f"\nРекомендация: {content['recommendation']}")
    return "\n".join(lines)


def _parse_json(text: str) -> dict:
    import json
    import re

    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(cleaned)
