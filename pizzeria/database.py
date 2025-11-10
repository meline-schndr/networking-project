import psycopg2
from psycopg2 import sql

class Database:
    """
    Classe base de données qui nous permet de récupérer tous les clients et les types de pizza.
    TODO: Ajouter une méthode pour récupérer la table de production
    """


    _ALLOWED_PIZZA_COLUMNS = ["Nom", "Taille", "Composition", "TPsProd", "Prix"]
    _ALLOWED_CLIENT_COLUMNS = ["ID", "Distance"]

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

    def get_clients_table(self) -> dict[int] | dict[None]:
        """
        Méthode pour récupérer la BDD Client.

        -> Retourne : dict{'ID client': distance_client} 

        """
        if not self.cur: return {}
        
        self.cur.execute(""" SELECT "ID", "Distance" FROM "Client" """)
        client_dicts = {}
        for ID, Distance in self.cur.fetchall():
            client_dicts[f"{ID}"] = Distance
        return client_dicts

    def get_pizzas_table(self, *columns_to_fetch: tuple[str]) -> list[dict] | list[None]:
        """
        Méthode pour récupérer la table des pizzas.
        
        - Si aucun argument n'est donné, prend toutes les colonnes.
        - Si des arguments sont donnés (ex: "Nom", "Taille"), 
          prend seulement ces colonnes.

        -> Retourne : liste de dictionnaire définissant chaque pizza (Nom, Taille, etc.)
                
        TODO: Ajouter documentation sur cette méthode car peu instinctive
        """
        if not self.cur: return []

        cols_to_build_sql = [] # Objets SQL sécurisés
        cols_to_return_str = [] # Noms des colonnes (str) pour le dict final

        # 1. Déterminer et valider les colonnes
        if not columns_to_fetch:
            # Cas 1: Pas d'argument, on prend tout (depuis la whitelist)
            columns_to_fetch = self._ALLOWED_PIZZA_COLUMNS
        
        for col_name in columns_to_fetch:
            if col_name in self._ALLOWED_PIZZA_COLUMNS:
                # On ajoute le nom formaté (ex: "Nom") à la liste SQL
                cols_to_build_sql.append(sql.Identifier(col_name))
                # On ajoute le nom simple (ex: Nom) à la liste str
                cols_to_return_str.append(col_name)
            else:
                # Si la colonne n'est pas dans la whitelist, on l'ignore
                print(f"[DATABASE] > WARNING: Colonne '{col_name}' ignorée (non valide ou non autorisée).")
        
        if not cols_to_build_sql:
            print("[DATABASE] > ERROR: Aucune colonne valide à récupérer.")
            return []

        # 2. Construire la requête de manière sécurisée
        # sql.SQL(', ').join(...) va créer "Nom", "Taille", "TPsProd"
        query = sql.SQL('SELECT {cols} FROM "Pizza"').format(
            cols=sql.SQL(', ').join(cols_to_build_sql)
        )
        
        # 3. Exécuter et formater
        self.cur.execute(query)
        pizza_list = []
        for row in self.cur.fetchall():
            # zip() combine les noms de colonnes et les valeurs
            # ex: zip(["Nom", "Taille"], ["Veggie", "G"]) -> [("Nom", "Veggie"), ("Taille", "G")]
            # dict() transforme cela en {"Nom": "Veggie", "Taille": "G"}
            pizza_dict = dict(zip(cols_to_return_str, row))
            pizza_list.append(pizza_dict)
            
        return pizza_list