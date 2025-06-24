import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
import json
import math
import time

# --- CONFIGURATION ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_ULTRASON = "SAE24/ultrason/temps"
MQTT_TOPIC_SOUND = "SAE24/son/amplitude"

DB_HOST = 'localhost'
DB_DATABASE = 'sae24_simulation'
DB_USER = 'root'
DB_PASSWORD = ''

SENSORS = { 'A': (0.25, 0.25), 'B': (0.25, 7.75), 'C': (7.75, 7.75) }

# --- CONSTANTES PHYSIQUES ---
SPEED_OF_SOUND = 343.0
SOUND_SOURCE_POWER = 100

# Dictionnaires pour stocker les données en cours de réception
current_ultrason_data = {}
current_sound_data = {}

def trilateration(distances):
    """Calcule la position par trilatération à partir de 3 distances"""
    try:
        x1, y1 = SENSORS['A']; r1 = distances['A'][0]
        x2, y2 = SENSORS['B']; r2 = distances['B'][0]
        x3, y3 = SENSORS['C']; r3 = distances['C'][0]

        A = 2 * (x2 - x1)
        B = 2 * (y2 - y1)
        C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
        D = 2 * (x3 - x2)
        E = 2 * (y3 - y2)
        F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2

        denominator = A * E - B * D
        if abs(denominator) < 1e-10: 
            return None
        
        x = (C * E - F * B) / denominator
        y = (A * F - D * C) / denominator
        return (x, y)
    except Exception as e:
        print(f"❌ Erreur pendant la trilatération: {e}")
        return None

def save_to_db(source_type, data_set, estimated_pos):
    """Sauvegarde les données dans la base"""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST, 
            database=DB_DATABASE, 
            user=DB_USER, 
            password=DB_PASSWORD
        )
        if connection.is_connected():
            cursor = connection.cursor()
            
            query = """INSERT INTO enregistrements 
                       (source_type, dist_a, dist_b, dist_c, 
                        valeur_brute_a, valeur_brute_b, valeur_brute_c, 
                        pos_x_estimee, pos_y_estimee) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            record = (
                source_type,
                data_set['A'][0], data_set['B'][0], data_set['C'][0],  # Distances
                data_set['A'][1], data_set['B'][1], data_set['C'][1],  # Valeurs brutes
                estimated_pos[0], estimated_pos[1]
            )
            
            cursor.execute(query, record)
            connection.commit()
            print(f"✅ Données ({source_type}) sauvées: Pos=({estimated_pos[0]:.2f}, {estimated_pos[1]:.2f})")

    except Error as e:
        print(f"❌ Erreur MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def process_complete_dataset(source_type, data_set):
    """Traite un jeu de données complet (3 capteurs)"""
    print(f"🧮 Calcul de trilatération pour {source_type}...")
    
    estimated_position = trilateration(data_set)
    
    if estimated_position:
        save_to_db(source_type, data_set, estimated_position)
        print(f"📊 Distances: A={data_set['A'][0]:.2f}m, B={data_set['B'][0]:.2f}m, C={data_set['C'][0]:.2f}m")
    else:
        print(f"❌ Impossible de calculer la position pour {source_type}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connecté au Broker MQTT!")
        client.subscribe([(MQTT_TOPIC_ULTRASON, 0), (MQTT_TOPIC_SOUND, 0)])
        print(f"   -> Abonné à {MQTT_TOPIC_ULTRASON}")
        print(f"   -> Abonné à {MQTT_TOPIC_SOUND}")
    else:
        print(f"❌ Échec de la connexion, code d'erreur {rc}\n")

def on_message(client, userdata, msg):
    global current_ultrason_data, current_sound_data
    
    try:
        payload = json.loads(msg.payload.decode())
        sensor_id = payload.get("sensorId")
        
        if not sensor_id or sensor_id not in SENSORS:
            print(f"⚠️ Capteur inconnu: {sensor_id}")
            return

        # Traitement des données ultrason
        if msg.topic == MQTT_TOPIC_ULTRASON and "time" in payload:
            raw_time = payload["time"]
            distance = (raw_time * SPEED_OF_SOUND) / 2
            
            current_ultrason_data[sensor_id] = (distance, raw_time)
            print(f"📡 [ULTRASON] {sensor_id}: temps={raw_time:.4f}s -> distance={distance:.2f}m")
            
            # Si on a les 3 capteurs ultrason, on traite
            if len(current_ultrason_data) == 3:
                print("🔊 Set ultrason complet reçu!")
                process_complete_dataset('ultrason', current_ultrason_data)
                current_ultrason_data = {}  # Reset pour le prochain set

        # Traitement des données son
        elif msg.topic == MQTT_TOPIC_SOUND and "amplitude" in payload:
            raw_amplitude = payload["amplitude"]
            if raw_amplitude > 0:
                distance = math.sqrt(SOUND_SOURCE_POWER / raw_amplitude)
                
                current_sound_data[sensor_id] = (distance, raw_amplitude)
                print(f"🔉 [SON] {sensor_id}: amplitude={raw_amplitude:.2f} -> distance={distance:.2f}m")
                
                # Si on a les 3 capteurs son, on traite
                if len(current_sound_data) == 3:
                    print("🎵 Set son complet reçu!")
                    process_complete_dataset('son', current_sound_data)
                    current_sound_data = {}  # Reset pour le prochain set
            else:
                print(f"⚠️ Amplitude invalide pour {sensor_id}: {raw_amplitude}")

    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
    except Exception as e:
        print(f"❌ Erreur dans on_message: {e}")

def run_service():
    print("=" * 60)
    print("🔧 SERVICE D'ENREGISTREMENT SAÉ24")
    print(f"   Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"   Base de données: {DB_HOST}/{DB_DATABASE}")
    print(f"   Topics surveillés:")
    print(f"     - {MQTT_TOPIC_ULTRASON}")
    print(f"     - {MQTT_TOPIC_SOUND}")
    print("=" * 60)
    
    client = mqtt.Client(client_id="db_logger_service_enhanced")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print("🔄 Démarrage du service... (Ctrl+C pour arrêter)")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du service demandé")
        client.disconnect()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == '__main__':
    run_service()