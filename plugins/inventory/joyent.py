#!/usr/bin/env python

# Author: Adham Helal <adham.helal@yetu.com>

'''
Requires smartdc module to run 
Config file 'joyent.ini' will be loaded from  the following paths
   1- CWD 
   2- env variable HELPER  

Supports the following caching options
1- no cache 
2- serve from cache till expiration time then refresh cache
3- smart cache serve from cache till expiration time 
   than fork a background process to refresh cache  
'''

import os
import sys
import ConfigParser
from datetime import datetime

try:
    import json
except ImportError:
    import simplejson as json


def safe_fail_stderr(msg):
    ## Print error and dont break ansible by printing an emtpy JSON
    print >> sys.stderr, msg
    print json.dumps(json.loads("{ \"\":\"\" }"), indent=4, sort_keys=True)
    sys.exit(1)

try:
    from smartdc import DataCenter
except ImportError:
    ## Print error but dont break ansible inventory
    safe_fail_stderr("Please install smartdc.")


class JoyentInventory(object):
    def __init__(self):
        self.inventory = {}
        self.get_config()

    def get_config(self):
        # Read config 
        self.config = ConfigParser.SafeConfigParser()
        my_name = os.path.abspath(sys.argv[0]).rstrip('.py')
        path_search = [ my_name + '.ini', 'joyent.ini']
        if os.environ.get('HELPER'):
            path_search.extend([os.environ.get('HELPER') + "/" + my_name + ".ini", os.environ.get('HELPER') + "/joyent.ini"])

        for config_filename in path_search:
            if os.path.exists(config_filename):
                self.config.read(config_filename)
                break

        self.cache_smart = self.config.getboolean('cache', 'cache_smart')
        self.cache_expire = self.config.getint('cache', 'cache_expire')
        self.cache_dir = self.config.get('cache', 'cache_dir')
        self.cache_file = self.cache_dir + "/ansible_joyent.cache"
        self.joyent_uri = self.config.get('api', 'uri')
        if self.config.get('auth', 'auth_type') == "key":
            self.joyent_secret = self.config.get('auth', 'auth_key')
            self.joyent_username = self.config.get('auth', 'auth_username')
            self.joyent_key_name = self.config.get('auth', 'auth_key_name')
            self.joyent_key_id = "/" + self.joyent_username + "/keys/" + self.joyent_key_name
        else:
            safe_fail_stderr("Only key method is supported for authentication")

    def use_smart_cache(self):
        try:
            pid = os.fork()
            if pid > 0:
                return  self.get_cache()
        except OSError, e:
            safe_fail_stderr("fork #1 failed: %d (%s)" % (e.errno, e.strerror))

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent, print eventual PID before
                sys.exit(0)
        except OSError, e:
            safe_fail_stderr("fork #2 failed: %d (%s)" % (e.errno, e.strerror))

        # Redirect standard file descriptors
        sys.stdin = open('/dev/null', 'r')
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
        self.build_inv_from_api()
        sys.exit(0)

    def check_cache(self):
        ''' Checks if we can server from cache or API call '''

        try:
            stats = os.stat(self.cache_file)
        except:
            # No cache or cant read just get from API
            return self.build_inv_from_api()

        seconds_since_last_modified = (datetime.now() - datetime.fromtimestamp(stats.st_mtime)).total_seconds()

        if seconds_since_last_modified < self.cache_expire:
            return self.get_cache()
        else:
            # cache expired
            if self.cache_smart:
                return self.use_smart_cache()
            else:
                return self.build_inv_from_api()

    def build_inv_from_api(self):
        servers = self.api_get()
        self.inventory["all"] = []
        self.inventory["hosts"] = {}
        for server in servers:
            ## Groups Management
            group = server.type
            if group is None:
                group = 'ungrouped'
            if not group in self.inventory:
                self.inventory.update({group: []})
            ## Add to a group and all
            self.inventory[group].append(server.name)
            self.inventory["all"].append(server.name)

            ## hosts Management
            if server.public_ips:
                ssh_connection = server.public_ips[0]
            elif server.private_ips:
                ssh_connection = server.private_ips[0]
            else:
                ssh_connection = server.name

            self.inventory["hosts"][server.name] = {"joyent_id": server.id,
                                  "joyent_public_ip": server.public_ips,
                                  "joyent_private_ip": server.private_ips,
                                  "ansible_ssh_host": ssh_connection}
            ##SmartOS python
            if server.type == "smartmachine":
                self.inventory["hosts"][server.name]["ansible_python_interpreter"] = "/opt/local/bin/python"
        self.save_cache()


    def api_get(self):
        """ Ask Joyent for all servers in a data center"""
        sdc = DataCenter(location=self.joyent_uri, key_id=self.joyent_key_id, secret=self.joyent_secret, verbose=False)
        servers = sdc.machines()
        return servers

    def get_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                self.inventory = json.load(f)
        except IOError, e:
            safe_fail_stderr("save cache IO Error")

    def save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.inventory, f)
        except IOError, e:
            safe_fail_stderr("save cache IO Error")

if __name__ == '__main__':
    joyent = JoyentInventory()
    ## Command line parser
    if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
        joyent.check_cache()
        print json.dumps(joyent.inventory, indent=4)
    elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
        joyent.check_cache()
        print json.dumps(joyent.inventory["hosts"][sys.argv[2]], indent=4)
    elif len(sys.argv) == 2 and (sys.argv[1] == '--pint'):
        print json.dumps(joyent.build_inv_from_api(), indent=4)
    else:
        print "Usage: %s --list or --host <hostname>" % sys.argv[0]
        sys.exit(1)

    sys.exit(0)
