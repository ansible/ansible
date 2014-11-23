import ConfigParser
import os
import sys


config_file = None


# copied from utils, avoid circular reference fun :)
def mk_boolean(value):
    if value is None:
        return False

    return str(value).lower() in ["true", "t", "y", "1", "yes"]


def get_config(p, section, key, env_var, default,
               boolean=False, integer=False, floating=False, islist=False):
    ''' return a configuration variable with casting '''
    value = _get_config(p, section, key, env_var, default)
    if boolean:
        return mk_boolean(value)
    if value and integer:
        return int(value)
    if value and floating:
        return float(value)
    if value and islist:
        return [x.strip() for x in value.split(',')]
    return value


def _get_config(p, section, key, env_var, default):
    ''' helper function for get_config '''
    if env_var is not None:
        value = os.environ.get(env_var, None)
        if value is not None:
            return value
    if p is not None:
        try:
            return p.get(section, key, raw=True)
        except:
            return default
    return default


def load_config_file():
    ''' Load Config File order(first found is used): ENV, CWD, HOME,
    /etc/ansible '''

    global config_file

    p = ConfigParser.ConfigParser()

    path0 = os.getenv("ANSIBLE_CONFIG", None)
    if path0 is not None:
        path0 = os.path.expanduser(path0)
    path1 = os.getcwd() + "/ansible.cfg"
    path2 = os.path.expanduser("~/.ansible.cfg")
    path3 = "/etc/ansible/ansible.cfg"

    for path in [path0, path1, path2, path3]:
        if path is not None and os.path.exists(path):
            try:
                p.read(path)
            except ConfigParser.Error as e:
                print "Error reading config file: \n%s" % e
                sys.exit(1)
            config_file = path
            return p
    return None


def get_config_file():
    return config_file
