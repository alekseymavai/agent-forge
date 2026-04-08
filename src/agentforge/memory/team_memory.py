"""team_memory.py — клиент Team Memory для AgentForge.

Хранит и извлекает командный опыт из воркспейса devteam (Integram).

Конфигурация (из env):
  INTEGRAM_URL              — базовый URL (по умолчанию https://ai2o.online)
  INTEGRAM_DEVTEAM_TOKEN    — JWT-токен (если уже получен, пропускает логин)
  INTEGRAM_DEVTEAM_EMAIL    — email для логина (если токен не задан)
  INTEGRAM_DEVTEAM_PASSWORD — пароль для логина

Требование Security: INTEGRAM_DEVTEAM_TOKEN отдельный от bibot-токена.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time as _time
from datetime import datetime, timezone
from typing import Any

import httpx

from agentforge.memory.schema import (
    TABLE_ANTIPATTERNS,
    TABLE_DECISIONS,
    TABLE_LESSONS,
    TABLE_PATTERNS,
    TABLE_TASK_LIFECYCLE,
    TABLE_TASKS,
)

logger = logging.getLogger(__name__)

WORKSPACE = "devteam"
DEFAULT_URL = "https://ai2o.online"


class TeamMemoryError(Exception):
    """Ошибка при работе с Team Memory."""


class TeamMemory:
    """Async-клиент для сохранения и извлечения командного опыта.

    Использование::

        async with TeamMemory() as mem:
            await mem.remember_pattern(
                name="RolePlugin вместо AgentBase",
                description="...",
                project="AgentForge",
            )
            results = await mem.recall("plugin lifecycle")
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ) -> None:
        self._base_url = (base_url or os.getenv("INTEGRAM_URL", DEFAULT_URL)).rstrip("/")
        self._token: str | None = token or os.getenv("INTEGRAM_DEVTEAM_TOKEN")
        self._email = email or os.getenv("INTEGRAM_DEVTEAM_EMAIL", "")
        self._password = password or os.getenv("INTEGRAM_DEVTEAM_PASSWORD", "")
        self._token_exp: float = 0
        self._http = httpx.AsyncClient(timeout=30)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def __aenter__(self) -> "TeamMemory":
        await self._ensure_auth()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._http.aclose()

    async def close(self) -> None:
        await self._http.aclose()

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def _ensure_auth(self) -> None:
        if self._token and _time.time() < self._token_exp:
            return
        if not self._email or not self._password:
            if not self._token:
                raise TeamMemoryError(
                    "Не задан токен или учётные данные. "
                    "Установите INTEGRAM_DEVTEAM_TOKEN или "
                    "INTEGRAM_DEVTEAM_EMAIL + INTEGRAM_DEVTEAM_PASSWORD."
                )
            # токен задан, exp неизвестен — доверяем до ошибки 401
            return
        resp = await self._http.post(
            f"{self._base_url}/api/v2/iam/login",
            json={"email": self._email, "password": self._password},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data.get("accessToken")
        if not self._token:
            raise TeamMemoryError(f"Логин провалился: {data}")
        self._token_exp = _time.time() + 3500
        logger.debug("TeamMemory: авторизован в Integram devteam")

    # ── Low-level ─────────────────────────────────────────────────────────────

    async def _call(self, tool: str, args: dict) -> Any:
        await self._ensure_auth()
        resp = await self._http.post(
            f"{self._base_url}/api/v2/{WORKSPACE}/ai/tool",
            json={"name": tool, "args": args, "skipHitl": True},
            headers={"Authorization": f"Bearer {self._token}"},
        )
        if resp.status_code == 401:
            # токен истёк — переавторизация один раз
            self._token = None
            self._token_exp = 0
            await self._ensure_auth()
            resp = await self._http.post(
                f"{self._base_url}/api/v2/{WORKSPACE}/ai/tool",
                json={"name": tool, "args": args, "skipHitl": True},
                headers={"Authorization": f"Bearer {self._token}"},
            )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise TeamMemoryError(f"Tool '{tool}' error: {data}")
        return data.get("data")

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # ── Remember ──────────────────────────────────────────────────────────────

    async def remember_pattern(
        self,
        name: str,
        description: str,
        context: str = "",
        example: str = "",
        project: str = "",
        tags: str = "",
    ) -> int:
        """Сохранить паттерн. Возвращает ID записи."""
        result = await self._call("create_object", {
            "typeId": TABLE_PATTERNS,
            "fields": {
                "name": name,
                "description": description,
                "context": context,
                "example": example,
                "project": project,
                "tags": tags,
                "created_at": self._now(),
            },
        })
        obj_id = result.get("id") if isinstance(result, dict) else None
        logger.info("TeamMemory: сохранён паттерн '%s' (id=%s)", name, obj_id)
        return obj_id or 0

    async def remember_antipattern(
        self,
        name: str,
        description: str,
        consequence: str = "",
        remedy: str = "",
        project: str = "",
        tags: str = "",
    ) -> int:
        result = await self._call("create_object", {
            "typeId": TABLE_ANTIPATTERNS,
            "fields": {
                "name": name,
                "description": description,
                "consequence": consequence,
                "remedy": remedy,
                "project": project,
                "tags": tags,
                "created_at": self._now(),
            },
        })
        obj_id = result.get("id") if isinstance(result, dict) else None
        logger.info("TeamMemory: сохранён антипаттерн '%s' (id=%s)", name, obj_id)
        return obj_id or 0

    async def remember_decision(
        self,
        adr_id: str,
        title: str,
        context: str,
        decision: str,
        consequences: str = "",
        project: str = "",
        status: str = "accepted",
    ) -> int:
        result = await self._call("create_object", {
            "typeId": TABLE_DECISIONS,
            "fields": {
                "adr_id": adr_id,
                "title": title,
                "context": context,
                "decision": decision,
                "consequences": consequences,
                "project": project,
                "status": status,
            },
        })
        obj_id = result.get("id") if isinstance(result, dict) else None
        logger.info("TeamMemory: сохранено решение %s '%s' (id=%s)", adr_id, title, obj_id)
        return obj_id or 0

    async def remember_lesson(
        self,
        title: str,
        what_happened: str,
        what_learned: str,
        how_to_apply: str = "",
        project: str = "",
        severity: str = "medium",
    ) -> int:
        result = await self._call("create_object", {
            "typeId": TABLE_LESSONS,
            "fields": {
                "title": title,
                "what_happened": what_happened,
                "what_learned": what_learned,
                "how_to_apply": how_to_apply,
                "project": project,
                "severity": severity,
                "created_at": self._now(),
            },
        })
        obj_id = result.get("id") if isinstance(result, dict) else None
        logger.info("TeamMemory: сохранён урок '%s' (id=%s)", title, obj_id)
        return obj_id or 0

    async def create_task(
        self,
        task_id: str,
        title: str,
        project: str = "",
        status: str = "in_progress",
    ) -> int:
        """Создать запись задачи в TASKS. Возвращает ID — нужен для log_task_step."""
        result = await self._call("create_object", {
            "typeId": TABLE_TASKS,
            "fields": {
                "task_id": task_id,
                "title": title,
                "project": project,
                "status": status,
                "created_at": self._now(),
            },
        })
        obj_id = result.get("id") if isinstance(result, dict) else None
        logger.info("TeamMemory: создана задача '%s' (id=%s)", title, obj_id)
        return obj_id or 0

    async def log_task_step(
        self,
        role: str,
        freedom: str,
        gift_content: str,
        parent_id: int,  # ID записи в TASKS (обязателен — child требует parentId)
    ) -> int:
        """Сохранить шаг задачи как child-запись TASKS."""
        result = await self._call("create_object", {
            "typeId": TABLE_TASK_LIFECYCLE,
            "parentId": parent_id,
            "fields": {
                "role": role,
                "freedom": freedom,
                "gift_content": gift_content[:2000],
                "timestamp": self._now(),
            },
        })
        obj_id = result.get("id") if isinstance(result, dict) else None
        return obj_id or 0

    # ── Recall ────────────────────────────────────────────────────────────────

    async def recall(self, question: str, limit: int = 5) -> list[dict]:
        """Поиск по всем таблицам памяти.

        Пробует semantic_search (векторный), при пустом ответе — list_objects с search.
        Возвращает список записей со служебным полем _table.
        """
        results: list[dict] = []

        table_names = {
            TABLE_PATTERNS:      "PATTERNS",
            TABLE_ANTIPATTERNS:  "ANTIPATTERNS",
            TABLE_DECISIONS:     "DECISIONS",
            TABLE_LESSONS:       "LESSONS",
        }

        for type_id, table_name in table_names.items():
            try:
                records = await self._search_table(type_id, question, limit)
                for rec in records:
                    rec["_table"] = table_name
                results.extend(records)
            except TeamMemoryError as e:
                logger.warning("TeamMemory.recall: ошибка поиска в %s: %s", table_name, e)

        return results

    async def _search_table(self, type_id: int, query: str, limit: int) -> list[dict]:
        """Поиск в одной таблице: семантика (5с таймаут) → фолбэк по ключевым словам."""
        # 1. semantic_search (векторный — работает после индексации).
        #    Таймаут 5с: если индексация ещё не готова, не блокируем весь recall.
        try:
            data = await asyncio.wait_for(
                self._call("semantic_search", {"query": query, "typeId": type_id, "limit": limit}),
                timeout=5.0,
            )
            records = self._extract_rows(data)
            if records:
                return records
        except (asyncio.TimeoutError, TeamMemoryError):
            pass

        # 2. Фолбэк: list_objects с поиском по отдельным значимым словам (≥4 символов).
        #    Текстовый поиск Integram работает по одному слову, не по фразе целиком.
        seen_ids: set = set()
        results: list[dict] = []
        for word in query.split():
            if len(word) < 4:
                continue
            data = await self._call("list_objects", {"typeId": type_id, "search": word, "limit": limit})
            for rec in self._extract_rows(data):
                if rec.get("id") not in seen_ids:
                    seen_ids.add(rec.get("id"))
                    results.append(rec)
            if len(results) >= limit:
                break
        return results[:limit]

    async def recall_from(self, table_id: int, question: str, limit: int = 10) -> list[dict]:
        """Поиск в конкретной таблице."""
        data = await self._call("semantic_search", {
            "query": question,
            "typeId": table_id,
            "limit": limit,
        })
        return self._extract_rows(data)

    async def list_patterns(self, limit: int = 50) -> list[dict]:
        data = await self._call("list_objects", {"typeId": TABLE_PATTERNS, "limit": limit})
        return self._extract_rows(data)

    async def list_decisions(self, limit: int = 50) -> list[dict]:
        data = await self._call("list_objects", {"typeId": TABLE_DECISIONS, "limit": limit})
        return self._extract_rows(data)

    async def list_tasks(self, limit: int = 50) -> list[dict]:
        """Список задач из TASKS (для agentforge status)."""
        data = await self._call("list_objects", {"typeId": TABLE_TASKS, "limit": limit})
        return self._extract_rows(data)

    @staticmethod
    def _extract_rows(data: Any) -> list[dict]:
        """Извлечь список записей из ответа Integram (rows или objects)."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("rows") or data.get("objects") or []
        return []
