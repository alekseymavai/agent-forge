# AgentForge — План реализации

> **Дата:** 7 апреля 2026 (обновлено 21.04.2026)
> **Статус:** Фазы 1–6 завершены. Следующая: Фаза 7.
> **Утверждает:** Алексей Мавай (`human_decision_required: True`)

---

## Телос

> «Когда Андрей говорит "создаём новый проект" —
> команда с памятью уже работает.
> Не один Claude меняет шляпы, а каждая роль знает своё место и помнит предыдущий проект.»

**Критерий готовности завода:**
`agentforge init ProjectX` + описание телоса → команда работает за 15 минут.

---

## ADR-001 — Ключевое архитектурное решение

**Решение:** Role = RolePlugin (микроядро), не AgentBase напрямую.

**Контекст:** В коде есть два паттерна — `AgentBase` (ABC с методом `run()`) и `Plugin`
из BEEBOT kernel (lifecycle: setup/teardown + DI-контейнер). Нужно выбрать один.

**Причина:** AgentForge должен позволять подменять роли под конкретный проект.
Plugin даёт заменяемость, топосортировку зависимостей и lifecycle из коробки.

**Последствия:** AgentBase остаётся как базовая логика внутри плагина.
Ядро (kernel/) не знает о конкретных ролях — только об интерфейсе RolePlugin.

---

## ADR-002 — Имя пакета

**Решение:** переименовать `team-infra` / `team_infra` → `agentforge`.

**Причина:** Пользователь видит `pip install agentforge` и `from agentforge import ...`.
Имя должно совпадать с именем продукта.

---

## Что уже реализовано (анамнезис)

```
src/agentforge/
├── gift.py            ✅  Gift dataclass, Freedom enum
├── agent_bus.py       ✅  файловая шина inbox/outbox/consensus/log
├── agent_core.py      ✅  AgentBase ABC, RoleManifest
├── project_context.py ✅  ProjectContext.load(), FragileZone, Decision
├── coordinator.py     ✅  запуск пайплайна → ConsensusReport
├── cli.py             ✅  agentforge init / run / status
├── kernel/            ✅  Plugin + Container + App (из BEEBOT)
├── memory/            ✅  schema.py + team_memory.py → agentforgememory
└── roles/             ✅  10 ролей (LLMRolePlugin)

docs/
├── agents/            ✅  10 контрактов ролей
├── team-protocol.md   ✅  протокол команды
└── architecture.md    ✅  v2.0

tests/                 ✅  44 теста зелёных
```

---

## Фазы реализации

### Фаза 1 — Ядро (2 дня)

Цель: AgentForge запускается, принимает задачу, возвращает ConsensusReport.

- [x] Переименовать `src/team_infra/` → `src/agentforge/` + обновить `pyproject.toml`
- [x] `src/agentforge/kernel/plugin.py` — abstract RolePlugin (адаптировать из BEEBOT kernel)
- [x] `src/agentforge/kernel/container.py` — DI-контейнер (перенести из BEEBOT)
- [x] `src/agentforge/kernel/app.py` — AgentForgeApp: register() + топосортировка + run()
- [x] `src/agentforge/coordinator.py` — запуск пайплайна ролей → ConsensusReport
- [x] `src/agentforge/__init__.py` — экспорт: AgentForge, Gift, AgentBus, ProjectContext
- [x] `tests/test_coordinator.py` — coordinator принимает task → ConsensusReport, human_decision_required=True

**✅ ЗАВЕРШЕНА 07.04.2026 — 9/9 тестов зелёных**

**Выход фазы:** `AgentForge.run(task, context)` → ConsensusReport (без реальных ролей, mock)

---

### Фаза 2 — Три роли-минимум (3 дня)

Цель: первый реальный прогон Scout → Architect → Security.

- [x] `src/agentforge/roles/scout.py` — договор из `BEEBOT/docs/agents/scout.md`
- [x] `src/agentforge/roles/architect.py` — договор из `BEEBOT/docs/agents/architect.md`
- [x] `src/agentforge/roles/security.py` — договор из `BEEBOT/docs/agents/security.md`, вес 1.3
- [x] `tests/test_roles.py` — Scout.run() → Gift с content; Security DECLINED → pipeline стоп
- [ ] Первый живой прогон на реальной задаче из AgentForge

**✅ ЗАВЕРШЕНА (кроме живого прогона) 07.04.2026 — 15/15 тестов зелёных**

**Выход фазы:** задача проходит через Scout → Architect → Security → ConsensusReport

---

### Фаза 3 — Team Memory (2 дня)

Цель: опыт сохраняется между сессиями и проектами.

