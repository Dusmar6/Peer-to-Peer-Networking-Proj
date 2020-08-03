import socket
import sys
import time
import threading
import random
import hashlib
import uuid
from os import listdir
from os.path import isfile, join

HOST = '127.0.0.1'
PORT = 8000


class node():

    def __init__(self, name, host, port):
        self.host = host
        self.port = port
        self.name = name
        self.EOT = b'0x004'
        
        # Keep track of nodes connected to us
        self.connectedNodes = []

        # Set flag for when a node is closed
        self.nodeOpen = True

        # Create unique node ID for each node 
        # (security not a major concern for this project so I chose a less secure 
        # hash of which is fast)
        num = hashlib.sha1()
        key = self.host + str(self.port) + str(random.randint(1, 9999))
        num.update(key.encode('utf-8'))
        self.id = num.hexdigest()

        # Start the TCP/IP socket for this node
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow sockets to multicast to other nodes

        #print("Node created!\nUsername: %s\nID: %s" % (self.name, self.id))
        

def mainNode(name, n):
    s = socket.socket()
    s.bind((n.host, n.port))
    s.listen(5)

    print("No connections found. Starting service.")
    time.sleep(0.1)
    print("Service Started...")
    time.sleep(0.1)
    print("Service listening")

    mainChild = True

    while n.nodeOpen:

        connection, addr = s.accept()
        clientID = connection.recv(1024).decode('utf-8')
        cID = clientID[:clientID.find(',')]
        cName = clientID[clientID.find(',') + 1:clientID.find(str(n.EOT))]
        print("Client connected!\nUsername: %s\nID: %s" % (cName, cID))

        if mainChild:
            mainChild = False
            thrd = threading.Thread(target=mainChildNode, args=(name, n))
            thrd.start()

           
    s.close()

def childNode(n):
    s = socket.socket()
    s.connect((n.host, n.port))
    identity = (n.id + "," + n.name + str(n.EOT)).encode('utf-8')
    s.send(identity)

    print("Connected to the network!")

    while n.nodeOpen:
        printMenu()
        choice = input('')
        time.sleep(0.1)
        executeMenu(n, choice)

def mainChildNode(name, mainNode):
    n = node(name, HOST, PORT)
    childNode(n)
    print("exited mainChild")
    return ''


def printMenu():
    print("What would you like to do?")
    time.sleep(0.1)
    print("1 --> See contents of all folders")
    time.sleep(0.1)
    print("2 --> Transfer all files")
    time.sleep(0.1)
    print("3 --> See connected Nodes")
    time.sleep(0.1)
    print("Enter y or Y to quit")


def executeMenu(n, choice):
    if choice == '1':
        fp = input('Filepath: ')
        print(getFileList(fp))
    elif choice == '2':
        transferFiles()
    elif choice == '3':
        getConnectedNodes()
    elif choice == 'y' or choice == 'Y':
        n.nodeOpen = False
    else:
        print("Enter Valid input please")



def getFileList(filepath):
    try:
        allFiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
        return allFiles
    except Exception as e:
        print("Filepath Invalid: " + str(e))
    return ''

def transferFiles():
    return ''

def getConnectedNodes():
    return '' 

def Main():

    name = "User: " + str(uuid.uuid4())
    n = node(name, HOST, PORT)

    while n.nodeOpen:
        try:
            childNode(n)
        except Exception:
            mainNode(name, n)

if __name__ == '__main__':
    Main()
        