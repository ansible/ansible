# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2020-04-12 12:08:42 alex>
#

"""
 EfficientIP inventory for ansible
 SOLIDserver Device Manager connection to gather devices filtered
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ipaddress
# import pprint
import logging

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.plugins.inventory import Constructable, Cacheable
from ansible.utils.display import Display
from ansible.errors import AnsibleError

try:
    from SOLIDserverRest import adv as sdsadv
    from SOLIDserverRest import SDSError
except ImportError:
    raise AnsibleError('The efficientip dynamic inventory'
                       ' plugin requires SOLIDserverRest')

logging.basicConfig(format='[%(filename)s:%(lineno)d]'
                    ' %(levelname)s: %(message)s',
                    level=logging.INFO)

DOCUMENTATION = '''
    name: efficientip
    plugin_type: inventory
    short_description: inventory based on EfficientIP IPAM
    requirements:
        - SOLIDserverRest > 2.0.1
        - python 3
    extends_documentation_fragment:
        - inventory_cache
    description:
        - Get inventory hosts from EfficientIP IPAM and Device Manager
        - Uses a YAML configuration file C(efficientip.(yml|yaml)).
    author:
        - Alex Chauvin (@efficientip)
    options:
        plugin:
            description: Token that ensures this is a source file for
                         the plugin.
            required: True
            choices: ['efficientip']
        api:
            description: information to get connected to the SOLIDserver
            required: True
            type: dictionary
        space:
            description: name of the space
            required: False
            type: string
            default: Local
        filter:
            description: list of filters to reduce the set of devices
                         returned from Device Manager. Can mix limit,
                         device_in_subnet, device_of_class,
                         device_metadata, device_intf_space. All
                         filter are additiionnal, all conditions must
                         match
            required: False
            type: dictionary
        group_metadata:
            description: regroup devices by metadata
            required: False
            type: list
'''

EXAMPLES = '''
# example with only credentials to get the whole content of Device Manager
plugin: efficientip
api:
 - host: 192.168.16.117
 - user: admin
 - password: admin
 - ssl_verify: false

# filter devices with interface in the IP range
filter:
 - device_in_subnet: 10.156.48.0/24

# filter devices with limit on number of result
filter:
 - limit: 5

# to get the ip address in addition to the name of the host,
# at least one IP filter
filter:
 - limit: 5
 - device_in_subnet: 0.0.0.0/0

# filter devices with specific class
filter:
 - device_of_class: AWS-EC2

# filter devices with metadata set to specific value
filter:
 - device_metadata:
   - cores: 1

# filter devices with interface in the specified space
filter:
 - device_intf_space: AWS

# use metadata for grouping, the group key1 will contain
# subgroup for each value (eg key1_on and key1_off)
group_metadata:
 - key1
 - key2

'''


DISPLAY = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    """ dynamic inventory module for EfficientIP Device Manager"""
    NAME = 'efficientip'

    sds = None
    space = None
    device_filter = []
    limit = 0
    group_metadata = []
    group_metadata_val = []

    def __init__(self):
        """ initialize the inventory module """
        super(InventoryModule, self).__init__()
        self.sds = None
        self.space = None
        self.limit = 0

    def sds_connect(self, config):
        """ connects to the SOLIDServer """
        conf_vars = {'ssl_verify': True}

        if 'api' not in config:
            DISPLAY.error("no api section in configuration")
            return None

        for params in config['api']:
            for param in params:
                if param in ['host', 'user', 'password', 'certificate']:
                    conf_vars[param] = params[param]
                elif param == 'ssl_verify':
                    conf_vars['ssl_verify'] = bool(params[param])

        if ('host' not in conf_vars
                or 'user' not in conf_vars
                or 'password' not in conf_vars):
            DISPLAY.error('missing parameter in api section'
                          ' (host, user, password)')
            return None

        if 'ssl_verify' in conf_vars and 'certificate' not in conf_vars:
            DISPLAY.error("missing certificate file with ssl verify")
            return None

        self.sds = sdsadv.SDS(ip_address=conf_vars['host'],
                              user=conf_vars['user'],
                              pwd=conf_vars['password'])

        try:
            if 'certificate' not in conf_vars:
                self.sds.connect(method="basicauth")
            else:
                self.sds.connect(method="basicauth",
                                 cert_file_path=conf_vars['certificate'])
                DISPLAY.debug('connected to', self.sds)

        except SDSError:
            DISPLAY.error("EfficientIP connection error to SOLIDserver")
            return None

        return True

    def sds_switch_space(self, config):
        """ get space and switch to it """
        space_name = 'Local'
        if 'space' in config:
            space_name = config['space']

        self.space = sdsadv.Space(sds=self.sds, name=space_name)
        self.space.refresh()

    def set_filter_in_subnet(self, address):
        """ add a filter based on device_in_subnet => in_subnet """
        try:
            ipv4 = str(ipaddress.IPv4Network(address))
        except ValueError:
            DISPLAY.error('ipv4 only subnet in device'
                          ' filter device_in_subnet')
            return False

        filt = {'type': 'in_subnet', 'val': ipv4}
        self.device_filter.append(filt)

        return True

    def set_filter_metadata(self, params):
        """ add a filter based on device_metadata """
        for metadatas in params:
            for metadata in metadatas.keys():
                filt = {'type': 'metadata'}
                filt['name'] = str(metadata)
                filt['val'] = str(metadatas[metadata])
                self.device_filter.append(filt)

    def sds_set_filters(self, config):
        """ get filters if any for devices """
        if 'filter' not in config:
            return True

        if not config['filter']:
            DISPLAY.warning('filter section empty')
            return False

        for params in config['filter']:
            for param in params:
                if param == 'device_in_subnet':
                    self.set_filter_in_subnet(params[param])

                elif param == 'device_of_class':
                    filt = {'type': 'of_class', 'val': str(params[param])}
                    self.device_filter.append(filt)

                elif param == 'device_intf_space':
                    filt = {'type': 'space', 'val': str(params[param])}
                    self.device_filter.append(filt)

                elif param == 'limit':
                    self.limit = int(params[param])
                    if self.limit < 0:
                        self.limit = 0

                elif param == 'device_metadata':
                    self.set_filter_metadata(params[param])

                else:
                    DISPLAY.error('unknwn param', str(param))
                    return False

        return True

    def sds_set_group(self, config):
        """ get metadata for enrich & group """
        if 'group_metadata' not in config:
            return True

        for group in config['group_metadata']:
            self.group_metadata.append(str(group))
            self.inventory.add_group(str(group))

        return True

    def verify_file(self, path):
        ''' can we get correct file '''
        if super(InventoryModule, self).verify_file(path):
            # base class verifies that file exists and
            # is readable by current user
            if path.endswith(('efficientip.yaml',
                              'efficientip.yml')):
                return True

        DISPLAY.debug("EfficientIP inventory requires"
                      " 'efficientip.yml' file")
        return False

    def _populate(self, adevs):
        for dev in adevs:
            badded = False

            # check if group
            for _group in self.group_metadata:
                if _group in dev and dev[_group] != '':
                    _group_val = "{1}_{2}".format(_group, dev[_group])
                    if _group_val not in self.group_metadata_val:
                        self.inventory.add_group(_group_val)
                        self.inventory.add_child(_group, _group_val)
                    self.inventory.add_host(dev['name'], _group_val)

                    badded = True

            if not badded:
                self.inventory.add_host(dev['name'])

            if 'extracted_ips' in dev:
                self.inventory.set_variable(dev['name'],
                                            'ansible_host',
                                            dev['extracted_ips'][0])

            for filt in self.device_filter:
                if filt['type'] == 'of_class':
                    self.inventory.set_variable(dev['name'],
                                                'eip_class',
                                                filt['val'])
                if filt['type'] == 'metadata':
                    self.inventory.set_variable(dev['name'],
                                                'eip_metadata_'
                                                '{1}'.format(filt['name']),
                                                filt['val'])
            # self.inventory.add_group('g1')

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self.load_cache_plugin()

        config = self._read_config_data(path)

        cache_key = self.get_cache_key(path)
        cache = self.get_option('cache')

        cache_needs_update = True
        adevs = []

        if cache:
            try:
                adevs = self._cache[cache_key]
                cache_needs_update = False
            except KeyError:
                cache_needs_update = True

        if cache_needs_update:
            # connects to the SOLIDserver
            if self.sds_connect(config) is None:
                return

            # check the presence of the space
            self.sds_switch_space(config)

            # set filters
            self.sds_set_filters(config)

            # set group
            self.sds_set_group(config)

            adevs = sdsadv.list_devices(self.sds,
                                        limit=self.limit,
                                        filters=self.device_filter,
                                        metadatas=self.group_metadata)

        if cache_needs_update or (not cache and self.get_option('cache')):
            self._cache[cache_key] = adevs

        self._populate(adevs)

#
# ansible-test sanity --test pylint lib/ansible/plugins/inventory/efficientip.py
# ansible-test sanity --test future-import-boilerplate lib/ansible/plugins/inventory/efficientip.py
# ansible-test sanity --test metaclass-boilerplate lib/ansible/plugins/inventory/efficientip.py
