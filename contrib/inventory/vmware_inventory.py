#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C): 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Requirements
#   - pyvmomi >= 6.0.0.2016.4

# TODO:
#   * more jq examples
#   * optional folder heriarchy

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

import atexit
import datetime
import itertools
import json
import os
import re
import ssl
import sys
import uuid
from time import time

import six
from jinja2 import Environment
from six import integer_types, string_types
from six.moves import configparser

try:
    import argparse
except ImportError:
    sys.exit('Error: This inventory script required "argparse" python module.  Please install it or upgrade to python-2.7')

try:
    from pyVmomi import vim, vmodl
    from pyVim.connect import SmartConnect, Disconnect
except ImportError:
    sys.exit("ERROR: This inventory script required 'pyVmomi' Python module, it was not able to load it")


def regex_match(s, pattern):
    '''Custom filter for regex matching'''
    reg = re.compile(pattern)
    if reg.match(s):
        return True
    else:
        return False


def select_chain_match(inlist, key, pattern):
    '''Get a key from a list of dicts, squash values to a single list, then filter'''
    outlist = [x[key] for x in inlist]
    outlist = list(itertools.chain(*outlist))
    outlist = [x for x in outlist if regex_match(x, pattern)]
    return outlist


class VMwareMissingHostException(Exception):
    pass


