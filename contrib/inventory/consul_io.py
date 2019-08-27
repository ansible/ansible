#!/usr/bin/env python

#
# (c) 2015, Steve Gargan <steve.gargan@gmail.com>
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

######################################################################

'''
Consul.io inventory script (http://consul.io)
======================================

Generates Ansible inventory from nodes in a Consul cluster. This script will
group nodes by:
 - datacenter,
 - registered service
 - service tags
 - service status
 - values from the k/v store

This script can be run with the switches
--list as expected groups all the nodes in all datacenters
--datacenter, to restrict the nodes to a single datacenter
--host to restrict the inventory to a single named node. (requires datacenter config)

The configuration for this plugin is read from a consul_io.ini file located in the
same directory as this inventory script. All config options in the config file
are optional except the host and port, which must point to a valid agent or
server running the http api. For more information on enabling the endpoint see.

http://www.consul.io/docs/agent/options.html

Other options include:

'datacenter':

which restricts the included nodes to those from the given datacenter
This can also be set with the environmental variable CONSUL_DATACENTER

'url':

the URL of the Consul cluster. host, port and scheme are derived from the
URL. If not specified, connection configuration defaults to http requests
to localhost on port 8500.
This can also be set with the environmental variable CONSUL_URL

'domain':

if specified then the inventory will generate domain names that will resolve
via Consul's inbuilt DNS. The name is derived from the node name, datacenter
and domain <node_name>.node.<datacenter>.<domain>. Note that you will need to
have consul hooked into your DNS server for these to resolve. See the consul
DNS docs for more info.

which restricts the included nodes to those from the given datacenter

'servers_suffix':

defining the a suffix to add to the service name when creating the service
group. e.g Service name of 'redis' and a suffix of '_servers' will add
each nodes address to the group name 'redis_servers'. No suffix is added
if this is not set

'tags':

boolean flag defining if service tags should be used to create Inventory
groups e.g. an nginx service with the tags ['master', 'v1'] will create
groups nginx_master and nginx_v1 to which the node running the service
will be added. No tag groups are created if this is missing.

'token':

ACL token to use to authorize access to the key value store. May be required
to retrieve the kv_groups and kv_metadata based on your consul configuration.

'kv_groups':

This is used to lookup groups for a node in the key value store. It specifies a
path to which each discovered node's name will be added to create a key to query
the key/value store. There it expects to find a comma separated list of group
names to which the node should be added e.g. if the inventory contains node
'nyc-web-1' in datacenter 'nyc-dc1' and kv_groups = 'ansible/groups' then the key
'ansible/groups/nyc-dc1/nyc-web-1' will be queried for a group list. If this query
 returned 'test,honeypot' then the node address to both groups.

'kv_metadata':

kv_metadata is used to lookup metadata for each discovered node. Like kv_groups
above it is used to build a path to lookup in the kv store where it expects to
find a json dictionary of metadata entries. If found, each key/value pair in the
dictionary is added to the metadata for the node. eg node 'nyc-web-1' in datacenter
'nyc-dc1' and kv_metadata = 'ansible/metadata', then the key
'ansible/metadata/nyc-dc1/nyc-web-1' should contain '{"databse": "postgres"}'

'availability':

if true then availability groups will be created for each service. The node will
be added to one of the groups based on the health status of the service. The
group name is derived from the service name and the configurable availability
suffixes

'available_suffix':

suffix that should be appended to the service availability groups for available
services e.g. if the suffix is '_up' and the service is nginx, then nodes with
healthy nginx services will be added to the nginix_up group. Defaults to
'_available'

'unavailable_suffix':

as above but for unhealthy services, defaults to '_unavailable'

Note that if the inventory discovers an 'ssh' service running on a node it will
register the port as ansible_ssh_port in the node's metadata and this port will
be used to access the machine.
```

'''

import os
import re
import argparse
import sys

from ansible.module_utils.six.moves import configparser


def get_log_filename():
    tty_filename = '/dev/tty'
    stdout_filename = '/dev/stdout'

    if not os.path.exists(tty_filename):
        return stdout_filename
    if not os.access(tty_filename, os.W_OK):
        return stdout_filename
    if os.getenv('TEAMCITY_VERSION'):
        return stdout_filename

    return tty_filename


