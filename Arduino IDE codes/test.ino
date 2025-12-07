#include <WebServer.h>

WebServer server(80);

void handleSet() {
  if (!server.hasArg("framesize") && !server.hasArg("quality")) {
    server.send(400, "text/plain", "Missing parameters");
    return;
  }

  sensor_t* s = esp_camera_sensor_get();

  // Frame size change
  if (server.hasArg("framesize")) {
    String fs = server.arg("framesize");
    framesize_t size;

    if (fs == "QQVGA") size = FRAMESIZE_QQVGA;      // 160x120
    else if (fs == "QQVGA2") size = FRAMESIZE_QQVGA2; // 128x160
    else if (fs == "HQVGA") size = FRAMESIZE_HQVGA;  // 240x176
    else if (fs == "QVGA") size = FRAMESIZE_QVGA;    // 320x240
    else if (fs == "CIF") size = FRAMESIZE_CIF;      // 352x288
    else if (fs == "VGA") size = FRAMESIZE_VGA;      // 640x480
    else {
      server.send(400, "text/plain", "Invalid framesize");
      return;
    }

    s->set_framesize(s, size);
  }

  // Quality change
  if (server.hasArg("quality")) {
    int q = server.arg("quality").toInt();  // 10–63
    if (q < 10) q = 10;
    if (q > 63) q = 63;
    s->set_quality(s, q);
  }

  // Brightness
  if (server.hasArg("brightness")) {
    int b = server.arg("brightness").toInt();  // -2 to 2
    s->set_brightness(s, b);
  }

  // Contrast
  if (server.hasArg("contrast")) {
    int c = server.arg("contrast").toInt();  // -2 to 2
    s->set_contrast(s, c);
  }

  // Saturation
  if (server.hasArg("saturation")) {
    int sa = server.arg("saturation").toInt(); // -2 to 2
    s->set_saturation(s, sa);
  }

  server.send(200, "text/plain", "OK");
}

void startCommandServer() {
  server.on("/set", handleSet);
  server.begin();
  Serial.println("Camera control server started!");
}
