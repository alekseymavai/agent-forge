# AgentForge

> «Кузница агентов» — универсальная команда разработчиков на онтологии дара.

**AgentForge** — переиспользуемая инфраструктура команды AI-агентов-разработчиков.
Подключи к любому проекту — команда сразу работает с общей памятью, протоколом даров и накопленным опытом.

## Философия

```
Команда = завод (предприятие)
  каждая роль  = лицо с призванием, не функция
  каждый шаг   = дар с телосом и анамнезисом
  CRM          = PLM-модуль фазы эксплуатации
  агент        = слуга → решает всегда человек
```

Основана на [PLM-GIFT онтологии](https://github.com/unidel2035/plm) (Гаврилов Денис, 2026).

## Концепция

```
[AgentForge] → [любой продукт]

Без AgentForge:   один агент меняет шляпы → амнезия между сессиями
С AgentForge:     команда лиц с памятью  → накопление опыта
```

## Три подсистемы

| Подсистема | Суть |
|-----------|------|
| **GiftBus** | Протокол передачи даров между ролями (telos / anamnesis / freedom) |
| **Team Memory** | Integram `agentforgememory` — Code Memory Graph (паттерны, ADR, уроки) |
| **Role Registry** | 10 лиц с призванием (см. Команда ниже) |

## Быстрый старт

```bash
# Подключить к проекту
pip install git+https://github.com/alekseymavai/agent-forge.git

# Инициализировать контекст проекта
cp agent-forge/templates/context.yaml docs/memory/context.yaml
# Отредактировать: telos, stack, fragile_zones
```

## Команда (10 ролей)

| # | Имя | English | Вес | Блокирует |
|---|-----|---------|-----|-----------|
| 0 | Хозяин | ProductOwner | 1.0 | может DEFER |
| 1 | Ведатель | Scout | 0.9 | нет |
| 2 | Зодчий | Architect | 1.0 | нет |
| 3 | Блюститель | SecurityReviewer | 1.3 | **да** |
| 4 | Делатель-тыл | BackendDev | 1.0 | нет |
| 5 | Делатель-лик | FrontendDev | 1.0 | нет |
| 6 | Испытат��ль | QA | 1.2 | может DEFER |
| 7 | Устроитель | DevOps | 1.0 | нет (гибрид) |
| 8 | Летописец | TechWriter | 1.0 | нет |
| 9 | Наставник | TeamLead | 1.5 | **да** |

Пайплайн: Наставник → Хозяин → Ведатель → Зодчий → Блюститель → Делатель-тыл / Делатель-лик (параллельно) → Испытатель → Устроитель → Летописец → Хозяин → Наставник

Подробные контракты: [`docs/agents/`](docs/agents/) | Протокол: [`docs/team-protocol.md`](docs/team-protocol.md)

## Структура

```
AgentForge/
├── src/agentforge/
│   ├── gift.py              # Gift dataclass + Freedom
│   ├── agent_bus.py         # файловая шина + лог
│   ├── agent_core.py        # базовый класс агента-лица
│   ├── coordinator.py       # оркестрация пайплайна
│   ├── project_context.py   # контекст проекта
│   ├── cli.py               # agentforge init / run / status
│   ├── kernel/              # Plugin + Container + App (микроядро из BEEBOT)
│   ├── memory/
│   │   ├── schema.py        # ID таблиц agentforgememory
│   │   └── team_memory.py   # Integram клиент
│   ├── roles/               # 10 ролей (LLMRolePlugin)
│   └── templates/           # шаблоны проекта
├── docs/
│   ├── plan.md              # план реализации
│   ├── architecture.md      # архитектура
│   ├── team-protocol.md     # протокол команды
│   └── agents/              # контракт ка��дой роли (10 файлов)
└── tests/
```

## Иерархия телоса

```
Телос задачи (польза для пользователя)
  > Security  (1.3× — блокирующая роль)
    > QA       (1.2× — зелёные тесты обязательны)
      > простота кода
        > скорость реализации
```

## Память команды

Workspace: **agentforgememory** (ai2o.online)

| Таблица | ID | Содержимое |
|---------|----|------------|
| PATTERNS | 240 | Архитектурные паттерны (5 записей) |
| ANTIPATTERNS | 414 | Антипаттерны (пустая, на будущее) |
| Архитектура_решений | 132 | ADR (3 записи) |
| LESSONS | 241 | Уроки (1 запись) |
| Агенты | 128 | 10 ролей с параметрами |
| Задачи | 125 | Трекинг задач |
| TASK_LIFECYCLE | 420 | Шаги выполнения (child → Задачи) |

## Проекты на AgentForge

| Проект | Статус |
|--------|--------|
| BEEBOT (Telegram-бот пчеловода) | подключён |

## Авторы

Андрей Гаврилов / [gaveron18](https://github.com/gaveron18)
Aleksey Mavai / [alekseymavai](https://github.com/alekseymavai)

Философская основа: PLM-GIFT — Гаврилов Денис / [unidel2035](https://github.com/unidel2035)
