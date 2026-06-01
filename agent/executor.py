import threading
from typing import Callable


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
        print(f"[AgentExecutor] ⚠️ {msg}")
        if speak:
            speak("The legacy agent executor is no longer used, sir.")
        return msg
