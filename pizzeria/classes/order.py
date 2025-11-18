from datetime import datetime, time, timedelta
from .pizza import Pizza


class Order:

    def __init__(self, order_time, client_id, pizza_name, pizza_size, quantity, delivery_time):
        self.time = order_time
        self.client_id = int(client_id)
        self.pizza_name = str(pizza_name)
        self.pizza_size = str(pizza_size)
        self.quantity = int(quantity)
        formatted_time = delivery_time.split(":")
        self.delivery_time = time(int(formatted_time[0]), int(formatted_time[1]), 0)
    

    def __str__(self):
        return ("")


    def get_time_before_delivery(self):
        try: 
            now = datetime.now()
            delivery_date = datetime.combine(now.date(), self.delivery_time)

            if delivery_date < now:
                delivery_date += timedelta(days=1)

            # Temps maximal autorisé pour prod + livraison
            duration = delivery_date - now
            return duration
        except ValueError:
            # Traitement de l'erreur
            print(f"--- COMMANDE REFUSEE (ID {self.client_id}) ---")
            print(f"Format d'heure invalide: {self.delivery_time}")
            print("----------------------------------\n")
            return None
