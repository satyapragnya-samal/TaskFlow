from extensions import db
from models import Notification

def send_notification(user_id, title, message, link=None):
    """Creates a notification record in MySQL for the target user."""
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to generate notification: {e}")