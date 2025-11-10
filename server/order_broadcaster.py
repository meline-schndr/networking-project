import socket
import time
import random
from datetime import datetime, timedelta

# --- Configuration ---
# Cible locale (localhost) et port de votre client
HOST = '127.0.0.1' 
PORT = 40100  # Le port sur lequel votre client udp.py écoute

# Intervalle d'envoi des commandes (en secondes)
INTERVALLE = 5

# Listes pour générer des données aléatoires (basées sur pizzas.txt et le PDF)
LISTE_PIZZAS = [
    "Veggie", "Margarita", "Reine", "Carnivore", "Orientale", 
    "Andalouse", "4_Fromages", "Chevre", "Chorizo", "Calzone"
]
LISTE_TAILLES = ["G", "M"]

print(f"--- Simulateur de Commandes Pizzas ---")
print(f"Envoi des commandes vers {HOST}:{PORT} toutes les {INTERVALLE} secondes.")
print("Appuyez sur CTRL+C pour arrêter.")

# Création du socket UDP
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # L'option SO_BROADCAST n'est pas nécessaire pour localhost, mais
    # elle serait requise pour un vrai broadcast réseau.
    # s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        while True:
            # 1. Générer l'heure et la date actuelles
            # Format: 26/11/2025 10:03:12
            now = datetime.now()
            date_heure = now.strftime('%d/%m/%Y %H:%M:%S')

            # 2. Générer un ID client aléatoire
            # Exemple: 530080
            LISTE_CLIENT_IDS = [529997, 530143, 529996, 530111, 530080]
            # On choisit un ID au hasard DANS CETTE LISTE
            id_client = random.choice(LISTE_CLIENT_IDS)

            # 3. Choisir une pizza et une taille
            nom_pizza = random.choice(LISTE_PIZZAS)
            taille = random.choice(LISTE_TAILLES)

            # 4. Générer une quantité
            quantite = random.randint(1, 5)

            # 5. Générer une heure de livraison souhaitée
            # (par ex. dans 30 à 90 minutes)
            delta_livraison = timedelta(minutes=random.randint(30, 90))
            heure_livraison = (now + delta_livraison).strftime('%H:%M') # Format: 10:40

            # Construire la chaîne de caractères de la commande
            # Format: << Date Heure, ID_Client, Nom_Pizza, Taille, Quantité, Heure_Livraison_Souhaitée »
            commande_str = f"{date_heure},{id_client},{nom_pizza},{taille},{quantite},{heure_livraison}"
            
            # Encoder le message en bytes pour l'envoi
            message_bytes = commande_str.encode('utf-8')

            # Envoyer le paquet UDP
            s.sendto(message_bytes, (HOST, PORT))
            
            print(f"Commande envoyée : {commande_str}")

            # Attendre avant d'envoyer la prochaine commande
            time.sleep(INTERVALLE)

    except KeyboardInterrupt:
        print("\nArrêt du simulateur.")