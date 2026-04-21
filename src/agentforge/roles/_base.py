"""_base.py — базовый класс для LLM-ролей AgentForge.

LLMRolePlugin:
  - получает LLM-клиент из DI-контейнера (или создаёт Anthropic по умолчанию)
  - предоставляет _call_llm() для подклассов
  - клиент инъектируется в тестах → роли тестируемы без реального API

Два режима работы:
  1. prompt-only (по умолчанию) — роли возвращают структурированный промт,
     обработка через текущую сессию Claude Code
  2. api — роли вызывают внешний LLM (Polza.ai и т.д.),
     включается через container.set("llm_mode", "api") или env AGENTFORGE_LLM_MODE=api
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any

from agentforge.gift import Gift
from agentforge.kernel.container import Container
from agentforge.kernel.plugin import RolePlugin

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"

# Режимы работы LLM
LLM_MODE_PROMPT = "prompt"  # по умолчанию — возвращает промт как текст
LLM_MODE_API = "api"        # вызывает внешний LLM API


class LLMRolePlugin(RolePlugin):
    """Базовый класс для ролей, которые вызывают LLM.

    Lifecycle:
      setup(container) — получить/создать LLM-клиент (или определить prompt-режим)
      run(task, gift)  — реализовать призвание роли

    Режимы:
      prompt (по умолчанию) — _call_llm() возвращает промт для обработки
                              через текущую сессию Claude Code
      api — _call_llm() вызывает внешний LLM (нужен ANTHROPIC_API_KEY)

    DI-контейнер:
      container.get("llm_client")  — если задан, используется напрямую
      container.get("llm_mode")    — "prompt" (default) или "api"
      container.set("llm_client", mock_client)  — для тестов
    """

    _client: Any = None
    _mode: str = LLM_MODE_PROMPT

    async def setup(self, container: Container) -> None:
        import os

        # Определить режим: контейнер → env → default (prompt)
        self._mode = (
            container.get("llm_mode")
            or os.environ.get("AGENTFORGE_LLM_MODE", "")
            or LLM_MODE_PROMPT
        ).lower()

        client = container.get("llm_client")

        if client is not None:
            # Клиент инъектирован (тесты или ручная настройка)
            self._client = client
            return

        if self._mode == LLM_MODE_API:
            # API-режим: создать AsyncAnthropic клиент
            try:
                import anthropic

                api_key = (
                    os.environ.get("ANTHROPIC_API_KEY")
                    or os.environ.get("CLAUDE_API_KEY")
                    or os.environ.get("POLZA_API_KEY")
                )
                base_url = (
                    os.environ.get("ANTHROPIC_BASE_URL")
                    or os.environ.get("CLAUDE_BASE_URL")
                )

                if not api_key:
                    raise RuntimeError(
                        "Режим api требует API-ключ. "
                        "Установите ANTHROPIC_API_KEY или переключитесь "
                        "на режим prompt (по умолчанию)."
                    )

                kwargs: dict = {"api_key": api_key}
                if base_url:
                    kwargs["base_url"] = base_url
                    kwargs["default_headers"] = {"Authorization": f"Bearer {api_key}"}

                client = anthropic.AsyncAnthropic(**kwargs)
                logger.info(
                    "LLMRolePlugin: создан AsyncAnthropic клиент (base_url=%s)",
                    base_url or "default",
                )
            except ImportError:
                raise RuntimeError(
                    "Для режима api нужна зависимость 'anthropic'. "
                    "Установите: pip install anthropic"
                )
            container.set("llm_client", client)
            self._client = client
        else:
            # prompt-режим: клиент не нужен
            logger.info(
                "LLMRolePlugin [%s]: режим prompt — промты для обработки через Claude Code",
                self.role_name,
            )

    async def _call_llm(
        self,
        system: str,
        user: str,
        max_tokens: int = 2000,
        model: str = DEFAULT_MODEL,
    ) -> str:
        """Вызвать LLM или вернуть промт в зависимости от режима.

        prompt-режим: возвращает структурированный промт (system + user)
        api-режим: вызывает внешний LLM и возвращает ответ
        """
        if self._client is not None:
            # Клиент есть (API-режим или инъектирован в тестах) — вызываем
            response = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text

        # prompt-режим (нет клиента): вернуть промт как структурированный текст
        return (
            f"=== ROLE: {self.role_name} ===\n"
            f"=== SYSTEM PROMPT ===\n{system}\n"
            f"=== USER MESSAGE ===\n{user}\n"
            f"=== END ==="
        )

    @abstractmethod
    async def run(self, task: str, gift: Gift | None) -> Gift:
        ...
