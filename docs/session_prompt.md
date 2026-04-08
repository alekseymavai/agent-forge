# AgentForge — Промт для новой сессии

> Скопируй этот промт целиком в начало новой сессии Claude Code

---

## Контекст

Разрабатываем **BEECRM** — CRM-систему для пчеловода Александра Дмитрова («Усадьба Дмитровых»).
Проект создан командой AgentForge (Scout → Architect → Security, 08.04.2026).

**Репозиторий:** `alekseymavai/beecrm` (приватный)
**Локально:** `/home/hive/BEECRM/`
**Сервер:** `ssh ai-agent@178.253.39.215`

---

## Что прочитать перед началом

1. `/home/hive/BEECRM/docs/architecture.md` — полная согласованная архитектура
2. `/home/hive/BEECRM/context.yaml` — телос проекта

---

## Что уже сделано (08.04.2026)

### AgentForge (фреймворк)
- Фазы 1–5 завершены, 44 теста зелёных
- Пакет `agentforge` установлен в `.venv`
- CLI: `agentforge init / run / status`
- 9 ролей: Scout, Architect, Security, ProductOwner, BackendDev, FrontendDev, QA, DevOps, TechWriter

### BEECRM (продукт)
- Первый живой прогон AgentForge: Scout → Architect → Security ✅
- Security YELLOW ACCEPTED (второй прогон)
- ADR-001 принят: FastAPI + SQLAlchemy 2.x + PostgreSQL + Alembic
- Архитектура сохранена в `docs/architecture.md`
- Репозиторий создан: `alekseymavai/beecrm`

### Сервер 178.253.39.215 (vm4115781.firstbyte.club)
- Ubuntu 22.04, 77GB диск
- Уже работает: nginx, MariaDB, Neo4j, Redis, Integram → `https://ai2o.online`
- Пользователь `ai-agent` создан, SSH по ключу работает
- Папки: `/home/ai-agent/BEECRM/`, `/home/ai-agent/logs/`
- sudoers: `systemctl beecrm` + docker мониторинг

### TeamMemory (devteam, https://ai2o.online)
- ADR-001 id=147: стек и Security Baseline
- LESSON id=155: настройка ai-agent на firstbyte.club
- TASK id=169: реализация ядра (Scout/Architect/Security ACCEPTED)

---

## Первый шаг в новой сессии

Реализовать базовый скелет BEECRM:

```
settings.py           ← os.environ[KEY], startup_check(), MAX_PAYLOAD_BYTES=65536
db.py                 ← SQLAlchemy engine + SessionLocal
models/client.py      ← Client: id, phone, email, name; UNIQUE(phone, email)
models/order.py       ← Order: id, client_id, source, status, payload JSONB
models/order_event.py ← OrderEvent append-only
migrations/0001_initial.py ← таблицы + CHECK octet_length(payload::text) <= 65536
```

---

## Ключевые решения (ADR-001)

1. Секреты — только `os.environ[KEY]`, никаких `.get(KEY, default)`
2. `startup_check()` вызывается в `lifespan` hook `main.py`
3. `MAX_PAYLOAD_BYTES = 65536` — единственный источник, импортируется в Pydantic и миграцию
4. `OrderEvent` — append-only на уровне сервиса
5. `BaseAdapter.normalize()` — template method, валидация физически встроена

---

## Открытые MEDIUM от Security (учесть при реализации)

1. Интеграционный тест CHECK constraint — на реальном PostgreSQL (testcontainers)
2. `json.dumps(payload, separators=(',',':'), ensure_ascii=False)` — зафиксировать явно
3. `openpyxl` открывать с `read_only=True, data_only=True`
4. `detect-secrets` pre-commit hook добавить в setup

---

## Польза.AI (LLM для ролей AgentForge)

```bash
export ANTHROPIC_API_KEY=pza_vcFPrgkRJRN88ztNWzsUH2bZOszEQQR_
export ANTHROPIC_BASE_URL=https://api.polza.ai
```

---

*Обновлён: 08.04.2026 — BEECRM инициализирован, сервер настроен, TeamMemory заполнена*
