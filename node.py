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
import files
import PySimpleGUI as sg
import json
import shutil

HOST = '192.168.2.151'
PORT = 8000
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

sock_list = []
masterlist = []

STX = "T02"
ETX = "T03"
EOT = "T04"
DEL = "DEL"  # send del + file name
ADD = "ADD"  # send add + file name + filesize + file data
UPD = "UPD"  # send udp + file name + filesize + file data (overwrite the file with this name)
MAS = "MAS"  # send MAS + masterlist
CCLEN = len(DEL)


class node():

    def __init__(self, name, myport, host, port, filepath=os.getcwd()):
        self.myhost = self.get_my_ip()
        self.myport = myport
        self.host = host
        self.port = port
        self.name = name
        self.fp = filepath + "/share/"

        # Set Control Characters for process, message and transmission
        # I know this isn't the proper way to do it, but it works
        # self.IDENTIFIER = "P01"
        # self.FILEPATH = "P02"
        # self.FILELIST = "P03"
        # self.FILEDATA = "P04"
        #
        # self.OK = "MOK"
        # self.ERR = "MER"
        #
        # self.STX = "T02"
        # self.ETX = "T03"
        # self.EOT = "T04"
        # self.DEL = "DEL" #send del + file name
        # self.ADD = "ADD" #send add + file name + filesize + file data
        # self.UPD = "UPD" #send udp + file name + filesize + file data (overwrite the file with this name)
        # self.MAS = "MAS" #send MAS + masterlist

        # Keep track of nodes connected to us
        self.connectedNodes = []

        # Set flag for when a node is closed
        self.nodeOpen = True

        # Create unique node ID for each node
        # (security not a major concern for this project so I chose a less secure
        # hash of which is fast)
        num = hashlib.sha1()
        key = self.host + str(self.port) + str(random.randint(1, 9999))
        num.update(key.encode(ENCODING))
        self.id = num.hexdigest()

        # # Start the TCP/IP socket for this node
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Node created!\nAddress: %s:%d\nUsername: %s" % (self.host, self.port, self.name))

    def get_file_list(self):
        return [f for f in listdir(self.fp) if isfile(join(self.fp, f))]

    def get_my_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("www.google.com", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip


def host_node(name, n):
    s = socket.socket()
    host = n.get_my_ip()
    s.bind((host, n.port))
    s.listen(5)
    print("Started Server at: (%s:%d)" % (host, n.port))

    t = threading.Thread(target=host_accept, args=(s, n))
    t.start()

    # k = threading.Thread(target=host_scan, args=(s, n))
    # k.start()

    host_console(name, n)


def host_delete_file(filename):
    try:
        os.remove(files.get_filepath(filename))  # removes it locally
        for file in masterlist:
            if file.name == filename:
                masterlist.remove(file)
        print("File removed")
    except:
        print("File could not be deleted. shouldnt be possible")

    for sock in sock_list:
        message = DEL + filename + EOT
        print("Sending: " + message)
        sock.send(message.encode(ENCODING))
        time.sleep(0.01)
        print("Sent Successfully!")


def host_update_file(name):
    global masterlist
    global sock_list

    myfiles = files.scan()
    for file in myfiles:
        if file.name == name:
            path = file.path

    for sock in sock_list:
        truepath = path
        fsize = os.path.getsize(truepath)
        message = UPD + name + ETX + str(fsize) + EOT
        print("Sending: " + message)
        sock.send(message.encode(ENCODING))
        time.sleep(0.01)
        with open(truepath, 'rb') as f:
            bytessent = 0
            while bytessent < fsize:
                data = f.read(BUFFER_SIZE)
                sock.send(data)
                bytessent += len(data)

            f.close()
            print("Sent Successfully!")


def masterlist_as_json():
    global masterlist
    j = {"masterlist": []}
    for file in masterlist:
        j["masterlist"].append({"name": file.name, "mod": file.mod, "path": file.path})
    return json.dumps(j)


def host_send_file(path, name):
    global masterlist
    global sock_list

    for sock in sock_list:
        truepath = files.get_working_directory() + "/" + name
        fsize = os.path.getsize(truepath)
        message = ADD + name + ETX + str(fsize) + EOT
        print("Sending: " + message)
        sock.send(message.encode(ENCODING))
        time.sleep(0.01)
        resp = sock.recv(BUFFER_SIZE).decode(ENCODING)

        # Only send the file if the client wants it
        if resp == "OK":
            print("They want it.")
            with open(truepath, 'rb') as k:
                bytessent = 0
                while bytessent < fsize:
                    data = k.read(BUFFER_SIZE)
                    sock.send(data)
                    bytessent += len(data)

                k.close()
                print("Sent Successfully!")
        else:
            print("They don't want it...")


def host_add_file(path, name):
    global masterlist
    global sock_list

    head, tail = os.path.split(path)
    masterlist.append(file.File(name))
    shutil.move(path, os.path.join(files.get_working_directory(), tail))  # adds it to share folder

    for sock in sock_list:
        truepath = files.get_working_directory() + "/" + tail
        fsize = os.path.getsize(truepath)
        message = ADD + name + ETX + str(fsize) + EOT
        print("Sending: " + message)
        sock.send(message.encode(ENCODING))
        time.sleep(0.01)
        resp = sock.recv(BUFFER_SIZE).decode(ENCODING)

        # Only send the file if the client wants it
        if resp == "OK":
            print("They want it.")
            with open(truepath, 'rb') as k:
                bytessent = 0
                while bytessent < fsize:
                    data = k.read(BUFFER_SIZE)
                    sock.send(data)
                    bytessent += len(data)

                k.close()
                print("Sent Successfully!")
        else:
            print("They don't want it...")


def host_add_request(sock, fsize, fname):
    print("host_add_request")


def host_send_all_files(sock):
    global masterlist
    global sock_list
    command = "MAS"
    sock.send(command.encode(ENCODING))
    time.sleep(0.1)
    resp = sock.recv(BUFFER_SIZE).decode(ENCODING)
    if resp == "OK":
        myfiles = files.scan()
        for file in myfiles:
            host_send_file(files.get_working_directory(), file.name)
            time.sleep(0.1)
    else:
        print("Didn't send Master List")
    # print('send masterlist')


def host_scan(sock):
    global masterlist

    # myfiles = files.scan()
    # for n in myfiles:
    #     if any(fol.name == n.name for fol in masterlist):
    #         #master has the file
    #         for m in masterlist:
    #             if m.name == n.name:
    #                 if m.mod < n.mod:
    #                     host_update_file(sock, n.path, n.name)
    #
    #     else:
    #         host_add_file(n.path, n.name)
    #         masterlist.append(n)
    #     time.sleep(0.1) # TODO not sure why, but the program doesn't work when this is not here
    #         #master is missing a file
    #         #send file to all


def host_accept(s, n):
    global sock_list

    print("Waiting to accept")
    while n.nodeOpen:
        conn, addr = s.accept()

        resp = conn.recv(BUFFER_SIZE).decode(ENCODING)
        print("Connected with: %s" % resp)

        sock_list.append(conn)
        host_send_all_files(conn)

        t = threading.Thread(target=host_listen, args=(str(addr[0]), n, conn))
        t.start()


def host_listen(name, n, sock):
    global sock_list

    while True:
        host_scan(sock)

        data = "Waiting for Direction"  # sock.recv(BUFFER_SIZE).decode(ENCODING)
        print(data)
        time.sleep(5)
        # TODO
        # each client can send one of the following to the host
        # new file - host downloads the file, host adds it to the masterlist, host sends the file to all other nodes (not back to the sender tho)
        # update file - host overwrites the file locally, host updates the mod time on the masterlist, host sends the overwrite message w/ file to all nodes (not back to sender)
        # delete file - host deletes the file from the masterlist, host deletes the message locally, host sends message to all nodes to delete their file with this name

        if data[:CCLEN] == UPD:
            fsize = int(data[data.find(ETX) + len(ETX):data.find(EOT)])
            fname = data[CCLEN:data.find(n.ETX)]
            host_add_request(sock, fsize, fname)

        # if data[:n.CCLEN] == n.IDENTIFIER:
        #     cID = data[n.CCLEN:data.find(ETX)]
        #     cName = data[data.find(ETX) + len(ETX):]
        #     print("Client connected!\nUsername: %s\nID: %s" % (cName, cID))
        # if data[:n.CCLEN] == n.FILEPATH:
        #     fp = data[n.CCLEN:data.find(n.EOT)]
        #     print(fp)
        # if data[:n.CCLEN] == n.FILELIST:
        #     fl = data[n.CCLEN:data.find(n.EOT)]
        #     print(fl)
        # if data[:n.CCLEN] == n.FILEDATA:
        #     fsize = int(data[data.find(n.ETX) + len(n.ETX):data.find(n.EOT)])
        #     fname = data[n.CCLEN:data.find(n.ETX)]
        #     print("Receiving file named: %s and of size: %d " % (fname, fsize))
        #     truepath = n.fp + "\\" + fname
        #     f = open(truepath, 'wb')
        #     bytesrecv = 0
        #     while bytesrecv < fsize:
        #         newdata = sock.recv(BUFFER_SIZE)
        #         bytesrecv += len(newdata)
        #         f.write(newdata)
        #     print("File received!")


def pop(msg='Something went wrong'):
    sg.popup('Error:', msg)


def host_console(name, n):
    sg.theme('Default1')

    layout = [
        [sg.Listbox(files.get_file_names(), size=(50, 10), key='list')],
        [sg.Button('Add File'),
         sg.Button('Update File'),
         sg.Button('Delete File'),
         sg.Button('Disconnect')]
    ]

    hel = sg.Window('Pee2pee', layout)
    while True:

        event, values = hel.read(timeout=3000)

        if event is None:
            break

        if event == 'Add File':
            filepath = sg.popup_get_file('File to add')
            host_add_file(filepath, os.path.basename(filepath))

        if event == 'Update File':
            filename = ''
            try:
                filename = values['list'][0]  # Throws an exception when nothing is selected, catch it here
            except:
                print("Make sure you have selected a file to update")
            if filename:
                host_update_file(filename)

        if event == 'Delete File':
            filename = ''
            try:
                filename = values['list'][0]  # Throws an exception when nothing is selected, catch it here
            except:
                print("Make sure you have selected a file to delete")
            if filename:
                host_delete_file(filename)

        if event == 'Disconnect':
            # delete connection
            host_close_connection()
            n.nodeOpen = False
            hel.close()
            login_window()

        hel['list'].update(files.get_file_names())


def host_close_connection():
    global sock_list
    for sock in sock_list:
        sock.close()


################################################################################


def client_node(n):
    s = socket.socket()
    s.connect((n.host, n.port))
    identity = "User: " + n.name
    s.send(identity.encode(ENCODING))
    print("Connected to the network!")

    client_clear_folder()

    t = threading.Thread(target=client_listen, args=("client_listener", s, n))
    t.start()

    client_console(s, n)

    """
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
            s.send(message.encode(ENCODING))
        if inp == '5':
            message = n.FILELIST + ' '.join(n.get_file_list()) + n.EOT
            print("Sending: " + message)
            s.send(message.encode(ENCODING))
        if inp == '6':
            n.fp = n.fp + "\\share"
            for f in n.get_file_list():
                truepath = n.fp + "\\" + f
                fsize = os.path.getsize(truepath)
                message = n.FILEDATA + f + n.ETX + str(fsize) + n.EOT
                print("Sending: " + message)
                s.send(message.encode(ENCODING))
                with open(truepath, 'rb') as f:
                    bytessent = 0
                    while bytessent < fsize:
                        data = f.read(BUFFER_SIZE)
                        s.send(data)
                        bytessent += len(data)
                f.close()
                print("Sent Successfully!")
                """


def client_listen(name, s, node):
    ##client listening for the host
    ##each client can recv one of the following from the host
    while True:
        try:
            data = s.recv(BUFFER_SIZE).decode(ENCODING)
        except:
            data = ""

        # TODO fix CCLEN and other identifier issues
        if data[:CCLEN] == "MAS":  # if the message is just the masterlist, pass it to client
            s.send("OK".encode(ENCODING))
        if data[:CCLEN] == "ADD":  # if the message is a new file to add - download to the share folder
            client_download_file(s, node, data)
        if data[:CCLEN] == "UPD":  # if the message is a new file to add - download to the share folder
            client_update_file_from_host(s, node, data)
        if data[:CCLEN] == "DEL":  # if the message is a new file to add - download to the share folder
            client_delete_file_from_host(s, node, data)


def client_clear_folder():
    shutil.rmtree(files.get_working_directory())
    check()


def client_delete_file_from_host(s, node, data):
    fname = data[CCLEN:data.find(EOT)]
    print("Request to delete %s" % fname)
    currfiles = node.get_file_list()

    if fname not in currfiles:

        print("do nothing pretty much")
    else:

        time.sleep(0.1)
        print("Deleting file named: %s " % (fname))
        try:
            os.remove(files.get_filepath(fname))
        except:
            print("something went wrong. shouldnt be possible")


"""    
def client_scan(masterlst, s):
    global masterlist
    s.send("OK".encode(ENCODING))
    files = f.scan()
    print("in client_scan")
    data = ''
    message = "GO!"
    while message != EOT:
        message = s.recv(BUFFER_SIZE).decode(ENCODING)
        data += message
        message = message[len(message)-len(EOT):]
    print(data)
    # mastlist = json.loads(data)
    # TODO Need to rethink how this works. Need to add just received master list to this client's master list
    for n in files:
        if any(fol.name == n.name for fol in masterlist):
            # master has the file
            for m in masterlist:
                if m.name == n.name:
                    if m.mod < n.mod:
                        client_update_file(n.path, s)
                        # local has updated file, master is out of date
                        # send file.path
        else:
            client_add_file(n.path, s)
            # master is missing a file
            # send file to all
            """


def client_delete_file(sock, filename):
    try:
        os.remove(files.get_filepath(filename))  # removes it locally
    except:
        print("File could not be deleted. shouldnt be possible")

    message = DEL + filename
    print("Sending: " + message)
    sock.send(message.encode(ENCODING))
    time.sleep(0.01)
    print("Sent Successfully!")


def client_update_file(sock, name):
    truepath = files.get_filepath(name)
    fsize = os.path.getsize(truepath)
    message = UPD + name + ETX + str(fsize) + EOT
    print("Sending: " + message)
    sock.send(message.encode(ENCODING))
    time.sleep(0.01)
    with open(truepath, 'rb') as k:
        bytessent = 0
        while bytessent < fsize:
            data = k.read(BUFFER_SIZE)
            sock.send(data)
            bytessent += len(data)

        k.close()
        print("Sent Successfully!")


def client_update_file_from_host(s, node, data):
    fsize = int(data[data.find(ETX) + len(ETX):data.find(EOT)])
    fname = data[CCLEN:data.find(ETX)]

    currfiles = node.get_file_list()
    if fname in currfiles:
        try:
            os.remove(node.fp + fname)
        except:
            print("something went wrong. shouldnt be possible")

    time.sleep(0.1)
    print("Upping file named: %s and of size: %d " % (fname, fsize))
    truepath = node.fp + fname
    f = open(truepath, 'wb')
    bytesrecv = 0
    while bytesrecv < fsize:
        newdata = s.recv(BUFFER_SIZE)
        bytesrecv += len(newdata)
        f.write(newdata)
    print("File upped!")


def client_download_file(s, node, data):
    fsize = int(data[data.find(ETX) + len(ETX):data.find(EOT)])
    fname = data[CCLEN:data.find(ETX)]

    currfiles = node.get_file_list()
    if fname not in currfiles:
        resp = "OK".encode(ENCODING)
        s.send(resp)
        time.sleep(0.1)
        print("Receiving file named: %s and of size: %d " % (fname, fsize))
        truepath = node.fp + fname
        f = open(truepath, 'wb')
        bytesrecv = 0
        while bytesrecv < fsize:
            newdata = s.recv(BUFFER_SIZE)
            bytesrecv += len(newdata)
            f.write(newdata)
        print("File received!")
    else:
        s.send("NO".encode(ENCODING))


def client_add_file(sock, path, name):
    head, tail = os.path.split(path)
    try:
        shutil.move(path, os.path.join(files.get_working_directory(), tail))  # adds it to share folder
    except:
        print("Something went wrong dd4r")

    truepath = path
    fsize = os.path.getsize(truepath)
    message = ADD + name + ETX + str(fsize) + EOT
    print("Sending: " + message)
    sock.send(message.encode(ENCODING))
    time.sleep(0.01)
    resp = sock.recv(BUFFER_SIZE).decode(ENCODING)

    # Only send the file if the client wants it
    if resp == "OK":
        print("They want it.")
        with open(truepath, 'rb') as k:
            bytessent = 0
            while bytessent < fsize:
                data = k.read(BUFFER_SIZE)
                sock.send(data)
                bytessent += len(data)

            k.close()
            print("Sent Successfully!")
    else:
        print("They don't want it...")


def client_console(s, n):
    sg.theme('Default1')

    layout = [
        [sg.Listbox(files.get_file_names(), size=(50, 10), key='list')],
        [sg.Button('Add File'),
         sg.Button('Update File'),
         sg.Button('Delete File'),
         sg.Button('Disconnect')]

    ]
    hel = sg.Window('Pee2pee', layout)
    while True:

        event, values = hel.read(timeout=3000)

        if event is None:
            sys.exit()
            break

        if event == 'Add File':
            filename = sg.popup_get_file('File to add')
            client_add_file(s, files.get_filepath(filename), filename, n)

        if event == 'Update File':
            filename = ''
            try:
                filename = values['list'][0]  # Throws an exception when nothing is selected, catch it here
            except:
                print("Make sure you have selected a file to update")
            if filename:
                client_update_file(s, filename)

        if event == 'Delete File':
            filename = ''
            try:
                filename = values['list'][0]  # Throws an exception when nothing is selected, catch it here
            except:
                print("Make sure you have selected a file to delete")
            if filename:
                client_delete_file(s, filename)

        if event == 'Disconnect':
            # delete connection
            s.close()
            hel.close()
            sys.exit()

        hel['list'].update(files.get_file_names())


#############################################################################


def check():
    if not os.path.isdir(files.get_working_directory()):
        os.mkdir(files.get_working_directory())
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'share')):
        os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'share'))
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')):
        os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp'))


def login_window():
    sg.theme('Default1')

    layout = [
        [sg.Text('Host IP:'), sg.InputText("192.168.2.151", key='ip', size=(30, 1))],
        # TODO get rid of the default text
        [sg.Text('Host Port:'), sg.InputText("8000", key='port', size=(20, 1))],
        [sg.Button('Connect to host')],
        [sg.Button('Host new connection')],
    ]

    window = sg.Window('Pee2pee', layout)
    while True:

        event, values = window.read()

        if event is None:
            sys.exit()
            break

        if event == 'Connect to host':
            try:
                name = "User: " + str(uuid.uuid4())
                print(values['ip'] + ":" + values['port'])
                n = node(name, 8000, values['ip'], int(values['port']))
                window.close()
                client_node(n)
            except SystemExit:
                sys.exit()
            except Exception as e:
                pop("Could not connect to host: " + str(e))
                login_window()

        if event == 'Host new connection':
            try:
                name = "User: " + str(uuid.uuid4())
                n = node(name, 8000, values['ip'], int(values['port']))
                window.close()
                host_node(name, n)
            except Exception as e:
                pop("Could not host new connection: " + str(e))
                login_window()


def main():
    check()
    login_window()


if __name__ == '__main__':
    main()