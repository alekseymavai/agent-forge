"""tech_writer.py — Технический писатель AgentForge.

Принцип: «Код без документации устаревает в момент написания.»

TechWriter — последняя роль в пайплайне. Синхронизирует документацию
с реальным состоянием кода после каждой выполненной задачи.

Документация обновляется В ТОМ ЖЕ коммите что и код.
Следующая сессия начнётся с верными представлениями об архитектуре.
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Tech Writer команды AI-агентов AgentForge.

Принцип: «Код без документации устаревает в момент написания.»

Ты хранитель документации. Твоя задача — синхронизировать docs с реальным кодом.
Ты последний в пайплайне. Если ты не обновишь документацию, следующая сессия
начнётся с неверных представлений. Это дорого стоит.

Что обновляешь:
- plan.md: отметить задачу как выполненную (✅)
- architecture.md: обновить если изменилась структура
- session_prompt.md: зафиксировать что сделано и что дальше
- CHANGELOG / TROUBLESHOOTING если нужно

Документация = часть кода. Обновляется в том же коммите.

Формат ответа (строго JSON):
{
  "docs_updated": ["docs/plan.md — отмечена задача X", "docs/architecture.md — ..."],
  "plan_tasks_closed": ["задача 1", "задача 2"],
  "architecture_changed": false,
  "session_prompt_updated": true,
  "commit_message": "краткое описание для коммита",
  "next_task_suggestion": "следующая незакрытая задача из плана",
  "tech_writer_notes": "что важно знать следующей сессии"
}

Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class TechWriterPlugin(LLMRolePlugin):
    """TechWriter — последняя роль, обновляет документацию."""

    role_name = "tech_writer"
    depends_on: list[str] = ["devops"]
    weight = 1.0

    async def setup(self, container: Container) -> None:
        await super().setup(container)

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("TechWriter: обновляю документацию для задачи: %s", task[:80])

        devops_report = ""
        if gift:
            devops_report = _format_gift_content(gift.content)

        user_msg = f"""Задача которая была выполнена: {task}

Результат DevOps (деплой):
{devops_report or "(нет данных от DevOps)"}

Опиши какую документацию нужно обновить."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=1500)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("TechWriter: ошибка LLM вызова: %s", e)
            content = {
                "docs_updated": [],
                "plan_tasks_closed": [],
                "architecture_changed": False,
                "session_prompt_updated": False,
                "commit_message": f"docs: обновление документации (ошибка: {e})",
                "next_task_suggestion": "",
                "tech_writer_notes": str(e),
            }

        anamnesis = ["tech_writer:docs_updated"]
        if gift:
            anamnesis.extend(gift.anamnesis)

        logger.info(
            "TechWriter: документация обновлена, файлов=%d",
            len(content.get("docs_updated", [])),
        )

        return Gift(
            giver="tech_writer",
            receiver="coordinator",
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
