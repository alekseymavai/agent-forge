# AgentForge — Архитектура

> **Версия:** 1.0 · 7 апреля 2026
> **Статус:** In Design
> **Источник:** ConsensusReport сессии 07.04.2026

---

## Телос системы

AgentForge — переиспользуемая инфраструктура команды AI-агентов-разработчиков.

```
Без AgentForge:   один Claude меняет шляпы → амнезия между сессиями
С AgentForge:     команда лиц с памятью   → накопление опыта между проектами
```

**Продукт завода:** программный проект с архитектурой, кодом и тестами,
созданный командой ролей по Gift Protocol, где финальное решение — за человеком.

---

## Структура пакета

```
AgentForge/
│
├── src/agentforge/
│   │
│   ├── kernel/                    ← ядро (стабильное, не меняется)
│   │   ├── plugin.py              ← abstract RolePlugin (интерфейс роли)
│   │   ├── container.py           ← DI-контейнер (set/get/require)
│   │   └── app.py                 ← AgentForgeApp: register() + топосортировка + run()
│   │
│   ├── protocols/                 ← контракты между ролями (уже реализованы)
│   │   ├── gift.py                ← Gift dataclass, Freedom enum
│   │   ├── agent_bus.py           ← файловая шина inbox/outbox/log
│   │   └── project_context.py    ← загрузка context.yaml
│   │
│   ├── coordinator.py             ← запуск пайплайна → ConsensusReport
│   │
│   ├── roles/                     ← плагины (заменяемы под проект)
│   │   ├── product_owner.py       ← голос заказчика
│   │   ├── scout.py               ← разведчик кода
│   │   ├── architect.py           ← проектировщик решения
│   │   ├── backend_dev.py         ← Python-разработчик
│   │   ├── frontend_dev.py        ← Vue-разработчик
│   │   ├── qa.py                  ← инженер качества (вес 1.2)
│   │   ├── security.py            ← аудитор безопасности (вес 1.3, блокирующий)
│   │   ├── devops.py              ← инженер деплоя
│   │   └── tech_writer.py         ← технический писатель
│   │
│   ├── memory/
│   │   ├── team_memory.py         ← Integram devteam клиент
│   │   └── schema.py              ← схема таблиц PATTERNS/DECISIONS/LESSONS
│   │
│   ├── cli.py                     ← agentforge init / run / status
│   └── __init__.py                ← публичный API: AgentForge, Gift, AgentBus
│
├── templates/
│   └── context.yaml               ← шаблон для нового проекта
│
├── docs/
│   ├── plan.md                    ← план реализации (этот файл — architecture.md)
│   ├── architecture.md            ← этот файл
│   └── agents/                    ← договоры ролей (из BEEBOT, адаптированные)
│
└── tests/
    ├── test_gift.py               ✅
    ├── test_agent_bus.py          ✅
    ├── test_coordinator.py        ← Фаза 1
    ├── test_roles.py              ← Фаза 2
    ├── test_team_memory.py        ← Фаза 3
    └── test_cli.py                ← Фаза 4
```

---

## Слои архитектуры

```
┌──────────────────────────────────────────────────────┐
│                   АНДРЕЙ                              │
│        телос: "создай проект X"                      │
│        решение: ConsensusReport → принять/отклонить  │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│              CLI / Python API                         │
│   agentforge init / run / status                     │
│   AgentForge.run(task, context_path)                 │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│                  ЯДРО (kernel/)                       │
│                                                       │
│  AgentForgeApp                                        │
│    .register(ScoutPlugin())                           │
│    .register(ArchitectPlugin())    топосортировка     │
│    .register(SecurityPlugin())  → lifecycle           │
│    .run(task, context)          → ConsensusReport     │
│                                                       │
│  Coordinator — запускает пайплайн ролей               │
│  Container   — DI: роли получают зависимости          │
└────────────────────┬─────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────┐      ┌──────────────────────┐
│  РОЛИ         │      │  ПРОТОКОЛЫ           │
│  (plugins)    │      │                      │
│               │      │  Gift                │
│  Scout        │ ←──► │  AgentBus            │
│  Architect    │      │  ProjectContext       │
│  Security     │      │                      │
│  QA           │      │  Каждый шаг = дар    │
│  ...          │      │  с телосом и         │
│               │      │  анамнезисом         │
└───────────────┘      └──────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│              TEAM MEMORY (Integram devteam)           │
│                                                       │
│  PATTERNS     — паттерны с природой и призванием     │
│  ANTIPATTERNS — что нельзя повторять (с инцидентом)  │
│  DECISIONS    — ADR с анамнезисом цепочки решений    │
│  LESSONS      — уроки из эксплуатации                │
│  TASK_LIFECYCLE — жизненный цикл каждой задачи       │
│                                                       │
│  Анамнезис: паттерн из проекта A со-присутствует     │
│  при выполнении задачи в проекте B                   │
└──────────────────────────────────────────────────────┘
```

