import psycopg2
import datetime

#Etablissement de la connexion au serveur de base de données
conn = psycopg2.connect(dbname = 'UE_ENS_PROJET', user = 'pguser', password = 'pguser', host = '192.168.40.117', port = '5432')
cur = conn.cursor()


def get_clients_table():
    cur.execute(""" SELECT "ID", "Distance" FROM "Client" """)
    client_dicts = {}
    for ID,Distance in cur.fetchall() :
        client_dicts[f"{ID}"] = Distance
    return client_dicts

def get_pizzas_table():
    cur.execute(""" SELECT "Nom", "Taille", "Composition", "TPsProd", "Prix" FROM "Pizza" """)

    pizza_list = []
    for Nom,Taille,Composition,TPsProd,Prix in cur.fetchall():
        pizza_list.append({
            "Nom": Nom,
            "Taille": Taille,
            "Composition": Composition,
            "TPsProd": TPsProd,
            "Prix": Prix
        })
    return pizza_list
        
def show_dict(dict: dict[str: any]):
    print("---------------------------------------------------")
    for key,value in dict.items():
        print(f'| {key:<15} | {value:<29} |')
    print("---------------------------------------------------\n")


if __name__ == "__main__":
    show_dict(get_clients_table())
    
    pizza_list = get_pizzas_table()
    for pizza in pizza_list:
        show_dict(pizza)