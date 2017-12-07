#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: azure_rm_publicipaddress

version_added: "2.1"

short_description: Manage Azure Public IP Addresses.

description:
    - Create, update and delete a Public IP address. Allows setting and updating the address allocation method and
      domain name label. Use the azure_rm_networkinterface module to associate a Public IP with a network interface.

options:
    resource_group:
        description:
            - Name of resource group with which the Public IP is associated.
        required: true
    allocation_method:
        description:
            - Control whether the assigned Public IP remains permanently assigned to the object. If not
              set to 'Static', the IP address my changed anytime an associated virtual machine is power cycled.
        choices:
            - Dynamic
            - Static
        default: Dynamic
        required: false
    domain_name_label:
        description:
            - The customizable portion of the FQDN assigned to public IP address. This is an explicit setting. If
              no value is provided, any existing value will be removed on an existing public IP.
        aliases:
            - domain_name_label
        required: false
        default: null
    name:
        description:
            - Name of the Public IP.
        required: true
    state:
        description:
            - Assert the state of the Public IP. Use 'present' to create or update a and
              'absent' to delete.
        default: present
        choices:
            - absent
            - present
        required: false
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        default: resource_group location
        required: false

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"
'''

EXAMPLES = '''
    - name: Create a public ip address
      azure_rm_publicipaddress:
        resource_group: testing
        name: my_public_ip
        allocation_method: Static
        domain_name: foobar

    - name: Delete public ip
      azure_rm_publicipaddress:
        resource_group: testing
        name: my_public_ip
        state: absent
'''

RETURN = '''
state:
    description: Facts about the current state of the object.
    returned: always
    type: dict
    sample: {
        "dns_settings": {},
        "etag": '"/"a5e56955-12df-445a-bda4-dc129d22c12f"',
        "idle_timeout_in_minutes": 4,
        "ip_address": "52.160.103.93",
        "location": "westus",
        "name": "publicip002",
        "provisioning_state": "Succeeded",
        "public_ip_allocation_method": "Static",
        "tags": {},
        "type": "Microsoft.Network/publicIPAddresses"
    }
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network.models import PublicIPAddress, PublicIPAddressDnsSettings
except ImportError:
    # This is handled in azure_rm_common
    pass


def pip_to_dict(pip):
    result = dict(
        name=pip.name,
        type=pip.type,
        location=pip.location,
        tags=pip.tags,
        public_ip_allocation_method=pip.public_ip_allocation_method,
        dns_settings=dict(),
        ip_address=pip.ip_address,
        idle_timeout_in_minutes=pip.idle_timeout_in_minutes,
        provisioning_state=pip.provisioning_state,
        etag=pip.etag
    )
    if pip.dns_settings:
        result['dns_settings']['domain_name_label'] = pip.dns_settings.domain_name_label
        result['dns_settings']['fqdn'] = pip.dns_settings.fqdn
        result['dns_settings']['reverse_fqdn'] = pip.dns_settings.reverse_fqdn
    return result


class AzureRMPublicIPAddress(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            allocation_method=dict(type='str', default='Dynamic', choices=['Dynamic', 'Static']),
            domain_name=dict(type='str', aliases=['domain_name_label']),
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.state = None
        self.tags = None
        self.allocation_method = None
        self.domain_name = None

        self.results = dict(
            changed=False,
            state=dict()
        )

        super(AzureRMPublicIPAddress, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                     supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        results = dict()
        changed = False
        pip = None

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        try:
            self.log("Fetch public ip {0}".format(self.name))
            pip = self.network_client.public_ip_addresses.get(self.resource_group, self.name)
            self.check_provisioning_state(pip, self.state)
            self.log("PIP {0} exists".format(self.name))
            if self.state == 'present':
                results = pip_to_dict(pip)
                if self.domain_name != results['dns_settings'].get('domain_name_label'):
                    self.log('CHANGED: domain_name_label')
                    changed = True
                    results['dns_settings']['domain_name_label'] = self.domain_name

                if self.allocation_method != results['public_ip_allocation_method']:
                    self.log("CHANGED: allocation_method")
                    changed = True
                    results['public_ip_allocation_method'] = self.allocation_method

                update_tags, results['tags'] = self.update_tags(results['tags'])
                if update_tags:
                    changed = True

            elif self.state == 'absent':
                self.log("CHANGED: public ip {0} exists but requested state is 'absent'".format(self.name))
                changed = True
        except CloudError:
            self.log('Public ip {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: pip {0} does not exist but requested state is 'present'".format(self.name))
                changed = True

        self.results['state'] = results
        self.results['changed'] = changed

        if self.check_mode:
            return results

        if changed:
            if self.state == 'present':
                if not pip:
                    self.log("Create new Public IP {0}".format(self.name))
                    pip = PublicIPAddress(
                        location=self.location,
                        public_ip_allocation_method=self.allocation_method,
                    )
                    if self.tags:
                        pip.tags = self.tags
                    if self.domain_name:
                        pip.dns_settings = PublicIPAddressDnsSettings(
                            domain_name_label=self.domain_name
                        )
                else:
                    self.log("Update Public IP {0}".format(self.name))
                    pip = PublicIPAddress(
                        location=results['location'],
                        public_ip_allocation_method=results['public_ip_allocation_method'],
                        tags=results['tags']
                    )
                    if self.domain_name:
                        pip.dns_settings = PublicIPAddressDnsSettings(
                            domain_name_label=self.domain_name
                        )
                self.results['state'] = self.create_or_update_pip(pip)
            elif self.state == 'absent':
                self.log('Delete public ip {0}'.format(self.name))
                self.delete_pip()

        return self.results

    def create_or_update_pip(self, pip):
        try:
            poller = self.network_client.public_ip_addresses.create_or_update(self.resource_group, self.name, pip)
            pip = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating {0} - {1}".format(self.name, str(exc)))
        return pip_to_dict(pip)

    def delete_pip(self):
        try:
            poller = self.network_client.public_ip_addresses.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting {0} - {1}".format(self.name, str(exc)))
        # Delete returns nada. If we get here, assume that all is well.
        self.results['state']['status'] = 'Deleted'
        return True


def main():
    AzureRMPublicIPAddress()

if __name__ == '__main__':
    main()
