#!/usr/bin/python

# Copyright: (c) 2018, Roald Nefs <info@roaldnefs.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: transip_vps
short_description: Create and delete a TransIP VPS
version_added: "2.9"
description:
    - Create and delete a TransIP VPS
options:
    state:
        description:
            - Indicate desired state of the target.
        default: present
        choices:
            - present
            - absent
    login:
        description:
            - The login name on the TransIP website.
        required: true
    private_key:
        description:
            - The private key used to communicate with the TransIP API.
        required: true
    product_name:
        description:
            - The name of the product.
        required: false
    operating_system_name:
        description:
            - The name of the operating system to install.
        required: false
    hostname:
        description:
            - The name of the host.
        required: false
    name:
        description:
            - The VPS to cancel.
        required: false
    end_time:
        description:
            - The time to cancel the VPS.
        default: end
        choices:
            - end
            - immediately
requirements:
  - transip >= 2.0.0
author: "Roald Nefs (@roaldnefs)"
'''

EXAMPLES = '''
# Create a new TransIP VPS
- name: create a new vps
  transip_vps:
    state: present
    login: transip_username
    private_key:
      - "-----BEGIN PRIVATE KEY-----"
      - "..."
      - "-----END PRIVATE KEY-----"
    product_name: vps-bladevps-x1
    operating_system_name: ubuntu-18.04
    hostname: my_hostname

# Delete an existing TransIP VPS
- name: delete ab existing vps
  transip_vps:
    state: absent
    login: transip_username
    private_key:
      - "-----BEGIN PRIVATE KEY-----"
      - "..."
      - "-----END PRIVATE KEY-----"
    name: username-vps99
    end_time: immediately
'''

RETURN = ''' # '''

import os
import traceback

TRANSIP_IMP_ERR = None
try:
    from transip.service.vps import VpsService
except ImportError:
    TRANSIP_IMP_ERR = traceback.format_exc()
    transip_found = False
else:
    transip_found = True

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class Vps(object):

    def __init__(self, module):
        self.module = module
        private_key = os.linesep.join(module.params.pop('private_key'))
        self.client = VpsService(
            login=module.params.pop('login'),
            private_key=private_key
        )

    def create(self):
        product_name = self.module.params.get('product_name')
        operating_system_name = self.module.params.get('operating_system_name')
        hostname = self.module.params.get('hostname')

        # Ensure the product is available
        products = [product.name for product in self.client.get_available_products()]
        if product_name not in products:
            self.module.exit_json(
                self.module.exit_json(
                    change=False,
                    msg='Product \'{0}\' not available'.format(product_name)
                )
            )

        # Ensure the operating system is available
        operating_systems = [system.name for system in self.client.get_operating_systems()]
        if operating_system_name not in operating_systems:
            self.module.exit_json(
                change=False,
                msg='Operating system \'{0}\' not available'.format(
                    operating_system_name
                )
            )

        # The vps would have been created if check_mode was off
        if self.module.check_mode:
            self.module.exit_json(change=True)

        # Create the vps
        self.client.order_vps(
            product_name=product_name,
            addons=None,
            operating_system_name=operating_system_name,
            hostname=hostname
        )
        self.module.exit_json(change=True, msg='VPS created')

    def delete(self):
        name = self.module.params.get('name')
        end_time = self.module.params.get('end_time')

        # Loop over all the existing vpses to ensure the vps exists before
        # attempting to delete it
        servers = [vps.name for vps in self.client.get_vpses()]
        if name not in servers:
            self.module.exit_json(changed=False, msg='VPS not found')

        # The vps would have been deleted if check_mode was off
        if self.module.check_mode:
            self.module.exit_json(change=True)

        # Delete the vps
        self.client.cancel_vps(vps_name=name, end_time=end_time)
        self.module.exit_json(change=True, msg='VPS deleted')


def run_module(module):
    state = module.params.pop('state')
    vps = Vps(module)
    if state == 'present':
        vps.create()
    if state == 'absent':
        vps.delete()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            login=dict(type='str', required=True),
            private_key=dict(type='list', no_log=True, required=True),
            product_name=dict(type='str'),
            operating_system_name=dict(type='str'),
            hostname=dict(type='str'),
            name=dict(type='str'),
            end_time=dict(choices=['end', 'immediately'], default='end'),
        ),
        required_if=([
            ('state', 'present', [
                'product_name',
                'operating_system_name',
                'hostname'
            ]),
            ('state', 'absent', ['name', 'end_time']),
        ]),
        supports_check_mode=True,
    )

    if not transip_found:
        module.fail_json(msg=missing_required_lib('transip'), exception=TRANSIP_IMP_ERR)

    run_module(module)


if __name__ == '__main__':
    main()
