from datetime import datetime, time, timedelta


class Order:

    def __init__(self, order_time, client_id: int, pizza_name: str, pizza_size: str, quantity: int, delivery_time: str):
        self.time = order_time
        self.client_id = int(client_id)
        self.pizza_name = str(pizza_name)
        self.pizza_size = str(pizza_size)
        self.quantity = int(quantity)
        formatted_time = delivery_time.split(":")
        self.delivery_time = time(int(formatted_time[0]), int(formatted_time[1]), 0)
    

    def __str__(self):
        return ""


    def get_time_before_delivery(self):
        try: 
            now = datetime.now()
            delivery_date = datetime.combine(now.date(), self.delivery_time)

            # Si Minuit dépassé
            if delivery_date < now:
                delivery_date += timedelta(days=1)

            # Temps maximal autorisé pour prod + livraison
            duration = delivery_date - now
            return duration
        except ValueError:
            # Traitement de l'erreur
            print(f"\n--- ❌ COMMANDE REFUSÉE (ID {self.client_id}) ---")
            print(f"Raison : Format d'heure invalide: {self.delivery_time}")
            print("----------------------------------\n")
            return None
