"""WebSocket consumer for real-time notification delivery."""
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebSocketConsumer

logger = logging.getLogger("agents")


class NotificationConsumer(AsyncJsonWebSocketConsumer):
    """Delivers real-time notifications to connected users.

    Clients connect to ``ws://<host>/ws/notifications/`` with a valid
    session cookie (Django session auth via ``AuthMiddlewareStack``).

    The consumer joins a per-user channel group so that any backend code
    can broadcast a notification via ``channel_layer.group_send``.
    """

    async def connect(self):
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.close(code=4001)
            return

        self.group_name = f"notifications_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send initial unread count on connect.
        count = await self._unread_count(user)
        await self.send_json({"type": "unread_count", "count": count})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """Handle client messages — currently supports mark-read requests."""
        action = content.get("action")
        user = self.scope["user"]

        if action == "mark_read":
            notification_id = content.get("id")
            updated = await self._mark_read(user, notification_id)
            await self.send_json({"type": "marked_read", "id": notification_id, "updated": updated})
            count = await self._unread_count(user)
            await self.send_json({"type": "unread_count", "count": count})

    # ── Group-send handlers (called via channel_layer.group_send) ─────

    async def notification_new(self, event):
        """Push a new notification to the client."""
        await self.send_json({
            "type": "new_notification",
            "notification": event["notification"],
        })

    async def notification_count(self, event):
        """Push an updated unread count to the client."""
        await self.send_json({
            "type": "unread_count",
            "count": event["count"],
        })

    # ── Database helpers ──────────────────────────────────────────────

    @database_sync_to_async
    def _unread_count(self, user):
        from .models import Notification
        return Notification.objects.filter(owner=user, read=False).count()

    @database_sync_to_async
    def _mark_read(self, user, notification_id=None):
        from .models import Notification
        qs = Notification.objects.filter(owner=user)
        if notification_id:
            qs = qs.filter(id=notification_id)
        return qs.update(read=True)
