"""/notifications: the logged-in user's messages (the Messages page and the unread badge)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from core import notify
from database import get_db
from models import Notification, User
from schemas import CountOut, InboxOut
from security import get_current_user

router = APIRouter()


@router.get("/me", response_model=InboxOut)
def my_messages(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Sent messages newest first, scheduled ones soonest first, and how many sent ones are unread."""
    mine = select(Notification).where(Notification.recipient_id == user.user_id)
    sent = db.scalars(mine.where(Notification.status == "sent").order_by(Notification.sent_at.desc())).all()
    scheduled = db.scalars(mine.where(Notification.status == "pending").order_by(Notification.scheduled_at)).all()
    return {"sent": sent, "scheduled": scheduled, "unread_count": sum(1 for n in sent if not n.read)}


@router.post("/read-all", response_model=CountOut)
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"count": notify.mark_all_read(db, user)}


@router.post("/send-now", response_model=CountOut)
def send_now(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Demo shortcut: send this user's scheduled messages immediately instead of waiting."""
    return {"count": notify.send_now_for(db, user)}
