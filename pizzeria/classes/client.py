class Client:

    def __init__(self, client_id, client_distance):
        self.client_id = int(client_id)
        self.client_distance = int(client_distance)
        
    def __str__(self):
        return (f"Client ID: {self.client_id} | Client Distance: {self.client_distance}min")