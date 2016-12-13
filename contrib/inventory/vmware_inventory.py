#!/usr/bin/env python

# Requirements
#   - pyvmomi >= 6.0.0.2016.4

# TODO:
#   * more jq examples
#   * optional folder heirarchy 

"""
$ jq '._meta.hostvars[].config' data.json | head
{
  "alternateguestname": "",
  "instanceuuid": "5035a5cd-b8e8-d717-e133-2d383eb0d675",
  "memoryhotaddenabled": false,
  "guestfullname": "Red Hat Enterprise Linux 7 (64-bit)",
  "changeversion": "2016-05-16T18:43:14.977925Z",
  "uuid": "4235fc97-5ddb-7a17-193b-9a3ac97dc7b4",
  "cpuhotremoveenabled": false,
  "vpmcenabled": false,
  "firmware": "bios",
"""

from __future__ import print_function

import argparse
import atexit
import datetime
import getpass
import jinja2
import os
import six
import ssl
import sys
import uuid

from collections import defaultdict
from six.moves import configparser
from time import time

HAS_PYVMOMI = False
try:
    from pyVmomi import vim
    from pyVim.connect import SmartConnect, Disconnect
    HAS_PYVMOMI = True
except ImportError:
    pass

try:
    import json
except ImportError:
    import simplejson as json

hasvcr = False
try:
    import vcr
    hasvcr = True
except ImportError:
    pass


