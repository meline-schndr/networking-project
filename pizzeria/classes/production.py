from datetime import datetime, timedelta
from typing import List, Tuple, Optional

class ProductionStation:
    """
    Représente un poste de production individuel.
    Gère sa capacité, ses restrictions et les tâches en cours.
    """
    def __init__(self, station_id: int, max_capacity: int, is_available: bool, supported_size: str, restrictions_str: str):
        self.id = station_id
        self.max_capacity = int(max_capacity) 
        self.is_available = is_available
        self.supported_size = supported_size # "" (toutes), "G" ou "M"
        
        self.restrictions = set(r.strip() for r in restrictions_str.split(',') if r.strip() and r.strip() != '---')
        
        self.tasks_in_progress: List[Tuple[int, datetime]] = [] 

    def get_used_capacity(self) -> int:
        """Calcule la capacité actuellement utilisée par les tâches en cours."""
        return sum(quantity for quantity, production_end_time in self.tasks_in_progress)

    def update(self, current_time: datetime) -> None:
        """
        Nettoyage : Supprime les tâches dont l'heure de fin est passée,
        libérant ainsi de la capacité pour de nouvelles commandes.
        """
        self.tasks_in_progress = [
            task for task in self.tasks_in_progress 
            if task[1] > current_time
        ]

    def can_accept(self, pizza_name: str, pizza_size: str, quantity: int) -> bool:
        """Vérifie si le poste peut accepter une nouvelle commande en fonction des restrictions, taille, et capacité."""
        
        # 1. Disponibilité
        if not self.is_available:
            return False
            
        # 2. Restriction
        if pizza_name in self.restrictions:
            return False
            
        # 3. Taille supportée
        # self.taille_supportee == "" signifie "toutes les tailles"
        if self.supported_size != "" and pizza_size != self.supported_size:
            return False
            
        # 4. Capacité restante
        remaining_capacity = self.max_capacity - self.get_used_capacity()
        if quantity > remaining_capacity:
            return False
            
        return True

    def assign_task(self, pizza_name: str, pizza_size: str, quantity: int, prod_time_per_pizza: int) -> datetime:
        """
        Ajoute une nouvelle tâche au poste et retourne son heure de fin.
        L'heure de fin est basée sur le TPsProd d'une seule pizza, car la capacité
        permet de faire les N pizzas en parallèle.
        """
        
        production_end_time = datetime.now() + timedelta(minutes=prod_time_per_pizza)

        self.tasks_in_progress.append((quantity, production_end_time))
        
        print(f"[STATION {self.id}] INFO > Nouvelle tâche : {quantity}x {pizza_name} ({pizza_size}). Capacité restante : {self.max_capacity - self.get_used_capacity()}. Tâche finie dans {production_end_time.strftime('%Hh%M')}.")
        
        return production_end_time


class ProductionManager:
    """
    Gère l'ensemble des postes de production.
    """
    def __init__(self, db_instance):
        self.stations: List[ProductionStation] = []
        self._load_stations(db_instance)

    def _load_stations(self, db):
        """Charge les postes depuis la BDD."""
        try:
            self.stations = db.get_table("Production")
            print(f"[PRODUCTION] > INFO: {len(self.stations)} postes de production chargés (Disponibles : {sum(1 for s in self.stations if s.is_available)}).")
        except Exception as e:
            print(f"[PRODUCTION] > ERROR: Impossible de démarrer les postes de production {e}")

    def update_all_stations(self, current_time: datetime) -> None:
        """Appelle la méthode de nettoyage sur tous les postes pour libérer la capacité."""
        for station in self.stations:
            station.update(current_time)
            
    def find_and_assign_station(self, pizza_name: str, pizza_size: str, quantity: int, prod_time_per_pizza: int) -> Tuple[Optional[int], Optional[datetime]]:
        """
        Cherche le premier poste disponible qui peut prendre la commande et l'assigne.
        """
        
        for station in sorted(self.stations, key=lambda s: s.id):
            if station.can_accept(pizza_name, pizza_size, quantity):
                production_end_time = station.assign_task(pizza_name, pizza_size, quantity, prod_time_per_pizza)
                return station.id, production_end_time
        
        return None, None
    
    def display_queues(self):
        """Affiche l'état actuel de tous les postes de production dans la console."""
        print("\n🏭 --- ÉTAT DES FILES D'ATTENTE (USINE) ---")
        
        for station in sorted(self.stations, key=lambda s: s.id):
            used = station.get_used_capacity()
            state = "✅ OUVERT" if station.is_available else "❌ FERMÉ"
            
            if station.max_capacity > 0:
                percent = min(10, int((used / station.max_capacity) * 10))
            else:
                percent = 0
            bar = "█" * percent + "░" * (10 - percent)
            
            print(f"Poste {station.id} [{state}] : [{bar}] Charge: {used}/{station.max_capacity}")
            

            if station.tasks_in_progress:
                for i, (qty, end_time) in enumerate(station.tasks_in_progress, 1):
                    remaining = end_time - datetime.now()
                    mins_left = int(remaining.total_seconds() // 60)
                    print(f"   ╚═ Tâche #{i} : {qty} pizzas (Fin : {end_time.strftime('%H:%M')} -> dans {mins_left} min)")
            else:
                print("   ╚═ (Libre)")
        
        print("----------------------------------------------\n")