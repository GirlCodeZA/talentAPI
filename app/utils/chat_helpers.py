from app.models.models import Message
from firebase_admin import firestore
from datetime import datetime
import uuid

db = firestore.client()

async def save_message(sender: str, receiver: str, content: str):
    """
    Saves a message to Firestore.
    Used for both chat and system-generated messages (like welcome emails).
    """
    message = Message(
        id=str(uuid.uuid4()),
        sender=sender,
        receiver=receiver,
        content=content,
        timestamp=datetime.utcnow(),
        isRead=False
    )

    db.collection("messages").add(message.dict())
    return message.dict()
