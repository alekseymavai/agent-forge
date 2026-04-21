# AgentForge — Архитектура

> **Версия:** 2.0 · 21 апреля 2026
> **Статус:** Active
> **Обновлено:** Фаза 6 завершена — 10 ролей, миграция на agentforgememory

---

## Телос системы

AgentForge — переиспользуемая инфраструктура команды AI-агентов-разработчиков.

```
Без AgentForge:   один Claude меняет шляпы → амнезия между сессиями
С AgentForge:     команда лиц с памятью   → накопление опыта между проектами
```

**Продукт завода:** программный проект с архитектурой, кодом и тестами,
созданный командой 10 ролей по Gift Protocol, где финальное решение — за человеком.

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
│   ├── gift.py                    ← Gift dataclass, Freedom enum
│   ├── agent_bus.py               ← файловая шина inbox/outbox/log
│   ├── project_context.py         ← загрузка context.yaml
│   ├── coordinator.py             ← запуск пайплайна → ConsensusReport
│   │
│   ├── roles/                     ← 10 плагинов (заменяемы под проект)
│   │   ├── _base.py               ← LLMRolePlugin (базовый класс с LLM)
│   │   ├── product_owner.py       ← Хозяин — голос пользователя (1.0)
│   │   ├── scout.py               ← Ведатель — разведчик кода (0.9)
│   │   ├── architect.py           ← Зодчий — проектировщик решения (1.0)
│   │   ├── security.py            ← Блюститель — аудитор безопасности (1.3, блокирующий)
│   │   ├── backend_dev.py         ← Делатель-тыл — Python-разработчик (1.0)
│   │   ├── frontend_dev.py        ← Делатель-лик — фронтенд-разработчик (1.0)
│   │   ├── qa.py                  ← Испытатель — контроль качества (1.2)
│   │   ├── devops.py              ← Устроитель — инженер деплоя (1.0, гибрид)
│   │   └── tech_writer.py         ← Летописец — технический писатель (1.0)
│   │
│   ├── memory/
│   │   ├── schema.py              ← ID таблиц workspace agentforgememory
│   │   └── team_memory.py         ← Integram agentforgememory клиент
│   │
│   ├── cli.py                     ← agentforge init / run / status
│   └── __init__.py                ← публичный API: AgentForge, Gift, AgentBus
│
├── templates/
│   └── context.yaml               ← шаблон для нового проекта
│
├── docs/
│   ├── plan.md                    ← план реализации по фазам
│   ├── architecture.md            ← этот файл
│   ├── team-protocol.md           ← протокол команды (пайплайн, консенсус, онтология)
│   └── agents/                    ← контракт каждой из 10 ролей
│
└── tests/
    ├── test_gift.py               ✅
    ├── test_agent_bus.py          ✅
    ├── test_coordinator.py        ✅
    ├── test_roles.py              ✅
    ├── test_team_memory.py        ✅
    └── test_cli.py                ✅
```

---

## Слои архитектуры

```
┌──────────────────────────────────────────────────────┐
│                   ЧЕЛОВЕК (Алексей)                   │
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
│    .register(TeamLeadPlugin())     10 ролей           │
│    .register(ScoutPlugin())        топосортировка     │
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
│  10 РОЛЕЙ     │      │  ПРОТОКОЛЫ           │
│  (plugins)    │      │                      │
│               │      │  Gift + Freedom      │
│  Наставник    │ ←──► │  AgentBus            │
│  Хозяин       │      │  ProjectContext       │
│  Ведатель     │      │                      │
│  Зодчий       │      │  Каждый шаг = дар    │
│  Блюститель   │      │  с телосом и         │
│  Делатели ×2  │      │  анамнезисом         │
│  Испытатель   │      │                      │
│  Устроитель   │      │                      │
│  Летописец    │      │                      │
└───────────────┘      └──────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│          TEAM MEMORY (Integram agentforgememory)      │
│                                                       │
│  PATTERNS (240)     — паттерны с призванием           │
│  ANTIPATTERNS (414) — что нельзя повторять            │
│  DECISIONS (132)    — ADR с анамнезисом решений       │
│  LESSONS (241)      — уроки из эксплуатации           │
│  AGENTS (128)       — 10 ролей с весами и призваниями │
│  TASKS (125)        — задачи пайплайна                │
│  TASK_LIFECYCLE(420)— жизненный цикл каждой задачи    │
│                                                       │
│  Анамнезис: паттерн из проекта A со-присутствует     │
│  при выполнении задачи в проекте B                   │
└──────────────────────────────────────────────────────┘
```

---

## Пайплайн выполнения задачи

```
Человек: "задача X — телос Y для пользователя"
  │
  ▼
Наставник (TeamLead, 1.5×)
  │  читает context.yaml + TeamMemory (анамнезис)
  │  инициализирует AgentBus (task_id, telos)
  │
  ├──► Хозяин (PO)      → требования + приоритет + критерии приёмки
  │         ↓
  ├──► Ведатель (Scout)  → Gift{карта кода, риски, паттерны}
  │         ↓
  ├──► Зодчий (Arch)     → план + 2 варианта + ADR
  │         ↓
  ├──► Блюститель (1.3×) → аудит OWASP
  │         │               DECLINED → pipeline стоп (HIGH найден)
  │         ↓
  ├──► Делатель-тыл  ─┐  параллельно (test-first)
  ├──► Делатель-лик  ─┘
  │         ↓
  ├──► Испытатель (1.2×) → тесты + линтеры; DEFER → возврат Делателям
  │         ↓
  ├──► Устроитель        → деплой (гибрид: скрипт + LLM при сбое)
  │         ↓
  ├──► Летописец         → session-лог + ARCHITECTURE.md + ConsensusReport
  │         ↓
  ├──► Хозяин            → приёмка по критериям
  │         ↓
  └──► Наставник         → фиксация в памяти команды
           │
           ▼
  ConsensusReport{
      human_decision_required: True   ← ВСЕГДА
  }
           │
           ▼
  Человек принимает решение

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
  > Наставник (1.5× — оркестратор, блокирующий)
    > Блюститель (1.3× — безопасность, блокирующий)
      > Испытатель (1.2× — красный тест стопит деплой)
        > Зодчий (1.0× — план согласован)
          > простота кода
            > скорость реализации
```

---

## Как подключить к проекту

```bash
# 1. Установить
pip install git+https://github.com/alekseymavai/agent-forge.git

# 2. Инициализировать
agentforge init MyProject

# 3. Описать телос (в context.yaml)
telos: "Описание цели проекта для пользователя"

# 4. Запустить
agentforge run --task "Описание задачи"

# → ConsensusReport: варианты, рекомендация, решение за человеком
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
*Версия: 2.0 — 21.04.2026*
*Обновлять при изменении структуры пакета или пайплайна*
