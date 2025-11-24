from datetime import datetime, timedelta
from typing import List, Tuple, Optional

class ProductionStation:
    """
    Poste de production gérant la capacité PARALLÈLE.
    """
    def __init__(self, station_id: int, max_capacity: int, is_available: bool, supported_size: str, restrictions_str: str):
        self.id = station_id
        self.max_capacity = int(max_capacity)
        self.is_available = is_available
        self.supported_size = supported_size
        self.restrictions = set(r.strip() for r in restrictions_str.split(',') if r.strip() and r.strip() != '---')
        
        # Format: (quantity, start_time, end_time, pizza_name, pizza_size)
        self.planning: List[Tuple[int, datetime, datetime, str, str]] = [] 

    def __str__(self):
        return f"ID: {self.id} | Capacité : {self.max_capacity} | Taille : {self.supported_size} | Restrict. : {self.restrictions}"

    def update(self, current_time: datetime) -> None:
        # On ne garde que les tâches qui finissent dans le futur
        self.planning = [t for t in self.planning if t[2] > current_time]

    def get_load_at_time(self, t: datetime) -> int:
        return sum(qty for qty, start, end, _, _ in self.planning if start <= t < end)

    def check_capacity_interval(self, start_t: datetime, end_t: datetime, qty_needed: int) -> bool:
        """
        Vérifie si la capacité est suffisante sur TOUT l'intervalle [start_t, end_t].
        """
        # 1. Vérifier la charge au moment du lancement
        if (self.max_capacity - self.get_load_at_time(start_t)) < qty_needed:
            return False

        # 2. Vérifier les pics de charge futurs pendant la cuisson
        for task_qty, task_start, task_end, _, _ in self.planning:
            # Si une autre tâche commence PENDANT que la nôtre est en cours
            if start_t < task_start < end_t:
                # On vérifie si ça passe à ce moment précis
                if (self.max_capacity - self.get_load_at_time(task_start)) < qty_needed:
                    return False
        return True

    def calculate_earliest_start(self, pizza_name: str, pizza_size: str, quantity: int, duration_minutes: int) -> Optional[datetime]:
        """Trouve le créneau le plus tôt disponible pour une durée donnée."""
        # Si poste est désactivé
        if not self.is_available: return None
        # Si le poste interdit la pizza 
        if pizza_name in self.restrictions: return None
        # Si le poste ne prend pas cette taille de pizza
        if self.supported_size != "-" and pizza_size != self.supported_size: return None
        # Si on dépasse la capacité max du poste
        if quantity > self.max_capacity: return None

        try:
            now = datetime.now()
            duration = timedelta(minutes=duration_minutes)

            # On teste "Maintenant" et chaque moment où une tâche se termine
            potential_starts = [now] + [t[2] for t in self.planning if t[2] > now]
            potential_starts.sort()

            for start_t in potential_starts:
                # Petit décalage pour être sûr d'être après la fin de la tâche précédente
                if start_t != now:
                    start_t += timedelta(seconds=1)

                end_t = start_t + duration
                
                # Utilisation de la nouvelle vérification sur intervalle
                if self.check_capacity_interval(start_t, end_t, quantity):
                    return start_t

            return None
        except Exception as e:
            print(f"[PROD] > ERROR: {e}")

    def assign_task(self, pizza_name: str, pizza_size: str, quantity: int, prod_time: int, start_time: datetime) -> datetime:
        end_time = start_time + timedelta(minutes=prod_time)
        self.planning.append((quantity, start_time, end_time, pizza_name, pizza_size))
        return end_time


class ProductionManager:
    def __init__(self, db_instance):
        self.stations: List[ProductionStation] = []
        self._load_stations(db_instance)

    def _load_stations(self, db):
        try:
            self.stations = db.get_table("Production")
        except Exception:
            self.stations = []
        self.stations.sort(key=lambda s: s.id)
        for station in self.stations:
        
            print(station )

    def update_all_stations(self, current_time: datetime) -> None:
        for station in self.stations:
            station.update(current_time)

    def find_and_assign_station(self, pizza_name: str, pizza_size: str, quantity: int, prod_time: int, delivery_deadline: datetime) -> Tuple[Optional[int], Optional[datetime]]:
        best_station = None
        best_end_time = None

        for station in self.stations:
            start_time = station.calculate_earliest_start(pizza_name, pizza_size, quantity, prod_time)
            if start_time:
                end_time = start_time + timedelta(minutes=prod_time)
                
                if end_time <= delivery_deadline:
                    if best_end_time is None or end_time < best_end_time:
                        best_end_time = end_time
                        best_station = (station, start_time)


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
            
            if station.restrictions == {'-'}:
                print(f"Poste {station.id} [{state}] [{bar}] {load}/{station.max_capacity} slots utilisés")
            else:
                print(f"Poste {station.id} [{state}] [{bar}] {load}/{station.max_capacity} slots utilisés [🚫 {station.restrictions}]")
            
            active_tasks = [t for t in station.planning if t[1] <= now < t[2]]
            future_tasks = [t for t in station.planning if t[1] > now]
            
            for qty, s, e, name, size in active_tasks:
                print(f"   🔥 CUISSON : {qty}x {name:<10} {size} (Fin : {e.strftime('%H:%M')})")
            for qty, s, e, name, size in future_tasks:
                
                wait = int((s - now).total_seconds()//60)
                print(f"   ⏳ RÉSERVÉ : {qty}x {name:<10} {size} (Début : {s.strftime('%H:%M')} | +{wait}m)")
            
            if not active_tasks and not future_tasks:
                print("   (Vide)")
        print("----------------------------------------------")