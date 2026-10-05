"""NTF-05: sending notifications once per template, order and recipient."""
from market.features.notifications.notification_models import Notification
from market.features.notifications.templates import render_subject
from market.infra import clock, ids
from market.infra.errors import ValidationError
from market.infra.repositories import repo

_REPO = "notifications"


def _already_sent(template: str, recipient: str, order_id: str) -> bool:
    return any(
        n.template == template and n.recipient == recipient and n.order_id == order_id
        for n in repo(_REPO).all()
    )


def send(template: str, recipient: str, order_id: str | None = None, **context) -> Notification | None:
    """Record a notification; returns None when NTF-05 suppresses a repeat.

    The same template for the same order and recipient goes out once. Notifications that belong
    to no order (low stock) are never deduplicated, because each one is about a different event.
    """
    if "@" not in recipient:
        raise ValidationError("recipient must be an email address")
    if order_id is not None and _already_sent(template, recipient, order_id):
        return None
    notification = Notification(
        notification_id=ids.next_id("NTF"), template=template, recipient=recipient,
        order_id=order_id, subject=render_subject(template, order_id=order_id, **context),
        sent_at=clock.now(),
    )
    repo(_REPO).add(notification.notification_id, notification)
    return notification


def list_sent(recipient: str | None = None, template: str | None = None) -> list[Notification]:
    """Sent notifications in the order they were sent, optionally filtered."""
    return [
        n for n in repo(_REPO).all()
        if (recipient is None or n.recipient == recipient)
        and (template is None or n.template == template)
    ]


def count_sent(recipient: str | None = None, template: str | None = None) -> int:
    """How many notifications match the filters."""
    return len(list_sent(recipient, template))


def last_sent(recipient: str, template: str | None = None) -> Notification | None:
    """Most recent notification to a recipient, optionally of one template."""
    sent = list_sent(recipient, template)
    return sent[-1] if sent else None


def preview(template: str, **context) -> str:
    """The subject a send would produce, without recording anything."""
    return render_subject(template, **context)


def recipients() -> list[str]:
    """Distinct recipients that received at least one notification, in first-seen order."""
    return list(dict.fromkeys(n.recipient for n in list_sent()))
