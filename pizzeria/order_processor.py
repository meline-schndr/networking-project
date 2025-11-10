from .database import Database
from .network import BroadCastReceiver
from datetime import datetime, time, timedelta

def _faisabilite(client_id: int, pizza_name: str, pizza_size: str, quantity: int, delivery_time: str, clients_table: dict, pizza_list: list[dict]) -> bool:
    """
    Fonction pour déterminer si le temps pour produire les pizzas et les livrer est inférieur à l'heure de livraison désirée.

    Paramètres : 
    - [int]  client_id      : ID du client qui a commandé
    - [str]  pizza_name     : Nom de la pizza commandée
    - [str]  pizza_size     : Taille de la pizza commandée                  (influence le temps de production)
    - [int]  quantity       : Quantité de pizzas commandées                 (multiplie le temps de production)
    - [str]  delivery_time  : Heure de livraison souhaitée par le client
    - [dict] clients_table  : Tableau des clients de la pizzeria            (pour récupérer la distance/temps de livraison)
    - [list] pizza_list     : Liste des propriétés des pizzas               (pour récupérer le temps de production de chaque pizza)

    -> Retourne un booléen qui indique si la commande peut être traitée ou pas. (Temps de prod + Livraison > Heure souhaitée)

    TODO: Ajouter de la logique pour le traitement des commandes en usine.
    """

    now = datetime.now() # Heure de maintenant
    try:
        # Calcul du temps à disposition pour la prod et la livraison (heure souhaitée - heure actuelle = temps maximal autorisé)
        new_time = delivery_time.split(":")
        target_time = time(int(new_time[0]), int(new_time[1]), 0)
        future_time = datetime.combine(now.date(), target_time)
        
        # Si la commande arrive après minuit
        if future_time < now:
            future_time += timedelta(days=1)

        # Temps maximal autorisé pour prod + livraison
        duration = future_time - now
        
    except ValueError:
        # Traitement de l'erreur
        print(f"--- COMMANDE REFUSEE (ID {client_id}) ---")
        print(f"Format d'heure invalide: {delivery_time}")
        print("----------------------------------\n")
        return

    # Recherche du temps de prod de la pizza
    for pizza in pizza_list:
        if pizza["Nom"] == pizza_name and pizza["Taille"] == pizza_size:
            production_time = pizza["TPsProd"]
            break
    
    # (Purement préventif) Vérifie si le client existe
    client_key = f"{client_id}"
    if client_key not in clients_table:
        print(f"\n--- COMMANDE REFUSEE ---")
        print(f"Le client ID {client_id} est inconnu.")
        print("--------------------------\n")
        return
    
    distance_client = clients_table[client_key]

    # Calcul de la faisabilité de la commande
    faisabilite = timedelta(minutes=distance_client+production_time*quantity)<duration

    # Affichage dans la console de la commande
    print("\n--- NOUVELLE COMMANDE ANALYSEE ---")
    print("Client habite à", distance_client, "minutes.\
        \nTemps de préparation de commande :", production_time*quantity, "minutes. \
        \nHeure de livraison souhaité :", target_time, f"(dans {duration} minutes).",
        "\nFaisabilité :", faisabilite)
    print("----------------------------------\n")

    # Renvoie faisabilité
    return faisabilite


def start_processing():
    """
    Point d'entrée principal pour le système de commandes.
    Charge les données et lance la boucle d'écoute UDP.
    """

    # Connexion aux bases de données
    print("[ORDER] > INFO: Initialisation de la connexion BDD...")
    db = Database() # Classe définie dans database.py
    clients_table = db.get_clients_table()
    pizza_list = db.get_pizzas_table("Nom", "Taille", "Composition", "TPsProd", "Prix")
    
    # Si pas d'entrées dans les tableaux récupérés
    if not clients_table or not pizza_list:
        print("[ORDER] > ERROR: Données BDD non chargées. Arrêt du script.")
        return

    print("[ORDER] > SUCCESS: Données chargées.")
    print("[ORDER] > INFO: En attente des commandes UDP...")

    # Boucle principale
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
                        # On vérifie si la commande est faisable ou non
                        _faisabilite(
                            commande["ID"], commande["Pizza"], commande["Taille"], 
                            commande["Quantité"], commande["Heure souhaitée"], clients_table, pizza_list
                        )
    except KeyboardInterrupt:
        # En cas d'arrêt forcé (Ctrl+C dans la console)
        print("\n[ORDER] > KILL: Arrêt du processeur de commandes.")
    finally:
        # 'db' sera détruit ici, et son __del__ fermera la connexion
        print("[ORDER] > INFO: Système de commandes arrêté.")
