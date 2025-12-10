import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Frontend łączy się pod: ws://localhost:8000/ws/notifications/
        # Możemy tu dodać logikę grup, np. dla konkretnego usera
        self.group_name = "global_notifications"

        # Dołącz do grupy
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Opuść grupę
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Handler otrzymania wiadomości z "wnętrza" backendu (od Celery)
    async def task_update(self, event):
        message = event["message"]
        
        # Wyślij wiadomość do Frontendu (WebSocket)
        await self.send(text_data=json.dumps({
            "type": "task_update",
            "data": message
        }))