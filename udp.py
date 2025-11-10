from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
from datetime import datetime, time, timedelta
from bdd import get_clients_table, get_pizzas_table


class BroadCastReceiver:
    
    def __init__(self, port, msg_len=8192, timeout = None):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        if timeout: self.sock.settimeout(timeout)
        self.sock.bind(('', port))
        self.msg_len = msg_len

    def __iter__(self):
        return self

    def __next__(self):
        try:
            data, addr = self.sock.recvfrom(self.msg_len)
            return data.decode(), addr
        except Exception as e:
            print("Got exception trying to recv %s" % e)
            raise StopIteration
             
    def __enter__(self):
        return self

    def __del__(self):
        self.sock.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()

def show_dict(dict: dict[str: any]):
    print("------------------------------------------")
    for key,value in dict.items():
        print(f'| {key:<15} | {value:<20} |')
    print("------------------------------------------\n")

def faisabilite(client_id: int, pizza_name: str, pizza_size: str, quantity: int, delivery_time: str):
    now = datetime.now()
    new_time = delivery_time.split(":")
    target_time = time(int(new_time[0]), int(new_time[1]), 0)
    future_time = datetime.combine(now.date(), target_time)
    duration = future_time - now
    pizza_list = get_pizzas_table()
    for pizza in pizza_list:
        if pizza["Nom"] == pizza_name and pizza["Taille"] == pizza_size:
            production_time = pizza["TPsProd"]
    clients_table = get_clients_table()
    distance_client = clients_table[f"{client_id}"]
    print("Client habite à", distance_client, "minutes.\
        \nTemps de préparation de commande :", production_time*quantity, "minutes. \
        \nHeure de livraison souhaité :", duration,
        "\nFaisabilité :", timedelta(minutes=distance_client+production_time*quantity)<duration)



with BroadCastReceiver(40100) as r:
    while True:
        data, addr = next(r)
        table = data.split(',')
        commande = {
            "Date / Heure": table[0],
            "ID": int(table[1]),
            "Pizza": table[2],
            "Taille": table[3],
            "Quantité": int(table[4]),
            "Heure souhaitée": table[5],
        }
        # show_dict(commande)
        faisabilite(commande["ID"], commande["Pizza"], commande["Taille"], commande["Quantité"], commande["Heure souhaitée"])