class VMWareInventory(object):

    __name__ = 'VMWareInventory'

    instances = []
    debug = False
    load_dumpfile = None
    write_dumpfile = None
    maxlevel = 1
    lowerkeys = True
    config = None
    cache_max_age = None
    cache_path_cache = None
    cache_path_index = None
    server = None
    port = None
    username = None
    password = None
    host_filters = []
    groupby_patterns = []

    bad_types = ['Array', 'disabledMethod', 'declaredAlarmState']
    if (sys.version_info > (3, 0)):
        safe_types = [int, bool, str, float, None]
    else:
        safe_types = [int, long, bool, str, float, None]
    iter_types = [dict, list]
    skip_keys = ['dynamicproperty', 'dynamictype', 'managedby', 'childtype']


    def _empty_inventory(self):
        return {"_meta" : {"hostvars" : {}}}


    def __init__(self, load=True):
        self.inventory = self._empty_inventory()

        if load:
            # Read settings and parse CLI arguments
            self.parse_cli_args()
            self.read_settings()

            # Check the cache
            cache_valid = self.is_cache_valid()

            # Handle Cache
            if self.args.refresh_cache or not cache_valid:
                self.do_api_calls_update_cache()
            else:
                self.debugl('# loading inventory from cache')
                self.inventory = self.get_inventory_from_cache()

    def debugl(self, text):
        if self.args.debug:
            try:
                text = str(text)
            except UnicodeEncodeError:
                text = text.encode('ascii','ignore')                            
            print(text)

    def show(self):
        # Data to print
        data_to_print = None
        if self.args.host:
            data_to_print = self.get_host_info(self.args.host)
        elif self.args.list:
            # Display list of instances for inventory
            data_to_print = self.inventory
        return json.dumps(data_to_print, indent=2)


    def is_cache_valid(self):

        ''' Determines if the cache files have expired, or if it is still valid '''

        valid = False

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                valid = True

        return valid


    def do_api_calls_update_cache(self):

        ''' Get instances and cache the data '''

        instances = self.get_instances()
        self.instances = instances
        self.inventory = self.instances_to_inventory(instances)
        self.write_to_cache(self.inventory, self.cache_path_cache)


    def write_to_cache(self, data, cache_path):

        ''' Dump inventory to json file '''

        with open(self.cache_path_cache, 'wb') as f:
            f.write(json.dumps(data))


    def get_inventory_from_cache(self):

        ''' Read in jsonified inventory '''

        jdata = None
        with open(self.cache_path_cache, 'rb') as f:
            jdata = f.read()
        return json.loads(jdata)


    def read_settings(self):

        ''' Reads the settings from the vmware_inventory.ini file '''

        scriptbasename = __file__
        scriptbasename = os.path.basename(scriptbasename)
        scriptbasename = scriptbasename.replace('.py', '')

        defaults = {'vmware': {
            'server': '',
            'port': 443,
            'username': '',
            'password': '',
            'validate_certs': True,
            'ini_path': os.path.join(os.path.dirname(__file__), '%s.ini' % scriptbasename),
            'cache_name': 'ansible-vmware',
            'cache_path': '~/.ansible/tmp',
            'cache_max_age': 3600,
                        'max_object_level': 1,
                        'alias_pattern': '{{ config.name + "_" + config.uuid }}',
                        'host_pattern': '{{ guest.ipaddress }}',
                        'host_filters': '{{ guest.gueststate == "running" }}',
                        'groupby_patterns': '{{ guest.guestid }},{{ "templates" if config.template else "guests"}}',
                        'lower_var_keys': True }
           }

        if six.PY3:
            config = configparser.ConfigParser()
        else:
            config = configparser.SafeConfigParser()

        # where is the config?
        vmware_ini_path = os.environ.get('VMWARE_INI_PATH', defaults['vmware']['ini_path'])
        vmware_ini_path = os.path.expanduser(os.path.expandvars(vmware_ini_path))
        config.read(vmware_ini_path)

        # apply defaults
        for k,v in defaults['vmware'].items():
            if not config.has_option('vmware', k):
                    config.set('vmware', k, str(v))

        # where is the cache?
        self.cache_dir = os.path.expanduser(config.get('vmware', 'cache_path'))
        if self.cache_dir and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # set the cache filename and max age
        cache_name = config.get('vmware', 'cache_name')
        self.cache_path_cache = self.cache_dir + "/%s.cache" % cache_name
        self.cache_max_age = int(config.getint('vmware', 'cache_max_age'))

        # mark the connection info 
        self.server =  os.environ.get('VMWARE_SERVER', config.get('vmware', 'server'))
        self.port = int(os.environ.get('VMWARE_PORT', config.get('vmware', 'port')))
        self.username = os.environ.get('VMWARE_USERNAME', config.get('vmware', 'username'))
        self.password = os.environ.get('VMWARE_PASSWORD', config.get('vmware', 'password'))
        self.validate_certs = os.environ.get('VMWARE_VALIDATE_CERTS', config.get('vmware', 'validate_certs'))
        if self.validate_certs in ['no', 'false', 'False', False]:
            self.validate_certs = False
        else:
            self.validate_certs = True

        # behavior control
        self.maxlevel = int(config.get('vmware', 'max_object_level'))
        self.lowerkeys = config.get('vmware', 'lower_var_keys')
        if type(self.lowerkeys) != bool:
            if str(self.lowerkeys).lower() in ['yes', 'true', '1']:
                self.lowerkeys = True
            else:    
                self.lowerkeys = False

        self.host_filters = list(config.get('vmware', 'host_filters').split(','))
        self.groupby_patterns = list(config.get('vmware', 'groupby_patterns').split(','))

        # save the config
        self.config = config    


    def parse_cli_args(self):

        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on PyVmomi')
        parser.add_argument('--debug', action='store_true', default=False,
                           help='show debug info')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                           help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                           help='Force refresh of cache by making API requests to VSphere (default: False - use cache files)')
        parser.add_argument('--max-instances', default=None, type=int,
                           help='maximum number of instances to retrieve')
        self.args = parser.parse_args()


    def get_instances(self):

        ''' Get a list of vm instances with pyvmomi '''

        instances = []        

        kwargs = {'host': self.server,
                  'user': self.username,
                  'pwd': self.password,
                  'port': int(self.port) }

        if hasattr(ssl, 'SSLContext') and not self.validate_certs:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
            kwargs['sslContext'] = context

        instances = self._get_instances(kwargs)
        return instances


    def _get_instances(self, inkwargs):

        ''' Make API calls '''

        instances = []
        si = SmartConnect(**inkwargs)

        self.debugl('# retrieving instances')            
        if not si:
            print("Could not connect to the specified host using specified "
                "username and password")
            return -1
        atexit.register(Disconnect, si)
        content = si.RetrieveContent()

        # Create a search container for virtualmachines
        container = content.rootFolder
        viewType = [vim.VirtualMachine]
        recursive = True
        containerView = content.viewManager.CreateContainerView(container, viewType, recursive)
        children = containerView.view
        for child in children:
            # If requested, limit the total number of instances
            if self.args.max_instances:
                if len(instances) >= (self.args.max_instances):
                    break
            instances.append(child)
        self.debugl("# total instances retrieved %s" % len(instances))

        instance_tuples = []    
        for instance in sorted(instances):    
            ifacts = self.facts_from_vobj(instance)
            instance_tuples.append((instance, ifacts))
        return instance_tuples


    def instances_to_inventory(self, instances):

        ''' Convert a list of vm objects into a json compliant inventory '''

        inventory = self._empty_inventory()
        inventory['all'] = {}
        inventory['all']['hosts'] = []
        last_idata = None
        total = len(instances)
        for idx,instance in enumerate(instances):
    
            # make a unique id for this object to avoid vmware's
            # numerous uuid's which aren't all unique.
            thisid = str(uuid.uuid4())
            idata = instance[1]

            # Put it in the inventory
            inventory['all']['hosts'].append(thisid)
            inventory['_meta']['hostvars'][thisid] = idata.copy()
            inventory['_meta']['hostvars'][thisid]['ansible_uuid'] = thisid

        # Make a map of the uuid to the alias the user wants
        name_mapping = self.create_template_mapping(inventory, 
                            self.config.get('vmware', 'alias_pattern'))

        # Make a map of the uuid to the ssh hostname the user wants
        host_mapping = self.create_template_mapping(inventory,
                            self.config.get('vmware', 'host_pattern'))


        # Reset the inventory keys
        for k,v in name_mapping.items():

            if not host_mapping or not k in host_mapping:
                continue

            # set ansible_host (2.x)
            try:
                inventory['_meta']['hostvars'][k]['ansible_host'] = host_mapping[k]
                # 1.9.x backwards compliance
                inventory['_meta']['hostvars'][k]['ansible_ssh_host'] = host_mapping[k]
            except Exception as e:
                continue

            if k == v:
                continue

            # add new key
            inventory['all']['hosts'].append(v)
            inventory['_meta']['hostvars'][v] = inventory['_meta']['hostvars'][k]

            # cleanup old key
            inventory['all']['hosts'].remove(k)
            inventory['_meta']['hostvars'].pop(k, None)

        self.debugl('# pre-filtered hosts:')
        for i in inventory['all']['hosts']:
            self.debugl('#   * %s' % i)
        # Apply host filters
        for hf in self.host_filters:
            if not hf:
                continue
            self.debugl('# filter: %s' % hf)
            filter_map = self.create_template_mapping(inventory, hf, dtype='boolean')
            for k,v in filter_map.items():
                if not v:
                    # delete this host
                    inventory['all']['hosts'].remove(k)
                    inventory['_meta']['hostvars'].pop(k, None)

        self.debugl('# post-filter hosts:')
        for i in inventory['all']['hosts']:
            self.debugl('#   * %s' % i)

        # Create groups
        for gbp in self.groupby_patterns:
            groupby_map = self.create_template_mapping(inventory, gbp)
            for k,v in groupby_map.items():
                if v not in inventory:
                    inventory[v] = {}
                    inventory[v]['hosts'] = []
                if k not in inventory[v]['hosts']:
                    inventory[v]['hosts'].append(k)    

        return inventory


    def create_template_mapping(self, inventory, pattern, dtype='string'):

        ''' Return a hash of uuid to templated string from pattern '''

        mapping = {}
        for k,v in inventory['_meta']['hostvars'].items():
            t = jinja2.Template(pattern)
            newkey = None
            try:           
                newkey = t.render(v)
                newkey = newkey.strip()
            except Exception as e:
                self.debugl(e)
            if not newkey:
                continue
            elif dtype == 'integer':
                newkey = int(newkey)
            elif dtype == 'boolean':
                if newkey.lower() == 'false':
                    newkey = False
                elif newkey.lower() == 'true':
                    newkey = True    
            elif dtype == 'string':
                pass        
            mapping[k] = newkey
        return mapping


    def facts_from_vobj(self, vobj, level=0):

        ''' Traverse a VM object and return a json compliant data structure '''

        # pyvmomi objects are not yet serializable, but may be one day ...
        # https://github.com/vmware/pyvmomi/issues/21

        # WARNING:
        # Accessing an object attribute will trigger a SOAP call to the remote.
        # Increasing the attributes collected or the depth of recursion greatly
        # increases runtime duration and potentially memory+network utilization.

        if level == 0:
            try:
                self.debugl("# get facts: %s" % vobj.name)
            except Exception as e:
                self.debugl(e)

        rdata = {}

        methods = dir(vobj)
        methods = [str(x) for x in methods if not x.startswith('_')]
        methods = [x for x in methods if not x in self.bad_types]
        methods = sorted(methods)

        for method in methods:
            # Attempt to get the method, skip on fail
            try:
                methodToCall = getattr(vobj, method)
            except Exception as e:
                continue
            # Skip callable methods
            if callable(methodToCall):
                continue
            if self.lowerkeys:
                method = method.lower()
            rdata[method] = self._process_object_types(methodToCall)

        return rdata


    def _process_object_types(self, vobj, level=0):
        ''' Serialize an object '''
        rdata = {}

        if vobj is None:
            rdata = None
        elif issubclass(type(vobj), str) or isinstance(vobj, str):
            if vobj.isalnum():
                rdata = vobj
            else:
                rdata = vobj.decode('ascii', 'ignore')
        elif issubclass(type(vobj), bool) or isinstance(vobj, bool):
            rdata = vobj
        elif issubclass(type(vobj), int) or isinstance(vobj, int):
            rdata = vobj
        elif issubclass(type(vobj), float) or isinstance(vobj, float):
            rdata = vobj
        elif issubclass(type(vobj), long) or isinstance(vobj, long):
            rdata = vobj
        elif issubclass(type(vobj), list) or issubclass(type(vobj), tuple):
            rdata = []
            try:
                vobj = sorted(vobj)
            except Exception as e:
                pass
            for vi in vobj:
                if (level+1 <= self.maxlevel):
                    #vid = self.facts_from_vobj(vi, level=(level+1))
                    vid = self._process_object_types(vi, level=(level+1))
                    if vid:
                        rdata.append(vid)
        elif issubclass(type(vobj), dict):
            pass
        elif issubclass(type(vobj), object):
            methods = dir(vobj)
            methods = [str(x) for x in methods if not x.startswith('_')]
            methods = [x for x in methods if not x in self.bad_types]
            methods = sorted(methods)

            for method in methods:
                # Attempt to get the method, skip on fail
                try:
                    methodToCall = getattr(vobj, method)
                except Exception as e:
                    continue
                if callable(methodToCall):
                    continue
                if self.lowerkeys:
                    method = method.lower()
                if (level+1 <= self.maxlevel):
                    rdata[method] = self._process_object_types(methodToCall, level=(level+1))
        else:
            pass

        if not rdata:
            rdata = None
        return rdata

    def get_host_info(self, host):
        
        ''' Return hostvars for a single host '''

        return self.inventory['_meta']['hostvars'][host]


if __name__ == "__main__":
    # Run the script
    print(VMWareInventory().show())


