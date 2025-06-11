#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

Servo myServo;
WebServer server(80);

const char* ssid = "Mcp";
const char* password = "12345678";

void setup() {
  Serial.begin(115200);
  myServo.attach(4); // GPIO 18'e bağlı servo
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("WiFi'ye bağlanıyor...");
  }
  
  Serial.println("IP: " + WiFi.localIP().toString());
  
  // API endpoint'leri
  server.on("/servo", HTTP_POST, handleServo);
  server.on("/servo/status", HTTP_GET, getServoStatus);
  
  server.begin();
}

void handleServo() {
  if (server.hasArg("angle")) {
    int angle = server.arg("angle").toInt();
    if (angle >= 0 && angle <= 180) {
      myServo.write(angle);
      server.send(200, "application/json", 
        "{\"status\":\"success\",\"angle\":" + String(angle) + "}");
    } else {
      server.send(400, "application/json", 
        "{\"status\":\"error\",\"message\":\"Açı 0-180 arası olmalı\"}");
    }
  }
}

void getServoStatus() {
  int currentAngle = myServo.read();
  server.send(200, "application/json", 
    "{\"current_angle\":" + String(currentAngle) + "}");
}

void loop() {
  server.handleClient();
}