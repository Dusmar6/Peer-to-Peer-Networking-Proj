import PySimpleGUI as sg
import threading
import webbrowser
import files as f
import os


def window():
    sg.theme('Default1')
    
    layout = [  
                        [sg.Text('Username:')],
                        [sg.InputText(key='username', size=(30,1))],
                        [sg.Text('Host IP:')],
                        [sg.InputText(key='IP', size=(30,1))],
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
                        [sg.Output( size=(50,10), key='-OUTPUT-')],
                        [sg.Button('Open Folder'), sg.Button('disconnect')]
                        
            ] 
    
    hel = sg.Window('Pee2pee', layout)
    while True:     
        
        event, values = hel.read(timeout=10000)

        if event is None:
            break
        
        if event == 'disconnect':
            #delete connection
            hel.close()
            window()
                
        if event == 'Open Folder':
            os.startfile(f.get_working_directory())

    window.close()

def check():
    if not os.path.isdir(f.get_working_directory()):
        os.mkdir(f.get_working_directory())
    

def validate_connection():
    return True

def main():
    check()
    window()
    
    

main()