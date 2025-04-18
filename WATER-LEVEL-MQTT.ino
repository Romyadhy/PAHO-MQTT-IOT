#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h> 

const char* ssid = "SGG UNDIKSHA";        
const char* password = "smartgreengarden";
const char* mqtt_server = "192.168.21.44";

WiFiClient espClient;
PubSubClient client(espClient);

const int waterLevelPin = 34;  
const int ledPin = 12;

void setup_wifi() {
  Serial.println("🔗 Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Connected to WiFi!");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("🔄 Connecting to MQTT...");
    if (client.connect("ESP32Client")) {
      Serial.println("✅ Connected!");
      client.subscribe("sensor/waterlevel"); 
    } else {
      Serial.print("❌ Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 5s...");
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("📩 Received message: ");
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  if (message == "1") {
    Serial.println("💡 Turning LED ON");
    digitalWrite(ledPin, HIGH);
  } else if (message == "0") {
    Serial.println("💡 Turning LED OFF");
    digitalWrite(ledPin, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(waterLevelPin, INPUT);
  pinMode(ledPin, OUTPUT); 

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  int sensorValue = analogRead(waterLevelPin);
  Serial.print("📊 Water Level: ");
  Serial.println(sensorValue);

  String waterLevel;
  if (sensorValue <= 500) {
    waterLevel = "Empty";
  } else if (sensorValue > 500 && sensorValue <= 1500) {
    waterLevel = "Low";
  } else if (sensorValue > 1500 && sensorValue <= 2500) {
    waterLevel = "Medium";
  } else {
    waterLevel = "High";
  }

  // 🔹 Buat objek JSON
  StaticJsonDocument<200> doc;
  doc["sensor_value"] = sensorValue;
  doc["status"] = waterLevel;

  // 🔹 Konversi JSON ke string
  char buffer[256];
  serializeJson(doc, buffer);

  Serial.print("📤 Sending JSON: ");
  Serial.println(buffer);

  // 🔹 Kirim JSON ke MQTT
  client.publish("sensor/waterlevel", buffer);

  delay(10000);
}
