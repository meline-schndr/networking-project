class Client:

    def __init__(self, client_id, client_distance):
        self.id = int(client_id)
        self.distance = int(client_distance)
        
    def __str__(self):
        return (f"Client ID: {self.id} | Client Distance: {self.distance}min")