from yaml import load
from ansible.parsing.yaml.loader import AnsibleLoader

def safe_load(stream):
    ''' implements yaml.safe_load(), except using our custom loader class '''
    return load(stream, AnsibleLoader)
