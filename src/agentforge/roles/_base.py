"""_base.py — базовый класс для LLM-ролей AgentForge.

LLMRolePlugin:
  - получает LLM-клиент из DI-контейнера (или создаёт Anthropic по умолчанию)
  - предоставляет _call_llm() для подклассов
  - клиент инъектируется в тестах → роли тестируемы без реального API
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any

from agentforge.gift import Gift
from agentforge.kernel.container import Container
from agentforge.kernel.plugin import RolePlugin

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"


class LLMRolePlugin(RolePlugin):
    """Базовый класс для ролей, которые вызывают LLM.

    Lifecycle:
      setup(container) — получить/создать LLM-клиент
      run(task, gift)  — реализовать призвание роли

    DI-контейнер:
      container.get("llm_client")  — если None, создаёт AsyncAnthropic()
      container.set("llm_client", mock_client)  — для тестов
    """

    _client: Any = None

    async def setup(self, container: Container) -> None:
        client = container.get("llm_client")
        if client is None:
            try:
                import anthropic

                client = anthropic.AsyncAnthropic()
                logger.info("LLMRolePlugin: создан AsyncAnthropic клиент")
            except ImportError:
                raise RuntimeError(
                    "Для работы LLM-ролей нужна зависимость 'anthropic'. "
                    "Установите: pip install anthropic"
                )
            container.set("llm_client", client)
        self._client = client

    async def _call_llm(
        self,
        system: str,
        user: str,
        max_tokens: int = 2000,
        model: str = DEFAULT_MODEL,
    ) -> str:
        """Вызвать LLM с системным промтом и пользовательским сообщением."""
        response = await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    @abstractmethod
    async def run(self, task: str, gift: Gift | None) -> Gift:
        ...