---

## Пайплайн выполнения задачи

```
Андрей: "задача X — телос Y для пользователя"
  │
  ▼
Coordinator
  │  читает context.yaml + TeamMemory (анамнезис)
  │  инициализирует AgentBus (task_id, telos)
  │
  ├──► Scout           → Gift{карта кода, риски, паттерны}
  │         ↓
  ├──► Architect       → получает Scout Gift
  │         │            предлагает 2 варианта решения
  │         ↓
  ├──► Security (1.3×) → атакует оба варианта
  │         │            DECLINED → pipeline стоп (HIGH найден)
  │         ↓
  Coordinator → ConsensusReport{
      варианты: [A, B],
      рекомендация: "вариант A — меньше рисков",
      security_status: GREEN,
      human_decision_required: True   ← ВСЕГДА
  }
  │
  ▼
Андрей выбирает вариант
  │
  ├──► Backend Dev  ─┐  параллельно
  ├──► Frontend Dev ─┘  (если нужен)
  │         ↓
  ├──► QA (1.2×)    → все тесты зелёные? иначе → Dev
  │         ↓
  ├──► Security     → нет HIGH уязвимостей? иначе → Dev
  │         ↓
  ├──► DevOps       → задеплоено и работает
  │         ↓
  └──► TechWriter   → документация обновлена

LESSON записан в TeamMemory
→ со-присутствует в следующей задаче
```

---

## RolePlugin — интерфейс роли

```python
# src/agentforge/kernel/plugin.py

class RolePlugin(ABC):
    """Каждая роль — плагин с призванием и lifecycle."""

    depends_on: list[str] = []      # роли от которых зависит
    role_name: str = ""             # идентификатор
    weight: float = 1.0             # вес в консенсусе

    @abstractmethod
    async def setup(self, container: Container) -> None:
        """Инициализация: загрузить зависимости из DI-контейнера."""
        ...

    @abstractmethod
    async def run(self, task: str, gift: Gift | None) -> Gift:
        """
        Выполнить призвание роли.
        Принять дар от предыдущей роли → выполнить работу → подарить следующей.
        """
        ...

    async def teardown(self) -> None:
        """Завершение работы роли."""
        pass
```

---

## ConsensusReport — выход к человеку

```python
@dataclass
class ConsensusReport:
    task_id: str
    telos: str
    gifts: list[Gift]              # дары всех ролей
    recommendation: str            # итоговая рекомендация
    variants: list[dict]           # варианты от Architect-а
    security_status: str           # GREEN | YELLOW | RED
    blocked: bool                  # True если Security DECLINED
    human_decision_required: bool  # ВСЕГДА True
    anamnesis_used: list[str]      # что вспомнили из TeamMemory
```

---

## Иерархия весов (приоритет при конфликте)

```
Телос задачи (польза для пользователя)
  > Security  (1.3× — блокирующая, P0 стопит всё)
    > QA       (1.2× — красный тест стопит деплой)
      > Architect (1.0× — план согласован)
        > простота кода
          > скорость реализации
```

---

## Как подключить к проекту

```bash
# 1. Установить
pip install agentforge

# 2. Инициализировать
agentforge init BEECRM

# 3. Описать телос (в context.yaml)
telos: "CRM-система для пчеловода. BEEBOT — smart frontend."

# 4. Запустить
agentforge run --task "Спроектируй модель данных клиента"

# → ConsensusReport: варианты, рекомендация, решение за Андреем
```

---

## Анамнезис проектирования

Источники из которых взята архитектура:

| Источник | Что взяли |
|----------|-----------|
| BEEBOT `src/kernel/` | Паттерн микроядра: Plugin + Container + TopologySort |
| BEEBOT `docs/agents/` | 9 договоров ролей с алгоритмами и правилами |
| PLM-GIFT (unidel2035/plm) | Gift Protocol, 5 аксиом, анамнезис как со-присутствие |
| TRADERAGENT | Weighted consensus, challenge-протокол Security |
| AgentForge текущий | gift.py, agent_bus.py, agent_core.py, project_context.py |

---

*Файл: docs/architecture.md*
*Версия: 1.0 — 07.04.2026*
*Обновлять при изменении структуры пакета или пайплайна*
