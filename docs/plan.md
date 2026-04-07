# AgentForge — План реализации

> **Дата:** 7 апреля 2026
> **Статус:** Согласован командой (Product Owner · Scout · Architect · Security · QA)
> **Утверждает:** Андрей Гаврилов (`human_decision_required: True`)

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
src/team_infra/
├── gift.py            ✅  Gift dataclass, Freedom enum, accept/defer/decline
├── agent_bus.py       ✅  файловая шина inbox/outbox/consensus/log
├── agent_core.py      ✅  AgentBase ABC, RoleManifest, ROLE_WEIGHTS
└── project_context.py ✅  ProjectContext.load(), FragileZone, Decision

tests/
├── test_gift.py       ✅
└── test_agent_bus.py  ✅

BEEBOT/docs/agents/    ✅  9 договоров ролей — готовы к переносу как промты
BEEBOT/src/kernel/     ✅  Plugin + Container + BeeBotApp — паттерн для адаптации
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

- [x] Создать воркспейс `devteam` в Integram (отдельный от `bibot`) — id:14, slug:devteam
- [ ] `INTEGRAM_DEVTEAM_TOKEN` — отдельная env переменная (требование Security)
- [x] Создать таблицы: `PATTERNS`(14), `ANTIPATTERNS`(15), `DECISIONS`(16), `LESSONS`(17), `TASK_LIFECYCLE`(18)
- [x] `src/agentforge/memory/team_memory.py` — Integram devteam клиент
- [x] `src/agentforge/memory/schema.py` — схема таблиц (typeIds 14–18)
- [x] Заполнить начальные записи из BEEBOT: 5 паттернов, 3 ADR, 2 антипаттерна
- [x] Схема обновлена: `TASKS`(127) + `TASK_LIFECYCLE`(133), `PATTERNS.decision_ref`
- [x] `create_task()` + `log_task_step(parent_id=...)` в team_memory.py
- [x] `tests/test_team_memory.py` — 28 тестов зелёных (28/28 всего)

**✅ ЗАВЕРШЕНА 07.04.2026 — 28/28 тестов зелёных**

**Выход фазы:** coordinator читает TeamMemory перед запуском ролей, передаёт анамнезис

---

### Фаза 4 — Шаблон + CLI (1 день)

Цель: `agentforge init ProjectX` — и завод готов к работе.

- [ ] `templates/context.yaml` — шаблон с плейсхолдерами (без реальных данных)
- [ ] `src/agentforge/cli.py` — команды: `init`, `run`, `status`
  - `agentforge init <name>` — создать папку + context.yaml + .gitignore
  - `agentforge run --task "..."` — запустить пайплайн
  - `agentforge status` — текущее состояние задач из TeamMemory
- [ ] API_KEY только из `os.environ` — не из аргументов CLI (требование Security)
- [ ] `.agent_bus/` в `.gitignore` шаблона
- [ ] `tests/test_cli.py` — init создаёт context.yaml; run возвращает ConsensusReport

**Выход фазы:** завод запускается одной командой

---

### Фаза 5 — Оставшиеся роли (2 дня)

- [ ] `src/agentforge/roles/product_owner.py`
- [ ] `src/agentforge/roles/backend_dev.py`
- [ ] `src/agentforge/roles/frontend_dev.py`
- [ ] `src/agentforge/roles/qa.py` — вес 1.2
- [ ] `src/agentforge/roles/devops.py`
- [ ] `src/agentforge/roles/tech_writer.py`

**Выход фазы:** полный пайплайн из 9 ролей

---

### Фаза 6 — Первый реальный проект (по готовности)

Запустить AgentForge на создании BEECRM:
- [ ] `agentforge init BEECRM`
- [ ] Описать телос: "CRM-система для пчеловода. Backend-центр. BEEBOT — smart frontend."
- [ ] Полный прогон: Scout → Architect → Security → ConsensusReport → решение Андрея
- [ ] BEEBOT подключается к AgentForge через `pip install agentforge`

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
*Следующий шаг: Фаза 1 — переименование пакета + kernel/ + coordinator.py*
