"""devops.py — Инженер деплоя AgentForge.

Принцип: «'Работает на моей машине' — не критерий. Работает в проде — критерий.»

DevOps получает зелёный отчёт от QA+Security и выполняет деплой:
  - Готовит PR по чёткому алгоритму
  - Знает особенности инфраструктуры (docker, SSH-туннели)
  - Не импровизирует — строго по алгоритму
  - Всегда готовит план отката
"""

from __future__ import annotations

import logging

from agentforge.gift import Freedom, Gift
from agentforge.kernel.container import Container
from agentforge.roles._base import LLMRolePlugin

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — DevOps Engineer команды AI-агентов AgentForge.

Принцип: «'Работает на моей машине' — не критерий. Работает в проде — критерий.»

Ты доводишь код до production. Строго по алгоритму, без импровизаций.
Ты знаешь инфраструктуру: docker, SSH-туннели, network_mode: host, systemd.
Ты ВСЕГДА готовишь план отката перед деплоем.

Алгоритм деплоя:
1. Проверить что ветка чистая, тесты зелёные (от QA)
2. Подготовить коммит (только нужные файлы, НЕ git add -A)
3. Создать PR
4. После мержа — обновить прод (НЕ git pull если squash-merge, а git reset --hard origin/main)
5. Перезапустить сервисы
6. Проверить что работает

Формат ответа (строго JSON):
{
  "deploy_steps": ["шаг 1", "шаг 2"],
  "files_to_commit": ["файл 1", "файл 2"],
  "services_to_restart": ["сервис 1"],
  "health_check": "команда для проверки работоспособности",
  "rollback_plan": "план отката если что-то пошло не так",
  "deployed": true,
  "deploy_notes": "особенности деплоя"
}

Отвечай ТОЛЬКО JSON, без markdown-блоков.
"""


class DevOpsPlugin(LLMRolePlugin):
    """DevOps — инженер деплоя, последний перед TechWriter."""

    role_name = "devops"
    depends_on: list[str] = ["qa"]
    weight = 1.0

    async def setup(self, container: Container) -> None:
        await super().setup(container)
        self._infra_notes = container.get("infra_notes") or ""

    async def run(self, task: str, gift: Gift | None) -> Gift:
        logger.info("DevOps: готовлю деплой для задачи: %s", task[:80])

        qa_report = ""
        if gift:
            qa_report = _format_gift_content(gift.content)

        user_msg = f"""Задача: {task}

Отчёт QA:
{qa_report or "(нет данных от QA)"}

Инфраструктурные особенности:
{self._infra_notes or "(стандартная инфраструктура)"}

Опиши план деплоя."""

        try:
            raw = await self._call_llm(SYSTEM_PROMPT, user_msg, max_tokens=1500)
            content = _parse_json(raw)
        except Exception as e:
            logger.error("DevOps: ошибка LLM вызова: %s", e)
            content = {
                "deploy_steps": [f"Ошибка: {e}"],
                "files_to_commit": [],
                "services_to_restart": [],
                "health_check": "",
                "rollback_plan": "git reset --hard HEAD~1",
                "deployed": False,
                "deploy_notes": str(e),
            }

        anamnesis = ["devops:deploy_planned"]
        if gift:
            anamnesis.extend(gift.anamnesis)

        logger.info(
            "DevOps: план готов, шагов=%d, deployed=%s",
            len(content.get("deploy_steps", [])),
            content.get("deployed"),
        )

        return Gift(
            giver="devops",
            receiver="tech_writer",
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
