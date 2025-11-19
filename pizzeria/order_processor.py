from .classes.order import Order
from .classes.database import Database
from .classes.network import BroadCastReceiver
from .classes.client import Client
from .classes.pizza import Pizza
from .classes.production import ProductionManager
from datetime import timedelta, datetime

def _check_feasibility(order: Order, clients_table: list[Client], pizza_list: list[Pizza], prod_manager: ProductionManager) -> bool:
    
    
    target_pizza = None
    for pizza in pizza_list:
        if pizza.name == order.pizza_name and pizza.size == order.pizza_size:
            target_pizza = pizza
            break
    if not target_pizza: return False

    
    for client in clients_table:
        if order.client_id == client.id:
            
            time_before_delivery = order.get_time_before_delivery()
            if not time_before_delivery: return False 
            
            # DEADLINE : La pizza doit être prête à cette heure précise pour que le livreur parte
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
                print("\n--- ✅ COMMANDE VALIDÉE ---")
                print(f"Pizza           : {order.quantity}x {order.pizza_name} ({order.pizza_size})")
                print(f"Poste           : #{station_id}")
                print(f"Fin Production  : {end_time.strftime('%H:%M:%S')}")
                print("---------------------------")
                prod_manager.display_queues()
                return True
            else:
                print(f"\n--- ❌ COMMANDE REFUSÉE (ID {order.client_id}) ---")
                print("Raison: Capacité insuffisante avant l'heure limite.")
                print("----------------------------------\n")
                return False
        
    return False

def start_processing():
    
    print("[ORDER] > INFO: Démarrage...")
    db = Database()
    clients = db.get_table("Client")
    pizzas = db.get_table("Pizza")
    prod_manager = ProductionManager(db)
    
    with BroadCastReceiver(40100) as r:
        while True:
            data, addr = next(r)
            if data:
                parts = data.split(',')
                if len(parts) == 6:
                    try:
                        order = Order(*parts)
                        _check_feasibility(order, clients, pizzas, prod_manager)
                    except Exception as e:
                        print(f"Erreur: {e}")