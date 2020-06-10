#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.tacp_ansible import tacp_utils


import tacp
from tacp.rest import ApiException


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: tacp_info

short_description: This is my test module

version_added: "2.9"

description:
    - "This is my longer description explaining my test module"

options:
    name:
        description:
            - This is the message to send to the test module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - tacp

author:
    - Xander Madsen (@xmadsen)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  tacp_instance:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  tacp_instance:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  tacp_instance:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the test module generates
    type: str
    returned: always
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = {
        "api_key": {"type": 'str', "required": True},
        "resource": {"type": 'str', "required": True,
                     "choices": [
                         "application",
                         "application_group",
                         "category",
                         "datacenter",
                         "firewall_profile",
                         "instance",
                         "marketplace_template",
                         "migration_zone",
                         "site",
                         "storage_pool",
                         "tag",
                         "template",
                         "user",
                         "vlan",
                         "vnet"]}
    }

    result = dict(
        changed=False,
        args=[]
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    result['args'] = module.params

    # Define configuration
    configuration = tacp.Configuration()
    configuration.host = "https://manage.cp.lenovo.com"
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.api_key['Authorization'] = module.params['api_key']
    api_client = tacp.ApiClient(configuration)

    resource_dict = {"application": tacp_utils.ApplicationResource,
                     "application_group": tacp_utils.ApplicationGroupResource,
                     "category": tacp_utils.CategoryResource,
                     "datacenter": tacp_utils.DatacenterResource,
                     "firewall_profile": tacp_utils.FirewallProfileResource,
                     "instance": tacp_utils.ApplicationResource,
                     "marketplace_template": tacp_utils.MarketplaceTemplateResource,
                     "migration_zone": tacp_utils.MigrationZoneResource,
                     "site": tacp_utils.SiteResource,
                     "storage_pool": tacp_utils.StoragePoolResource,
                     "tag": tacp_utils.TagResource,
                     "template": tacp_utils.TemplateResource,
                     "user": tacp_utils.UserResource,
                     "vlan": tacp_utils.VlanResource,
                     "vnet": tacp_utils.VnetResource
                     }

    resource = resource_dict[module.params['resource']](api_client)

    items = [item.to_dict() for item in resource.filter()]

    if module.params['resource'] == 'migration_zone':
        application_resource = tacp_utils.ApplicationResource(
            api_client)
        category_resource = tacp_utils.CategoryResource(
            api_client)
        datacenter_resource = tacp_utils.DatacenterResource(
            api_client)
        for item in items:
            if 'applications' in item:
                for application in item['applications']:
                    application['name'] = application_resource.get_by_uuid(
                        application['uuid']).to_dict()['name']

            if 'allocations' in item:
                if 'categories' in item['allocations']:
                    for category in item['allocations']['categories']:
                        category['name'] = category_resource.get_by_uuid(
                            category['category_uuid']).to_dict()['name']

                if 'datacenters' in item['allocations']:
                    for datacenter in item['allocations']['datacenters']:
                        datacenter['name'] = datacenter_resource.get_by_uuid(
                            datacenter['datacenter_uuid']).to_dict()['name']

    elif module.params['resource'] == 'datacenter':
        vnet_resource = tacp_utils.VnetResource(api_client)
        vlan_resource = tacp_utils.VlanResource(api_client)
        tag_resource = tacp_utils.TagResource(api_client)
        for item in items:
            if 'networks' in item:
                for network in item['networks']:
                    try:
                        network['name'] = vnet_resource.get_by_uuid(
                            network['uuid']).to_dict()['name']
                        network['network_type'] = 'vnet'
                    except Exception:
                        network['name'] = vlan_resource.get_by_uuid(
                            network['uuid']).to_dict()['name']
                        network['network_type'] = 'vlan'
            if 'tags' in item:
                for tag in item['tags']:
                    tag['name'] = tag_resource.get_by_uuid(
                        tag['uuid']).to_dict()['name']

    result[module.params['resource']] = items

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
