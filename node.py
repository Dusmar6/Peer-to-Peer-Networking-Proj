import socket
import sys
import time
import threading
import random
import hashlib
import uuid
import os
from os import listdir
from os.path import isfile, join

HOST = '127.0.0.1'
PORT = 8000
BUFFER_SIZE = 1024


class node():

    def __init__(self, name, host, port, filepath = os.getcwd()):
        self.host = host
        self.port = port
        self.name = name
        self.fp = filepath

        # Set Control Characters for process, message and transmission
        # I know this isn't the proper way to do it, but it works
        self.IDENTIFIER = "P01"
        self.FILEPATH = "P02"
        self.FILELIST = "P03"
        self.FILEDATA = "P04"

        self.OK = "MOK"
        self.ERR = "MER"

        self.STX = "T02"
        self.ETX = "T03"
        self.EOT = "T04"


        self.CCLEN = len(self.IDENTIFIER)
        
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

        # # Start the TCP/IP socket for this node
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Node created!\nUsername: %s\nID: %s" % (self.name, self.id))

    def get_file_list(self):
        return [f for f in listdir(self.fp) if isfile(join(self.fp, f))]

def server_node(name, n):
    s = socket.socket()
    s.bind((n.host, n.port))
    s.listen(5)

    print("No connections found. Starting service.")
    time.sleep(0.1)
    print("Service Started...")
    time.sleep(0.1)
    print("Service listening")

    while n.nodeOpen:

        conn, addr = s.accept()

        t = threading.Thread(target=new_connection, args=(str(addr[0]), n, conn))
        t.start()


def client_node(n):
    s = socket.socket()
    s.connect((n.host, n.port))
    identity = n.IDENTIFIER + n.id + n.ETX + n.name + n.EOT
    s.send(identity.encode('utf-8'))
    print("Connected to the network!")

    while n.nodeOpen:

        print_menu()
        inp = input("")
        if inp == 'y':
            n.nodeOpen = False
        if inp == '1':
            print("CWD has following inside:")
            for f in n.get_file_list():
                print("  " + f)
        if inp == '2':
           print(n.fp)
        if inp == '3':
            n.fp = n.fp + "\\share"
        if inp == '4':
            message = n.FILEPATH + n.fp + n.EOT
            print("Sending: " + message)
            s.send(message.encode('utf-8'))
        if inp == '5':
            message = n.FILELIST + ' '.join(n.get_file_list()) + n.EOT
            print("Sending: " + message)
            s.send(message.encode('utf-8'))
        if inp == '6':
            n.fp = n.fp + "\\share"
            for f in n.get_file_list():
                truepath = n.fp + "\\" + f
                fsize = os.path.getsize(truepath)
                message = n.FILEDATA + f + n.ETX + str(fsize) + n.EOT
                print("Sending: " + message)
                s.send(message.encode('utf-8'))
                with open(truepath, 'rb') as f:
                    bytessent = 0
                    while bytessent < fsize:
                        data = f.read(BUFFER_SIZE)
                        s.send(data)
                        bytessent += len(data)

                f.close()
                print("Sent Successfully!")


def new_connection(name, n, sock):
    while True:
        data = sock.recv(BUFFER_SIZE).decode('utf-8')

        if data[:n.CCLEN] == n.IDENTIFIER:
            cID = data[n.CCLEN:data.find(n.ETX)]
            cName = data[data.find(n.ETX) + len(n.ETX):]
            print("Client connected!\nUsername: %s\nID: %s" % (cName, cID))
        if data[:n.CCLEN] == n.FILEPATH:
            fp = data[n.CCLEN:data.find(n.EOT)]
            print(fp)
        if data[:n.CCLEN] == n.FILELIST:
            fl = data[n.CCLEN:data.find(n.EOT)]
            print(fl)
        if data[:n.CCLEN] == n.FILEDATA:
            fsize = int(data[data.find(n.ETX) + len(n.ETX):data.find(n.EOT)])
            fname = data[n.CCLEN:data.find(n.ETX)]
            print("Receiving file named: %s and of size: %d " % (fname, fsize))
            truepath = n.fp + "\\" + fname
            f = open(truepath, 'wb')
            bytesrecv = 0
            while bytesrecv < fsize:
                newdata = sock.recv(BUFFER_SIZE)
                bytesrecv += len(newdata)
                f.write(newdata)
            print("File received!")



def print_menu():
    print("What would you like to do?")
    time.sleep(0.1)
    print("1 --> See contents of your folders")
    time.sleep(0.1)
    print("2 --> See file path")
    time.sleep(0.1)
    print("3 --> Set file path")
    time.sleep(0.1)
    print("4 --> Send your file path")
    time.sleep(0.1)
    print("5 --> Send file names in your file path")
    time.sleep(0.1)
    print("Enter y or Y to quit")


def main():

    name = "User: " + str(uuid.uuid4())
    n = node(name, HOST, PORT)

    while n.nodeOpen:
        try:
            client_node(n)
        except Exception:
            server_node(name, n)



if __name__ == '__main__':
    main()