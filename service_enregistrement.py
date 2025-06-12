import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
import json
import math
import time

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "SAE24/simulation/ultrason"

DB_HOST = 'localhost'
DB_DATABASE = 'sae24_simulation'
DB_USER = 'root'
DB_PASSWORD = ''

SENSORS = {
    'A': (0.25, 0.25),
    'B': (0.25, 7.75),
    'C': (7.75, 7.75)
}

current_distances = {}

def trilateration(distances):
    try:
        x1, y1 = SENSORS['A']
        x2, y2 = SENSORS['B']
        x3, y3 = SENSORS['C']

        r1 = distances['A']
        r2 = distances['B']
        r3 = distances['C']

        A = 2 * (x2 - x1)
        B = 2 * (y2 - y1)
        C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
        D = 2 * (x3 - x2)
        E = 2 * (y3 - y2)
        F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2

        denominator = A * E - B * D
        if abs(denominator) < 1e-10:
            print("Warning: Trilateration denominator is close to zero. Sensors might be collinear.")
            return None

        x = (C * E - F * B) / denominator
        y = (A * F - D * C) / denominator

        return (x, y)
    except Exception as e:
        print(f"An error occurred during trilateration: {e}")
        return None

def save_to_db(distances, estimated_pos):
    try:
        connection = mysql.connector.connect(host=DB_HOST,
                                             database=DB_DATABASE,
                                             user=DB_USER,
                                             password=DB_PASSWORD)
        if connection.is_connected():
            cursor = connection.cursor()
            
            query = """INSERT INTO enregistrements (dist_a, dist_b, dist_c, pos_x_estimee, pos_y_estimee) 
                       VALUES (%s, %s, %s, %s, %s)"""
            
            record = (
                distances.get('A'), 
                distances.get('B'), 
                distances.get('C'),
                estimated_pos[0],
                estimated_pos[1]
            )
            
            cursor.execute(query, record)
            connection.commit()
            print(f"✅ Data saved to DB: Pos=({estimated_pos[0]:.2f}, {estimated_pos[1]:.2f})")

    except Error as e:
        print(f"Error while connecting to MySQL or saving data: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect, return code {rc}\n")

def on_message(client, userdata, msg):
    global current_distances
    
    try:
        payload = json.loads(msg.payload.decode())
        sensor_id = payload.get("sensorId")
        distance = payload.get("distance")

        if sensor_id and isinstance(distance, (int, float)):
            print(f"   -> Received distance {distance:.2f}m from Sensor {sensor_id}")
            current_distances[sensor_id] = distance

        if 'A' in current_distances and 'B' in current_distances and 'C' in current_distances:
            print("--- All 3 distances received, performing trilateration... ---")
            
            estimated_position = trilateration(current_distances)
            
            if estimated_position:
                save_to_db(current_distances, estimated_position)
            
            current_distances = {}
            print("--- Waiting for next set of data ---")

    except json.JSONDecodeError:
        print(f"Warning: Received a malformed JSON message on topic {msg.topic}")
    except Exception as e:
        print(f"An error occurred in on_message: {e}")

def run_service():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, client_id="db_logger_service")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Could not connect to MQTT Broker at {MQTT_BROKER}. Please ensure it's running. Error: {e}")
        return

    client.loop_forever()

if __name__ == '__main__':
    run_service()