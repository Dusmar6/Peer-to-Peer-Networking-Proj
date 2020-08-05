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
import file
import files as f
import PySimpleGUI as sg
import json

HOST = '127.0.0.1'
PORT = 8000
BUFFER_SIZE = 1024

sock_list = []
masterlist = []

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
        self.DEL = "DEL" #send del + file name
        self.ADD = "ADD" #send add + file name + filesize + file data
        self.UPD = "UPD" #send udp + file name + filesize + file data (overwrite the file with this name)
        self.MAS = "MAS" #send MAS + masterlist


        self.CCLEN = len(self.DEL)
        
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
    
    t = threading.Thread(target=accept, args=(s, n))
    t.start()
    
    k = threading.Thread(target=host_scan, args=(s, n))
    k.start()
    
    while True:
        host_menu()
        inp = int(input())
        
        if inp == 1:
            host_delete_file()
        elif inp == 2:
            try:
                os.startfile(os.path.dirname(os.path.realpath(__file__)), 'share')
            except:
                check()
        elif inp == 3:
            for sock in sock_list:
                sock.close()
            
def host_menu():
    print("1: Delete File.\n2: Open Folder\n3: Disconnect")
    
def host_delete_file():
    sg.theme('Default1')
    layout = [
         [sg.Listbox(f.get_file_names(), size=(50, 10), key='list')],
          sg.Button('Delete File')
    ]
    hel = sg.Window('Pee2pee', layout)
    while True:
        event, values = hel.read()
        if event is None:
            break
        if event =='Delete File':
            filename = values['list'][0]
            print("Deleting", filename)
            if filename != '' and filename != None:
                try:
                    os.remove(f.get_filepath(filename)) #removes it locally
                    for file in masterlist:
                        if file.name == filename:
                            masterlist.remove(file)
                            print("todo: send out message to delete the file with this name")
                    #send message to everyone to delete the file
                except:
                    print("File could not be deleted.")

def host_update_file(path):
    global masterlist
    global sock_list

    for sock in sock_list:
        truepath = path
        fsize = os.path.getsize(truepath)
        message = node.ADD + truepath + node.ETX + str(fsize) + node.EOT
        print("Sending: " + message)
        sock.send(message.encode('utf-8'))
        with open(truepath, 'rb') as f:
            bytessent = 0
            while bytessent < fsize:
                data = f.read(BUFFER_SIZE)
                sock.send(data)
                bytessent += len(data)

            f.close()
            print("Sent Successfully!")
    print("todo: update master list, send file to everyone, tell them to overwrite the file of the same name")

def masterlist_as_json():
    global masterlist
    j = {"masterlist": []}
    for file in masterlist:
        j["masterlist"].append({"name": file.name, "mod": file.mod,  "path": file.path})
    return json.dumps(j)
  
def host_add_file(path, node):
    global masterlist
    global sock_list

    for sock in sock_list:
        truepath = path
        fsize = os.path.getsize(truepath)
        message = node.ADD + truepath + node.ETX + str(fsize) + node.EOT
        print("Sending: " + message)
        sock.send(message.encode('utf-8'))
        with open(truepath, 'rb') as f:
            bytessent = 0
            while bytessent < fsize:
                data = f.read(BUFFER_SIZE)
                sock.send(data)
                bytessent += len(data)

            f.close()
            print("Sent Successfully!")

def host_add_request(sock, fsize, fname):
    print("host_add_request")


def host_send_masterlist():
    global masterlist
    global sock_list
    print('send masterlist')
    
def host_scan(sock, node):
    global masterlist

    while True:
        host_send_masterlist()
        time.sleep(1)
        files = f.scan()
        for n in files:
            if any(fol.name == n.name for fol in masterlist):
                #master has the file
                for m in masterlist:
                    if m.name == n.name:
                        if m.mod < n.mod:
                            host_update_file(n.path)

            else:
                print("File name: %s\nPath: %s\nMod: %d" %(n.name, n.path, n.mod))
                host_add_file(n.path, node)
                #master is missing a file
                #send file to all
    
