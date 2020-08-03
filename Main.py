import PySimpleGUI as sg
import threading
import webbrowser
import files as f
import os


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

    # layout = [
    #     [sg.Output(size=(50, 10), key='-OUTPUT-')],
    #     [sg.Button('Open Folder'),
    #      sg.Button('Sync Files'),
    #      sg.Button('Disconnect')]
    #
    # ]

    column1 = [
        [
            sg.Text("Folder to Sync To"),
            sg.In(size = (25, 1), enable_events=True, key="-FOLDER-"),
            sg.FolderBrowse(),
        ],
        [
            sg.Listbox(
                values=[], enable_events=True, size=(40, 20), key='-FILE LIST-'
            )
        ],
    ]

    column2 = [
        [
            sg.Text("Available Files to Sync"), # Add number of nodes that are connected, maybe??
        ],
        [
            sg.Listbox(
                values=[], enable_events=True, size=(40, 20), key='-SYNC LIST-'
            )
        ],
        [
            sg.Button('Sync Files'),
            sg.Button('Disconnect')
        ],
    ]

    layout = [
        [
            sg.Column(column1),
            sg.VSeparator(),
            sg.Column(column2),
        ]
    ]

    hel = sg.Window('Pee2pee', layout)
    while True:

        event, values = hel.read(timeout=10000)

        if event is None:
            break

        if event == 'Disconnect':
            # delete connection
            hel.close()
            window()

        if event == '-FOLDER-':
            folder = values["-FOLDER-"]
            fileList = os.listdir(folder)
            fnames = [
                f
                for f in fileList
                if os.path.isfile(os.path.join(folder, f))
            ]
            hel["-FILE LIST-"].update(fnames)


        if event == 'Sync Files':
            # TODO open new window that shows progress maybe?
            break


def check():
    if not os.path.isdir(f.get_working_directory()):
        os.mkdir(f.get_working_directory())


def validate_connection():
    # TODO connect to network
    return True

def compare_lists():
    # TODO compare list we have vs list of other nodes, return the missing files to display
    return True

def main():
    check()
    window()


main()