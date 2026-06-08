import time

try:
    import psutil
except ImportError:
    psutil = None


def jarvis_status(parameters: dict, player=None) -> str:
    query = parameters.get("query", "status").lower()
    if "version" in query or "mark" in query:
        return _get_version()
    elif "memory" in query or "remember" in query:
        return _get_memory_stats()
    elif "status" in query or "health" in query:
        return _get_full_status()
    elif "activity" in query or "today" in query:
        return _get_today_activity()
    elif "uptime" in query or "running" in query:
        return _get_uptime()
    elif "capability" in query or "capabilities" in query or "what can" in query:
        return _get_capabilities()
    else:
        return _get_full_status()


def _get_version() -> str:
    return (
        "Mark Thirty-Nine, sir. Cryp V2, "
        "running on Gemini 2.5 Flash Native Audio. "
        "Built on Ubuntu by Awais."
    )


def _get_memory_stats() -> str:
    try:
        from memory.memory_manager import load_memory, load_recent_episodes
        mem = load_memory()
        total_facts = sum(
            len(v) for v in mem.values()
            if isinstance(v, dict)
        )
        episodes = load_recent_episodes(n=100)
        return (
            f"I have {total_facts} stored facts across "
            f"{len(mem)} memory categories, "
            f"and {len(episodes)} conversation episodes "
            f"on record, sir."
        )
    except Exception as e:
        return f"Memory stats unavailable: {e}"


def _get_full_status() -> str:
    try:
        cpu = psutil.cpu_percent(interval=0)
        mem = psutil.virtual_memory()
        dsk = psutil.disk_usage("/")
        bat = psutil.sensors_battery()
        bat_str = ""
        if bat is not None:
            state = "charging" if bat.power_plugged else "discharging"
            bat_str = f"Battery at {int(bat.percent)}% and {state}. "
        from memory.memory_manager import load_memory
        mem_data = load_memory()
        total_facts = sum(
            len(v) for v in mem_data.values()
            if isinstance(v, dict)
        )
        return (
            f"All systems operational, sir. "
            f"CPU at {int(cpu)}%, RAM at {int(mem.percent)}%, "
            f"disk at {int(dsk.percent)}%. "
            f"{bat_str}"
            f"{total_facts} facts in memory. "
            f"Running Phase 4 intelligence stack."
        )
    except Exception as e:
        return f"Status check failed: {e}"


def _get_today_activity() -> str:
    try:
        from memory.memory_manager import load_recent_episodes
        from datetime import date
        today = str(date.today())
        episodes = load_recent_episodes(n=10)
        today_eps = [
            ep for ep in episodes
            if ep.get("started_at", "").startswith(today)
        ]
        if not today_eps:
            return "No activity recorded today yet, sir."
        tools_today = []
        for ep in today_eps:
            tools_today.extend(ep.get("tools_used", []))
        unique_tools = list(dict.fromkeys(tools_today))
        total_turns = sum(
            ep.get("user_turns", 0) for ep in today_eps
        )
        return (
            f"Today's activity: {len(today_eps)} session(s), "
            f"{total_turns} exchanges. "
            f"Tools used: {', '.join(unique_tools[:5]) if unique_tools else 'none'}."
        )
    except Exception as e:
        return f"Activity data unavailable: {e}"


def _get_uptime() -> str:
    try:
        boot_time = psutil.boot_time()
        uptime_secs = time.time() - boot_time
        hours = int(uptime_secs // 3600)
        minutes = int((uptime_secs % 3600) // 60)
        return (
            f"System has been running for "
            f"{hours} hours and {minutes} minutes, sir."
        )
    except Exception as e:
        return f"Uptime unavailable: {e}"


def _get_capabilities() -> str:
    return (
        "I can control your computer, browse the web via "
        "Kimi WebBridge, manage files, write and run code, "
        "search the web, control applications, send messages, "
        "monitor your system, remember facts across sessions, "
        "execute multi-step tasks via ReAct reasoning, "
        "and give you proactive briefings and suggestions. "
        "Ask me anything, sir."
    )
