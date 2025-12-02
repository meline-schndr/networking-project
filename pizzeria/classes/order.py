from datetime import datetime, time, timedelta


class Order:

    def __init__(self, order_time: str, client_id: int, pizza_name: str, pizza_size: str, quantity: int, delivery_time: str):
        try:
            self.timestamp = datetime.strptime(order_time, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            self.timestamp = datetime.now()
        print(self.timestamp, datetime.now())
        self.client_id = int(client_id)
        self.pizza_name = str(pizza_name)
        self.pizza_size = str(pizza_size)
        self.quantity = int(quantity)
        formatted_deadline = delivery_time.split(":")
        self.delivery_time = time(int(formatted_deadline[0]), int(formatted_deadline[1]), 0)
    

    def __str__(self):
        return ""


    def get_time_before_delivery(self):
        try: 
            ref_now = self.timestamp
            delivery_date = datetime.combine(ref_now.date(), self.delivery_time)

            # Si Minuit dépassé
            if delivery_date < ref_now:
                delivery_date += timedelta(days=1)

            # Temps maximal autorisé pour prod + livraison
            duration = delivery_date - ref_now
            return duration
        except ValueError:
            # Traitement de l'erreur
            print(f"\n--- ❌ COMMANDE REFUSÉE (ID {self.client_id}) ---")
            print(f"Raison : Format d'heure invalide: {self.delivery_time}")
            print("----------------------------------\n")
            return None
