# AgentForge — Промт для новой сессии

> Скопируй этот промт целиком в начало новой сессии Claude Code в папке `/home/hive/AgentForge/`

---

## Контекст проекта

Мы разрабатываем **AgentForge** — переиспользуемую инфраструктуру команды AI-агентов-разработчиков на онтологии дара (PLM-GIFT).

**Телос:**
> «Когда Алексей говорит "создаём новый проект" — команда с памятью уже работает.»

**Продукт завода:** программный проект (код + архитектура + тесты), созданный командой ролей по Gift Protocol. Финальное решение — всегда за Алексеем (`human_decision_required: True`).

---

## Что было сделано в предыдущей сессии (07.04.2026)

### Фаза 1 — ЗАВЕРШЕНА ✅

**ADR-001:** Role = RolePlugin (микроядро), не AgentBase напрямую.
**ADR-002:** Переименовано `team_infra` → `agentforge`.

### Что реализовано:
```
src/agentforge/__init__.py          ✅  публичный API
src/agentforge/gift.py              ✅  Gift dataclass, Freedom enum
src/agentforge/agent_bus.py         ✅  файловая шина inbox/outbox/log
src/agentforge/agent_core.py        ✅  AgentBase ABC, ROLE_WEIGHTS
src/agentforge/project_context.py   ✅  ProjectContext.load() из context.yaml
src/agentforge/kernel/plugin.py     ✅  abstract RolePlugin
src/agentforge/kernel/container.py  ✅  DI-контейнер
src/agentforge/kernel/app.py        ✅  AgentForgeApp: register + тoposort + setup/teardown
src/agentforge/coordinator.py       ✅  Coordinator → ConsensusReport
tests/test_coordinator.py           ✅  4 теста (9 всего)
pyproject.toml                      ✅  name=agentforge, build_meta backend
```

Критерий Фазы 1 выполнен:
- `AgentForge.run(task)` → ConsensusReport, `human_decision_required=True`
- Security DECLINED → `blocked=True`, `security_status=RED`

### Что нужно сделать (план в `docs/plan.md`):
```
Фаза 2 (3д): roles/ — Scout, Architect, Security  ← СЛЕДУЮЩИЙ ШАГ
Фаза 3 (2д): memory/team_memory.py — Integram devteam
Фаза 4 (1д): templates/context.yaml + cli.py
Фаза 5 (2д): оставшиеся 6 ролей
Фаза 6:      первый реальный проект BEECRM
```

---

## Первые действия в новой сессии

1. Прочитать `docs/plan.md` — найти первую незакрытую задачу Фазы 2
2. Прочитать `docs/architecture.md` — структура roles/ и пайплайн
3. Прочитать договоры ролей в `BEEBOT/docs/agents/scout.md`, `architect.md`, `security.md`
4. Реализовать роли по ADR-001 (RolePlugin, не AgentBase)

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
*Обновлён: 07.04.2026 — Фаза 1 завершена*
