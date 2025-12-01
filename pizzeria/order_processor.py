import select
from datetime import datetime, timedelta
from .classes.order import Order
from .classes.database import Database
from .classes.network import BroadCastReceiver
from .classes.client import Client
from .classes.pizza import Pizza
from .classes.production import ProductionManager

def get_pizza_prod_time(pizza_name:  str, pizza_size: str, pizzas_list: list[Pizza]) -> int:
    """Helper pour retrouver le temps de prod (INT) depuis la liste des pizzas."""
    for p in pizzas_list:
        if p.name == pizza_name and p.size == pizza_size:
            return int(p.production_time)
    return 999 # Valeur par défaut pénalisante

def _check_feasibility(order: Order, client_map: dict[int, Client], pizza_list: list[Pizza], prod_manager: ProductionManager, stats) -> bool:
    target_pizza = None
    for pizza in pizza_list:
        if pizza.name == order.pizza_name and pizza.size == order.pizza_size:
            target_pizza = pizza
            break
    if not target_pizza: 
        print(f"Pizza inconnue: {order.pizza_name}")
        return False

    # Récupération rapide du client via le dictionnaire
    client = client_map.get(order.client_id)
    if client:
        time_before_delivery = order.get_time_before_delivery()
        if not time_before_delivery: return False 
        
        delivery_deadline = datetime.now() + time_before_delivery - timedelta(minutes=client.distance)
        prod_manager.update_all_stations(datetime.now())

        station_id, end_time = prod_manager.find_and_assign_station(
            order.pizza_name, 
            order.pizza_size, 
            order.quantity, 
            target_pizza.production_time,
            delivery_deadline
        )

        if station_id:
            stats.accepted_orders += 1
            print("\n--- ✅ COMMANDE VALIDÉE ---")
            print(f"Client          : {order.client_id} (Dist: {client.distance}m)")
            print(f"Pizza           : {order.quantity}x {order.pizza_name} ({order.pizza_size})")
            print(f"Poste           : #{station_id}")
            print(f"Fin Production  : {end_time.strftime('%H:%M:%S')}")
            print("---------------------------")
            prod_manager.display_queues()
            return True
        else:
            stats.refused_orders += 1
            print(f"\n--- ❌ COMMANDE REFUSÉE (ID {order.client_id}) ---")
            print(f"Raison: Capacité insuffisante pour {order.pizza_name}")
            print(f"A livrer avant : {order.delivery_time}")

            print("----------------------------------\n")
            return False
    
    print(f"Client inconnu: {order.client_id}")
    return False

def start_processing(stats) -> None:
    print("[ORDER] > INFO: Démarrage Système (Batching + Least Slack Time Sort)...")
    
    # Initialisation des Bases de Données
    db = Database()
    clients_list = db.get_table("Client")
    pizzas = db.get_table("Pizza")
    prod_manager = ProductionManager(db)
    
    # NOTE : Ici on simplifie la complexité, la liste des clients 
    #        est très longue, la parcourir à chaque commande est 
    #        gourmande en complexité donc on la cartographie.
    #        O(n) -> O(1)
    client_map = {c.id: c for c in clients_list}

    # Paramètres du Batch Processing
    BATCH_SIZE = 4          # Taille idéale du lot
    BUFFER_TIMEOUT = 12.0    # Temps max d'attente (secondes)
    
    order_buffer = []
    buffer_start_time = None

    with BroadCastReceiver(40100) as r:
        sock = r.sock 
        
        while True:
            try:
                # 1. Calcul du timeout dynamique pour select
                # -> Si le buffer a des éléments, on attend 
                #    seulement le temps restant avant les 6s
                #
                # -> Sinon, on attend indéfiniment (None) 
                #    qu'une première commande arrive

                if order_buffer and buffer_start_time:
                    elapsed = (datetime.now() - buffer_start_time).total_seconds()
                    remaining = BUFFER_TIMEOUT - elapsed
                    current_select_timeout = max(0, remaining) # Si négatif, on met 0 (non-bloquant)
                else:
                    current_select_timeout = None

                # 2. Attente intelligente (Réseau OU Timeout)
                #    La fonction 'select.select()' autorise le programme à "dormir" 
                #    jusqu'à ce qu'il se passe quelque chose (ex: paquet reçu) _OU_
                #    que le temps imparti (ex: le reste des 6 secondes) soit écoulé.

                ready, _, _ = select.select([sock], [], [], current_select_timeout)

                # 3. Traitement Réseau
                if ready:
                    data = next(r)
                    if data:
                        parts = data.split(',')
                        if len(parts) == 6:
                            order = Order(*parts)
                            
                            # Initialisation du chrono au premier élément du buffer
                            if not order_buffer:
                                buffer_start_time = datetime.now()
                                
                            order_buffer.append(order)
                            print(f"[BUFFER] Reçu: {order.quantity}x {order.pizza_name} (En attente: {len(order_buffer)}/{BATCH_SIZE})")

                # 4. Vérification des conditions de déclenchement (Flush)
                is_batch_full = len(order_buffer) >= BATCH_SIZE
                is_timeout = False
                if order_buffer and buffer_start_time:
                    if (datetime.now() - buffer_start_time).total_seconds() >= BUFFER_TIMEOUT:
                        is_timeout = True

                # 5. Traitement du lot si nécessaire
                if order_buffer and (is_batch_full or is_timeout):
                    trigger = "TAILLE ATTEINTE" if is_batch_full else f"TIMEOUT ({BUFFER_TIMEOUT}s)"
                    print(f"\n[OPTIMISATION] > Tri Intelligent déclenché par : {trigger}")
                    
                    def calculate_slack(o: Order) -> timedelta:
                        """
                        Fonction qui détermine l'urgence d'une commande :
                        Une pizza livrée en 1h qui a une grosse durée de 
                        livraison sera traitée AVANT qu'une pizza à livrer 
                        dans 30min mais qui n'a que 2min de route.

                        # Slack = (Heure Livraison) - (Maintenant) - (Prod) - (Trajet)
                        # Plus le Slack est petit, plus c'est URGENT.
                        """
                        client = client_map.get(o.client_id)
                        dist = client.distance if client else 0
                        prod = get_pizza_prod_time(o.pizza_name, o.pizza_size, pizzas)
                        
                        time_avail = o.get_time_before_delivery()
                        if not time_avail: return timedelta(days=999) # Non prioritaire si erreur
                        
                        # Temps nécessaire minimal (Trajet + Prod)
                        time_needed = timedelta(minutes=dist + prod)
                        
                        # Marge de manœuvre (Slack)
                        return time_avail - time_needed

                    # On trie par marge croissante (les plus tendus en premier)
                    order_buffer.sort(key=calculate_slack)

                    # Exécution
                    for sorted_order in order_buffer:
                        _check_feasibility(sorted_order, client_map, pizzas, prod_manager, stats)

                    # Reset du buffer
                    order_buffer.clear()
                    buffer_start_time = None

            except (StopIteration, KeyboardInterrupt):
                print("\n[ORDER] > KILL: Arrêt du processeur de commandes.")
                break
            except Exception as e:
                print(f"[ORDER] > FATAL: Erreur boucle principale: {e}")
                order_buffer.clear()
                buffer_start_time = None