class VMWareInventory(object):
    __name__ = 'VMWareInventory'

    guest_props = False
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
    cache_dir = None
    server = None
    port = None
    username = None
    password = None
    validate_certs = True
    host_filters = []
    skip_keys = []
    groupby_patterns = []

    safe_types = [bool, str, float, None] + list(integer_types)
    iter_types = [dict, list]

    bad_types = ['Array', 'disabledMethod', 'declaredAlarmState']

    vimTableMaxDepth = {
        "vim.HostSystem": 2,
        "vim.VirtualMachine": 2,
    }

    custom_fields = {}

    # use jinja environments to allow for custom filters
    env = Environment()
    env.filters['regex_match'] = regex_match
    env.filters['select_chain_match'] = select_chain_match

    # translation table for attributes to fetch for known vim types

    vimTable = {
        vim.Datastore: ['_moId', 'name'],
        vim.ResourcePool: ['_moId', 'name'],
        vim.HostSystem: ['_moId', 'name'],
    }

    @staticmethod
    def _empty_inventory():
        return {"_meta": {"hostvars": {}}}

    def __init__(self, load=True):
        self.inventory = VMWareInventory._empty_inventory()

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
                self.debugl('loading inventory from cache')
                self.inventory = self.get_inventory_from_cache()

    def debugl(self, text):
        if self.args.debug:
            try:
                text = str(text)
            except UnicodeEncodeError:
                text = text.encode('ascii', 'ignore')
            print('%s %s' % (datetime.datetime.now(), text))

    def show(self):
        # Data to print
        self.debugl('dumping results')
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
        self.inventory = self.instances_to_inventory(self.get_instances())
        self.write_to_cache(self.inventory)

    def write_to_cache(self, data):
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
            'skip_keys': 'declaredalarmstate,'
                         'disabledmethod,'
                         'dynamicproperty,'
                         'dynamictype,'
                         'environmentbrowser,'
                         'managedby,'
                         'parent,'
                         'childtype,'
                         'resourceconfig',
            'alias_pattern': '{{ config.name + "_" + config.uuid }}',
            'host_pattern': '{{ guest.ipaddress }}',
            'host_filters': '{{ runtime.powerstate == "poweredOn" }}',
            'groupby_patterns': '{{ guest.guestid }},{{ "templates" if config.template else "guests"}}',
            'lower_var_keys': True,
            'custom_field_group_prefix': 'vmware_tag_',
            'groupby_custom_field': False}
        }

        if six.PY3:
            config = configparser.ConfigParser()
        else:
            config = configparser.SafeConfigParser()

        # where is the config?
        vmware_ini_path = os.environ.get('VMWARE_INI_PATH', defaults['vmware']['ini_path'])
        vmware_ini_path = os.path.expanduser(os.path.expandvars(vmware_ini_path))
        config.read(vmware_ini_path)

        if 'vmware' not in config.sections():
            config.add_section('vmware')

        # apply defaults
        for k, v in defaults['vmware'].items():
            if not config.has_option('vmware', k):
                config.set('vmware', k, str(v))

        # where is the cache?
        self.cache_dir = os.path.expanduser(config.get('vmware', 'cache_path'))
        if self.cache_dir and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # set the cache filename and max age
        cache_name = config.get('vmware', 'cache_name')
        self.cache_path_cache = self.cache_dir + "/%s.cache" % cache_name
        self.debugl('cache path is %s' % self.cache_path_cache)
        self.cache_max_age = int(config.getint('vmware', 'cache_max_age'))

        # mark the connection info
        self.server = os.environ.get('VMWARE_SERVER', config.get('vmware', 'server'))
        self.debugl('server is %s' % self.server)
        self.port = int(os.environ.get('VMWARE_PORT', config.get('vmware', 'port')))
        self.username = os.environ.get('VMWARE_USERNAME', config.get('vmware', 'username'))
        self.debugl('username is %s' % self.username)
        self.password = os.environ.get('VMWARE_PASSWORD', config.get('vmware', 'password', raw=True))
        self.validate_certs = os.environ.get('VMWARE_VALIDATE_CERTS', config.get('vmware', 'validate_certs'))
        if self.validate_certs in ['no', 'false', 'False', False]:
            self.validate_certs = False

        self.debugl('cert validation is %s' % self.validate_certs)

        # behavior control
        self.maxlevel = int(config.get('vmware', 'max_object_level'))
        self.debugl('max object level is %s' % self.maxlevel)
        self.lowerkeys = config.get('vmware', 'lower_var_keys')
        if type(self.lowerkeys) != bool:
            if str(self.lowerkeys).lower() in ['yes', 'true', '1']:
                self.lowerkeys = True
            else:
                self.lowerkeys = False
        self.debugl('lower keys is %s' % self.lowerkeys)
        self.skip_keys = list(config.get('vmware', 'skip_keys').split(','))
        self.debugl('skip keys is %s' % self.skip_keys)
        temp_host_filters = list(config.get('vmware', 'host_filters').split('}},'))
        for host_filter in temp_host_filters:
            host_filter = host_filter.rstrip()
            if host_filter != "":
                if not host_filter.endswith("}}"):
                    host_filter += "}}"
                self.host_filters.append(host_filter)
        self.debugl('host filters are %s' % self.host_filters)

        temp_groupby_patterns = list(config.get('vmware', 'groupby_patterns').split('}},'))
        for groupby_pattern in temp_groupby_patterns:
            groupby_pattern = groupby_pattern.rstrip()
            if groupby_pattern != "":
                if not groupby_pattern.endswith("}}"):
                    groupby_pattern += "}}"
                self.groupby_patterns.append(groupby_pattern)
        self.debugl('groupby patterns are %s' % self.groupby_patterns)
        # Special feature to disable the brute force serialization of the
        # virtulmachine objects. The key name for these properties does not
        # matter because the values are just items for a larger list.
        if config.has_section('properties'):
            self.guest_props = []
            for prop in config.items('properties'):
                self.guest_props.append(prop[1])

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
        kwargs = {'host': self.server,
                  'user': self.username,
                  'pwd': self.password,
                  'port': int(self.port)}

        if hasattr(ssl, 'SSLContext') and not self.validate_certs:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
            kwargs['sslContext'] = context

        return self._get_instances(kwargs)

    def _get_instances(self, inkwargs):
        ''' Make API calls '''
        instances = []
        try:
            si = SmartConnect(**inkwargs)
        except ssl.SSLError as connection_error:
            if '[SSL: CERTIFICATE_VERIFY_FAILED]' in str(connection_error) and self.validate_certs:
                sys.exit("Unable to connect to ESXi server due to %s, "
                         "please specify validate_certs=False and try again" % connection_error)

        except Exception as exc:
            self.debugl("Unable to connect to ESXi server due to %s" % exc)
            sys.exit("Unable to connect to ESXi server due to %s" % exc)

        self.debugl('retrieving all instances')
        if not si:
            sys.exit("Could not connect to the specified host using specified "
                     "username and password")
        atexit.register(Disconnect, si)
        content = si.RetrieveContent()

        # Create a search container for virtualmachines
        self.debugl('creating containerview for virtualmachines')
        container = content.rootFolder
        viewType = [vim.VirtualMachine]
        recursive = True
        containerView = content.viewManager.CreateContainerView(container, viewType, recursive)
        children = containerView.view
        for child in children:
            # If requested, limit the total number of instances
            if self.args.max_instances:
                if len(instances) >= self.args.max_instances:
                    break
            instances.append(child)
        self.debugl("%s total instances in container view" % len(instances))

        if self.args.host:
            instances = [x for x in instances if x.name == self.args.host]

        instance_tuples = []
        for instance in sorted(instances):
            if self.guest_props:
                ifacts = self.facts_from_proplist(instance)
            else:
                ifacts = self.facts_from_vobj(instance)
            instance_tuples.append((instance, ifacts))
        self.debugl('facts collected for all instances')

        try:
            cfm = content.customFieldsManager
            if cfm is not None and cfm.field:
                for f in cfm.field:
                    if f.managedObjectType == vim.VirtualMachine:
                        self.custom_fields[f.key] = f.name
                self.debugl('%d custom fields collected' % len(self.custom_fields))
        except vmodl.RuntimeFault as exc:
            self.debugl("Unable to gather custom fields due to %s" % exc.msg)
        except IndexError as exc:
            self.debugl("Unable to gather custom fields due to %s" % exc)

        return instance_tuples

    def instances_to_inventory(self, instances):
        ''' Convert a list of vm objects into a json compliant inventory '''
        self.debugl('re-indexing instances based on ini settings')
        inventory = VMWareInventory._empty_inventory()
        inventory['all'] = {}
        inventory['all']['hosts'] = []
        for idx, instance in enumerate(instances):
            # make a unique id for this object to avoid vmware's
            # numerous uuid's which aren't all unique.
            thisid = str(uuid.uuid4())
            idata = instance[1]

            # Put it in the inventory
            inventory['all']['hosts'].append(thisid)
            inventory['_meta']['hostvars'][thisid] = idata.copy()
            inventory['_meta']['hostvars'][thisid]['ansible_uuid'] = thisid

        # Make a map of the uuid to the alias the user wants
        name_mapping = self.create_template_mapping(
            inventory,
            self.config.get('vmware', 'alias_pattern')
        )

        # Make a map of the uuid to the ssh hostname the user wants
        host_mapping = self.create_template_mapping(
            inventory,
            self.config.get('vmware', 'host_pattern')
        )

        # Reset the inventory keys
        for k, v in name_mapping.items():

            if not host_mapping or k not in host_mapping:
                continue

            # set ansible_host (2.x)
            try:
                inventory['_meta']['hostvars'][k]['ansible_host'] = host_mapping[k]
                # 1.9.x backwards compliance
                inventory['_meta']['hostvars'][k]['ansible_ssh_host'] = host_mapping[k]
            except Exception:
                continue

            if k == v:
                continue

            # add new key
            inventory['all']['hosts'].append(v)
            inventory['_meta']['hostvars'][v] = inventory['_meta']['hostvars'][k]

            # cleanup old key
            inventory['all']['hosts'].remove(k)
            inventory['_meta']['hostvars'].pop(k, None)

        self.debugl('pre-filtered hosts:')
        for i in inventory['all']['hosts']:
            self.debugl('  * %s' % i)
        # Apply host filters
        for hf in self.host_filters:
            if not hf:
                continue
            self.debugl('filter: %s' % hf)
            filter_map = self.create_template_mapping(inventory, hf, dtype='boolean')
            for k, v in filter_map.items():
                if not v:
                    # delete this host
                    inventory['all']['hosts'].remove(k)
                    inventory['_meta']['hostvars'].pop(k, None)

        self.debugl('post-filter hosts:')
        for i in inventory['all']['hosts']:
            self.debugl('  * %s' % i)

        # Create groups
        for gbp in self.groupby_patterns:
            groupby_map = self.create_template_mapping(inventory, gbp)
            for k, v in groupby_map.items():
                if v not in inventory:
                    inventory[v] = {}
                    inventory[v]['hosts'] = []
                if k not in inventory[v]['hosts']:
                    inventory[v]['hosts'].append(k)

        if self.config.get('vmware', 'groupby_custom_field'):
            for k, v in inventory['_meta']['hostvars'].items():
                if 'customvalue' in v:
                    for tv in v['customvalue']:
                        newkey = None
                        field_name = self.custom_fields[tv['key']] if tv['key'] in self.custom_fields else tv['key']
                        values = []
                        keylist = map(lambda x: x.strip(), tv['value'].split(','))
                        for kl in keylist:
                            try:
                                newkey = "%s%s_%s" % (self.config.get('vmware', 'custom_field_group_prefix'), str(field_name), kl)
                                newkey = newkey.strip()
                            except Exception as e:
                                self.debugl(e)
                            values.append(newkey)
                        for tag in values:
                            if not tag:
                                continue
                            if tag not in inventory:
                                inventory[tag] = {}
                                inventory[tag]['hosts'] = []
                            if k not in inventory[tag]['hosts']:
                                inventory[tag]['hosts'].append(k)

        return inventory

    def create_template_mapping(self, inventory, pattern, dtype='string'):
        ''' Return a hash of uuid to templated string from pattern '''
        mapping = {}
        for k, v in inventory['_meta']['hostvars'].items():
            t = self.env.from_string(pattern)
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

    def facts_from_proplist(self, vm):
        '''Get specific properties instead of serializing everything'''

        rdata = {}
        for prop in self.guest_props:
            self.debugl('getting %s property for %s' % (prop, vm.name))
            key = prop
            if self.lowerkeys:
                key = key.lower()

            if '.' not in prop:
                # props without periods are direct attributes of the parent
                vm_property = getattr(vm, prop)
                if isinstance(vm_property, vim.CustomFieldsManager.Value.Array):
                    temp_vm_property = []
                    for vm_prop in vm_property:
                        temp_vm_property.append({'key': vm_prop.key,
                                                 'value': vm_prop.value})
                    rdata[key] = temp_vm_property
                else:
                    rdata[key] = vm_property
            else:
                # props with periods are subkeys of parent attributes
                parts = prop.split('.')
                total = len(parts) - 1

                # pointer to the current object
                val = None
                # pointer to the current result key
                lastref = rdata

                for idx, x in enumerate(parts):

                    if isinstance(val, dict):
                        if x in val:
                            val = val.get(x)
                        elif x.lower() in val:
                            val = val.get(x.lower())
                    else:
                        # if the val wasn't set yet, get it from the parent
                        if not val:
                            try:
                                val = getattr(vm, x)
                            except AttributeError as e:
                                self.debugl(e)
                        else:
                            # in a subkey, get the subprop from the previous attrib
                            try:
                                val = getattr(val, x)
                            except AttributeError as e:
                                self.debugl(e)

                        # make sure it serializes
                        val = self._process_object_types(val)

                    # lowercase keys if requested
                    if self.lowerkeys:
                        x = x.lower()

                    # change the pointer or set the final value
                    if idx != total:
                        if x not in lastref:
                            lastref[x] = {}
                        lastref = lastref[x]
                    else:
                        lastref[x] = val

        return rdata

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
                self.debugl("get facts for %s" % vobj.name)
            except Exception as e:
                self.debugl(e)

        rdata = {}

        methods = dir(vobj)
        methods = [str(x) for x in methods if not x.startswith('_')]
        methods = [x for x in methods if x not in self.bad_types]
        methods = [x for x in methods if not x.lower() in self.skip_keys]
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

            rdata[method] = self._process_object_types(
                methodToCall,
                thisvm=vobj,
                inkey=method,
            )

        return rdata

    def _process_object_types(self, vobj, thisvm=None, inkey='', level=0):
        ''' Serialize an object '''
        rdata = {}

        if type(vobj).__name__ in self.vimTableMaxDepth and level >= self.vimTableMaxDepth[type(vobj).__name__]:
            return rdata

        if vobj is None:
            rdata = None
        elif type(vobj) in self.vimTable:
            rdata = {}
            for key in self.vimTable[type(vobj)]:
                try:
                    rdata[key] = getattr(vobj, key)
                except Exception as e:
                    self.debugl(e)

        elif issubclass(type(vobj), str) or isinstance(vobj, str):
            if vobj.isalnum():
                rdata = vobj
            else:
                rdata = vobj.decode('ascii', 'ignore')
        elif issubclass(type(vobj), bool) or isinstance(vobj, bool):
            rdata = vobj
        elif issubclass(type(vobj), integer_types) or isinstance(vobj, integer_types):
            rdata = vobj
        elif issubclass(type(vobj), float) or isinstance(vobj, float):
            rdata = vobj
        elif issubclass(type(vobj), list) or issubclass(type(vobj), tuple):
            rdata = []
            try:
                vobj = sorted(vobj)
            except Exception:
                pass

            for idv, vii in enumerate(vobj):
                if level + 1 <= self.maxlevel:
                    vid = self._process_object_types(
                        vii,
                        thisvm=thisvm,
                        inkey=inkey + '[' + str(idv) + ']',
                        level=(level + 1)
                    )

                    if vid:
                        rdata.append(vid)

        elif issubclass(type(vobj), dict):
            pass

        elif issubclass(type(vobj), object):
            methods = dir(vobj)
            methods = [str(x) for x in methods if not x.startswith('_')]
            methods = [x for x in methods if x not in self.bad_types]
            methods = [x for x in methods if not inkey + '.' + x.lower() in self.skip_keys]
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
                if level + 1 <= self.maxlevel:
                    try:
                        rdata[method] = self._process_object_types(
                            methodToCall,
                            thisvm=thisvm,
                            inkey=inkey + '.' + method,
                            level=(level + 1)
                        )
                    except vim.fault.NoPermission:
                        self.debugl("Skipping method %s (NoPermission)" % method)
        else:
            pass

        return rdata

    def get_host_info(self, host):
        ''' Return hostvars for a single host '''

        if host in self.inventory['_meta']['hostvars']:
            return self.inventory['_meta']['hostvars'][host]
        elif self.args.host and self.inventory['_meta']['hostvars']:
            match = None
            for k, v in self.inventory['_meta']['hostvars'].items():
                if self.inventory['_meta']['hostvars'][k]['name'] == self.args.host:
                    match = k
                    break
            if match:
                return self.inventory['_meta']['hostvars'][match]
            else:
                raise VMwareMissingHostException('%s not found' % host)
        else:
            raise VMwareMissingHostException('%s not found' % host)


if __name__ == "__main__":
    # Run the script
    print(VMWareInventory().show())
