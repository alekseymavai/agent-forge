"""cli.py — консольный интерфейс AgentForge.

Команды:
  agentforge init <name>       — создать новый проект
  agentforge run --task "..."  — запустить пайплайн (по умолчанию prompt-режим)
  agentforge run --task "..." --api  — запустить через внешний LLM API
  agentforge status            — статус задач из Team Memory

Режимы LLM:
  prompt (по умолчанию) — роли генерируют промты для обработки через Claude Code
  api (--api или AGENTFORGE_LLM_MODE=api) — роли вызывают внешний LLM

Требование Security: API-ключи только из os.environ, не из аргументов CLI.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path


# ── init ──────────────────────────────────────────────────────────────────────


def _init(name: str) -> None:
    project_dir = Path(name)
    if project_dir.exists():
        print(f"Ошибка: папка '{name}' уже существует.", file=sys.stderr)
        sys.exit(1)

    project_dir.mkdir(parents=True)

    # Шаблон из пакета
    template = Path(__file__).parent / "templates" / "context.yaml"
    context_text = template.read_text(encoding="utf-8")
    context_text = context_text.replace("MyProject", name)
    (project_dir / "context.yaml").write_text(context_text, encoding="utf-8")

    # .gitignore — .agent_bus/ не попадает в репо (требование Security)
    gitignore = ".agent_bus/\n__pycache__/\n*.pyc\n.env\n"
    (project_dir / ".gitignore").write_text(gitignore, encoding="utf-8")

    print(f"Проект '{name}' создан:")
    print(f"  {name}/context.yaml  — опиши телос")
    print(f"  {name}/.gitignore    — .agent_bus/ исключён")
    print(f"\nСледующий шаг:")
    print(f"  cd {name}")
    print(f"  agentforge run --task \"Спроектируй модуль X\"")


# ── run ───────────────────────────────────────────────────────────────────────


async def _run_async(task: str, context_path: str, use_api: bool = False) -> None:
    from agentforge.coordinator import Coordinator
    from agentforge.kernel.app import AgentForgeApp
    from agentforge.project_context import ProjectContext
    from agentforge.roles.architect import ArchitectPlugin
    from agentforge.roles.scout import ScoutPlugin
    from agentforge.roles.security import SecurityPlugin

    # Определить режим: --api или env AGENTFORGE_LLM_MODE=api
    llm_mode = "api" if use_api else os.environ.get("AGENTFORGE_LLM_MODE", "prompt")

    if llm_mode == "api":
        # API-ключ только из env (требование Security)
        api_key = (
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("CLAUDE_API_KEY")
            or os.environ.get("POLZA_API_KEY")
        )
        if not api_key:
            print(
                "Ошибка: режим --api требует API-ключ.\n"
                "Установите переменную окружения:\n"
                "  export ANTHROPIC_API_KEY=sk-ant-...\n\n"
                "Или запустите без --api для работы через Claude Code.",
                file=sys.stderr,
            )
            sys.exit(1)
        print("Режим: API (внешний LLM)")
    else:
        print("Режим: prompt (обработка через Claude Code)")

    # Загрузить контекст проекта
    telos = task
    if Path(context_path).exists():
        ctx = ProjectContext.load(context_path)
        telos = ctx.telos or task
    else:
        print(f"Предупреждение: '{context_path}' не найден — используем задачу как телос.")

    # Запустить пайплайн
    app = AgentForgeApp()
    app.container.set("llm_mode", llm_mode)
    app.register(ScoutPlugin())
    app.register(ArchitectPlugin())
    app.register(SecurityPlugin())

    coordinator = Coordinator(app, telos=telos)
    report = await coordinator.run(task)

    print("\n" + "=" * 60)
    print(report.summary())
    print("=" * 60 + "\n")


def _run(task: str, context_path: str, use_api: bool = False) -> None:
    asyncio.run(_run_async(task, context_path, use_api))


# ── status ────────────────────────────────────────────────────────────────────


async def _status_async() -> None:
    from agentforge.memory.team_memory import TeamMemory, TeamMemoryError

    try:
        async with TeamMemory() as mem:
            tasks = await mem.list_tasks()
    except TeamMemoryError as e:
        print(f"Ошибка подключения к Team Memory: {e}", file=sys.stderr)
        sys.exit(1)

    if not tasks:
        print("Нет задач в Team Memory.")
        return

    print(f"\n{'ID задачи':<12} {'Проект':<16} {'Статус':<12} Заголовок")
    print("-" * 72)
    for t in tasks:
        print(
            f"{str(t.get('task_id', '')):<12} "
            f"{str(t.get('project', '')):<16} "
            f"{str(t.get('status', '')):<12} "
            f"{str(t.get('title', ''))[:30]}"
        )
    print()


def _status() -> None:
    asyncio.run(_status_async())


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agentforge",
        description="AgentForge — команда AI-агентов-разработчиков на онтологии дара",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="команда")

    # init
    init_p = subparsers.add_parser("init", help="создать новый проект")
    init_p.add_argument("name", help="имя проекта (создаёт папку)")

    # run
    run_p = subparsers.add_parser("run", help="запустить пайплайн агентов")
    run_p.add_argument("--task", required=True, help="описание задачи")
    run_p.add_argument(
        "--context", default="context.yaml", help="путь к context.yaml (по умолчанию: ./context.yaml)"
    )
    run_p.add_argument(
        "--api", action="store_true",
        help="использовать внешний LLM API (нужен ANTHROPIC_API_KEY)",
    )

    # status
    subparsers.add_parser("status", help="статус задач из Team Memory")

    args = parser.parse_args()

    if args.command == "init":
        _init(args.name)
    elif args.command == "run":
        _run(args.task, args.context, args.api)
    elif args.command == "status":
        _status()
    else:
        parser.print_help()
