import PySimpleGUI as sg
import threading
import webbrowser
import files as f
import os
import file


def window():
    sg.theme('Default1')

    layout = [
        [sg.Text('Username:')],
        [sg.InputText(key='username', size=(30, 1))],
        [sg.Text('Host IP:')],
        [sg.InputText(key='IP', size=(30, 1))],
        [sg.Button('connect')]

    ]

    window = sg.Window('Pee2pee', layout)
    while True:

        event, values = window.read(timeout=10000)

        if event is None:
            break

        if event == 'connect':
            if validate_connection():
                window.close()
                connected()

    window.close()


def connected():
    sg.theme('Default1')

    layout = [
         [sg.Listbox(f.get_file_names(), size=(50, 10), key='list')],
         [sg.Button('Open Folder'),
          sg.Button('Delete File'),
          sg.Button('Disconnect')]
    
    ]

    hel = sg.Window('Pee2pee', layout)
    while True:

        event, values = hel.read(timeout=10000)
        
        scan()

        if event is None:
            break
        
        if event =='Delete File':
            filename = values['list'][0]
            print(filename)
            if filename != '' and filename != None:
                delete_file(filename)
                
        if event == 'Disconnect':
            # delete connection
            
            close_connection()
            hel.close()
            window()

        if event == 'Open Folder':
            os.startfile(f.get_working_directory())
        
        hel['list'].update(f.get_file_names())


def check():
    if not os.path.isdir(f.get_working_directory()):
        os.mkdir(f.get_working_directory())
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'share')):
        os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'share'))
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')):
        os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp'))

def validate_connection():
    # TODO connect to network
    print('todo')
    #need to ass host logic'
    #if host, return 1
    #if node return 2
    #if cant connect, return 0
    
    return 1

def scan():
    files = f.scan()
    masterfiles = get_master()
    for c in files:
        print(str(c))

    for n in files:
        if any(fol.name == n.name for fol in masterfiles):
            #master has the file
            for m in masterfiles:
                if m.name == n.name:
                    if m.mod < n.mod:
                        update_file(n.path)
                        #local has updated file, master is out of date
                        #send file.path
        else:
            send_file(n.path)
            #master is missing a file
            #send file to all

def send_file(filepath): #send this file to everyone and add to the masterlist
    print('todo1')

def update_file(filepath): #update this file for everyone and update the last-modified time in the master list
    print('todo2')

def delete_file(name):
    #send request to delete file to everyone and remove from masterlist
    print('todo3')
    try:
        os.remove(f.get_filepath(name)) #removes it locally
    except:
        print('shit')
    
def get_master():
    print('todo4')
    #implement
    list = []
    list.append(file.File('photo.jpg', '1234124'))
    return list

def close_connection():
    print('todo5')

def main():
    check()
    window()


main()