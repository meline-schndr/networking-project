import socket
import sys
import time

##SERVEUR TCP + html
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST, PORT = 'localhost', 10000
sock.bind((HOST, PORT))
sock.listen(1)

print('SERVEUR @' + str(HOST) + ' SUR LE PORT ' + str(PORT))
print('EN ATTENTE DE CLIENT...')
connection, client_address = sock.accept()
print('NOUVEAU CLIENT ' + str(client_address))

cmpt=0
while True:

  data = connection.recv(2028).decode('utf-8')
  #print(data)

  cmpt+=1

  ##Creation du HEADER HTML
  connection.send('HTTP/1.0 200 OK\n'.encode())
  connection.send('Content-Type: text/html\n'.encode())
  connection.send('\n'.encode()) # le HEADER et le BODY doivent etre separes d'une ligne

  ##Creation du BODY HTML. Message HTML entre triple-quote
  message = \
  """<html>
    <body>
      <h1>Hello World</h1>
      Vos informations : """+str(client_address)+"""
      <br>
      Nombre de connexion(s) : """+str(cmpt)+"""
    </body>
  </html>"""
  connection.send(message.encode())
  connection.close()
  time.sleep(1)
  connection, client_address = sock.accept() #Attente d'un nouvel acces a la page HTML