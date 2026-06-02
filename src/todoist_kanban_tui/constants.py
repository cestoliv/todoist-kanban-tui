from pathlib import Path

APP_DIR = Path.home() / ".todoist-kanban-tui"
SOCKET_PATH = APP_DIR / "refresh.sock"
PID_PATH = APP_DIR / "tui.pid"

DEFAULT_REFRESH_SECONDS = 300
