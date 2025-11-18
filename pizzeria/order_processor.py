from .classes.order import Order
from .classes.database import Database
from .classes.network import BroadCastReceiver
from .classes.client import Client
from .classes.pizza import Pizza
from datetime import timedelta, datetime

def _faisabilite(order: Order, clients_table: list[Client], pizza_list: list[Pizza]) -> bool:
    """
    Fonction pour déterminer si le temps pour produire les pizzas et les livrer est inférieur à l'heure de livraison désirée.

    Paramètres : 
    - Order        order          : Commande
    - list[Client] clients_table  : Tableau des clients de la pizzeria            (pour récupérer la distance/temps de livraison)
    - list[Pizza]  pizza_list     : Liste des propriétés des pizzas               (pour récupérer le temps de production de chaque pizza)

    -> Retourne un booléen qui indique si la commande peut être traitée ou pas. (Temps de prod + Livraison > Heure souhaitée)

    TODO: Ajouter de la logique pour le traitement des commandes en usine.
    """

    # Recherche du temps de prod de la pizza
    for pizza in pizza_list:
        if pizza.name == order.pizza_name and pizza.size == order.pizza_size:
            production_time = pizza.production_time
            break
    
    # (Purement préventif) Vérifie si le client existe

    for client in clients_table:
        if order.client_id == client.id:
            # Calcul de la faisabilité de la commande
            duration = order.get_time_before_delivery()
            if duration:
                total_prod_time = client.distance + production_time * order.quantity
                faisabilite = timedelta(minutes = total_prod_time) < duration

                # Affichage dans la console de la commande
                print("\n--- NOUVELLE COMMANDE ANALYSEE ---")
                print("Temps de libraison               :", client.distance, "minutes.\
                     \nTemps de préparation de commande :", production_time * order.quantity, "minutes. \
                     \nTemps total de préparation       :", total_prod_time, "minutes.\
                     \nHeure de livraison souhaité      :", f"(dans {int(duration.total_seconds()//60)} minutes).",
                     "\nFaisabilité :", faisabilite)
                print("----------------------------------\n")

                # Renvoie faisabilité
                return faisabilite
        
        
    print(f"\n--- COMMANDE REFUSEE ---")
    print(f"Le client ID {client.id} est inconnu.")
    print("--------------------------\n")
    return


def start_processing():
    """
    Point d'entrée principal pour le système de commandes.
    Charge les données et lance la boucle d'écoute UDP.
    """

    # Connexion aux bases de données
    print("[ORDER] > INFO: Initialisation de la connexion BDD...")
    db = Database() # Classe définie dans database.py
    clients = db.get_table("Client")
    pizzas = db.get_table("Pizza")
    
    
    # Si pas d'entrées dans les tableaux récupérés
    if not clients or not pizzas:
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
                        order = Order(*table)
                        # On vérifie si la commande est faisable ou non
                        _faisabilite(order, clients, pizzas)
    except KeyboardInterrupt:
        # En cas d'arrêt forcé (Ctrl+C dans la console)
        print("\n[ORDER] > KILL: Arrêt du processeur de commandes.")
    finally:
        # 'db' sera détruit ici, et son __del__ fermera la connexion
        print("[ORDER] > INFO: Système de commandes arrêté.")
