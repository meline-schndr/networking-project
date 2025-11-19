from datetime import datetime, timedelta
from typing import List, Tuple, Optional

class ProductionStation:
    """
    Poste de production gérant la capacité PARALLÈLE (plusieurs pizzas cuisent en même temps).
    """
    def __init__(self, station_id: int, max_capacity: int, is_available: bool, supported_size: str, restrictions_str: str):
        self.id = station_id
        self.max_capacity = int(max_capacity)
        self.is_available = is_available
        self.supported_size = supported_size
        
        self.restrictions = set(r.strip() for r in restrictions_str.split(',') if r.strip() and r.strip() != '---')
        
        self.planning: List[Tuple[int, datetime, datetime, str]] = [] 

    def update(self, current_time: datetime) -> None:
        """
        Nettoyage : On supprime les tâches totalement terminées pour l'historique,
        mais pour le calcul de capacité future, on a juste besoin de savoir quand elles finissent.
        (Ici on garde tout le planning futur pour les calculs, on ne nettoie que le passé lointain si besoin)
        """
        self.planning = [t for t in self.planning if t[2] > current_time]

    def get_load_at_time(self, t: datetime) -> int:
        """
        Calcule la capacité utilisée à un instant 't' précis.
        Une tâche occupe de la place si elle a commencé (start <= t) et n'est pas finie (t < end).
        """
        return sum(qty for qty, start, end, _ in self.planning if start <= t < end)

    def calculate_earliest_start(self, pizza_name: str, pizza_size: str, quantity: int) -> Optional[datetime]:
        """
        Cherche le moment le plus tôt où 'quantity' places sont libres simultanément.
        """
        # 1. Vérifs techniques (Incompatibilités)
        if not self.is_available: return None
        if pizza_name in self.restrictions: return None
        if self.supported_size != "" and pizza_size != self.supported_size: return None
        if quantity > self.max_capacity: return None

        now = datetime.now()

        # 2. Est-ce qu'on a la place MAINTENANT ?
        if (self.max_capacity - self.get_load_at_time(now)) >= quantity:
            return now

        # 3. Si non, on regarde le futur.
        # Les moments intéressants sont les moments où une tâche SE TERMINE (libérant de la place).
        future_end_times = sorted([task[2] for task in self.planning if task[2] > now])
        
        for t in future_end_times:
            # À cet instant 't', la tâche précédente vient de finir.
            # On vérifie la charge restante à cet instant précis.
            # (Note: On ajoute une micro-seconde pour être sûr d'être "après" la fin)
            check_time = t + timedelta(seconds=1) 
            
            current_load = self.get_load_at_time(check_time)
            if (self.max_capacity - current_load) >= quantity:
                return t

        return None

    def assign_task(self, pizza_name: str, pizza_size: str, quantity: int, prod_time: int, start_time: datetime) -> datetime:
        """Enregistre la production."""
        end_time = start_time + timedelta(minutes=prod_time)
        self.planning.append((quantity, start_time, end_time, pizza_name))
        return end_time


class ProductionManager:
    def __init__(self, db_instance):
        self.stations: List[ProductionStation] = []
        self._load_stations(db_instance)

    def _load_stations(self, db):
        """Charge la BDD ou les données par défaut (Fallback)."""
        try:
            self.stations = db.get_table("Production")
        except Exception:
            self.stations = []

        if not self.stations:
            # Configuration par défaut (6 postes)
            print("[PRODUCTION] > INFO: Chargement des 6 postes par défaut.")
            self.stations = [
                ProductionStation(1, 30, True, "", "Veggie, Chevre"),
                ProductionStation(2, 25, True, "", ""),
                ProductionStation(3, 18, True, "G", "Chevre, 4_Fromages"),
                ProductionStation(4, 20, True, "M", ""),
                ProductionStation(5, 27, False, "M", ""),
                ProductionStation(6, 15, True, "", "")
            ]

    def update_all_stations(self, current_time: datetime) -> None:
        for station in self.stations:
            station.update(current_time)

    def find_and_assign_station(self, pizza_name: str, pizza_size: str, quantity: int, prod_time: int, delivery_deadline: datetime) -> Tuple[Optional[int], Optional[datetime]]:
        """
        Trouve le poste capable de finir le plus tôt possible (Earliest Finish Time).
        """
        best_station = None
        best_end_time = None

        for station in self.stations:
            # Quand ce poste peut-il commencer ?
            start_time = station.calculate_earliest_start(pizza_name, pizza_size, quantity)
            
            if start_time:
                end_time = start_time + timedelta(minutes=prod_time)
                
                # Est-ce que ça rentre dans le délai du client ?
                if end_time <= delivery_deadline:
                    # Est-ce que c'est mieux que ce qu'on a trouvé avant ?
                    # On privilégie le poste qui finit le plus tôt.
                    if best_end_time is None or end_time < best_end_time:
                        best_end_time = end_time
                        best_station = (station, start_time)
                    
                    # Load Balancing simple : Si deux postes finissent à la même heure (ex: maintenant),
                    # on pourrait choisir celui qui est le moins chargé, mais ici on privilégie la vitesse.

        if best_station:
            station_obj, start_t = best_station
            final_end = station_obj.assign_task(pizza_name, pizza_size, quantity, prod_time, start_t)
            return station_obj.id, final_end

        return None, None

    def display_queues(self):
        """Affiche l'utilisation de la capacité parallèle."""
        print("\n🏭 --- ÉTAT DES FOURS ---")
        now = datetime.now()
        
        for station in sorted(self.stations, key=lambda s: s.id):
            load = station.get_load_at_time(now)
            state = "✅" if station.is_available else "❌"
            
            ratio = load / station.max_capacity if station.max_capacity > 0 else 0
            bar_len = int(ratio * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            
            print(f"Poste {station.id} [{state}] [{bar}] {load}/{station.max_capacity} slots utilisés")
            
            active_tasks = [t for t in station.planning if t[1] <= now < t[2]]
            future_tasks = [t for t in station.planning if t[1] > now]
            
            for qty, s, e, name in active_tasks:
                print(f"   🔥 CUISSON : {qty}x {name:<10} (Fin : {e.strftime('%H:%M')})")
            for qty, s, e, name in future_tasks:
                
                wait = int((s - now).total_seconds()//60)
                print(f"   ⏳ RÉSERVÉ : {qty}x {name:<10} (Début : {s.strftime('%H:%M')} | +{wait}m)")
            
            if not active_tasks and not future_tasks:
                print("   (Vide)")
        print("----------------------------------------------")