DOCUMENTATION = r'''
    name: Infoblox
    plugin_type: inventory
    author:
      - Will Tome (@willtome)
    short_description: Infoblox inventory plugin
    version_added: "2.10"
    description:
        - Infoblox inventory plugin
    options:
        host:
            description: Infoblox server
            type: string
            required: True
            env:
                - name: INFOBLOX_HOST
        username:
            description: username 
            type: string
            required: True
            env:
                - name: INFOBLOX_USERNAME
        password:
            description: password
            type: string
            secret: true
            env:
                - name: INFOBLOX_PASSWORD
        extattrs:
            description: restrict returned hosts by extensible attributes
            default: {}
        hostfilter:
            description: restrict returned hosts
            default: {}
    requirements:
        - python >= 3.4
        - infoblox-client
'''

EXAMPLES = r'''
plugin: infoblox
host: blox.example.com
username: admin
'''

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils.net_tools.nios.api import WapiInventory
from ansible.module_utils.net_tools.nios.api import normalize_extattrs, flatten_extattrs
from ansible.module_utils.six import iteritems


class InventoryModule(BaseInventoryPlugin):

    NAME = 'infoblox'

    def parse(self, inventory, loader, path, cache=True):  # Plugin interface (2)
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        provider = { 'host': self.get_option('host'),
                        'username': self.get_option('username'),
                        'password': self.get_option('password')}

        wapi = WapiInventory(provider)

        host_filter = self.get_option('hostfilter')
        extattrs = normalize_extattrs(self.get_option('extattrs'))
        return_fields = ['name', 'view', 'extattrs', 'ipv4addrs']

        print(host_filter)

        hosts = wapi.get_object('record:host',
                            host_filter,
                            extattrs=extattrs,
                            return_fields=return_fields)

        for host in hosts:
            group_name = self.inventory.add_group(host['view'])
            host_name = self.inventory.add_host(host['name'])
            self.inventory.add_child(group_name, host_name)

            self.inventory.set_variable(host_name, 'view', host['view'])

            for key, value in iteritems(flatten_extattrs(host['extattrs'])):
                self.inventory.set_variable(host_name, key, value)
