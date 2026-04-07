"""schema.py — ID таблиц и колонок в воркспейсе devteam (Integram).

Воркспейс: devteam (id: 14, slug: devteam)
URL: https://ai2o.online
Создан: 07.04.2026

Не менять typeId без обновления Integram — это ссылки на реальные таблицы.
"""

# ── Таблицы ──────────────────────────────────────────────────────────────────

TABLE_PATTERNS       = 14   # Успешные паттерны
TABLE_ANTIPATTERNS   = 15   # Антипаттерны и ловушки
TABLE_DECISIONS      = 16   # ADR — архитектурные решения
TABLE_LESSONS        = 17   # Уроки из выполненных задач
TABLE_TASKS          = 127  # Задачи пайплайна (родитель для TASK_LIFECYCLE)
TABLE_TASK_LIFECYCLE = 133  # Шаги задачи (child → TASKS, baseType=127)

# ── Колонки PATTERNS (14) ─────────────────────────────────────────────────────
# Алиасы для create_object / list_objects

PATTERNS_COLS = {
    "name":        "name",         # string — название паттерна
    "description": "description",  # memo   — подробное описание
    "context":     "context",      # memo   — когда применять
    "example":     "example",      # memo   — пример кода/псевдокода
    "project":     "project",      # string — из какого проекта
    "tags":        "tags",         # string — теги через запятую
    "created_at":  "created_at",   # datetime
}

# ── Колонки ANTIPATTERNS (15) ─────────────────────────────────────────────────

ANTIPATTERNS_COLS = {
    "name":        "name",
    "description": "description",  # что делает антипаттерн плохим
    "consequence": "consequence",   # что случится если не избежать
    "remedy":      "remedy",        # что делать вместо
    "project":     "project",
    "tags":        "tags",
    "created_at":  "created_at",
}

# ── Колонки DECISIONS (16) ───────────────────────────────────────────────────

DECISIONS_COLS = {
    "adr_id":       "adr_id",       # string — ADR-001, ADR-002 …
    "title":        "title",        # string — короткое название
    "context":      "context",      # memo   — почему это решение понадобилось
    "decision":     "decision",     # memo   — что решили
    "consequences": "consequences", # memo   — последствия (плюсы/минусы)
    "project":      "project",
    "status":       "status",       # proposed | accepted | deprecated
}

# ── Колонки LESSONS (17) ─────────────────────────────────────────────────────

LESSONS_COLS = {
    "title":        "title",
    "what_happened":  "what_happened",   # memo — что произошло
    "what_learned":   "what_learned",    # memo — сам урок
    "how_to_apply":   "how_to_apply",    # memo — как применять дальше
    "project":      "project",
    "severity":     "severity",          # low | medium | high
    "created_at":   "created_at",
}

# ── Колонки TASK_LIFECYCLE (18) ───────────────────────────────────────────────

TASK_LIFECYCLE_COLS = {
    "task_id":     "task_id",      # string — uuid задачи
    "task_title":  "task_title",   # string — описание задачи
    "role":        "role",         # string — Scout, Architect, Security …
    "freedom":     "freedom",      # string — ACCEPTED | DEFERRED | DECLINED
    "gift_content":"gift_content", # memo   — содержание дара
    "project":     "project",
    "timestamp":   "timestamp",    # datetime
}
