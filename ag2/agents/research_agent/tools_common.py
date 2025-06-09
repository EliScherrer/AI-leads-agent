#tools_common.py

from typing import Any, List, Tuple, Dict
from autogen.agentchat.group import ReplyResult
from agents.research_agent.schemas import OrchestrationContext, AgentContextEntry

__all__ = [
    "find_entry",
    "list_agents_and_keys",
    "get_agent_variable",
    "update_agent_variable",
]


# ──────────────────────────────────────────────────────────
#  Core lookup helper
# ──────────────────────────────────────────────────────────
def find_entry(
    ctx_vars: Any,
    agent_name: str,
    technical_name: str,
) -> Tuple[OrchestrationContext, List[AgentContextEntry], AgentContextEntry]:
    """
    Returns (orchard, agent_list, entry) for a given agent_name & technical_name.
    Raises KeyError if the combination is not found.
    """
    orchard: OrchestrationContext = ctx_vars["orchestration_context"]

    agent_list = orchard.agents.root.get(agent_name)
    if agent_list is None:
        raise KeyError(f"agent '{agent_name}' not in orchard")

    for entry in agent_list:
        if entry.technical_name == technical_name:
            return orchard, agent_list, entry

    raise KeyError(f"technical_name '{technical_name}' not under agent '{agent_name}'")


# ──────────────────────────────────────────────────────────
#  Shared utility tools
# ──────────────────────────────────────────────────────────
def list_agents_and_keys(context_variables: Any) -> ReplyResult:
    """
    Read-only map of every agent’s data stores.
    For each key we show the *current* value-type so tools can act safely.
    """
    orchard = context_variables["orchestration_context"]
    overview: dict[str, list[dict[str, Any]]] = {}

    for agent_name, entries in orchard.agents.root.items():
        overview[agent_name] = [
            {
                "technical_name": e.technical_name,
                "description": e.description,
                # now returns {key: "type"} instead of just key names
                "data_keys": {k: type(v).__name__ for k, v in e.data.items()},
            }
            for e in entries
        ]

    return ReplyResult(
        message=f"(Tool) Agents overview: {overview}",
        context_variables=context_variables,
    )



def get_agent_variable(
    agent_name: str,
    technical_name: str,
    keys: List[str],
    context_variables: Any,
) -> ReplyResult:
    """Return the requested keys from agent_name.technical_name (no changes)."""
    _, _, entry = find_entry(context_variables, agent_name, technical_name)

    retrieved = {k: entry.data.get(k) for k in keys}

    return ReplyResult(
        message=f"(Tool) Data for {agent_name}.{technical_name}: {retrieved}",
        context_variables=context_variables,
    )


def update_agent_variable(
    agent_name: str,
    technical_name: str,
    key: str,
    value: Any,
    context_variables: Any,
    replace: bool = False,
) -> ReplyResult:
    """
    • If `replace=True` → hard-overwrite the existing value
    • Otherwise the operation adapts to the current value-type:

        ─ list   → append / extend
        ─ dict   → update
        ─ scalar → replace

    • Type-mismatch raises a clear error instead of silently mutating types.
    """
    orchard, _, entry = find_entry(context_variables, agent_name, technical_name)

    current = entry.data.get(key)
    if current is None or replace:
        entry.data[key] = value

    else:
        # ---------- LIST ----------
        if isinstance(current, list):
            if isinstance(value, list):
                current.extend(value)
            else:
                current.append(value)

        # ---------- DICT ----------
        elif isinstance(current, dict):
            if not isinstance(value, dict):
                raise TypeError(
                    f"{agent_name}.{technical_name}.{key} expects dict; got {type(value).__name__}"
                )
            current.update(value)

        # ---------- SCALAR ----------
        else:
            if isinstance(current, type(value)):
                entry.data[key] = value
            else:
                raise TypeError(
                    f"{agent_name}.{technical_name}.{key} expects {type(current).__name__}; got {type(value).__name__}"
                )

    context_variables["orchestration_context"] = orchard  # re-assign for clarity
    return ReplyResult(
        message=f"(Tool) Updated {agent_name}.{technical_name}.{key} -> {entry.data[key]}",
        context_variables=context_variables,
    )

