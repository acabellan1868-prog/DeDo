"""Variables de entorno de DeDo."""

import os

RUTA_BD = os.getenv("DEDO_DB_PATH", "data/dedo.db")
NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
FIDO_API_URL = os.getenv("FIDO_API_URL", "")
