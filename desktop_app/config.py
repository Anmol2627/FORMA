import os

APP_NAME = "FORMA"
WINDOW_TITLE = "FORMA | Learn in small steps"
WINDOW_WIDTH = 1240
WINDOW_HEIGHT = 760
MIN_WIDTH = 1000
MIN_HEIGHT = 650

# API Configuration
API_BASE_URL = os.getenv("FORMA_API_BASE_URL", "http://127.0.0.1:5000/api/v1").rstrip("/")
API_TIMEOUT_SECONDS = int(os.getenv("FORMA_API_TIMEOUT", "15"))
