from app.models.models import Message
from fastapi import APIRouter, HTTPException, Body, Query
from firebase_admin import firestore
from fastapi.responses import JSONResponse

db = firestore.client()
chat_router = APIRouter()

@chat_router.post("/messages", tags=["Chat"])
async def save_message(message: Message = Body(...)):
    """
    Send a message (stores in Firestore under 'messages').
    """
    try:
        db.collection("messages").add(message.dict())
        return {"message": "Message sent successfully", "data": message.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e}")


@chat_router.get("/messages", tags=["Chat"])
async def get_conversation(user1: str = Query(...), user2: str = Query(...)):
    """
    Fetch all messages between two users (sorted by timestamp).
    """
    try:
        messages_ref = db.collection("messages")
        query = messages_ref.where("sender", "in", [user1, user2]).where("receiver", "in", [user1, user2])
        results = query.stream()

        messages = [doc.to_dict() for doc in results]
        messages = sorted(messages, key=lambda x: x["timestamp"])

        return {"conversation": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {e}")


@chat_router.get("/user-messages", tags=["Chat"])
async def get_conversation(user1: str = Query(...)):
    """
    Fetch all user messages (sorted by timestamp).
    """
    try:
        messages_ref = db.collection("messages")
        query = messages_ref.where("receiver", "in", [user1])
        results = query.stream()

        messages = [doc.to_dict() for doc in results]
        messages = sorted(messages, key=lambda x: x["timestamp"])

        return {"conversation": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {e}")


@chat_router.put("/messages/read", tags=["Chat"])
async def mark_as_read(sender: str = Query(...), receiver: str = Query(...)):
    """
    Mark all messages as read between two users.
    """
    try:
        query = db.collection("messages").where("sender", "==", sender).where("receiver", "==", receiver).where("isRead", "==", False)
        for doc in query.stream():
            doc_ref = db.collection("messages").document(doc.id)
            doc_ref.update({"isRead": True})

        return {"message": "Messages marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update messages: {e}")


@chat_router.delete("/messages", tags=["Chat"])
async def delete_messages(user1: str = Query(None), user2: str = Query(None), message_id: str = Query(None)):
    """
    Delete messages:
    - If `message_id` is provided, delete that specific message.
    - If `user1` and `user2` are provided, delete all messages between them.
    """
    try:
        if message_id:
            # Delete specific message by ID
            doc_ref = db.collection("messages").document(message_id)
            if doc_ref.get().exists:
                doc_ref.delete()
                return {"message": f"Message {message_id} deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail=f"Message {message_id} not found")

        elif user1 and user2:
            # Delete all conversation messages
            query = db.collection("messages").where("sender", "in", [user1, user2]).where("receiver", "in", [user1, user2])
            deleted_count = 0
            for doc in query.stream():
                db.collection("messages").document(doc.id).delete()
                deleted_count += 1
            return {"message": f"Deleted {deleted_count} messages between {user1} and {user2}"}
        else:
            raise HTTPException(status_code=400, detail="Provide either message_id or both user1 and user2")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete messages: {e}")
