
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from gpiozero import DigitalInputDevice
import math
import paho.mqtt.client as mqtt
import json

# Créer le bus I2C
i2c = busio.I2C(board.SCL, board.SDA)		

# Créer l'objet ADC avec le bus I2C
ads = ADS.ADS1115(i2c)

# Créer des entrées asymétriques sur les canaux
chan0 = AnalogIn(ads, ADS.P0)  # Canal principal pour le capteur sonore
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

# CONFIGURATION MQTT
MQTT_BROKER = "SAE24_simulation"  # Nom ou IP du broker
MQTT_PORT = 1883                  # Port standard MQTT
MQTT_TOPIC_DETECTION = "capteur/detection"  # Topic pour les détections
MQTT_TOPIC_STATUS = "capteur/status"        # Topic pour le statut
MQTT_CLIENT_ID = "capteur_sonore_01"        # ID unique du client

# Variables MQTT
mqtt_client = None
mqtt_connected = False
# Choisir la configuration de votre pièce (décommenter la ligne appropriée)
# CONFIGURATION DE LA PIÈCE
# Choisir la configuration de votre pièce (décommenter la ligne appropriée)
LARGEUR_PIECE = 8.0  # Pour 64m² : 8m x 8m
LONGUEUR_PIECE = 8.0
# LARGEUR_PIECE = 0.5  # Pour 0.25m² : 0.5m x 0.5m
# LONGUEUR_PIECE = 0.5

# Position du capteur dans le coin (0,0)
POSITION_CAPTEUR_X = 0.0
POSITION_CAPTEUR_Y = 0.0

# Calcul des distances caractéristiques de la pièce
DISTANCE_MAX = math.sqrt(LARGEUR_PIECE**2 + LONGUEUR_PIECE**2)  # Diagonale
DISTANCE_CENTRE = math.sqrt((LARGEUR_PIECE/2)**2 + (LONGUEUR_PIECE/2)**2)  # Vers le centre
DISTANCE_COIN_OPPOSE = DISTANCE_MAX  # Coin opposé

# Configuration des seuils basés sur les dimensions de la pièce
# Principe : Plus la tension est élevée, plus l'objet est proche
TENSION_MAX_CAPTEUR = 5.0  # Tension maximale du capteur (à ajuster selon votre matériel)
SEUIL_DETECTION_MIN = 0.05  # Seuil minimum pour détecter un objet

# Calcul des seuils adaptatifs basés sur la géométrie de la pièce
def calculer_seuils():
    """
    Calcule les seuils de tension basés sur les distances caractéristiques
    Utilise le principe : amplitude ∝ 1/distance²
    """
    # Coefficient de calibration (à ajuster selon votre capteur)
    K_CALIBRATION = 2.0
    
    seuils = {
        'tres_proche': K_CALIBRATION * (1 / (0.5**2)),      # Moins de 50cm
        'proche': K_CALIBRATION * (1 / (1.0**2)),           # Moins de 1m
        'moyen': K_CALIBRATION * (1 / (2.0**2)),            # Moins de 2m
        'centre': K_CALIBRATION * (1 / (DISTANCE_CENTRE**2)), # Vers le centre
        'loin': K_CALIBRATION * (1 / (DISTANCE_MAX**2))     # Diagonale max
    }
    
    # Normalisation des seuils pour rester dans la plage du capteur
    max_seuil = max(seuils.values())
    if max_seuil > TENSION_MAX_CAPTEUR:
        facteur = TENSION_MAX_CAPTEUR / max_seuil
        for key in seuils:
            seuils[key] *= facteur
    
    return seuils

SEUILS = calculer_seuils()

delayTime = 0.3

# Initialisation GPIO
digital_pin = DigitalInputDevice(24, pull_up=False)

# Buffer pour lisser les mesures
buffer_size = 7
voltage_buffer = []

def estimer_distance(voltage):
    """
    Estime la distance basée sur la tension et la géométrie de la pièce
    Utilise la formule inverse : distance ≈ √(K/tension)
    """
    if voltage <= SEUIL_DETECTION_MIN:
        return None
    
    # Coefficient de calibration (ajustable selon le capteur)
    K_DISTANCE = 2.0
    distance_estimee = math.sqrt(K_DISTANCE / voltage)
    
    # Limite la distance à la diagonale maximale de la pièce
    return min(distance_estimee, DISTANCE_MAX)

def analyser_position(voltage):
    """
    Analyse la position de l'objet dans la pièce basée sur la tension
    """
    if voltage < SEUIL_DETECTION_MIN:
        return "Aucun objet détecté"
    
    if voltage >= SEUILS['tres_proche']:
        return "Objet à moins de 50 cm"
    elif voltage >= SEUILS['proche']:
        return "Objet à moins d'un mètre"
    elif voltage >= SEUILS['moyen']:
        return "Objet à moins de deux mètres"
    elif voltage >= SEUILS['centre']:
        return "Objet à moins de trois mètres"
    else:
        return "Objet détecté au-delà de trois mètres"



