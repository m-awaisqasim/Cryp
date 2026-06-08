import threading
from typing import Callable

from core.logger import get_logger

log = get_logger(__name__)


class AgentExecutor:

    def execute(
        self,
        goal:        str,
        speak:       Callable | None        = None,
        cancel_flag: threading.Event | None = None,
    ) -> str:
        msg = (
            "AgentExecutor is deprecated. The agent_task tool now runs "
            "the ReAct loop directly. See agent/react_loop.py."
        )
        log.warning("agent_executor_deprecated", message=msg)
        if speak:
            speak("The legacy agent executor is no longer used, sir.")
        return msg
