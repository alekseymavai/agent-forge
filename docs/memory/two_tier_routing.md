# Two-tier memory routing — методология

**Назначение:** правило разделения memory artifacts между universal AF workspace и project-specific workspace. Применяется Летописцем при closure фазы и модератором при decision log.

**Уровень:** методологический (universal). Project-specific instance этого правила живёт в репо проекта.

---

## Принцип

Любой AF проект, накапливающий память дольше одного спринта, держит **два уровня памяти**:

| Уровень | Workspace | Что хранит |
|---------|-----------|-----------|
| **Universal** | `agentforgememory` (или эквивалент) | Методологические PATTERNS / LESSONS / ANTIPATTERNS — применимы в любом AF проекте |
| **Project** | свой workspace (например `devteam`, `team-X`) | Project-specific decisions, lessons, AF phase reports |

Без routing правила обе таблицы PATTERNS/LESSONS/ANTIPATTERNS дублируются и Летописец путается куда писать. Без двух уровней — методологические уроки тонут в project-specific шуме.

---

## Litmus-тест

Летописец задаёт себе один вопрос:

> "Этот урок будет полезен в другом проекте на AgentForge — или специфичен только для этого проекта?"

- **Универсальный** → universal workspace (`agentforgememory`)
- **Project-specific** → свой workspace проекта

Если сомневаешься — пиши в project workspace (downside меньше: лишний project-урок < потерянный методологический).

---

## Routing категории

| Тип артефакта | Куда |
|---------------|------|
| Методологический паттерн (как работают роли, формат Gift'ов, split-session) | universal · PATTERNS |
| Методологический урок (Scout пропускает при детальном чтении; роль X нарушает Y) | universal · LESSONS |
| Методологический антипаттерн (модератор пишет команды Worker'у; >3 пункта = нарушение роли) | universal · ANTIPATTERNS |
| PO decision с rationale | project · DECISIONS |
| Closure фазы AF (consensus report) | project · AFConsensusReports |
| Project-specific паттерн (особенности кода, конфигов проекта) | project · PATTERNS |
| Project-specific урок (баг этого проекта, особенность его инфры) | project · LESSONS |
| Project-specific антипаттерн (специфические гонки, deploy-практики проекта) | project · ANTIPATTERNS |

---

## Примеры разграничения

| Урок | Куда | Почему |
|------|------|--------|
| "Scout output был неточен N раз за фазу — паттерн методологии" | universal · LESSONS | Любой AF проект столкнётся |
| "Конкретный bug не передавался в exchange order — silent skip" | project · LESSONS | Project-specific код |
| "Architect Gift должен иметь TL;DR-первой строкой" | universal · PATTERNS | Универсальная практика |
| "Dead code feature X нужен только при условии Y проекта" | project · LESSONS | Завязано на specific architecture |
| "skipHitl=true для AI-tools в Integram" | universal · PATTERNS | Любой Integram-based проект |
| "Komitet vN verdict id=NNN — DEFER feature Z" | project · phase reports | Project-specific |

---

## Edge cases

1. **Universal infra специфика** (Integram API, AgentBus, kernel patterns) → universal
2. **Project infra специфика** (specific exchange API, specific DB schema) → project
3. **General deploy patterns** → universal
4. **Production drift конкретного проекта** → project

---

## Format template (одинаков для PATTERNS/LESSONS/ANTIPATTERNS)

```
name: <краткое название>
description: <суть в 1-2 предложениях>
context: <когда применять / проявляется>
example: <код или пример, опционально для PATTERNS>
tags: <comma-separated tags из convention>
```

Для DECISIONS добавляется:

```
alternatives: <какие варианты рассмотрели>
why_chosen: <почему выбрали именно этот>
```

---

## Tags convention

**Universal workspace:**
- Роль: `role:scout`, `role:architect`, `role:po`, `role:tech-writer`
- Тип: `methodology`, `pipeline`, `gift-protocol`, `split-session`, `two-tier-routing`
- Слой: `infra`, `integram`, `agentbus`, `kernel`

**Project workspace** (примеры тегов — каждый проект свои):
- Phase: `phase-A`, `phase-T`
- Sprint/commit: `sprint-Nx`, `commit-<sha>`
- Domain: project-specific (например для trading: `dca`, `mdd`, `smc`, `risk`)

---

## Project-instance template

Каждый AF проект создаёт свой `<project>/docs/.../routing_rule.md`, который ссылается на этот universal документ и добавляет:

1. **Конкретные workspace IDs** проекта (`agentforgememory` table IDs + project workspace + table IDs)
2. **Project-specific tags** (phase names, domain tags)
3. **Project-specific edge cases** если они есть
4. **Ссылку обратно на universal** как source of truth для обновлений методологии

Пример project-instance: `github.com/alekseymavai/TRADERAGENT/blob/main/docs/agentforge/letopisets_routing_rule.md`

---

## Когда применять

- **Worker Летописец** — при closure каждого Sprint/фазы AF, перед коммитом final report.
- **Модератор (outer Хозяин)** — при фиксации decision log.
- **Self-audit** — если обнаружен паттерн нарушения роли, записать как methodology lesson.

---

## Связь

- `docs/agents/tech_writer.md` — роль Летописца (этот документ — обязательное чтение)
- `docs/team-protocol.md` — общий протокол команды
- AgentForge memory как Pattern: `agentforgememory · PATTERNS · "Two-tier memory routing для AF проектов"`

---

## История

| Дата | Версия | Что |
|---|---|---|
| 2026-05-04 | 1.0 | Извлечено как universal методология из TRADERAGENT instance (`docs/agentforge/letopisets_routing_rule.md`). Закрепляет паттерн двухуровневой памяти AF. |
