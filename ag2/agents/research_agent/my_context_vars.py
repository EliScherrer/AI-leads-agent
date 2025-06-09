# my_context_vars.py

from typing import Any
from autogen.agentchat.group import ContextVariables as _CV
from agents.research_agent.schemas import OrchestrationContext

class StrictContextVariables(_CV):
    """
    A specialized ContextVariables that enforces:

    - key 'orchestration_context' must exist
    - it must always be an OrchestrationContext instance
    - it cannot be deleted
    """

    _KEY = "orchestration_context"

    @staticmethod
    def _validate(val: Any) -> OrchestrationContext:
        if not isinstance(val, OrchestrationContext):
            raise TypeError(
                f"`{StrictContextVariables._KEY}` must be an OrchestrationContext, got {type(val).__name__}"
            )
        return val

    def __setitem__(self, key: str, value: Any) -> None:
        if key == self._KEY:
            value = self._validate(value)
        super().__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        if key == self._KEY:
            raise KeyError(f"'{self._KEY}' may not be deleted")
        super().__delitem__(key)

    @classmethod
    def new(cls, orch_ctx: OrchestrationContext) -> "StrictContextVariables":
        cv = cls()
        cv[cls._KEY] = orch_ctx
        return cv
