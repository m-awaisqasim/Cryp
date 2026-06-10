# config/__init__.py
from config.settings import GEMINI_API_KEY, OS_SYSTEM

def get_config() -> dict:
    return {
        "gemini_api_key": GEMINI_API_KEY,
        "os_system": OS_SYSTEM
    }

def get_os() -> str:
    return OS_SYSTEM

def is_windows() -> bool: return OS_SYSTEM == "windows"
def is_mac()     -> bool: return OS_SYSTEM == "darwin"
def is_linux()   -> bool: return OS_SYSTEM == "linux"