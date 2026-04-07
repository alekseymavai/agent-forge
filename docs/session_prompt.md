# AgentForge — Промт для новой сессии

> Скопируй этот промт целиком в начало новой сессии Claude Code в папке `/home/hive/AgentForge/`

---

## Контекст проекта

Мы разрабатываем **AgentForge** — переиспользуемую инфраструктуру команды AI-агентов-разработчиков на онтологии дара (PLM-GIFT).

**Телос:**
> «Когда Андрей говорит "создаём новый проект" — команда с памятью уже работает.»

**Продукт завода:** программный проект (код + архитектура + тесты), созданный командой ролей по Gift Protocol. Финальное решение — всегда за Андреем (`human_decision_required: True`).

---

## Что было сделано в предыдущей сессии (07.04.2026)

### Решения принятые командой (ConsensusReport):

**ADR-001:** Role = RolePlugin (микроядро), не AgentBase напрямую.
Роли должны быть заменяемы под проект. Plugin даёт lifecycle + DI + топосортировку.

**ADR-002:** Переименовать `team-infra` / `team_infra` → `agentforge`.

### Что уже реализовано:
```
src/team_infra/gift.py            ✅  Gift dataclass, Freedom enum
src/team_infra/agent_bus.py       ✅  файловая шина inbox/outbox/log
src/team_infra/agent_core.py      ✅  AgentBase ABC, ROLE_WEIGHTS
src/team_infra/project_context.py ✅  ProjectContext.load() из context.yaml
tests/test_gift.py                ✅
tests/test_agent_bus.py           ✅
```

### Что нужно сделать (план в `docs/plan.md`):
```
Фаза 1 (2д): kernel/ + coordinator.py  ← СЛЕДУЮЩИЙ ШАГ
Фаза 2 (3д): roles/ — Scout, Architect, Security
Фаза 3 (2д): memory/team_memory.py — Integram devteam
Фаза 4 (1д): templates/context.yaml + cli.py
Фаза 5 (2д): оставшиеся 6 ролей
Фаза 6:      первый реальный проект BEECRM
```

---

## Первые действия в новой сессии

1. Прочитать `docs/plan.md` — план с задачами по фазам
2. Прочитать `docs/architecture.md` — структура пакета и пайплайн
3. Прочитать `src/team_infra/gift.py` и `agent_core.py` — что уже есть
4. Запустить команду Scout: проверить текущее состояние кода

---

## Анамнезис — откуда берём паттерны

**Микроядро (Plugin + Container + App):**
```
/home/hive/BEEBOT/src/kernel/plugin.py
/home/hive/BEEBOT/src/kernel/container.py
/home/hive/BEEBOT/src/kernel/app.py
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
- `.agent_bus/` — в `.gitignore`
- `context.yaml` — только `${ENV_VAR}`, никаких секретов в файле
- CLI: API_KEY только из `os.environ`, не из аргументов командной строки

---

## Как работает команда в этом проекте

Перед каждой нетривиальной задачей — прогон по ролям (имитация или реальные субагенты):

```
Product Owner → Scout → Architect → Security → ConsensusReport → Андрей решает
```

После реализации:
```
QA → Security → DevOps → TechWriter
```

Каждая роль имеет договор в `/home/hive/BEEBOT/docs/agents/<role>.md`.
Используй их как системные промты при смене шляп.

---

## Критерий готовности Фазы 1

```python
from agentforge import AgentForge

forge = AgentForge.load("docs/memory/context.yaml")
report = await forge.run("Спроектируй модуль X")

assert report.human_decision_required == True
assert report.recommendation != ""
```

---

*Файл: docs/session_prompt.md*
*Создан: 07.04.2026*
*Обновлять после каждой значимой сессии*
