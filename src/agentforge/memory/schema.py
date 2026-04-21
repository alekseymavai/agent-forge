"""schema.py — ID таблиц и колонок в воркспейсе agentforgememory (Integram).

Воркспейс: agentforgememory (slug: agentforgememory)
URL: https://ai2o.online
Создан: 21.04.2026 (мигрировано из devteam)

Не менять typeId без обновления Integram — это ссылки на реальные таблицы.
"""

# ── Воркспейс ────────────────────────────────────────────────────────────────

WORKSPACE_SLUG = "agentforgememory"

# ── Таблицы ──────────────────────────────────────────────────────────────────

TABLE_PATTERNS       = 240  # Успешные паттерны
TABLE_ANTIPATTERNS   = 414  # Антипаттерны и ловушки
TABLE_DECISIONS      = 132  # ADR — архитектурные решения (Архитектура_решений)
TABLE_LESSONS        = 241  # Уроки из выполненных задач
TABLE_TASKS          = 125  # Задачи пайплайна (родитель для TASK_LIFECYCLE)
TABLE_TASK_LIFECYCLE = 420  # Шаги задачи (child → TASKS, baseType=125)
TABLE_AGENTS         = 128  # Агенты (10 ролей команды)

# ── Колонки PATTERNS (240) ────────────────────────────────────────────────────
# Алиасы для create_object / list_objects

PATTERNS_COLS = {
    "name":        "name",         # string — название паттерна
    "description": "description",  # memo   — подробное описание
    "context":     "context",      # memo   — когда применять
    "example":     "example",      # memo   — пример кода/псевдокода
    "tags":        "tags",         # string — теги через запятую
}

# ── Колонки ANTIPATTERNS (414) ────────────────────────────────────────────────

ANTIPATTERNS_COLS = {
    "name":        "name",
    "description": "description",  # что делает антипаттерн плохим
    "consequence": "consequence",   # что случится если не избежать
    "remedy":      "remedy",        # что делать вместо
    "project":     "project",
    "tags":        "tags",
}

# ── Колонки DECISIONS / Архитектура_решений (132) ────────────────────────────

DECISIONS_COLS = {
    "adr_id":       "adr_id",       # string — ADR-001, ADR-002 …
    "title":        "Название",     # string — короткое название (alias в agentforgememory)
    "description":  "Описание",     # memo   — описание решения
    "context":      "context",      # memo   — почему это решение понадобилось
    "decision":     "decision",     # memo   — что решили
    "consequences": "consequences", # memo   — последствия (плюсы/минусы)
    "status":       "status",       # proposed | accepted | deprecated
}

# ── Колонки LESSONS (241) ────────────────────────────────────────────────────

LESSONS_COLS = {
    "name":           "name",            # string — название урока
    "what_happened":  "what_happened",   # memo — что произошло
    "what_learned":   "what_learned",    # memo — сам урок
    "how_to_apply":   "how_to_apply",    # memo — как применять дальше
    "severity":       "severity",        # low | medium | high
}

# ── Колонки TASK_LIFECYCLE (420) ──────────────────────────────────────────────

TASK_LIFECYCLE_COLS = {
    "name":        "name",         # string — описание шага
    "role":        "role",         # string — Scout, Architect, Security …
    "freedom":     "freedom",      # string — ACCEPTED | DEFERRED | DECLINED
    "gift_content":"gift_content", # memo   — содержание дара
}

# ── Колонки AGENTS (128) ─────────────────────────────────────────────────────

AGENTS_COLS = {
    "name":          "Имя",           # string — русское имя роли
    "description":   "Описание",      # memo   — описание роли
    "role_name_en":  "role_name_en",  # string — английское имя (Scout, Architect…)
    "weight":        "weight",        # number — вес голоса
    "can_block":     "can_block",     # bool   — блокирует ли пайплайн
    "pipeline_order":"pipeline_order",# number — порядок в пайплайне
    "calling":       "calling",       # memo   — призвание (онтология дара)
}
