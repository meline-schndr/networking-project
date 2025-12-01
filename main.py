from pizzeria import order_processor
import threading
import sys
from web.tcp import run_web_server_thread
from pizzeria.classes.stats import SharedContext, PizzeriaStats

if __name__ == "__main__":
    print("[MAIN] > INFO: Lancement du système complet (Engine + Web)...")

    context = SharedContext()

    context.stats = PizzeriaStats()

    web_thread = threading.Thread(target=run_web_server_thread, args=(context,), daemon=True)
    web_thread.start()

    try:
        order_processor.start_processing(context)
        print("[MAIN] > SUCCESS: Script arrêté avec succès.")
    except KeyboardInterrupt:
        print("\n[MAIN] > Arrêt demandé par l'utilisateur.")
        sys.exit(0)