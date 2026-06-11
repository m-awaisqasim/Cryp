import json
import os
import subprocess
import urllib.request


WEBBRIDGE_URL = "http://127.0.0.1:10086"
WEBBRIDGE_BIN = os.path.expanduser("~/.kimi-webbridge/bin/kimi-webbridge")


def _command(action: str, args: dict = None, session: str = "cryp-task") -> str:
    payload = json.dumps({
        "action": action,
        "args": args or {},
        "session": session,
    }).encode()
    req = urllib.request.Request(
        f"{WEBBRIDGE_URL}/command",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        if data.get("ok"):
            result = data.get("data", {})
            return json.dumps(result, indent=2)
        return f"WebBridge error: {data}"
    except Exception as e:
        return f"WebBridge failed: {e}"


def webbridge_tool(parameters: dict, player=None) -> str:
    action = parameters.get("action", "navigate")
    args = {k: v for k, v in parameters.items() if k != "action"}
    session = parameters.get("session", "cryp-task")

    if action == "status":
        try:
            r = subprocess.run(
                [WEBBRIDGE_BIN, "status"],
                capture_output=True, text=True, timeout=10,
            )
            return r.stdout or r.stderr or "Status unavailable."
        except Exception as e:
            return f"Status check failed: {e}"

    return _command(action, args, session)
