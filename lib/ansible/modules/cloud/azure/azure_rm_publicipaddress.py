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
                    'supported_by': 'community'}


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
            - dynamic
            - static
            - Static
            - Dynamic
        default: dynamic
    domain_name:
        description:
            - The customizable portion of the FQDN assigned to public IP address. This is an explicit setting. If
              no value is provided, any existing value will be removed on an existing public IP.
        aliases:
            - domain_name_label
    name:
        description:
            - Name of the Public IP.
        required: true
    state:
        description:
            - Assert the state of the Public IP. Use C(present) to create or update a and
              C(absent) to delete.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    sku:
        description:
            - The public IP address SKU.
        choices:
            - basic
            - standard
            - Basic
            - Standard
        version_added: 2.6
    ip_tags:
        description:
            - List of IpTag associated with the public IP address.
            - Each element should contain type:value pair.
        suboptions:
            type:
                description: Sets the ip_tags type.
            value:
                description: Sets the ip_tags value.
        version_added: 2.8
    idle_timeout:
        description:
            - Idle timeout in minutes.
        type: int
        version_added: 2.8
    version:
        description:
            - The public IP address version.
        choices:
            - ipv4
            - ipv6
        default: ipv4
        version_added: 2.8

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
        resource_group: myResourceGroup
        name: my_public_ip
        allocation_method: static
        domain_name: foobar

    - name: Delete public ip
      azure_rm_publicipaddress:
        resource_group: myResourceGroup
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
        "public_ip_allocation_method": "static",
        "tags": {},
        "type": "Microsoft.Network/publicIPAddresses"
    }
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils._text import to_native

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


def pip_to_dict(pip):
    result = dict(
        name=pip.name,
        type=pip.type,
        location=pip.location,
        tags=pip.tags,
        public_ip_allocation_method=pip.public_ip_allocation_method.lower(),
        public_ip_address_version=pip.public_ip_address_version.lower(),
        dns_settings=dict(),
        ip_address=pip.ip_address,
        idle_timeout_in_minutes=pip.idle_timeout_in_minutes,
        provisioning_state=pip.provisioning_state,
        etag=pip.etag,
        sku=pip.sku.name
    )
    if pip.dns_settings:
        result['dns_settings']['domain_name_label'] = pip.dns_settings.domain_name_label
        result['dns_settings']['fqdn'] = pip.dns_settings.fqdn
        result['dns_settings']['reverse_fqdn'] = pip.dns_settings.reverse_fqdn
    if pip.ip_tags:
        result['ip_tags'] = [dict(type=to_native(x.ip_tag_type), value=to_native(x.tag)) for x in pip.ip_tags]
    return result


ip_tag_spec = dict(
    type=dict(type='str', required=True),
    value=dict(type='str', required=True)
)


class AzureRMPublicIPAddress(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            version=dict(type='str', default='ipv4', choices=['ipv4', 'ipv6']),
            allocation_method=dict(type='str', default='dynamic', choices=['Dynamic', 'Static', 'dynamic', 'static']),
            domain_name=dict(type='str', aliases=['domain_name_label']),
            sku=dict(type='str', choices=['Basic', 'Standard', 'basic', 'standard']),
            ip_tags=dict(type='list', elements='dict', options=ip_tag_spec),
            idle_timeout=dict(type='int')
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.state = None
        self.tags = None
        self.allocation_method = None
        self.domain_name = None
        self.sku = None
        self.version = None
        self.ip_tags = None
        self.idle_timeout = None

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

        # capitalize the sku and allocation_method. basic => Basic, Basic => Basic.
        self.allocation_method = self.allocation_method.capitalize() if self.allocation_method else None
        self.sku = self.sku.capitalize() if self.sku else None
        self.version = 'IPv4' if self.version == 'ipv4' else 'IPv6'

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
                domain_lable = results['dns_settings'].get('domain_name_label')
                if self.domain_name is not None and ((self.domain_name or domain_lable) and self.domain_name != domain_lable):
                    self.log('CHANGED: domain_name_label')
                    changed = True
                    results['dns_settings']['domain_name_label'] = self.domain_name

                if self.allocation_method.lower() != results['public_ip_allocation_method'].lower():
                    self.log("CHANGED: allocation_method")
                    changed = True
                    results['public_ip_allocation_method'] = self.allocation_method

                if self.sku and self.sku != results['sku']:
                    self.log("CHANGED: sku")
                    changed = True
                    results['sku'] = self.sku

                if self.version.lower() != results['public_ip_address_version'].lower():
                    self.log("CHANGED: version")
                    changed = True
                    results['public_ip_address_version'] = self.version

                if self.idle_timeout and self.idle_timeout != results['idle_timeout_in_minutes']:
                    self.log("CHANGED: idle_timeout")
                    changed = True
                    results['idle_timeout_in_minutes'] = self.idle_timeout

                if str(self.ip_tags or []) != str(results.get('ip_tags') or []):
                    self.log("CHANGED: ip_tags")
                    changed = True
                    results['ip_tags'] = self.ip_tags

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
                    pip = self.network_models.PublicIPAddress(
                        location=self.location,
                        public_ip_address_version=self.version,
                        public_ip_allocation_method=self.allocation_method if self.version == 'IPv4' else None,
                        sku=self.network_models.PublicIPAddressSku(name=self.sku) if self.sku else None,
                        idle_timeout_in_minutes=self.idle_timeout if self.idle_timeout and self.idle_timeout > 0 else None
                    )
                    if self.ip_tags:
                        pip.ip_tags = [self.network_models.IpTag(ip_tag_type=x.type, tag=x.value) for x in self.ip_tags]
                    if self.tags:
                        pip.tags = self.tags
                    if self.domain_name:
                        pip.dns_settings = self.network_models.PublicIPAddressDnsSettings(
                            domain_name_label=self.domain_name
                        )
                else:
                    self.log("Update Public IP {0}".format(self.name))
                    pip = self.network_models.PublicIPAddress(
                        location=results['location'],
                        public_ip_allocation_method=results['public_ip_allocation_method'],
                        tags=results['tags']
                    )
                    if self.domain_name:
                        pip.dns_settings = self.network_models.PublicIPAddressDnsSettings(
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
