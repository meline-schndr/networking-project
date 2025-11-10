from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR

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