def lisser_mesure(nouvelle_valeur):
    """
    Lisse les mesures pour éviter les variations erratiques
    """
    global voltage_buffer
    
    voltage_buffer.append(nouvelle_valeur)
    if len(voltage_buffer) > buffer_size:
        voltage_buffer.pop(0)
    
    return sum(voltage_buffer) / len(voltage_buffer)

# FONCTIONS MQTT
def on_connect(client, userdata, flags, rc):
    """Callback appelé lors de la connexion au broker MQTT"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print( Connexion MQTT réussie")
        # Publier un message de statut
        publier_status("ONLINE")
    else:
        mqtt_connected = False
        print(f" Échec connexion MQTT, code: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback appelé lors de la déconnexion du broker MQTT"""
    global mqtt_connected
    mqtt_connected = False
    print(" Déconnexion MQTT")

def on_publish(client, userdata, mid):
    """Callback appelé après publication d'un message"""
    pass  # Optionnel: pour debug

def initialiser_mqtt():
    """Initialise la connexion MQTT"""
    global mqtt_client
    
    try:
        mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_publish = on_publish
        
        print(f" Connexion au broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()  # Démarre la boucle en arrière-plan
        
        # Attendre la connexion (max 5 secondes)
        for i in range(50):
            if mqtt_connected:
                break
            time.sleep(0.1)
        
        if not mqtt_connected:
            print(" Timeout connexion MQTT - Continuera en mode local")
        
    except Exception as e:
        print(f" Erreur initialisation MQTT: {e}")
        mqtt_client = None

def publier_detection(message, tension, timestamp=None):
    """Publie une détection via MQTT"""
    if not mqtt_connected or mqtt_client is None:
        return
    
    try:
        if timestamp is None:
            timestamp = time.time()
        
        # Création du payload JSON
        payload = {
            "message": message,
            "tension": round(tension, 3),
            "timestamp": timestamp,
            "capteur_id": MQTT_CLIENT_ID,
            "piece_config": {
                "largeur": LARGEUR_PIECE,
                "longueur": LONGUEUR_PIECE,
                "surface": LARGEUR_PIECE * LONGUEUR_PIECE
            }
        }
        
        # Publication
        result = mqtt_client.publish(MQTT_TOPIC_DETECTION, json.dumps(payload))
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f" MQTT envoyé: {message}")
        else:
            print(f" Erreur envoi MQTT: {result.rc}")
            
    except Exception as e:
        print(f" Erreur publication MQTT: {e}")

def publier_status(status):
    """Publie le statut du capteur"""
    if not mqtt_connected or mqtt_client is None:
        return
    
    try:
        payload = {
            "status": status,
            "timestamp": time.time(),
            "capteur_id": MQTT_CLIENT_ID
        }
        
        mqtt_client.publish(MQTT_TOPIC_STATUS, json.dumps(payload))
        
    except Exception as e:
        print(f" Erreur publication statut: {e}")

# Affichage des informations de configuration
print("=== CAPTEUR SONORE DE POSITIONNEMENT AVEC MQTT ===")
print(f"Configuration de la pièce: {LARGEUR_PIECE}m x {LONGUEUR_PIECE}m")
print(f"Surface: {LARGEUR_PIECE * LONGUEUR_PIECE}m²")
print(f"Distance maximale (diagonale): {DISTANCE_MAX:.2f}m")
print(f"Capteur positionné dans le coin (0,0)")
print(f"Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
print(f"Topics: {MQTT_TOPIC_DETECTION}, {MQTT_TOPIC_STATUS}")

print("\nInitialisation MQTT...")
initialiser_mqtt()

print("Initialisation capteur...")
time.sleep(2)
print("Détection active !\n")

try:
    compteur = 0
    derniere_detection = ""
    
    while True:
        # Lecture et lissage de la tension
        tension_brute = chan0.voltage
        tension_lissee = lisser_mesure(tension_brute)
        
        # Analyse de la position
        message_position = analyser_position(tension_lissee)
        
        # Affichage local
        print(message_position)
        
        # Envoi MQTT seulement si le message a changé (évite le spam)
        if message_position != derniere_detection:
            publier_detection(message_position, tension_lissee)
            derniere_detection = message_position
        
        compteur += 1
        
        # Envoi périodique du statut (toutes les 50 mesures)
        if compteur % 50 == 0:
            publier_status("ACTIVE")
            print(f" Heartbeat envoyé (mesure #{compteur})")
        
        time.sleep(delayTime)

except KeyboardInterrupt:
    print("\n\nArrêt du programme par l'utilisateur")
    publier_status("OFFLINE")
    print(f"Total de mesures effectuées: {compteur}")
except Exception as e:
    print(f"Erreur: {e}")
    publier_status("ERROR")
finally:
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    print("Programme terminé")

