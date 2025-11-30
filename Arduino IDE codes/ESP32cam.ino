#include "esp_camera.h"
#include <WiFi.h>
#include <WebSocketsClient.h>

// WiFi credentials
const char* ssid = "Password dibo na";
const char* password = "mone nai";

// WebSocket server info
const char* ws_server_host = "192.168.68.101";
const uint16_t ws_server_port = 8000;
const char* ws_server_path = "/ws/camera/";

// WebSocket client
WebSocketsClient webSocket;

// Camera pin config
#define PWDN_GPIO_NUM    32
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27
#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22

void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;  // QVGA: 320x240
  config.jpeg_quality = 15;
  config.fb_count = 1;

  esp_camera_init(&config);
}

// WebSocket event handler
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      Serial.println("WebSocket connected!");
      break;
    case WStype_DISCONNECTED:
      Serial.println("WebSocket disconnected.");
      break;
    case WStype_ERROR:
      Serial.println("WebSocket error.");
      break;
  }
}

void setup() {
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nWiFi connected!");

  // Initialize camera
  setupCamera();

  // Connect to WebSocket server
  webSocket.begin(ws_server_host, ws_server_port, ws_server_path);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);  // auto-reconnect every 5s
}

void loop() {
  // Handle WebSocket
  webSocket.loop();

  // Only send frame if WebSocket is connected
  if (webSocket.isConnected()) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      return;
    }

    // Send JPEG frame as binary
    webSocket.sendBIN(fb->buf, fb->len);

    // Return the frame buffer
    esp_camera_fb_return(fb);

    delay(100);  // ~10 FPS
  }
}