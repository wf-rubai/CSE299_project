import base64
from channels.generic.websocket import AsyncWebsocketConsumer

# Keep track of all connected browsers
connected_browsers = set()

class CameraConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        connected_browsers.add(self)
        print(f"Browser connected! Total: {len(connected_browsers)}")

    async def disconnect(self, close_code):
        connected_browsers.discard(self)
        print(f"Browser disconnected. Total: {len(connected_browsers)}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive data from ESP32 (binary) or other clients
        and broadcast to all connected browsers.
        """
        if bytes_data:
            # Convert JPEG bytes to Base64
            frame_base64 = base64.b64encode(bytes_data).decode('utf-8')
            await self.broadcast(frame_base64)

    async def broadcast(self, frame_base64):
        for browser in connected_browsers.copy():
            try:
                await browser.send(text_data=frame_base64)
            except:
                # If a browser disconnected, remove it
                connected_browsers.discard(browser)