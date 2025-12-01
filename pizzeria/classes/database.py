import psycopg2

from .client import Client
from .pizza import Pizza
from .production import ProductionStation
from psycopg2 import sql

class Database:
    """
    Classe base de données qui nous permet de récupérer tous les clients et les types de pizza.
    TODO: Ajouter une méthode pour récupérer la table de production
    """


    _ALLOWED_COLUMNS = {
        "Client":       ["ID",      "Distance"],
                        # int       # int
        "Pizza":        ["Nom",     "Taille",       "Composition",      "TPsProd",  "Prix"],
                        # str       # str           # str               # int       # int
        "Production":   ["Poste",   "Capacite",     "Disponibilite",    "Taille",   "Restriction"]
                        # int       # int           # bool              # str       # str
    }

    def __init__(self, dbname: str = 'UE_ENS_PROJET', user: str = 'pguser', password: str = 'pguser', host: str = 'localhost', port: str = '5432') -> None:
        """
        Constructeur de la classe, par défaut, se connecte à une machine en local qui contient les bases de données.
        TODO: Implémenter 'dotenv' (library Python pour masquer mot de passe)
        """
        try:
            self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            self.cur = self.conn.cursor()
            print("[DATABASE] > SUCCESS: Connexion à la BDD réussie.")
        except psycopg2.OperationalError as e:
            print(f"[DATABASE] > ERROR: Impossible de se connecter à la BDD. {e}")
            self.conn = None
            self.cur = None

    def __del__(self) -> None:
        """
        Méthode pour se déconnecter du serveur des bases de données.
        """
        if self.cur: self.cur.close()
        if self.conn:
            self.conn.close()
            print("[DATABASE] > INFO: Connexion à la BDD fermée.")
    
    def update_table(self):
        return


    def get_table(self, table_name: str, *columns_to_fetch: tuple [str]) -> list[Client] | list[Pizza] | list:
        """
        Méthode pour récupérer les colonnes d'une base de données.

        Paramètres : 
        - str          table_name        : Le nom de la base de données à récupérer
        - tuple[str]   columns_to_fetch  : Les colonnes à récupérer (Non précisé -> Toutes)

        -> Retourne une liste d'objets Client/Pizza/Poste

        
        """
        if not self.cur: return []

        cols_to_build_sql = []
        cols_to_return_str = [] 

        if table_name in self._ALLOWED_COLUMNS.keys():
            if not columns_to_fetch:
                columns_to_fetch =  self._ALLOWED_COLUMNS[table_name]

            for col_name in columns_to_fetch:
                if col_name in self._ALLOWED_COLUMNS[table_name]:
                    cols_to_build_sql.append(sql.Identifier(col_name))

                    cols_to_return_str.append(col_name)

                else:
                    print(f"[DATABASE] > WARNING: Colonne '{col_name}' ignorée (non valide ou non autorisée).")

            if not cols_to_build_sql:
                print("[DATABASE] > ERROR: Aucune colonne valide à récupérer.")
                return []

            query = sql.SQL('SELECT {cols} FROM "{table_name}"').format(
                cols=sql.SQL(', ').join(cols_to_build_sql),
                table_name = sql.SQL(table_name)
            )

            self.cur.execute(query)
            table_list = []

            for row in self.cur.fetchall():
                if table_name == "Client":
                    client = Client(row[0], row[1])
                    table_list.append(client)
                elif table_name == "Pizza":
                    pizza = Pizza(row[0], row[1], row[2], row[3], row[4])
                    table_list.append(pizza)
                elif table_name == "Production":
                    prod_station = ProductionStation(row[0], row[1], row[2], row[3], row[4])
                    table_list.append(prod_station)

            return table_list
            
        
        print("[DATABASE] > WARN: Base de donnée non renseignée.")
        return []
    
    def __del__(self):
        """
        Destructeur : Ferme le curseur et la connexion.
        Ceci est appelé automatiquement lorsque l'objet n'est plus utilisé.
        """
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            print("[DATABASE] INFO > Connexion à la BDD fermée.")