from datetime import datetime
from app.firebase import db

async def log_error(message: str, context: dict = None):
    log_entry = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "context": context or {},
    }
    db.collection("logs").add(log_entry)
