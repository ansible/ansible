#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
# Copyright (c) 2019 Matti Ranta, (@techknowlogick)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_mariadbserver_facts
version_added: "2.8"
short_description: Get Azure MariaDB Server facts.
description:
    - Get facts of MariaDB Server.

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    name:
        description:
            - The name of the server.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"
    - "Matti Ranta (@techknowlogick)"

'''

EXAMPLES = '''
  - name: Get instance of MariaDB Server
    azure_rm_mariadbserver_facts:
      resource_group: myResourceGroup
      name: server_name

  - name: List instances of MariaDB Server
    azure_rm_mariadbserver_facts:
      resource_group: myResourceGroup
'''

RETURN = '''
servers:
    description: A list of dictionaries containing facts for MariaDB servers.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.DBforMariaDB/servers/myabdud1223
        resource_group:
            description:
                - Resource group name.
            returned: always
            type: str
            sample: myResourceGroup
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: myabdud1223
        location:
            description:
                - The location the resource resides in.
            returned: always
            type: str
            sample: eastus
        sku:
            description:
                - The SKU of the server.
            returned: always
            type: complex
            contains:
                name:
                    description:
                        - The name of the SKU
                    returned: always
                    type: str
                    sample: GP_Gen4_2
                tier:
                    description:
                        - The tier of the particular SKU
                    returned: always
                    type: str
                    sample: GeneralPurpose
                capacity:
                    description:
                        - The scale capacity.
                    returned: always
                    type: int
                    sample: 2
        storage_mb:
            description:
                - The maximum storage allowed for a server.
            returned: always
            type: int
            sample: 128000
        enforce_ssl:
            description:
                - Enable SSL enforcement.
            returned: always
            type: bool
            sample: False
        admin_username:
            description:
                - "The administrator's login name of a server."
            returned: always
            type: str
            sample: serveradmin
        version:
            description:
                - Server version.
            returned: always
            type: str
            sample: "9.6"
        user_visible_state:
            description:
                - A state of a server that is visible to user.
            returned: always
            type: str
            sample: Ready
        fully_qualified_domain_name:
            description:
                - The fully qualified domain name of a server.
            returned: always
            type: str
            sample: myabdud1223.mys.database.azure.com
        tags:
            description: Tags assigned to the resource. Dictionary of string:string pairs.
            type: dict
            sample: { tag1: abc }
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.rdbms.mariadb import MariaDBManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMMariaDbServerFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            ),
            tags=dict(
                type='list'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.resource_group = None
        self.name = None
        self.tags = None
        super(AzureRMMariaDbServerFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if (self.resource_group is not None and
                self.name is not None):
            self.results['servers'] = self.get()
        elif (self.resource_group is not None):
            self.results['servers'] = self.list_by_resource_group()
        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mariadb_client.servers.get(resource_group_name=self.resource_group,
                                                       server_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for MariaDB Server.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_item(response))

        return results

    def list_by_resource_group(self):
        response = None
        results = []
        try:
            response = self.mariadb_client.servers.list_by_resource_group(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for MariaDB Servers.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_item(item))

        return results

    def format_item(self, item):
        d = item.as_dict()
        d = {
            'id': d['id'],
            'resource_group': self.resource_group,
            'name': d['name'],
            'sku': d['sku'],
            'location': d['location'],
            'storage_mb': d['storage_profile']['storage_mb'],
            'version': d['version'],
            'enforce_ssl': (d['ssl_enforcement'] == 'Enabled'),
            'admin_username': d['administrator_login'],
            'user_visible_state': d['user_visible_state'],
            'fully_qualified_domain_name': d['fully_qualified_domain_name'],
            'tags': d.get('tags')
        }

        return d


def main():
    AzureRMMariaDbServerFacts()


if __name__ == '__main__':
    main()
