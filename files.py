import configparser
import os
import shutil


def get_config():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        idi = config['config']['working directory']
    except:
        write_default_config()
        config.read('config.ini')
    return config

def write_default_config():
    config = configparser.ConfigParser()
    config['config']= {}
    config['config']['working directory'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'share')

    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        
def get_working_directory():
    config = get_config()
    return config['config']['working directory']

def set_working_directory(path):
    config = get_config()
    config['config']['working directory']= path
            
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        
def get_files_names():
    files = os.listdir(get_working_directory())
    
    if len(files) == 0:
        files.append(' ')

    return files

def get_filepath(name):
    return os.path.join(get_working_directory(), name)

