import select
from datetime import datetime, timedelta
from .classes.order import Order
from .classes.database import Database
from .classes.network import BroadCastReceiver
from .classes.client import Client
from .classes.pizza import Pizza
from .classes.production import ProductionManager
from .classes.stats import SharedContext, PizzeriaStats

def get_pizza_prod_time(pizza_name: str, pizza_size: str, pizzas_list: list[Pizza]) -> int:
    """Helper pour retrouver le temps de prod (INT) depuis la liste des pizzas."""
    for p in pizzas_list:
        if p.name == pizza_name and p.size == pizza_size:
            return int(p.production_time)
    return 999 # Valeur par défaut pénalisante

def _check_feasibility(order: Order, client_map: dict[int, Client], pizza_list: list[Pizza], prod_manager: ProductionManager, stats: PizzeriaStats, db: Database) -> bool:
    """
    Fonction qui détermine la faisabilité d'une commande de pizzas.
    1.  On vérifie que la pizza existe bien dans notre DB locale et que le client aussi

        On a besoin que les deux existent pour récupérer le temps de livraison 
        nécessaire ainsi que les infos de durée de prod de pizza

    2.  On calcule le temps de production nécessaire à la pizza
    3.  On compare le temps de prod à la deadline imposée

    Soit la commande est réalisable ET livrable dans les temps 
    ->  Commande acceptée (True)

    Soit elle ne l'est pas
    ->  Commande rejetée (False)

    """

    # Check que la pizza est bien dans notre DB (préventif pour empêcher erreur)
    target_pizza = None
    for pizza in pizza_list:
        if pizza.name == order.pizza_name and pizza.size == order.pizza_size:
            target_pizza = pizza
            break
    # Si pizza non trouvée
    if not target_pizza: 
        # Peut-être nouvelle pizza sortie par le gérant
        # Donc on vérifie dans la DB centrale si on a une nouvelle pizza
        print(f"[CACHE MISS] Recherche BDD pour Pizza: {order.pizza_name}...")
        
        new_pizza = db.get_entity("Pizza", ("Nom", order.pizza_name), ("Taille", order.pizza_size))
        
        # Si on a bien une nouvelle pizza on ajoute notre nouvelle pizza à la liste.
        if new_pizza:
            target_pizza = new_pizza
            pizza_list.append(new_pizza)
        else:
            # Si pas de nouvelle pizza -> Erreur, commande refusée
            # FALLBACK
            print(f"\n--- ❌ COMMANDE REFUSÉE (ID {order.client_id}) ---")
            print(f"Raison: La pizza {order.pizza_name} n'existe pas.")
            print("----------------------------------\n")
            return False

    client = client_map.get(order.client_id)

    # Si client inexistant dans notre DB
    if not client:
        # Peut-être nouveau client
        # Donc on vérifie dans la DB centrale si on a un nouveau client
        print(f"[CACHE MISS] Recherche BDD pour Client: {order.client_id}...")
        
        new_client = db.get_entity("Client", ("ID", order.client_id))
        
        # Si on a bien un nouveau client on ajoute notre nouveau client à la liste
        if new_client:
            client = new_client
            client_map[client.id] = client
            
        else:
            # Si pas de nouveau client -> Erreur, commande refusée
            # FALLBACK
            print(f"\n--- ❌ COMMANDE REFUSÉE (ID {order.client_id}) ---")
            print(f"Raison: Le client {order.client_id} n'existe pas.")
            print("----------------------------------\n")
            return False

    # Si on a bien un client existant (et une pizza)
    # NOTE: On a besoin que les deux existent pour récupérer le temps de livraison 
    #       nécessaire ainsi que les infos de durée de prod de pizza

    # Calcul du temps disponible pour prod + livraison
    time_before_delivery = order.get_time_before_delivery()
    if not time_before_delivery: return False 
    delivery_deadline = datetime.now() + time_before_delivery - timedelta(minutes=client.distance)
    
    # On met à jour les infos qu'on a sur chacun des postes de production
    prod_manager.update_all_stations(datetime.now())

    # On détermine le meilleur poste de production pour notre commande (best candidate)
    station_id, end_time = prod_manager.find_and_assign_station(
        order.pizza_name, 
        order.pizza_size, 
        order.quantity, 
        target_pizza.production_time,
        delivery_deadline
    )

    # Une fois qu'on a notre poste de prod assigné, on envoie la commande
    if station_id:
        stats.accepted_orders += 1
            
        # --- LOGIQUE DE COMPTAGE DES INGRÉDIENTS ---
        # On parcourt chaque caractère de la composition de la pizza cible
        # target_pizza.composition ressemble à "JVBJ,VBJV,VVJJ..."
        for char in target_pizza.composition:
            if char in stats.ingredients:
                # On multiplie par la quantité commandée !
                stats.ingredients[char] += (1 * order.quantity)

        stats.accepted_orders += 1
        print("\n--- ✅ COMMANDE VALIDÉE ---")
        print(f"Client          : {order.client_id} (Dist: {client.distance}m)")
        print(f"Pizza           : {order.quantity}x {order.pizza_name} ({order.pizza_size})")
        print(f"Poste           : #{station_id}")
        print(f"Fin Production  : {end_time.strftime('%H:%M:%S')}")
        print("---------------------------")
        # prod_manager.display_queues()
        return True
    
    # FALLBACK si deadline impossible à respecter
    else:
        stats.refused_orders += 1
        print(f"\n--- ❌ COMMANDE REFUSÉE (ID {order.client_id}) ---")
        print(f"Raison: Deadline impossible à respecter {order.pizza_name}")
        print(f"A livrer avant : {order.delivery_time}")

        print("----------------------------------\n")
        return False