- [x] Создать воркспейс `agentforgememory` в Integram (мигрировано из devteam 21.04.2026)
- [ ] `INTEGRAM_DEVTEAM_TOKEN` — отдельная env переменная (требование Security)
- [x] Таблицы: PATTERNS(240), ANTIPATTERNS(414), DECISIONS(132), LESSONS(241), AGENTS(128), TASKS(125), TASK_LIFECYCLE(420)
- [x] `src/agentforge/memory/team_memory.py` — Integram agentforgememory клиент
- [x] `src/agentforge/memory/schema.py` — схема таблиц agentforgememory
- [x] Заполнить начальные записи: 5 паттернов, 3 ADR, 1 урок
- [x] `create_task()` + `log_task_step(parent_id=...)` в team_memory.py
- [x] `tests/test_team_memory.py` — 28 тестов зелёных (28/28 всего)

**✅ ЗАВЕРШЕНА 07.04.2026 — 28/28 тестов зелёных**

**Выход фазы:** coordinator читает TeamMemory перед запуском ролей, передаёт анамнезис

---

### Фаза 4 — Шаблон + CLI (1 день)

Цель: `agentforge init ProjectX` — и завод готов к работе.

- [x] `templates/context.yaml` — шаблон с плейсхолдерами (без реальных данных)
- [x] `src/agentforge/cli.py` — команды: `init`, `run`, `status`
  - `agentforge init <name>` — создать папку + context.yaml + .gitignore
  - `agentforge run --task "..."` — запустить пайплайн
  - `agentforge status` — текущее состояние задач из TeamMemory
- [x] API_KEY только из `os.environ` — не из аргументов CLI (требование Security)
- [x] `.agent_bus/` в `.gitignore` шаблона
- [x] `tests/test_cli.py` — init создаёт context.yaml; run возвращает ConsensusReport

**✅ ЗАВЕРШЕНА 08.04.2026 — 34/34 тестов зелёных**

**Выход фазы:** завод запускается одной командой

---

### Фаза 5 — Оставшиеся роли (2 дня)

- [x] `src/agentforge/roles/product_owner.py`
- [x] `src/agentforge/roles/backend_dev.py`
- [x] `src/agentforge/roles/frontend_dev.py`
- [x] `src/agentforge/roles/qa.py` — вес 1.2
- [x] `src/agentforge/roles/devops.py`
- [x] `src/agentforge/roles/tech_writer.py`

**✅ ЗАВЕРШЕНА 08.04.2026 — 44/44 тестов зелёных**

**Выход фазы:** полный пайплайн из 10 ролей

---

### Фаза 6 — Команда и документация (1 день)

Цель: 10 ролей зафиксированы в документации, память мигрирована в agentforgememory.

- [x] 10 контрактов ролей в `docs/agents/*.md` (алгоритм, вход/выход, правила)
- [x] `docs/team-protocol.md` — протокол команды (пайплайн, консенсус, онтология дара)
- [x] Миграция workspace: devteam → agentforgememory (ai2o.online)
- [x] Таблицы ANTIPATTERNS(414), TASK_LIFECYCLE(420) — созданы в agentforgememory
- [x] `schema.py` + `team_memory.py` — обновлены под agentforgememory
- [x] Таблица Агенты(128) — 10 ролей с весами и призваниями
- [x] `README.md` — 10 ролей, пайплайн, структура, Team Memory
- [x] `architecture.md` v2.0 — актуальная архитектура

**✅ ЗАВЕРШЕНА 21.04.2026**

**Выход фазы:** полная документация команды, workspace agentforgememory настроен

---

### Фаза 7 — Первый реальный проект (по готовности)

Запустить AgentForge на реальном проекте:
- [ ] `agentforge init <ProjectName>`
- [ ] Описать телос
- [ ] Полный прогон: Наставник → ... → ConsensusReport → решение Алексея
- [ ] Проект подключается к AgentForge через `pip install agentforge`

---

## Требования безопасности (от Security Reviewer)

| Требование | Фаза | Приоритет |
|-----------|------|-----------|
| `INTEGRAM_DEVTEAM_TOKEN` отдельный от `bibot` | 3 | MEDIUM |
| `.agent_bus/` в `.gitignore` | 1 | MEDIUM |
| `context.yaml` — только `${ENV_VAR}`, без секретов | 4 | LOW |
| CLI API_KEY только из `os.environ` | 4 | LOW |

---

## Метрики готовности

| Метрика | Критерий |
|---------|---------|
| Фаза 1 готова | `AgentForge.run(task, context)` → ConsensusReport |
| Фаза 2 готова | Scout → Architect → Security прогон без ошибок |
| Фаза 3 готова | паттерн из задачи A найден при выполнении задачи B |
| Фаза 4 готова | `agentforge init X` → команда работает за 15 минут |
| Завод работает | Security DECLINED → задача не идёт дальше |

---

*Файл: docs/plan.md*
*Согласован: сессия 07.04.2026 — Product Owner, Scout, Architect, Security, QA*
*Обновлён: 21.04.2026 — Фазы 1–6 завершены*
*Следующий шаг: Фаза 7 — первый реальный проект*
