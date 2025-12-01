from pizzeria import order_processor
import threading
import sys
from web.tcp import run_web_server_thread


class PizzeriaStats:
    def __init__(self):
        self.accepted_orders = 0
        self.refused_orders = 0

if __name__ == "__main__":
    print("[MAIN] > INFO: Lancement du système complet (Engine + Web)...")

    stats = PizzeriaStats()

    web_thread = threading.Thread(target=run_web_server_thread, args=(stats,), daemon=True)
    web_thread.start()

    try:
        order_processor.start_processing(stats)
        print("[MAIN] > SUCCESS: Script arrêté avec succès.")
    except KeyboardInterrupt:
        print("\n[MAIN] > Arrêt demandé par l'utilisateur.")
        sys.exit(0)