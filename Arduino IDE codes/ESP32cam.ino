#include "esp_camera.h"
#include <WiFi.h>
#include <WebSocketsClient.h>

// ============================
// WiFi credentials
// ============================
const char* ssid = "TPP242";
const char* password = "11223344";

// ============================
// WebSocket server info
// ============================
const char* ws_server_host = "10.162.211.102";  // 🔁 CHANGE if server IP changes
const uint16_t ws_server_port = 8000;           // 🔁 CHANGE if port changes
const char* ws_server_path = "/ws/camera/";

// WebSocket client
WebSocketsClient webSocket;

// ============================
// Camera pin config (AI-Thinker)
// ============================
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

// ============================
// Camera Setup
// ============================
void setupCamera() {
  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk  = XCLK_GPIO_NUM;
  config.pin_pclk  = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href  = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn  = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  // ============================
  // 🔧 PERFORMANCE TUNING (CHANGE HERE)
  // ============================

  config.xclk_freq_hz = 20000000;      // Camera clock (20 MHz stable)
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size = FRAMESIZE_QQVGA; // ✅ 160x120 (VERY FAST)
  // Other options you can try:
  // FRAMESIZE_QQVGA2 (128x160)
  // FRAMESIZE_QCIF   (176x144)
  // FRAMESIZE_QVGA   (320x240)  <-- slower

  config.jpeg_quality = 63;            // ✅ LOW QUALITY (0 = best, 63 = worst)
  // Try 30–40 if you want better quality

  config.fb_count = 1;                 // Single frame buffer → low latency

  // ============================
  // Init camera
  // ============================
  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed!");
    ESP.restart();
  }
}

// ============================
// WebSocket Event Handler
// ============================
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  if (type == WStype_CONNECTED) {
    Serial.println("WebSocket connected");
  } else if (type == WStype_DISCONNECTED) {
    Serial.println("WebSocket disconnected");
  }
}

void setup() {
  Serial.begin(115200);

  // ============================
  // Connect WiFi
  // ============================
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nWiFi connected");
  Serial.println(WiFi.localIP());

  // Init camera
  setupCamera();

  // Connect WebSocket
  webSocket.begin(ws_server_host, ws_server_port, ws_server_path);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(3000);
}

void loop() {
  webSocket.loop();

  if (!webSocket.isConnected()) return;

  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) return;

  webSocket.sendBIN(fb->buf, fb->len);
  esp_camera_fb_return(fb);

  // ============================
  // ⏱ FPS CONTROL (CHANGE HERE)
  // ============================
  delay(25);   // ✅ 25 ms ≈ 40 FPS
}
