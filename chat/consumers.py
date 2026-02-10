import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from chat.models import Conversation

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        if not user or isinstance(user, AnonymousUser):
            await self.close(code=4001)
            return

        self.convo_id = self.scope["url_route"]["kwargs"]["convo_id"]
        self.rm_id = await self.get_rm_id(user)

        allowed = await self.user_can_access(user, self.convo_id)
        if not allowed:
            await self.close(code=4003)
            return

        # ✅ CHAT ONLY
        await self.channel_layer.group_add(
            f"chat_{self.convo_id}",
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            f"chat_{self.convo_id}",
            self.channel_name
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def message_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "message_status",
            "message_id": event["message_id"],
            "status": event["status"],
        }))

    @database_sync_to_async
    def get_rm_id(self, user):
        return user.rm.id

    @database_sync_to_async
    def user_can_access(self, user, convo_id):
        return Conversation.objects.filter(
            id=convo_id,
            rm__user=user
        ).exists()

from channels.db import database_sync_to_async

class InboxConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        if not user or isinstance(user, AnonymousUser):
            await self.close(code=4001)
            return

        # ✅ SAFE ORM access
        self.rm_id = await self.get_rm_id(user)

        await self.channel_layer.group_add(
            f"inbox_rm_{self.rm_id}",
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            f"inbox_rm_{self.rm_id}",
            self.channel_name
        )

    async def inbox_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "inbox_update",
            "conversation_id": event["conversation_id"],
            "preview": event.get("preview"),
            "unread": event.get("unread", 0),
            "notify": event.get("notify", False),
        }))

    # ✅ THIS IS THE FIX
    @database_sync_to_async
    def get_rm_id(self, user):
        return user.rm.id
