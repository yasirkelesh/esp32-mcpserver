#include <WiFi.h>
#include <WebServer.h>
#include <raspiServo.h>
#include <ArduinoJson.h> // ArduinoJson kütüphanesini dahil et

// --- Sabitler ---
// Kodun başında sabitleri tanımlamak, yönetimi kolaylaştırır.
const char* WIFI_SSID = "wifi";
const char* WIFI_PASSWORD = "12345678";
const int SERVO_PIN = 18;
const int BAUD_RATE = 115200;
const int SERVER_PORT = 80;

// --- Nesneler ---
Servo myServo;
WebServer server(SERVER_PORT);

void setup() {
  Serial.begin(BAUD_RATE);
  myServo.attach(SERVO_PIN);
  
  // WiFi Bağlantısı
  Serial.print("WiFi'ye bağlanıyor...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nBağlantı başarılı!");
  Serial.print("IP Adresi: ");
  Serial.println(WiFi.localIP());
  
  // API endpoint'leri (Rotalar)
  server.on("/servo", HTTP_POST, handleServo);
  server.on("/servo/status", HTTP_GET, getServoStatus);
  
  server.begin();
  Serial.println("HTTP sunucusu başlatıldı.");
}

// Servo motorunu kontrol eden fonksiyon
void handleServo() {
  // ArduinoJson ile verimli JSON oluşturma
  StaticJsonDocument<200> jsonResponse;
  
  if (server.hasArg("angle")) {
    int angle = server.arg("angle").toInt();
    
    if (angle >= 0 && angle <= 180) {
      myServo.write(angle);
      
      // Başarı mesajı
      jsonResponse["status"] = "success";
      jsonResponse["angle"] = angle;
      
      String response;
      serializeJson(jsonResponse, response);
      server.send(200, "application/json", response);
      
    } else {
      // Hata mesajı
      jsonResponse["status"] = "error";
      jsonResponse["message"] = "Açı 0-180 arasında olmalı";
      
      String response;
      serializeJson(jsonResponse, response);
      server.send(400, "application/json", response);
    }
  } else {
    // Argüman eksik hatası
    jsonResponse["status"] = "error";
    jsonResponse["message"] = "Gerekli 'angle' parametresi eksik.";
    
    String response;
    serializeJson(jsonResponse, response);
    server.send(400, "application/json", response);
  }
}

// Servo durumunu getiren fonksiyon
void getServoStatus() {
  StaticJsonDocument<100> jsonResponse;
  int currentAngle = myServo.read();
  
  jsonResponse["current_angle"] = currentAngle;
  
  String response;
  serializeJson(jsonResponse, response);
  server.send(200, "application/json", response);
}

void loop() {
  server.handleClient();
}