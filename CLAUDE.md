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

### Текущий статус (21.04.2026):
- Фазы 1–6 завершены, 45 тестов зелёных
- Пакет: `agentforge` (pip install, from agentforge import ...)
- 10 ролей (LLMRolePlugin), CLI, Team Memory (agentforgememory)
- Два режима LLM: prompt (по умолчанию, через Claude Code) и api (--api, внешний LLM)
- Следующая: Фаза 7 — первый реальный проект

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
- Пайплайн 10 ролей: Наставник → Хозяин → Ведатель → Зодчий → Блюститель → Делатели → Испытатель → Устроитель → Летописец → ConsensusReport
- Память сессий — в TeamMemory (agentforgememory), не в файлах
