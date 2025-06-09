# schemas.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any

class AgentContextEntry(BaseModel):
    """
    Each entry in an agent's list.
    """
    technical_name: str
    description: str
    data: Dict[str, Any] = Field(default_factory=dict)

class AgentsContext(BaseModel):
    """
    Instead of agent_name -> AgentContextEntry,
    we have agent_name -> List[AgentContextEntry].
    """
    root: Dict[str, List[AgentContextEntry]] = Field(default_factory=dict)

class SessionDetails(BaseModel):
    session_id: str
    session_started: str

class OrchestrationContext(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    session_details: SessionDetails
    agents: AgentsContext
