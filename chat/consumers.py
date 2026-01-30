import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from chat.models import Conversation


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = None  # ✅ IMPORTANT

        user = self.scope.get("user")

        # 🔒 Auth check
        if not user or isinstance(user, AnonymousUser):
            await self.close(code=4001)
            return

        self.convo_id = self.scope["url_route"]["kwargs"]["convo_id"]

        # 🔒 Permission check
        allowed = await self.user_can_access(user, self.convo_id)
        if not allowed:
            await self.close(code=4003)
            return

        self.group_name = f"chat_{self.convo_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # ✅ SAFE cleanup
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def user_can_access(self, user, convo_id):
        return Conversation.objects.filter(
            id=convo_id,
            rm__user=user
        ).exists()
