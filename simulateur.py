import paho.mqtt.client as mqtt
import time
import math
import json
import random

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "SAE24/simulation/ultrason"
ROOM_WIDTH = 8.0
ROOM_HEIGHT = 8.0
SENSORS = {'A': (0.25, 0.25), 'B': (0.25, 7.75), 'C': (7.75, 7.75)}
MOVE_SPEED = 1.0
UPDATE_INTERVAL = 0.5
NOISE_LEVEL = 0.05

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker successfully!")
    else:
        print(f"Failed to connect, return code {rc}")

def run_simulation():
    client = mqtt.Client(client_id="simulation_publisher")
    client.on_connect = on_connect
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except ConnectionRefusedError:
        print("Connection to MQTT broker refused. Is the broker running?")
        return
    client.loop_start()
    
    print("Starting simulation with random walk...")
    start_point = (random.uniform(2, 6), random.uniform(2, 6))

    while True:
        target_point = (random.uniform(1, ROOM_WIDTH - 1), random.uniform(1, ROOM_HEIGHT - 1))
        print(f"New random destination: ({target_point[0]:.2f}, {target_point[1]:.2f})")
        distance_to_target = calculate_distance(start_point, target_point)

        if distance_to_target > 0:
            direction_vector = ((target_point[0] - start_point[0]) / distance_to_target, (target_point[1] - start_point[1]) / distance_to_target)
            steps_in_segment = int(distance_to_target / (MOVE_SPEED * UPDATE_INTERVAL))
            for step in range(steps_in_segment + 1):
                current_pos_x = start_point[0] + direction_vector[0] * MOVE_SPEED * UPDATE_INTERVAL * step
                current_pos_y = start_point[1] + direction_vector[1] * MOVE_SPEED * UPDATE_INTERVAL * step
                current_position = (current_pos_x, current_pos_y)
                for sensor_id, sensor_pos in SENSORS.items():
                    dist = calculate_distance(current_position, sensor_pos)
                    noisy_dist = dist + random.uniform(-NOISE_LEVEL, NOISE_LEVEL)
                    payload = json.dumps({"sensorId": sensor_id, "distance": round(noisy_dist, 4)})
                    client.publish(MQTT_TOPIC, payload)
                print(f"Simulated Pos: ({current_pos_x:.2f}, {current_pos_y:.2f}) -> Published 3 sensor distances")
                time.sleep(UPDATE_INTERVAL)
        start_point = target_point

if __name__ == '__main__':
    run_simulation()