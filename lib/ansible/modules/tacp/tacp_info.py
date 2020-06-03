#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.tacp_ansible import tacp_utils


import json
import tacp
import sys
from tacp.rest import ApiException
from pprint import pprint

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: tacp_instance

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
    module_args = dict(
        api_key=dict(type='str', required=True),
        resource=dict(type='str', required=True,
                      choices=[
                          "application",
                          "application_group",
                          "category",
                          "datacenter",
                          "firewall_profile",
                          "marketplace_template",
                          "migration_zone",
                          "site",
                          "storage_pool",
                          "tag",
                          "template",
                          "user",
                          "vlan",
                          "vnet"])
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        args=[]
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    def fail_with_reason(reason):
        result['msg'] = reason
        module.fail_json(**result)

    # Return the inputs for debugging purposes
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

    all_resources = resource.get_all()

    if module.params['resource'] == 'migration_zone':
        for resource in all_resources:
            if 'applications' in resource:
                applicationResource = tacp_utils.ApplicationResource(api_client)
                for application in resource['applications']:
                    application['name'] = applicationResource.get_by_uuid(application['uuid'])['name']
            if 'allocations' in resource:
                if 'categories' in resource['allocations']:
                    categoryResource = tacp_utils.CategoryResource(
                        api_client)
                    for category in resource['allocations']['categories']:
                        category['name'] = categoryResource.get_by_uuid(category['category_uuid'])[
                        'name']
                if 'datacenters' in resource['allocations']:
                    datacenterResource = tacp_utils.DatacenterResource(
                        api_client)
                    for datacenter in resource['allocations']['datacenters']:
                        datacenter['name'] = datacenterResource.get_by_uuid(datacenter['datacenter_uuid'])[
                            'name']
    result[module.params['resource']] = all_resources
    

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