def start_processing(context: SharedContext) -> None:
    """"
    Fonction principale qui est une boucle itérative.

    ->  On récupère quelques commandes
    ->  On compare l'urgence de chacune pour avoir la priorité (Least Slack Time)
    ->  On envoie en prod les commandes
    """
    
    # Initialisation des Bases de Données
    db = Database()
    if (db.conn, db.cur) == (None, None): return
    clients_list = db.get_table("Client")
    pizzas = db.get_table("Pizza")
    prod_manager = ProductionManager(db)

    # Initialisations des stats et infos IHM
    context.prod_manager = prod_manager
    stats = context.stats

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

    # On démarre l'écoute du serveur de commandes UDP
    with BroadCastReceiver(40100) as r:
        print("[ORDER] > INFO: En attente de commandes...")
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
                    current_select_timeout = max(0, int(remaining)) # Si négatif, on met 0 (non-bloquant)
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

                # 5. Traitement du lot (comparaison des Slack (Urgences))
                if order_buffer and (is_batch_full or is_timeout):
                    trigger = "TAILLE ATTEINTE" if is_batch_full else f"TIMEOUT ({BUFFER_TIMEOUT}s)"
                    print(f"\n[OPTIMISATION] > Tri Intelligent déclenché par : {trigger}")
                    
                    def calculate_slack(o: Order) -> timedelta:
                        """
                        Fonction qui détermine l'urgence (Slackà d'une commande :
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

                    # Exécution, on check la faisabilité dans l'ordre d'importance
                    for sorted_order in order_buffer:
                        _check_feasibility(sorted_order, client_map, pizzas, prod_manager, stats, db)

                    # Reset du buffer
                    order_buffer.clear()
                    buffer_start_time = None

            # FALLBACK si Ctrl+C ou crash fatal
            except (StopIteration, KeyboardInterrupt):
                print("\n[ORDER] > KILL: Arrêt du processeur de commandes.")
                break
            except Exception as e:
                print(f"[ORDER] > FATAL: Erreur boucle principale: {e.args[0]}")
                order_buffer.clear()
                buffer_start_time = None