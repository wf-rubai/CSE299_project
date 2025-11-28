import base64
from channels.generic.websocket import AsyncWebsocketConsumer

class CameraConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        # bytes_data is the JPEG frame from ESP32
        if bytes_data:
            # Convert to base64 for HTML display
            frame_base64 = base64.b64encode(bytes_data).decode('utf-8')
            await self.send(text_data=frame_base64)