def setup_logging():
    filename = get_log_filename()

    import logging.config
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
        },
        'root': {
            'level': os.getenv('ANSIBLE_INVENTORY_CONSUL_IO_LOG_LEVEL', 'WARN'),
            'handlers': ['console'],
        },
        'handlers': {
            'console': {
                'class': 'logging.FileHandler',
                'filename': filename,
                'formatter': 'simple',
            },
        },
        'loggers': {
            'iso8601': {
                'qualname': 'iso8601',
                'level': 'INFO',
            },
        },
    })
    logger = logging.getLogger('consul_io.py')
    logger.debug('Invoked with %r', sys.argv)


if os.getenv('ANSIBLE_INVENTORY_CONSUL_IO_LOG_ENABLED'):
    setup_logging()


import json

try:
    import consul
except ImportError as e:
    sys.exit("""failed=True msg='python-consul required for this module.
See https://python-consul.readthedocs.io/en/latest/#installation'""")

from ansible.module_utils.six import iteritems


class ConsulInventory(object):

    def __init__(self):
        ''' Create an inventory based on the catalog of nodes and services
        registered in a consul cluster'''
        self.node_metadata = {}
        self.nodes = {}
        self.nodes_by_service = {}
        self.nodes_by_tag = {}
        self.nodes_by_datacenter = {}
        self.nodes_by_kv = {}
        self.nodes_by_availability = {}
        self.current_dc = None
        self.inmemory_kv = []
        self.inmemory_nodes = []

        config = ConsulConfig()
        self.config = config

        self.consul_api = config.get_consul_api()

        if config.has_config('datacenter'):
            if config.has_config('host'):
                self.load_data_for_node(config.host, config.datacenter)
            else:
                self.load_data_for_datacenter(config.datacenter)
        else:
            self.load_all_data_consul()

        self.combine_all_results()
        print(json.dumps(self.inventory, sort_keys=True, indent=2))

    def bulk_load(self, datacenter):
        index, groups_list = self.consul_api.kv.get(self.config.kv_groups, recurse=True, dc=datacenter)
        index, metadata_list = self.consul_api.kv.get(self.config.kv_metadata, recurse=True, dc=datacenter)
        index, nodes = self.consul_api.catalog.nodes(dc=datacenter)
        self.inmemory_kv += groups_list
        self.inmemory_kv += metadata_list
        self.inmemory_nodes += nodes

    def load_all_data_consul(self):
        ''' cycle through each of the datacenters in the consul catalog and process
            the nodes in each '''
        self.datacenters = self.consul_api.catalog.datacenters()
        for datacenter in self.datacenters:
            self.current_dc = datacenter
            self.bulk_load(datacenter)
            self.load_data_for_datacenter(datacenter)

    def load_availability_groups(self, node, datacenter):
        '''check the health of each service on a node and add the node to either
        an 'available' or 'unavailable' grouping. The suffix for each group can be
        controlled from the config'''
        if self.config.has_config('availability'):
            for service_name, service in iteritems(node['Services']):
                for node in self.consul_api.health.service(service_name)[1]:
                    if self.is_service_available(node, service_name):
                        suffix = self.config.get_availability_suffix(
                            'available_suffix', '_available')
                    else:
                        suffix = self.config.get_availability_suffix(
                            'unavailable_suffix', '_unavailable')
                    self.add_node_to_map(self.nodes_by_availability,
                                         service_name + suffix, node['Node'])

    def is_service_available(self, node, service_name):
        '''check the availability of the service on the node beside ensuring the
        availability of the node itself'''
        consul_ok = service_ok = False
        for check in node['Checks']:
            if check['CheckID'] == 'serfHealth':
                consul_ok = check['Status'] == 'passing'
            elif check['ServiceName'] == service_name:
                service_ok = check['Status'] == 'passing'
        return consul_ok and service_ok

    def consul_get_kv_inmemory(self, key):
        result = filter(lambda x: x['Key'] == key, self.inmemory_kv)
        return result.pop() if result else None

    def consul_get_node_inmemory(self, node):
        result = filter(lambda x: x['Node'] == node, self.inmemory_nodes)
        return {"Node": result.pop(), "Services": {}} if result else None

    def load_data_for_datacenter(self, datacenter):
        '''processes all the nodes in a particular datacenter'''
        if self.config.bulk_load == 'true':
            nodes = self.inmemory_nodes
        else:
            index, nodes = self.consul_api.catalog.nodes(dc=datacenter)
        for node in nodes:
            self.add_node_to_map(self.nodes_by_datacenter, datacenter, node)
            self.load_data_for_node(node['Node'], datacenter)

    def load_data_for_node(self, node, datacenter):
        '''loads the data for a single node adding it to various groups based on
        metadata retrieved from the kv store and service availability'''

        if self.config.suffixes == 'true':
            index, node_data = self.consul_api.catalog.node(node, dc=datacenter)
        else:
            node_data = self.consul_get_node_inmemory(node)
        node = node_data['Node']

        self.add_node_to_map(self.nodes, 'all', node)
        self.add_metadata(node_data, "consul_datacenter", datacenter)
        self.add_metadata(node_data, "consul_nodename", node['Node'])

        self.load_groups_from_kv(node_data)
        self.load_node_metadata_from_kv(node_data)
        if self.config.suffixes == 'true':
            self.load_availability_groups(node_data, datacenter)
            for name, service in node_data['Services'].items():
                self.load_data_from_service(name, service, node_data)

    def load_node_metadata_from_kv(self, node_data):
        ''' load the json dict at the metadata path defined by the kv_metadata value
            and the node name add each entry in the dictionary to the node's
            metadata '''
        node = node_data['Node']
        if self.config.has_config('kv_metadata'):
            key = "%s/%s/%s" % (self.config.kv_metadata, self.current_dc, node['Node'])
            if self.config.bulk_load == 'true':
                metadata = self.consul_get_kv_inmemory(key)
            else:
                index, metadata = self.consul_api.kv.get(key)
            if metadata and metadata['Value']:
                try:
                    metadata = json.loads(metadata['Value'])
                    for k, v in metadata.items():
                        self.add_metadata(node_data, k, v)
                except Exception:
                    pass

    def load_groups_from_kv(self, node_data):
        ''' load the comma separated list of groups at the path defined by the
            kv_groups config value and the node name add the node address to each
            group found '''
        node = node_data['Node']
        if self.config.has_config('kv_groups'):
            key = "%s/%s/%s" % (self.config.kv_groups, self.current_dc, node['Node'])
            if self.config.bulk_load == 'true':
                groups = self.consul_get_kv_inmemory(key)
            else:
                index, groups = self.consul_api.kv.get(key)
            if groups and groups['Value']:
                for group in groups['Value'].split(','):
                    self.add_node_to_map(self.nodes_by_kv, group.strip(), node)

    def load_data_from_service(self, service_name, service, node_data):
        '''process a service registered on a node, adding the node to a group with
        the service name. Each service tag is extracted and the node is added to a
        tag grouping also'''
        self.add_metadata(node_data, "consul_services", service_name, True)

        if self.is_service("ssh", service_name):
            self.add_metadata(node_data, "ansible_ssh_port", service['Port'])

        if self.config.has_config('servers_suffix'):
            service_name = service_name + self.config.servers_suffix

        self.add_node_to_map(self.nodes_by_service, service_name, node_data['Node'])
        self.extract_groups_from_tags(service_name, service, node_data)

    def is_service(self, target, name):
        return name and (name.lower() == target.lower())

    def extract_groups_from_tags(self, service_name, service, node_data):
        '''iterates each service tag and adds the node to groups derived from the
        service and tag names e.g. nginx_master'''
        if self.config.has_config('tags') and service['Tags']:
            tags = service['Tags']
            self.add_metadata(node_data, "consul_%s_tags" % service_name, tags)
            for tag in service['Tags']:
                tagname = service_name + '_' + tag
                self.add_node_to_map(self.nodes_by_tag, tagname, node_data['Node'])

    def combine_all_results(self):
        '''prunes and sorts all groupings for combination into the final map'''
        self.inventory = {"_meta": {"hostvars": self.node_metadata}}
        groupings = [self.nodes, self.nodes_by_datacenter, self.nodes_by_service,
                     self.nodes_by_tag, self.nodes_by_kv, self.nodes_by_availability]
        for grouping in groupings:
            for name, addresses in grouping.items():
                self.inventory[name] = sorted(list(set(addresses)))

    def add_metadata(self, node_data, key, value, is_list=False):
        ''' Pushed an element onto a metadata dict for the node, creating
            the dict if it doesn't exist '''
        key = self.to_safe(key)
        node = self.get_inventory_name(node_data['Node'])

        if node in self.node_metadata:
            metadata = self.node_metadata[node]
        else:
            metadata = {}
            self.node_metadata[node] = metadata
        if is_list:
            self.push(metadata, key, value)
        else:
            metadata[key] = value

    def get_inventory_name(self, node_data):
        '''return the ip or a node name that can be looked up in consul's dns'''
        domain = self.config.domain
        if domain:
            node_name = node_data['Node']
            if self.current_dc:
                return '%s.node.%s.%s' % (node_name, self.current_dc, domain)
            else:
                return '%s.node.%s' % (node_name, domain)
        else:
            return node_data['Address']

    def add_node_to_map(self, map, name, node):
        self.push(map, name, self.get_inventory_name(node))

    def push(self, my_dict, key, element):
        ''' Pushed an element onto an array that may not have been defined in the
            dict '''
        key = self.to_safe(key)
        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be used
         as Ansible groups '''
        return re.sub(r'[^A-Za-z0-9\-\.]', '_', word)

    def sanitize_dict(self, d):

        new_dict = {}
        for k, v in d.items():
            if v is not None:
                new_dict[self.to_safe(str(k))] = self.to_safe(str(v))
        return new_dict

    def sanitize_list(self, seq):
        new_seq = []
        for d in seq:
            new_seq.append(self.sanitize_dict(d))
        return new_seq


class ConsulConfig(dict):

    def __init__(self):
        self.read_settings()
        self.read_cli_args()
        self.read_env_vars()

    def has_config(self, name):
        if hasattr(self, name):
            return getattr(self, name)
        else:
            return False

    def read_settings(self):
        ''' Reads the settings from the consul_io.ini file (or consul.ini for backwards compatibility)'''
        config = configparser.SafeConfigParser()
        if os.path.isfile(os.path.dirname(os.path.realpath(__file__)) + '/consul_io.ini'):
            config.read(os.path.dirname(os.path.realpath(__file__)) + '/consul_io.ini')
        else:
            config.read(os.path.dirname(os.path.realpath(__file__)) + '/consul.ini')

        config_options = ['host', 'token', 'datacenter', 'servers_suffix',
                          'tags', 'kv_metadata', 'kv_groups', 'availability',
                          'unavailable_suffix', 'available_suffix', 'url',
                          'domain', 'suffixes', 'bulk_load']
        for option in config_options:
            value = None
            if config.has_option('consul', option):
                value = config.get('consul', option).lower()
            setattr(self, option, value)

    def read_cli_args(self):
        ''' Command line argument processing '''
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based nodes in a Consul cluster')

        parser.add_argument('--list', action='store_true',
                            help='Get all inventory variables from all nodes in the consul cluster')
        parser.add_argument('--host', action='store',
                            help='Get all inventory variables about a specific consul node,'
                                 'requires datacenter set in consul.ini.')
        parser.add_argument('--datacenter', action='store',
                            help='Get all inventory about a specific consul datacenter')

        args = parser.parse_args()
        arg_names = ['host', 'datacenter']

        for arg in arg_names:
            if getattr(args, arg):
                setattr(self, arg, getattr(args, arg))

    def read_env_vars(self):
        env_var_options = ['datacenter', 'url']
        for option in env_var_options:
            value = None
            env_var = 'CONSUL_' + option.upper()
            if os.environ.get(env_var):
                setattr(self, option, os.environ.get(env_var))

    def get_availability_suffix(self, suffix, default):
        if self.has_config(suffix):
            return self.has_config(suffix)
        return default

    def get_consul_api(self):
        '''get an instance of the api based on the supplied configuration'''
        host = 'localhost'
        port = 8500
        token = None
        scheme = 'http'

        if hasattr(self, 'url'):
            from ansible.module_utils.six.moves.urllib.parse import urlparse
            o = urlparse(self.url)
            if o.hostname:
                host = o.hostname
            if o.port:
                port = o.port
            if o.scheme:
                scheme = o.scheme

        if hasattr(self, 'token'):
            token = self.token
            if not token:
                token = 'anonymous'
        return consul.Consul(host=host, port=port, token=token, scheme=scheme)


ConsulInventory()
