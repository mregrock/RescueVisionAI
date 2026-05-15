from pathlib import Path

SERVICE_NAME = "rescue-vision-ai"
SERVICE_VERSION = "0.1.0"

CORS_ORIGINS = ["*"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROTOCOLS_PATH = PROJECT_ROOT / "protocols.json"
