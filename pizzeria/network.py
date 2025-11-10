from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR

class BroadCastReceiver:
    """
    Classe récepteur Broadcast UDP qui nous permet de recevoir les commandes de pizzas.
    """
    def __init__(self, port: int, msg_len: int = 8192, timeout:int = None) -> None:
        """
        Constructeur de la classe, nécessite forcément un port d'écoute, autre arguments optionnels.
        """
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        if timeout: self.sock.settimeout(timeout)
        self.sock.bind(('', port))
        self.msg_len = msg_len

    def __iter__(self):
        return self

    def __next__(self) -> tuple[str, any]:
        """
        Méthode pour récupérer nouvelle commande.
        """
        try:
            data, addr = self.sock.recvfrom(self.msg_len)
            return data.decode(), addr
        except Exception as e:
            print("Got exception trying to recv %s" % e)
            raise StopIteration
             
    def __enter__(self):
        return self

    def __del__(self):
        """
        Méthode pour arrêter l'écouter UDP.
        """
        self.sock.close()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Méthode pour arrêter l'écouter UDP.
        """
        self.sock.close()