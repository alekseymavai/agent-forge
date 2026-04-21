# AgentForge — Промт для новой сессии

> Скопируй этот промт целиком в начало новой сессии Claude Code

---

## Контекст

Разрабатываем **AgentForge** — переиспользуемую инфраструктуру команды AI-агентов-разработчиков.

**Репозиторий:** `alekseymavai/agent-forge`
**Локально:** `/home/hive/AgentForge/`
**GitHub:** https://github.com/alekseymavai/agent-forge

---

## Что прочитать перед началом

1. `docs/plan.md` — план по фазам, найти первую незакрытую задачу
2. `docs/architecture.md` — структура пакета и пайплайн (v2.0)
3. `docs/team-protocol.md` — протокол команды (10 ролей, консенсус, онтология дара)

---

## Что уже сделано (21.04.2026)

### Фазы 1–6 завершены (44 теста зелёных)

- **Ядро:** kernel/ (Plugin + Container + App), coordinator.py → ConsensusReport
- **Протоколы:** gift.py (Gift + Freedom), agent_bus.py, project_context.py
- **10 ролей** (LLMRolePlugin): Хозяин(PO), Ведатель(Scout), Зодчий(Architect), Блюститель(Security,1.3), Делатель-тыл(Backend), Делатель-лик(Frontend), Испытатель(QA,1.2), Устроитель(DevOps), Летописец(TechWriter), Наставник(TeamLead,1.5)
- **CLI:** `agentforge init / run / status`
- **Team Memory:** workspace agentforgememory (ai2o.online)
- **Документация:** 10 контрактов ролей, team-protocol.md, architecture.md v2.0

### Пайплайн

```
Наставник → Хозяин → Ведатель → Зодчий → Блюститель
  → Делатель-тыл / Делатель-лик (параллельно)
  → Испытатель → Устроитель → Летописец
  → Хозяин → Наставник → ConsensusReport
```

### Team Memory (agentforgememory, ai2o.online)

| Таблица | ID |
|---------|----|
| PATTERNS | 240 |
| ANTIPATTERNS | 414 |
| Архитектура_решений | 132 |
| LESSONS | 241 |
| Агенты | 128 |
| Задачи | 125 |
| TASK_LIFECYCLE | 420 |

---

## Следующий шаг

**Фаза 7 — первый реальный проект:**
- `agentforge init <ProjectName>` + описание телоса
- Полный прогон пайплайна → ConsensusReport → решение Алексея

---

## LLM для ролей AgentForge

```bash
export ANTHROPIC_API_KEY=<ключ из менеджера секретов>
export ANTHROPIC_BASE_URL=https://api.polza.ai
```

---

*Обновлён: 21.04.2026 — Фазы 1–6 завершены, команда 10 ролей зафиксирована*
