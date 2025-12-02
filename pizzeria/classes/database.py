import psycopg2

from .client import Client
from .pizza import Pizza
from .production import ProductionStation
from psycopg2 import sql

class Database:
    """
    Classe base de données qui nous permet de récupérer tous les clients et les types de pizza.
    """

    def __init__(self, dbname: str = 'UE_ENS_PROJET', user: str = 'pguser', password: str = 'pguser', host: str = 'localhost', port: str = '5432') -> None:
        """
        Constructeur de la classe, par défaut, se connecte à une machine en local qui contient les bases de données.
        TODO: Implémenter 'dotenv' (library Python pour masquer mot de passe)
        """
        # Tentative de connexion à la DB centrale
        try:
            self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            self.cur = self.conn.cursor()
            self._ALLOWED_COLUMNS = {}
            print("[DATABASE] > SUCCESS: Connexion à la BDD réussie.")
            self.get_columns("Client", "Pizza", "Production")

        # FALLBACK d'erreur -> pas réussi à se connecter
        except psycopg2.OperationalError as e:
            print(f"[DATABASE] > ERROR: {e.args[0].split("\n")[0]}")
            self.conn = None
            self.cur = None

    def __del__(self) -> None:
        """
        Méthode pour se déconnecter du serveur des bases de données.
        (C'est pour faire les choses proprement parce qu'ici on aime la propreté.)
        """
        if self.cur: self.cur.close()
        if self.conn:
            self.conn.close()
            print("[DATABASE] > INFO: Connexion à la BDD fermée.")
    
    def get_entity(self, table_name: str, *filters: tuple[str, any]) -> Client | Pizza | ProductionStation | None:
        """
        NOTE:   Il n'est pas impossible qu'entre le moment où le script se lance,
                de nouveau clients aient commandé.
                ->  Table des clients désynchronisée donc client inconnu puisqu'on 
                    fetch la DB qu'au lancement du script.

                Cette méthode permet donc de vérifier si une 'entité' (élément)
                existe bel et bien.

                Dans ce cas, on update la liste des objets (clients) pour ajouter ce
                nouveau client.

                On en profite également pour extrapoler en imaginant que cela pouvait
                aussi arriver pour des nouveau types de pizza, ou même que l'usine de
                prod est modifiée.

                ->  D'où l'utilisation d'une méthode unique qui prend un/des *args
                    au lieu d'avoir une méthode pour chaque DB.

        TLDR:   Récupère une entité unique depuis la BDD en fonction de filtres dynamiques.
        
        USE:
            db.get_entity("Client", ("ID", 529997))
            db.get_entity("Pizza", ("Nom", "Veggie"), ("Taille", "G"))

        """

        # Vérifications préventives de la table et récupération des colonnes autorisées
        if not self.cur: return None
        self.__init__()
        if table_name not in self._ALLOWED_COLUMNS:
            print(f"[DATABASE] > ERROR: Table '{table_name}' inconnue.")
            return None

        columns = self._ALLOWED_COLUMNS[table_name]
        
        # Construction de la requête SQL de base.
        # On sélectionne explicitement les colonnes pour garantir l'ordre 
        # (assez important à l'unpack un peu après.)
        query = sql.SQL("SELECT {cols} FROM {table}").format(
            cols=sql.SQL(', ').join(map(sql.Identifier, columns)),
            table=sql.Identifier(table_name)
        )

        # Construction dynamique des filtres pour trouver l'entité.
        # (Condition SQL 'WHERE')
        if filters:
            where_parts = []
            query_values = []

            # Pour chaque couple (nom_propriété, valeur_propriété)
            for col_name, val in filters:
                # Sécurité : On vérifie que la colonne existe pour cette table
                if col_name not in columns:
                    print(f"[DATABASE] > WARN: Colonne '{col_name}' invalide pour {table_name}.")
                    return None
                
                # On ajoute "NomColonne = %s" à notre condition WHERE

                # Ex1: "ID = 53612"
                # Ex2: "Nom = Hawaïenne" (oui c'est un code engagé l'ananas c'est cool ptdr)
                where_parts.append(sql.SQL("{} = %s").format(sql.Identifier(col_name)))
                query_values.append(val)
            
            # Une fois les filtres parcourus, on colle les morceaux 
            # avec des " AND " à notre query initiale
            query += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_parts)
        else:
            # Pas de filtre ? On ne veut probablement pas récupérer TOUTE la table ici
            return None

        try:
            # Exécution de la requête SQL
            self.cur.execute(query, tuple(query_values))

            # Tuple réponse
            row = self.cur.fetchone()

            # Si tuple de réponse -> table locale pas à jour donc faut update la notre
            if row:
                print(f"[DATABASE] > INFO: Entité trouvée dynamiquement dans {table_name}.")

                # Mise à jour de la DB locale
                # L'opérateur *row "déplie" le tuple pour le passer en arguments au constructeur
                if table_name == "Client": return Client(*row) 
                elif table_name == "Pizza": return Pizza(*row)
                elif table_name == "Production": return ProductionStation(*row)
            
            # Si pas de tuple -> vraie erreur parce client inexistant dans DB centrale
            return None

        # FALLBACK au cas où y'aurait une erreur de con
        except Exception as e:
            print(f"[DATABASE] > ERROR (get_entity): {e}")
            # Protection du rollback pour éviter le crash FATAL
            try:
                if self.conn and not self.conn.closed:
                    self.conn.rollback()
            except Exception:
                pass # Si le rollback échoue, on ignore
            return None

    def get_columns(self, *table_name: tuple[str]):
        """
        Méthode qui récupère les colonnes d'une ou plusieurs DB.

        """
        try:
            for name in table_name:
                query = sql.SQL('SELECT * FROM "{table_name}" LIMIT 0').format(
                        table_name = sql.SQL(name)
                    )
                self.cur.execute(query)

                colnames = [desc[0] for desc in self.cur.description]

                self._ALLOWED_COLUMNS[name] = colnames

        except Exception as e:
            print(f"[DATABASE] > WARN: Échec de l'introspection ({e}). Utilisation du schéma par défaut.")
            self._ALLOWED_COLUMNS = {
            "Client":       ["ID",      "Distance"],
                            # int       # int
            "Pizza":        ["Nom",     "Taille",       "Composition",      "TPsProd",  "Prix"],
                            # str       # str           # str               # int       # int
            "Production":   ["Poste",   "Capacite",     "Disponibilite",    "Taille",   "Restriction"]
                            # int       # int           # bool              # str       # str
            }

    def get_table(self, table_name: str, *columns_to_fetch: tuple[str]) -> list[Client] | list[Pizza] | list:
        """
        Méthode pour récupérer les lignes d'une base de données.
        Gérée dynamiquement avec un *columns_to_fetch parce que c'est cool et ça évite
        De faire plusieurs méthodes qui se ressemblent pour chaqune des DB.

        Paramètres : 
        - str          table_name        : Le nom de la base de données à récupérer
        - tuple[str]   *columns_to_fetch : Les colonnes à récupérer (Non précisé -> Toutes)

        -> Retourne une liste d'objets Client/Pizza/Poste

        """

        # Check pour s'assurer qu'on est bien connecté à la DB centrale
        if not self.cur: return []

        # Colonnes
        cols_to_build_sql = []
        cols_to_return_str = [] 

        # Si le nom de la DB est bien dans notre dico -> On continue
        if table_name in self._ALLOWED_COLUMNS.keys():

            # Si on ne connait pas les colonnes de la DB, on les récupère
            # avec notre dico général
            if not columns_to_fetch:
                columns_to_fetch =  self._ALLOWED_COLUMNS[table_name]

            # Boucle pour unpack les différentes colonnes de la DB à récupérer
            for col_name in columns_to_fetch:
                if col_name in self._ALLOWED_COLUMNS[table_name]:
                    cols_to_build_sql.append(sql.Identifier(col_name))
                    cols_to_return_str.append(col_name)

                else:
                    print(f"[DATABASE] > WARNING: Colonne '{col_name}' ignorée (non valide ou non autorisée).")

            # FALLBACK si le code ne trouve pas de colonnes valides à récupérer
            if not cols_to_build_sql:
                print("[DATABASE] > ERROR (get_table): Aucune colonne valide à récupérer.")
                return []

            # On construit notre requête SQL en fonction des colonnes qu'on a demandé.
            query = sql.SQL('SELECT {cols} FROM "{table_name}"').format(
                cols=sql.SQL(', ').join(cols_to_build_sql),
                table_name = sql.SQL(table_name)
            )

            # On execute notre requête
            self.cur.execute(query)

            # Liste des objets récupérés
            table_list = []

            # Pour chaque ligne de DB qu'on a récupéré, on créé un objet et 
            # on l'ajoute à une liste d'objets.
            for row in self.cur.fetchall():
                if table_name == "Client":
                    client = Client(*row)
                    table_list.append(client)
                elif table_name == "Pizza":
                    pizza = Pizza(*row)
                    table_list.append(pizza)
                elif table_name == "Production":
                    prod_station = ProductionStation(*row)
                    table_list.append(prod_station)

            # On renvoie la DB 'locale', qui est une liste d'objets.
            return table_list
        
        # FALLBACK si le nom de la base de données n'existe pas dans notre dico
        print("[DATABASE] > WARN: Base de donnée non renseignée.")
        return []
    
    def __del__(self):
        """
        Destructeur : Ferme le curseur et la connexion.
        Ceci est appelé automatiquement lorsque l'objet n'est plus utilisé.
        (On aime toujours autant la propreté ici)
        """
        if hasattr(self, 'cur') and self.cur: 
            self.cur.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("[DATABASE] > INFO: Connexion à la BDD fermée proprement.")