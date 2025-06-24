import paho.mqtt.client as mqtt
import time
import math
import json
import random

# --- CONFIGURATION ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# NOUVEAU : Modes possibles
# 'ultrasound' : Mode ultrason seulement
# 'sound' : Mode son seulement  
# 'both' : Alternance entre les deux modes
# 'dual' : Envoie les deux types simultanément
SIMULATION_MODE = 'both'  # Changez ici selon vos besoins

# Paramètres de la pièce et des capteurs
ROOM_WIDTH = 8.0
ROOM_HEIGHT = 8.0
SENSORS = {'A': (0.25, 0.25), 'B': (0.25, 7.75), 'C': (7.75, 7.75)}

# Paramètres de la simulation
MOVE_SPEED = 1.0
UPDATE_INTERVAL = 0.5 
NOISE_LEVEL = 0.05

# --- CONSTANTES PHYSIQUES ---
SPEED_OF_SOUND = 343.0 
SOUND_SOURCE_POWER = 100 

# Variables pour l'alternance des modes
current_mode_index = 0
modes_cycle = ['ultrasound', 'sound']

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Connecté au Broker MQTT!")
    else:
        print(f"❌ Échec de la connexion, code d'erreur {rc}")

def send_sensor_data(client, current_position, mode):
    """Envoie les données pour un mode donné"""
    print(f"  -> 📡 Envoi des données en mode: {mode.upper()}")
    
    for sensor_id, sensor_pos in SENSORS.items():
        dist = calculate_distance(current_position, sensor_pos)
        
        if mode == 'ultrasound':
            # Mode ultrason : calculer le temps de vol
            true_time = (dist / SPEED_OF_SOUND) * 2
            noisy_time = true_time + random.uniform(-NOISE_LEVEL * true_time, NOISE_LEVEL * true_time)
            payload = json.dumps({"sensorId": sensor_id, "time": round(noisy_time, 6)})
            topic = "SAE24/ultrason/temps"
            client.publish(topic, payload)
            print(f"     {sensor_id}: temps={noisy_time:.4f}s -> {topic}")

        elif mode == 'sound':
            # Mode son : calculer l'amplitude
            if dist < 0.1: dist = 0.1  # Éviter division par zéro
            true_amplitude = SOUND_SOURCE_POWER / (dist**2)
            noisy_amplitude = true_amplitude + random.uniform(-NOISE_LEVEL * true_amplitude, NOISE_LEVEL * true_amplitude)
            payload = json.dumps({"sensorId": sensor_id, "amplitude": round(noisy_amplitude, 4)})
            topic = "SAE24/son/amplitude"
            client.publish(topic, payload)
            print(f"     {sensor_id}: amplitude={noisy_amplitude:.2f} -> {topic}")

def run_simulation():
    global current_mode_index
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="advanced_simulation_publisher")
    client.on_connect = on_connect
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except ConnectionRefusedError:
        print("❌ Connexion au broker refusée. Le broker est-il en cours d'exécution ?")
        return
    client.loop_start()
    
    print(f"🚀 Démarrage de la simulation en mode: '{SIMULATION_MODE.upper()}'")
    
    if SIMULATION_MODE == 'both':
        print("🔄 Alternance automatique entre ultrason et son")
    elif SIMULATION_MODE == 'dual':
        print("🔀 Envoi simultané des deux types de données")
    
    start_point = (random.uniform(2, 6), random.uniform(2, 6))

    while True:
        target_point = (random.uniform(1, ROOM_WIDTH - 1), random.uniform(1, ROOM_HEIGHT - 1))
        print(f"\n🎯 Nouvelle destination : ({target_point[0]:.2f}, {target_point[1]:.2f})")
        distance_to_target = calculate_distance(start_point, target_point)

        if distance_to_target > 0:
            direction_vector = ((target_point[0] - start_point[0]) / distance_to_target, 
                              (target_point[1] - start_point[1]) / distance_to_target)
            steps_in_segment = int(distance_to_target / (MOVE_SPEED * UPDATE_INTERVAL))
            
            for step in range(steps_in_segment + 1):
                current_pos_x = start_point[0] + direction_vector[0] * MOVE_SPEED * UPDATE_INTERVAL * step
                current_pos_y = start_point[1] + direction_vector[1] * MOVE_SPEED * UPDATE_INTERVAL * step
                current_position = (current_pos_x, current_pos_y)
                
                print(f"📍 Position simulée: ({current_pos_x:.2f}, {current_pos_y:.2f})")

                # Décider quel(s) mode(s) utiliser
                if SIMULATION_MODE == 'ultrasound':
                    send_sensor_data(client, current_position, 'ultrasound')
                    
                elif SIMULATION_MODE == 'sound':
                    send_sensor_data(client, current_position, 'sound')
                    
                elif SIMULATION_MODE == 'both':
                    # Alternance entre les modes
                    current_mode = modes_cycle[current_mode_index]
                    send_sensor_data(client, current_position, current_mode)
                    current_mode_index = (current_mode_index + 1) % len(modes_cycle)
                    
                elif SIMULATION_MODE == 'dual':
                    # Envoyer les deux types de données
                    send_sensor_data(client, current_position, 'ultrasound')
                    time.sleep(0.1)  # Petit délai entre les envois
                    send_sensor_data(client, current_position, 'sound')

                time.sleep(UPDATE_INTERVAL)
        
        start_point = target_point

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 SIMULATEUR SAÉ24 - Configuration:")
    print(f"   Mode: {SIMULATION_MODE}")
    print(f"   Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"   Vitesse déplacement: {MOVE_SPEED} m/s")
    print(f"   Intervalle mise à jour: {UPDATE_INTERVAL}s")
    print("=" * 60)
    
    run_simulation()