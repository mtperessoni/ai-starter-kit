"""NTF-01 to NTF-05: the record of a notification that was sent."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Notification:
    notification_id: str
    template: str
    recipient: str
    order_id: str | None
    subject: str
    sent_at: datetime