def accept(s, n):
    print("Waiting to accept")
    while n.nodeOpen:

        conn, addr = s.accept()

        t = threading.Thread(target=new_connection, args=(str(addr[0]), n, conn))
        t.start()
    
def new_connection(name, n, sock):
    global sock_list
    
    sock_list.append(sock)
    
    while True:
        
        
        data = sock.recv(BUFFER_SIZE).decode('utf-8')
        #TODO
        #each client can send one of the following to the host
        #new file - host downloads the file, host adds it to the masterlist, host sends the file to all other nodes (not back to the sender tho)
        #update file - host overwrites the file locally, host updates the mod time on the masterlist, host sends the overwrite message w/ file to all nodes (not back to sender)
        #delete file - host deletes the file from the masterlist, host deletes the message locally, host sends message to all nodes to delete their file with this name

        if data[:n.CCLEN] == n.UPD:
            fsize = int(data[data.find(n.ETX) + len(n.ETX):data.find(n.EOT)])
            fname = data[n.CCLEN:data.find(n.ETX)]
            host_add_request(sock, fsize, fname)


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


################################################################################


def client_node(n):
    s = socket.socket()
    s.connect((n.host, n.port))
    identity = n.IDENTIFIER + n.id + n.ETX + n.name + n.EOT
    s.send(identity.encode('utf-8'))
    print("Connected to the network!")
    
    t = threading.Thread(target=client_listen, args=("client_listener", s))
    t.start()

    host_menu()

    while n.nodeOpen:

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
                
                
def client_listen(name, s):
    
    ##client listening for the host
    ##each client can recv one of the following from the host
    while True:
        
        data = s.recv(BUFFER_SIZE).decode('utf-8')
        
        if data[:node.CCLEN] == node.MAS: # if the message is just the masterlist, pass it to client
            client_scan(masterlist, s)
        if data[:node.CCLEN] == node.ADD: # if the message is a new file to add - download to the share folder
             print("todo")
        if False: # if the message is an updated file - overwrite the local file with the same name
            print("todo")
        if False: # if the message is a delete request - delete the file with that name
            print("todo")
    
def client_scan(masterlist, s):
    files = f.scan()
    
    for c in files:
        print(str(c))

    for n in files:
        if any(fol.name == n.name for fol in masterlist):
            #master has the file
            for m in masterlist:
                if m.name == n.name:
                    if m.mod < n.mod:
                        client_update_file(n.path, s)
                        #local has updated file, master is out of date
                        #send file.path
        else:
            client_add_file(n.path, s)
            #master is missing a file
            #send file to all


def client_delete_file():
    sg.theme('Default1')
    layout = [
         [sg.Listbox(f.get_file_names(), size=(50, 10), key='list')],
          sg.Button('Delete File')
    ]
    hel = sg.Window('Pee2pee', layout)
    while True:
        event, values = hel.read()
        if event is None:
            break
        if event =='Delete File':
            filename = values['list'][0]
            print("Deleting", filename)
            if filename != '' and filename != None:
                try:
                    # Toto send message to the host to delete the file
                    
                    os.remove(f.get_filepath(filename)) #removes it locally
                except:
                    print("File could not be deleted.")

def client_update_file(path):
    print("todo: send update request to the host")


def client_add_file(path):
    print("send file to host")


#############################################################################


def check():
    if not os.path.isdir(f.get_working_directory()):
        os.mkdir(f.get_working_directory())
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'share')):
        os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'share'))
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')):
        os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp'))
         
def main():
    check()
    name = "User: " + str(uuid.uuid4())
    n = node(name, HOST, PORT)

    while n.nodeOpen:
        try:
            client_node(n)
        except Exception:
            server_node(name, n)



if __name__ == '__main__':
    main()