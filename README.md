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
| **Team Memory** | Integram `devteam` — Code Memory Graph (паттерны, ADR, уроки) |
| **Role Registry** | Лица с призванием: Scout, Architect, Dev, QA, Security, DevOps, TechWriter |

## Быстрый старт

```bash
# Подключить к проекту
pip install git+https://github.com/alekseymavai/agent-forge.git

# Инициализировать контекст проекта
cp agent-forge/templates/context.yaml docs/memory/context.yaml
# Отредактировать: telos, stack, fragile_zones
```

## Структура

```
AgentForge/
├── src/team_infra/
│   ├── gift.py          # Gift dataclass + GiftBus
│   ├── team_memory.py   # Integram devteam клиент
│   ├── agent_bus.py     # файловая шина + лог
│   ├── agent_core.py    # базовый класс агента-лица
│   └── roles/           # Scout, Architect, Dev, QA, Security, DevOps, TechWriter
├── docs/
│   ├── plan.md          # план реализации
│   ├── concept.md       # полная философия
│   └── agents/          # договор каждой роли
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

## Проекты на AgentForge

| Проект | Статус |
|--------|--------|
| BEEBOT (Telegram-бот пчеловода) | подключается в Фазе 5 |

## Авторы

Андрей Гаврилов / [gaveron18](https://github.com/gaveron18)
Aleksey Mavai / [alekseymavai](https://github.com/alekseymavai)

Философская основа: PLM-GIFT — Гаврилов Денис / [unidel2035](https://github.com/unidel2035)
