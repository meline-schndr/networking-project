from .classes.order import Order
from .classes.database import Database
from .classes.network import BroadCastReceiver
from .classes.client import Client
from .classes.pizza import Pizza
from .classes.production import ProductionManager
from datetime import timedelta, datetime

def _find_client_and_pizza(order: Order, clients_table: list[Client], pizza_list: list[Pizza]) -> tuple[Client | None, Pizza | None]:
    """
    Fonction utilitaire pour trouver les objets Client et Pizza dans les listes correspondantes
    """
    client_obj = next((c for c in clients_table if c.id == order.client_id), None)
    pizza_obj = next((p for p in pizza_list if p.name == order.pizza_name and p.size == order.pizza_size), None)
    return client_obj, pizza_obj


def _check_time_feasibility(order: Order, client: Client, pizza: Pizza) -> bool:
    duration = timedelta(minutes = (client.distance + pizza.production_time*order.quantity))
    return duration < order.get_time_before_delivery(), duration


def _process_order(order: Order, clients_list: list[Client], pizzas_list: list[Pizza], prod_manager: ProductionManager) -> bool:
    """
    Fonction pour déterminer si le temps pour produire les pizzas et les livrer est inférieur à l'heure de livraison désirée.

    Paramètres : 
    - Order        order          : Commande
    - list[Client] clients_table  : Tableau des clients de la pizzeria            (pour récupérer la distance/temps de livraison)
    - list[Pizza]  pizza_list     : Liste des propriétés des pizzas               (pour récupérer le temps de production de chaque pizza)

    -> Retourne un booléen qui indique si la commande peut être traitée ou pas. (Temps de prod + Livraison > Heure souhaitée)

    TODO: Ajouter de la logique pour le traitement des commandes en usine.
    """

    client, pizza = _find_client_and_pizza(order, clients_list, pizzas_list)
    
    if not client:
        print(f"\n--- COMMANDE REFUSEE ---")
        print(f"Le client ID {order.client_id} est inconnu.")
        print("--------------------------\n")
        return
    
    if not pizza:
        print(f"\n--- COMMANDE REFUSEE ---")
        print(f"La pizza {order.pizza_name} ({order.pizza_size}) est inconnue.")
        print("--------------------------\n")
        return

    is_time_feasible, total_prod_time = _check_time_feasibility(order, client, pizza)

    assigned_station = None
    end_prod_time = None

    if is_time_feasible:
        station_id, end_time = prod_manager.find_and_assign_station(
            order.pizza_name,
            order.pizza_size,
            order.quantity,
            pizza.production_time
        )

        if station_id is not None:
            assigned_station = station_id
            end_prod_time = end_time

    if is_time_feasible and assigned_station is not None:
        print("\n--- COMMANDE ACCEPTEE ---")
        print("Temps de libraison               :", client.distance, "minutes.\
                \nTemps de préparation de commande :", pizza.production_time * order.quantity, "minutes. \
                \nTemps total de préparation       :", total_prod_time, "minutes.\
                \nHeure de livraison souhaité      :", order.delivery_time,
                "\nFaisabilité :", is_time_feasible)
        print("----------------------------------\n")
        prod_manager.display_queues()

    else:
        reason = "usine saturée" if is_time_feasible else "délai de livraison trop court"
        print(f"\n--- COMMANDE REFUSEE ---")
        print(f"Raison : {reason}.")
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

    prod_manager = ProductionManager(db)
    
    
    # Si pas d'entrées dans les tableaux récupérés
    if not clients or not pizzas or not prod_manager.stations:
        print("[ORDER] > ERROR: Données BDD non chargées. Arrêt du script.")
        return

    print("[ORDER] > SUCCESS: Données chargées.")
    print("[ORDER] > INFO: En attente des commandes UDP...")

    # Boucle principale
    try:
        with BroadCastReceiver(40100) as r:
            while True:

                prod_manager.update_all_stations(datetime.now()) 
                
                data, addr = next(r)
                table = data.split(',')
                
                if len(table) == 6:
                        order = Order(*table)
                        # On vérifie si la commande est faisable ou non
                        _process_order(order, clients, pizzas, prod_manager)
    except KeyboardInterrupt:
        # En cas d'arrêt forcé (Ctrl+C dans la console)
        print("\n[ORDER] > KILL: Arrêt du processeur de commandes.")
    finally:
        # 'db' sera détruit ici, et son __del__ fermera la connexion
        print("[ORDER] > INFO: Système de commandes arrêté.")
