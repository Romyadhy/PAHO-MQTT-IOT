# PAHO-MQTT-IOT Python Scripts

This repository contains a collection of Python scripts for testing and running MQTT-based IoT solutions. The code is organized in a separated way to help you test publisher, subscriber, and Telegram bot integration for real-time monitoring and control of IoT devices (such as water level sensors).

## Folder Contents

- `pub.py` — MQTT Publisher and Telegram Bot integration. Allows sending commands to devices via MQTT and Telegram.
- `sub.py` — MQTT Subscriber with MySQL and Telegram integration. Receives sensor data, stores it in a database, and can notify via Telegram.
- `bot_telegram_mqtt_fixed.py` — Example of a fixed Telegram bot integrated with MQTT for advanced use cases.
- `getTemperature.py`, `tescalibrator.py`, `tesdanyap.py`, `teshalohalo.py`, `testdscal.py` — Additional test scripts for various IoT scenarios.
- `WATER-LEVEL-MQTT.ino` — Example Arduino/ESP code for the water level sensor (for reference).

## Requirements

- Python 3.8+
- MQTT Broker (e.g., Mosquitto)
- MySQL Server (for `sub.py`)
- Telegram Bot (create via BotFather and get the token)
- Required Python packages:
  - `paho-mqtt`
  - `python-telegram-bot`
  - `mysql-connector-python`

Install dependencies:
```bash
pip install paho-mqtt python-telegram-bot mysql-connector-python
```

## Usage

### 1. MQTT Publisher (`pub.py`)
- Publishes commands to the MQTT broker.
- Can be controlled via Telegram bot commands (e.g., `/send LED_ON`).
- Edit the broker IP, port, and Telegram token as needed.

### 2. MQTT Subscriber (`sub.py`)
- Subscribes to sensor data topics.
- Stores received data in MySQL.
- Sends real-time updates to Telegram users (if configured).
- Edit the broker IP, database credentials, and Telegram token as needed.

### 3. Real-Time Monitoring
- Use the Telegram bot to subscribe for real-time updates.
- The subscriber will push new sensor data to your Telegram chat.

### 4. Additional Scripts
- Use the other Python scripts for specific IoT tests or experiments as needed.

### 5. Arduino/ESP Code
- Use `WATER-LEVEL-MQTT.ino` as a reference for your device firmware to publish sensor data to the MQTT broker.

## Example Workflow
1. Start your MQTT broker and MySQL server.
2. Run `sub.py` to listen for sensor data and enable Telegram notifications.
3. Run `pub.py` to send commands via MQTT or Telegram.
4. Use your IoT device (with the provided `.ino` code) to publish sensor data.
5. Monitor data and control devices in real-time via Telegram.

## Notes
- All scripts are separated for modular testing and learning.
- Adjust IP addresses, tokens, and credentials to match your environment.
- For production, consider improving security and error handling.

---

**Author:** Romyadhy

**License:** MIT
