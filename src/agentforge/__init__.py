"""
AgentForge — переиспользуемая инфраструктура команды AI-агентов-разработчиков.
Онтология дара (PLM-GIFT). Финальное решение — всегда за человеком.
"""

__version__ = "0.1.0"

from agentforge.agent_bus import AgentBus
from agentforge.coordinator import ConsensusReport, Coordinator
from agentforge.gift import Freedom, Gift
from agentforge.kernel.app import AgentForgeApp
from agentforge.kernel.container import Container
from agentforge.kernel.plugin import RolePlugin
from agentforge.memory.team_memory import TeamMemory, TeamMemoryError
from agentforge.project_context import ProjectContext

__all__ = [
    "AgentForgeApp",
    "AgentBus",
    "ConsensusReport",
    "Container",
    "Coordinator",
    "Freedom",
    "Gift",
    "ProjectContext",
    "RolePlugin",
    "TeamMemory",
    "TeamMemoryError",
]
