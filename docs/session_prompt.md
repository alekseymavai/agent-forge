# AgentForge — Промт для новой сессии

> Скопируй этот промт целиком в начало новой сессии Claude Code в папке `/home/hive/AgentForge/`

---

## Контекст проекта

Мы разрабатываем **AgentForge** — переиспользуемую инфраструктуру команды AI-агентов-разработчиков на онтологии дара (PLM-GIFT).

**Телос:**
> «Когда Алексей говорит "создаём новый проект" — команда с памятью уже работает.»

**Продукт завода:** программный проект (код + архитектура + тесты), созданный командой ролей по Gift Protocol. Финальное решение — всегда за Алексеем (`human_decision_required: True`).

---

## Что было сделано в предыдущей сессии (08.04.2026, финал)

### Фазы 1–3 — ЗАВЕРШЕНЫ ✅

**ADR-001:** Role = RolePlugin (микроядро), не AgentBase напрямую.
**ADR-002:** Переименовано `team_infra` → `agentforge`.

### Что реализовано:
```
src/agentforge/__init__.py              ✅  публичный API
src/agentforge/gift.py                  ✅  Gift dataclass, Freedom enum
src/agentforge/agent_bus.py             ✅  файловая шина inbox/outbox/log
src/agentforge/agent_core.py            ✅  AgentBase ABC, ROLE_WEIGHTS
src/agentforge/project_context.py       ✅  ProjectContext.load() из context.yaml
src/agentforge/kernel/plugin.py         ✅  abstract RolePlugin
src/agentforge/kernel/container.py      ✅  DI-контейнер
src/agentforge/kernel/app.py            ✅  AgentForgeApp: register + toposort + setup/teardown
src/agentforge/coordinator.py           ✅  Coordinator → ConsensusReport
src/agentforge/roles/scout.py           ✅  ScoutPlugin
src/agentforge/roles/architect.py       ✅  ArchitectPlugin
src/agentforge/roles/security.py        ✅  SecurityPlugin (вес 1.3)
src/agentforge/roles/_base.py           ✅  базовый LLM-плагин
src/agentforge/memory/team_memory.py    ✅  Integram devteam клиент
src/agentforge/memory/schema.py         ✅  typeIds: PATTERNS(14), ANTIPATTERNS(15),
                                             DECISIONS(16), LESSONS(17),
                                             TASKS(127), TASK_LIFECYCLE(133)
tests/ (28 тестов, 1 skipped)           ✅  все зелёные
pyproject.toml                          ✅  name=agentforge, установлен в .venv
```

### Сессия 08.04.2026:
- Подтверждён доступ к Integram MCP (devteam воркспейс, 6 таблиц)
- Установлен пакет в `.venv` (`pip install -e .`)
- Удалён мёртвый `src/team_infra/`
- Фаза 4: CLI — `agentforge init / run / status`, 6 тестов ✅
- Фаза 5: 6 ролей — ProductOwner, BackendDev, FrontendDev, QA, DevOps, TechWriter, 10 тестов ✅
- Итого: 44 тестов зелёных ✅

### Что нужно сделать (план в `docs/plan.md`):
```
Фаза 6: первый реальный прогон на BEECRM  ← СЛЕДУЮЩИЙ ШАГ
  - agentforge init BEECRM
  - описать телос
  - полный прогон с реальным LLM
```

---

## Первые действия в новой сессии

1. Прочитать `docs/plan.md` — Фаза 6
2. `agentforge init BEECRM` — создать проект
3. Описать телос в `BEECRM/context.yaml`
4. Запустить полный пайплайн с реальным LLM (нужен `ANTHROPIC_API_KEY`)

---

## Анамнезис — откуда берём паттерны

**Микроядро (Plugin + Container + App):**
```
src/agentforge/kernel/plugin.py     ← уже адаптировано
src/agentforge/kernel/container.py  ← уже адаптировано
src/agentforge/kernel/app.py        ← уже адаптировано
```

**Договоры ролей (9 файлов):**
```
/home/hive/BEEBOT/docs/agents/scout.md
/home/hive/BEEBOT/docs/agents/architect.md
/home/hive/BEEBOT/docs/agents/security.md
/home/hive/BEEBOT/docs/agents/qa.md
/home/hive/BEEBOT/docs/agents/backend_dev.md
/home/hive/BEEBOT/docs/agents/frontend_dev.md
/home/hive/BEEBOT/docs/agents/devops.md
/home/hive/BEEBOT/docs/agents/tech_writer.md
/home/hive/BEEBOT/docs/agents/product_owner.md
```

---

## Требования Security (учесть при реализации)

- `INTEGRAM_DEVTEAM_TOKEN` — отдельная env переменная (не токен bibot)
- `.agent_bus/` — в `.gitignore` ✅
- `context.yaml` — только `${ENV_VAR}`, никаких секретов в файле
- CLI: API_KEY только из `os.environ`, не из аргументов командной строки

---

## Как работает команда в этом проекте

Перед каждой нетривиальной задачей — прогон по ролям (имитация или реальные субагенты):

```
Product Owner → Scout → Architect → Security → ConsensusReport → Алексей решает
```

После реализации:
```
QA → Security → DevOps → TechWriter
```

Каждая роль имеет договор в `/home/hive/BEEBOT/docs/agents/<role>.md`.

---

## Критерий готовности Фазы 2

```python
# Первый живой прогон Scout → Architect → Security
app = AgentForgeApp()
app.register(ScoutPlugin())     # читает код, возвращает карту
app.register(ArchitectPlugin()) # предлагает 2 варианта
app.register(SecurityPlugin())  # атакует варианты

coordinator = Coordinator(app, telos="...")
report = await coordinator.run("Спроектируй модуль X")

assert report.security_status in ("GREEN", "YELLOW", "RED")
assert len(report.gifts) == 3
```

---

*Файл: docs/session_prompt.md*
*Обновлён: 08.04.2026 — Фазы 1–5 завершены, следующий шаг: Фаза 6 (BEECRM)*
