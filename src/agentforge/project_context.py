"""
project_context.py — загрузка context.yaml

Машинно-читаемый контекст проекта.
Каждый агент читает его при старте.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class FragileZone:
    file: str
    reason: str
    telos_risk: str = "MEDIUM"  # LOW | MEDIUM | HIGH | CRITICAL


@dataclass
class Decision:
    id: str
    summary: str
    anamnesis: list[str] = field(default_factory=list)


@dataclass
class ProjectContext:
    project: str
    telos: str
    version: str = ""
    lifecycle_stage: str = "In Design"  # In Design | In Review | Released | In Change | Obsolete
    stack: dict = field(default_factory=dict)
    fragile_zones: list[FragileZone] = field(default_factory=list)
    current_state: dict = field(default_factory=dict)
    decisions: list[Decision] = field(default_factory=list)
    team_memory_workspace: str = "devteam"
    agent_bus_dir: str = ".agent_bus"

    @classmethod
    def load(cls, path: str = "docs/memory/context.yaml") -> "ProjectContext":
        data = yaml.safe_load(Path(path).read_text())

        fragile_zones = [
            FragileZone(**z) for z in data.get("fragile_zones", [])
        ]
        decisions = [
            Decision(**d) for d in data.get("decisions", [])
        ]

        return cls(
            project=data["project"],
            telos=data.get("telos", ""),
            version=data.get("version", ""),
            lifecycle_stage=data.get("lifecycle_stage", "In Design"),
            stack=data.get("stack", {}),
            fragile_zones=fragile_zones,
            current_state=data.get("current_state", {}),
            decisions=decisions,
            team_memory_workspace=data.get("team_memory_workspace", "devteam"),
            agent_bus_dir=data.get("agent_bus_dir", ".agent_bus"),
        )

    def is_fragile(self, filepath: str) -> Optional[FragileZone]:
        """Проверить: является ли файл хрупкой зоной."""
        for zone in self.fragile_zones:
            if zone.file in filepath:
                return zone
        return None

    def critical_zones(self) -> list[FragileZone]:
        return [z for z in self.fragile_zones if z.telos_risk == "CRITICAL"]
