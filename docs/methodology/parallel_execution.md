# Multi-worker parallel execution discipline

**Назначение:** правила избежания конфликтов при параллельной работе нескольких AF сессий (модераторов и Worker'ов) над одним проектом.

**Уровень:** методологический (universal). Project-specific instance — в репо проекта.

---

## Когда применяется

Алексей (PO) или другой product owner запускает **N>1 модераторов и/или Worker'ов параллельно** в одной кодовой базе. Без discipline это приводит к:

- merge конфликтам в git
- race condition при push
- противоречивым PO решениям между модераторами
- дубликатам в memory
- production deploy collisions

---

## 7 видов конфликтов

### 1. Git merge конфликты в коде

**Риск:** два Worker'а правят одни файлы — даже на разных ветках merge ломается.
**Avoid:** Worker'ам **РАЗНЫЕ домены** (разные файлы / модули / конфиги). Если оба трогают одну и ту же зону — параллелить НЕЛЬЗЯ.

### 2. Push race на main

**Риск:** оба Worker'а пушат в main одновременно → race condition.
**Avoid:** каждый Worker работает в своей feature branch `worker-<phase>/<sprint>`, модератор сводит в main через PR. Не оба напрямую в main.

### 3. Конфликтующие PO решения от модераторов

**Риск:** модератор A одобрил scope X, модератор B одобрил Y — архитектурно противоречат.
**Avoid:** единый **decision log** (project workspace · DECISIONS таблица) — все модераторы туда пишут. Перед GREEN модератор проверяет свежие decisions на пересечение с активной фазой другого модератора.

### 4. Cross-session context drift

**Риск:** модераторы не видят друг друга → противоречивые constraints для своих Worker'ов.
**Avoid:** **shared kanban файл** `docs/agentforge/active_queue.md` (TODO / IN PROGRESS / OBSERVATION / CLOSED) — обновляется и читается всеми модераторами и Worker'ами. Обязательное чтение перед стартом любой фазы.

### 5. Memory дубли в Integram

**Риск:** два Летописца пишут одинаковый урок → дубли в PATTERNS/LESSONS.
**Avoid:** Летописец перед `create_object` делает search по `name + tags` — если совпадает, использует `update_object` или skip с пометкой.

### 6. Production deploy race

**Риск:** Worker A готовит deploy фазы X, Worker B — фазы Y → прод получает оба одновременно.
**Avoid:** **deploy queue** — только одна фаза в active deploy. Перед push на main модератор проверяет нет ли другой фазы в observation window. Либо явный **deploy_lock file** `docs/agentforge/deploy_lock.md` с timestamp + phase + ETA окончания observation.

### 7. Shared compute resource overload

**Риск:** два regression run одновременно перегружают тестовый сервер.
**Avoid:** persistent runs только в tmux/screen, проверка load (`top`/`uptime`) перед стартом. При высокой нагрузке — ждать, не стартовать.

---

## Pre-start checklist для Worker'а

Перед началом любой фазы Worker session должен:

1. `git pull origin main` + `git fetch --all` — свежий контекст
2. Прочитать `docs/agentforge/active_queue.md` — что в активе у других
3. Проверить deploy_lock — есть ли активная prod observation
4. Заявить свой domain (файлы / конфиги которые будет трогать) в active_queue
5. Создать feature branch `worker-<phase>/<sprint>`
6. Только после этого — старт AF пайплайна

---

## Pre-GREEN checklist для модератора

Перед выдачей GREEN на новую фазу модератор должен:

1. Прочитать `active_queue.md` — что параллельно идёт
2. Проверить decision log (project DECISIONS) — нет ли pending decision от другого модератора, которое влияет на текущую фазу
3. Проверить domain overlap — Worker этой фазы и Worker другой активной фазы не должны трогать одни файлы
4. Если overlap — последовательно, не параллельно (false-parallelism)
5. Записать новую фазу в active_queue с явным domain claim

---

## PO (Product Owner) discipline

- **Лимит 2 параллельные задачи макс** — больше съедает PO bandwidth на context switching.
- **Архитектурно связанные задачи — последовательно** (например если фаза B блокирует фазу C, не пытаться их параллелить).
- **Decision log в реальном времени** — модератор фиксирует ключевое решение сразу, не "в конце фазы".
- **Sync point раз в день** — обзор всех active фаз, не только своей. Лучше utром, перед открытием новых фаз.

---

## State files (общие для всех сессий)

**`docs/agentforge/active_queue.md`** — kanban активных фаз. Формат:

```markdown
## TODO
- [phase-X] PORTFOLIO HALT fix — owner: WORKER-1, blocking: EW-4b

## IN PROGRESS
- [phase-Y] Phase 9 Config Extraction — owner: WORKER-2, started: 2026-MM-DD,
  domain: bot/config/, configs/

## OBSERVATION
- [phase-Z] AF Phase A — observed since 2026-05-04, ETA closure: 2026-05-05

## CLOSED (за последние 7 дней)
- [phase-T] State Truth — closed 2026-05-03, report: docs/memory/agentforge_reports/report_phaseT_20260503.md
```

**`docs/agentforge/deploy_lock.md`** — текущая фаза в active deploy / observation:

```markdown
ACTIVE DEPLOY: phase-A
Started: 2026-05-04T14:30 UTC
Worker: <session-id-or-name>
ETA observation end: 2026-05-04T14:30 UTC + 24h
Rollback procedure: <link to plan>

NEXT IN QUEUE:
- phase-B (PORTFOLIO HALT fix) — waiting for phase-A closure
```

При закрытии фазы — Летописец чистит deploy_lock.

---

## Сигналы что параллелизм идёт не туда

Если в течение фазы:

- Два модератора одновременно пишут противоречивые constraints одному Worker'у — STOP, синхронизироваться.
- Worker не может pull из main без conflict — domain overlap, остановиться.
- Decision log имеет 2+ свежих pending decision из разных модераторов — синхронизировать перед продолжением.
- Test server load >90% — не стартовать regression run.
- Deploy_lock не пуст и просрочен ETA — модератор активной фазы должен закрыть наблюдение или продлить ETA с обоснованием.

---

## Связь с другими документами

- `docs/memory/two_tier_routing.md` — куда писать уроки от parallel execution
- `docs/agents/team_lead.md` — Наставник в AF проводит post-mortem параллельных фаз
- Project instance — в каждом AF проекте свой файл с конкретными paths/IDs

---

## История

| Дата | Версия | Что |
|---|---|---|
| 2026-05-04 | 1.0 | Извлечено как universal методология из обсуждения 2-модератор / 2-worker сценария в TRADERAGENT. Закрепляет правила избежания конфликтов и discipline для PO. |
