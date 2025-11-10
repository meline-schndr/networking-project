from .database import Database
from .network import BroadCastReceiver
from datetime import datetime, time, timedelta

def _faisabilite(client_id: int, pizza_name: str, pizza_size: str, quantity: int, delivery_time: str, clients_table: dict, pizza_list: list[dict]):
    now = datetime.now()
    try:
        new_time = delivery_time.split(":")
        target_time = time(int(new_time[0]), int(new_time[1]), 0)
        future_time = datetime.combine(now.date(), target_time)
        
        if future_time < now:
            future_time += timedelta(days=1)
        duration = future_time - now
    except ValueError:
        print(f"--- COMMANDE REFUSEE (ID {client_id}) ---")
        print(f"Format d'heure invalide: {delivery_time}")
        print("----------------------------------\n")
        return

    for pizza in pizza_list:
        if pizza["Nom"] == pizza_name and pizza["Taille"] == pizza_size:
            production_time = pizza["TPsProd"]
            break
    
    client_key = f"{client_id}"
    if client_key not in clients_table:
        print(f"\n--- COMMANDE REFUSEE ---")
        print(f"Le client ID {client_id} est inconnu.")
        print("--------------------------\n")
        return
    
    distance_client = clients_table[client_key]

    print("\n--- NOUVELLE COMMANDE ANALYSEE ---")
    print("Client habite à", distance_client, "minutes.\
        \nTemps de préparation de commande :", production_time*quantity, "minutes. \
        \nHeure de livraison souhaité :", target_time, f"(dans {duration} minutes).",
        "\nFaisabilité :", timedelta(minutes=distance_client+production_time*quantity)<duration)
    print("----------------------------------\n")

    return timedelta(minutes=distance_client+production_time*quantity)<duration


def start_processing():
    """
    Point d'entrée principal pour le système de commandes.
    Charge les données et lance la boucle d'écoute UDP.
    """
    print("[ORDER] > INFO: Initialisation de la connexion BDD...")
    db = Database()
    clients_table = db.get_clients_table()
    pizza_list = db.get_pizzas_table("Nom", "Taille", "Composition", "TPsProd", "Prix")
    
    if not clients_table or not pizza_list:
        print("[ORDER] > ERROR: Données BDD non chargées. Arrêt du script.")
        return # On arrête la fonction

    print("[ORDER] > SUCCESS: Données chargées.")
    print("[ORDER] > INFO: En attente des commandes UDP...")

    # C'est votre boucle principale
    try:
        with BroadCastReceiver(40100) as r:
            while True:
                data, addr = next(r)
                table = data.split(',')
                
                if len(table) == 6:
                        commande = {
                            "Date / Heure": table[0],
                            "ID": int(table[1]),
                            "Pizza": table[2],
                            "Taille": table[3],
                            "Quantité": int(table[4]),
                            "Heure souhaitée": table[5],
                        }
                        # On passe les tables chargées à la fonction
                        _faisabilite(
                            commande["ID"], commande["Pizza"], commande["Taille"], 
                            commande["Quantité"], commande["Heure souhaitée"], clients_table, pizza_list
                        )
    except KeyboardInterrupt:
        print("\n[ORDER] > KILL: Arrêt du processeur de commandes.")
    finally:
        # 'db' sera détruit ici, et son __del__ fermera la connexion
        print("[ORDER] > INFO: Système de commandes arrêté.")