import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from .app import FormaApp
except (ImportError, ValueError):
    from app import FormaApp


def main():
    app = FormaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
