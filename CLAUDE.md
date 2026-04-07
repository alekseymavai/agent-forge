# Claude Context — Алексей Мавай

Этот файл читается автоматически при старте каждой сессии в ~/AgentForge.
Общайся по-русски. Имя пользователя: Алексей.

---

## Владелец проекта

- **Имя:** Алексей Мавай
- **GitHub:** `alekseymavai`
- **Машина:** hive (локальная, общая с gaveron18)
- **Проекты Алексея:** AgentForge, BEEBOT

> Внимание: глобальный `/home/hive/CLAUDE.md` принадлежит Андрею Гаврилову (gaveron18).
> В сессиях из `~/AgentForge/` — работаем в контексте Алексея.

---

## AgentForge

- **Локально:** `/home/hive/AgentForge/`
- **GitHub:** https://github.com/alekseymavai/agent-forge
- **Push:** через `alekseymavai` (авторизован на машине)

### При старте сессии читать:
1. `docs/plan.md` — план по фазам, найти первую незакрытую задачу
2. `docs/architecture.md` — структура пакета и пайплайн
3. `docs/session_prompt.md` — контекст предыдущей сессии

### Текущий статус (07.04.2026):
- Фаза 1 — Ядро: **в работе** (следующий шаг)
- Фундамент: gift.py, agent_bus.py, agent_core.py, project_context.py ✅
- Пакет называется `team_infra` — нужно переименовать в `agentforge` (ADR-002)

### Анамнезис (откуда берём паттерны):
- `BEEBOT/src/kernel/` — микроядро (Plugin + Container + BeeBotApp)
- `BEEBOT/docs/agents/` — договоры 9 ролей

---

## BEEBOT

- **Локально:** `/home/hive/BEEBOT/`
- **GitHub:** https://github.com/alekseymavai/BEEBOT (upstream)
- **VPS:** `ai-agent@185.233.200.13`
- **Инструкция:** `/home/hive/BEEBOT/CLAUDE.md`

---

## Git / GitHub

- **Активный аккаунт для AgentForge:** `alekseymavai`
- **Переключить:** `gh auth switch -u alekseymavai && gh auth setup-git`
- **После работы вернуть:** `gh auth switch -u gaveron18` (если нужно для других проектов)

---

## Правила работы

- Push только через `alekseymavai`
- Каждое открытие сохранять в память СРАЗУ
- Финальное решение — всегда за Алексеем (`human_decision_required: True`)
- Команда работает по ролям: Product Owner → Scout → Architect → Security → ConsensusReport
- Обновлять `docs/session_prompt.md` в конце каждой значимой сессии
