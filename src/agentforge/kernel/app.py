"""AgentForgeApp — ядро AgentForge.

Ядро отвечает за:
  1. Регистрацию ролей-плагинов
  2. Топологическую сортировку по зависимостям (Kahn's algorithm)
  3. Последовательную инициализацию (setup)
  4. Запуск пайплайна ролей (run)
  5. Graceful shutdown в обратном порядке (teardown)

Ядро не знает о конкретных ролях — только об интерфейсе RolePlugin.
"""

from __future__ import annotations

import logging

from agentforge.kernel.container import Container
from agentforge.kernel.plugin import RolePlugin

logger = logging.getLogger(__name__)


def _topo_sort(roles: list[RolePlugin]) -> list[RolePlugin]:
    """Топологическая сортировка ролей по зависимостям (Kahn's algorithm).

    Raises:
        ValueError: циклические зависимости или неизвестная зависимость.
    """
    by_name: dict[str, RolePlugin] = {r.role_name: r for r in roles}

    for r in roles:
        for dep in r.depends_on:
            if dep not in by_name:
                raise ValueError(
                    f"Роль '{r.role_name}' зависит от '{dep}', "
                    f"но такая роль не зарегистрирована."
                )

    in_degree: dict[str, int] = {r.role_name: 0 for r in roles}
    dependents: dict[str, list[str]] = {r.role_name: [] for r in roles}

    for r in roles:
        for dep in r.depends_on:
            in_degree[r.role_name] += 1
            dependents[dep].append(r.role_name)

    queue = [name for name, deg in in_degree.items() if deg == 0]
    result: list[RolePlugin] = []

    while queue:
        name = queue.pop(0)
        result.append(by_name[name])
        for dependent in dependents[name]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(result) != len(roles):
        remaining = [name for name, deg in in_degree.items() if deg > 0]
        raise ValueError(f"Циклические зависимости между ролями: {remaining}")

    return result


class AgentForgeApp:
    """Ядро AgentForge — регистрирует роли и управляет их lifecycle."""

    def __init__(self) -> None:
        self.container = Container()
        self._roles: list[RolePlugin] = []
        self._sorted: list[RolePlugin] = []

    def register(self, role: RolePlugin) -> "AgentForgeApp":
        """Зарегистрировать роль. Возвращает self для chaining."""
        if not role.role_name:
            raise ValueError(f"Роль {type(role).__name__} не задала role_name.")
        existing = [r.role_name for r in self._roles]
        if role.role_name in existing:
            raise ValueError(f"Роль '{role.role_name}' уже зарегистрирована.")
        self._roles.append(role)
        logger.debug("Роль зарегистрирована: %s", role.role_name)
        return self

    async def setup(self) -> None:
        """Инициализировать все роли в порядке топосортировки."""
        self._sorted = _topo_sort(self._roles)
        names = [r.role_name for r in self._sorted]
        logger.info("Порядок инициализации ролей: %s", names)
        for role in self._sorted:
            logger.info("  → setup: %s", role.role_name)
            await role.setup(self.container)

    async def teardown(self) -> None:
        """Graceful shutdown — teardown в обратном порядке инициализации."""
        for role in reversed(self._sorted):
            try:
                await role.teardown()
            except Exception as e:
                logger.warning("Ошибка teardown роли '%s': %s", role.role_name, e)

    @property
    def sorted_roles(self) -> list[RolePlugin]:
        """Роли в порядке исполнения (после setup)."""
        return list(self._sorted)
