import os
import sys
from pathlib import Path

# Ensure root workspace directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app import create_app  # noqa: E402
# Import models so Alembic / Flask-Migrate detects them

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
