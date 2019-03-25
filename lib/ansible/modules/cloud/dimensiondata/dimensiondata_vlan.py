#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Dimension Data
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   - Adam Friedman  <tintoy@tintoy.io>
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: dimensiondata_vlan
short_description: Manage a VLAN in a Cloud Control network domain.
extends_documentation_fragment:
  - dimensiondata
  - dimensiondata_wait
description:
  - Manage VLANs in Cloud Control network domains.
version_added: "2.5"
author: 'Adam Friedman (@tintoy)'
options:
  name:
    description:
      - The name of the target VLAN.
      - Required if C(state) is C(present).
  description:
    description:
      - A description of the VLAN.
  network_domain:
    description:
      - The Id or name of the target network domain.
    required: true
  private_ipv4_base_address:
    description:
        - The base address for the VLAN's IPv4 network (e.g. 192.168.1.0).
  private_ipv4_prefix_size:
    description:
        - The size of the IPv4 address space, e.g 24.
        - Required, if C(private_ipv4_base_address) is specified.
  state:
    description:
      - The desired state for the target VLAN.
      - C(readonly) ensures that the state is only ever read, not modified (the module will fail if the resource does not exist).
    choices: [present, absent, readonly]
    default: present
  allow_expand:
    description:
      - Permit expansion of the target VLAN's network if the module parameters specify a larger network than the VLAN currently posesses?
      - If C(False), the module will fail under these conditions.
      - This is intended to prevent accidental expansion of a VLAN's network (since this operation is not reversible).
    type: bool
    default: 'no'
'''

EXAMPLES = '''
# Add or update VLAN
- dimensiondata_vlan:
    region: na
    location: NA5
    network_domain: test_network
    name: my_vlan1
    description: A test VLAN
    private_ipv4_base_address: 192.168.23.0
    private_ipv4_prefix_size: 24
    state: present
    wait: yes
# Read / get VLAN details
- dimensiondata_vlan:
    region: na
    location: NA5
    network_domain: test_network
    name: my_vlan1
    state: readonly
    wait: yes
# Delete a VLAN
- dimensiondata_vlan:
    region: na
    location: NA5
    network_domain: test_network
    name: my_vlan_1
    state: absent
    wait: yes
'''

RETURN = '''
vlan:
    description: Dictionary describing the VLAN.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: VLAN ID.
            type: str
            sample: "aaaaa000-a000-4050-a215-2808934ccccc"
        name:
            description: VLAN name.
            type: str
            sample: "My VLAN"
        description:
            description: VLAN description.
            type: str
            sample: "My VLAN description"
        location:
            description: Datacenter location.
            type: str
            sample: NA3
        private_ipv4_base_address:
            description: The base address for the VLAN's private IPV4 network.
            type: str
            sample: 192.168.23.0
        private_ipv4_prefix_size:
            description: The prefix size for the VLAN's private IPV4 network.
            type: int
            sample: 24
        private_ipv4_gateway_address:
            description: The gateway address for the VLAN's private IPV4 network.
            type: str
            sample: 192.168.23.1
        private_ipv6_base_address:
            description: The base address for the VLAN's IPV6 network.
            type: str
            sample: 2402:9900:111:1195:0:0:0:0
        private_ipv6_prefix_size:
            description: The prefix size for the VLAN's IPV6 network.
            type: int
            sample: 64
        private_ipv6_gateway_address:
            description: The gateway address for the VLAN's IPV6 network.
            type: str
            sample: 2402:9900:111:1195:0:0:0:1
        status:
            description: VLAN status.
            type: str
            sample: NORMAL
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dimensiondata import DimensionDataModule, UnknownNetworkError

try:
    from libcloud.common.dimensiondata import DimensionDataVlan, DimensionDataAPIException

    HAS_LIBCLOUD = True

except ImportError:
    DimensionDataVlan = None

    HAS_LIBCLOUD = False


class DimensionDataVlanModule(DimensionDataModule):
    """
    The dimensiondata_vlan module for Ansible.
    """

    def __init__(self):
        """
        Create a new Dimension Data VLAN module.
        """

        super(DimensionDataVlanModule, self).__init__(
            module=AnsibleModule(
                argument_spec=DimensionDataModule.argument_spec_with_wait(
                    name=dict(required=True, type='str'),
                    description=dict(default='', type='str'),
                    network_domain=dict(required=True, type='str'),
                    private_ipv4_base_address=dict(default='', type='str'),
                    private_ipv4_prefix_size=dict(default=0, type='int'),
                    allow_expand=dict(required=False, default=False, type='bool'),
                    state=dict(default='present', choices=['present', 'absent', 'readonly'])
                ),
                required_together=DimensionDataModule.required_together()
            )
        )

        self.name = self.module.params['name']
        self.description = self.module.params['description']
        self.network_domain_selector = self.module.params['network_domain']
        self.private_ipv4_base_address = self.module.params['private_ipv4_base_address']
        self.private_ipv4_prefix_size = self.module.params['private_ipv4_prefix_size']
        self.state = self.module.params['state']
        self.allow_expand = self.module.params['allow_expand']

        if self.wait and self.state != 'present':
            self.module.fail_json(
                msg='The wait parameter is only supported when state is "present".'
            )

    def state_present(self):
        """
        Ensure that the target VLAN is present.
        """

        network_domain = self._get_network_domain()

        vlan = self._get_vlan(network_domain)
        if not vlan:
            if self.module.check_mode:
                self.module.exit_json(
                    msg='VLAN "{0}" is absent from network domain "{1}" (should be present).'.format(
                        self.name, self.network_domain_selector
                    ),
                    changed=True
                )

            vlan = self._create_vlan(network_domain)
            self.module.exit_json(
                msg='Created VLAN "{0}" in network domain "{1}".'.format(
                    self.name, self.network_domain_selector
                ),
                vlan=vlan_to_dict(vlan),
                changed=True
            )
        else:
            diff = VlanDiff(vlan, self.module.params)
            if not diff.has_changes():
                self.module.exit_json(
                    msg='VLAN "{0}" is present in network domain "{1}" (no changes detected).'.format(
                        self.name, self.network_domain_selector
                    ),
                    vlan=vlan_to_dict(vlan),
                    changed=False
                )

                return

            try:
                diff.ensure_legal_change()
            except InvalidVlanChangeError as invalid_vlan_change:
                self.module.fail_json(
                    msg='Unable to update VLAN "{0}" in network domain "{1}": {2}'.format(
                        self.name, self.network_domain_selector, invalid_vlan_change
                    )
                )

            if diff.needs_expand() and not self.allow_expand:
                self.module.fail_json(
                    msg='The configured private IPv4 network size ({0}-bit prefix) for '.format(
                        self.private_ipv4_prefix_size
                    ) + 'the VLAN differs from its current network size ({0}-bit prefix) '.format(
                        vlan.private_ipv4_range_size
                    ) + 'and needs to be expanded. Use allow_expand=true if this is what you want.'
                )

            if self.module.check_mode:
                self.module.exit_json(
                    msg='VLAN "{0}" is present in network domain "{1}" (changes detected).'.format(
                        self.name, self.network_domain_selector
                    ),
                    vlan=vlan_to_dict(vlan),
                    changed=True
                )

            if diff.needs_edit():
                vlan.name = self.name
                vlan.description = self.description

                self.driver.ex_update_vlan(vlan)

            if diff.needs_expand():
                vlan.private_ipv4_range_size = self.private_ipv4_prefix_size
                self.driver.ex_expand_vlan(vlan)

            self.module.exit_json(
                msg='Updated VLAN "{0}" in network domain "{1}".'.format(
                    self.name, self.network_domain_selector
                ),
                vlan=vlan_to_dict(vlan),
                changed=True
            )

    def state_readonly(self):
        """
        Read the target VLAN's state.
        """

        network_domain = self._get_network_domain()

        vlan = self._get_vlan(network_domain)
        if vlan:
            self.module.exit_json(
                vlan=vlan_to_dict(vlan),
                changed=False
            )
        else:
            self.module.fail_json(
                msg='VLAN "{0}" does not exist in network domain "{1}".'.format(
                    self.name, self.network_domain_selector
                )
            )

    def state_absent(self):
        """
        Ensure that the target VLAN is not present.
        """

        network_domain = self._get_network_domain()

        vlan = self._get_vlan(network_domain)
        if not vlan:
            self.module.exit_json(
                msg='VLAN "{0}" is absent from network domain "{1}".'.format(
                    self.name, self.network_domain_selector
                ),
                changed=False
            )

            return

        if self.module.check_mode:
            self.module.exit_json(
                msg='VLAN "{0}" is present in network domain "{1}" (should be absent).'.format(
                    self.name, self.network_domain_selector
                ),
                vlan=vlan_to_dict(vlan),
                changed=True
            )

        self._delete_vlan(vlan)

        self.module.exit_json(
            msg='Deleted VLAN "{0}" from network domain "{1}".'.format(
                self.name, self.network_domain_selector
            ),
            changed=True
        )

    def _get_vlan(self, network_domain):
        """
        Retrieve the target VLAN details from CloudControl.

        :param network_domain: The target network domain.
        :return: The VLAN, or None if the target VLAN was not found.
        :rtype: DimensionDataVlan
        """

        vlans = self.driver.ex_list_vlans(
            location=self.location,
            network_domain=network_domain
        )
        matching_vlans = [vlan for vlan in vlans if vlan.name == self.name]
        if matching_vlans:
            return matching_vlans[0]

        return None

    def _create_vlan(self, network_domain):
        vlan = self.driver.ex_create_vlan(
            network_domain,
            self.name,
            self.private_ipv4_base_address,
            self.description,
            self.private_ipv4_prefix_size
        )

        if self.wait:
            vlan = self._wait_for_vlan_state(vlan.id, 'NORMAL')

        return vlan

    def _delete_vlan(self, vlan):
        try:
            self.driver.ex_delete_vlan(vlan)

            # Not currently supported for deletes due to a bug in libcloud (module will error out if "wait" is specified when "state" is not "present").
            if self.wait:
                self._wait_for_vlan_state(vlan, 'NOT_FOUND')

        except DimensionDataAPIException as api_exception:
            self.module.fail_json(
                msg='Failed to delete VLAN "{0}" due to unexpected error from the CloudControl API: {1}'.format(
                    vlan.id, api_exception.msg
                )
            )

    def _wait_for_vlan_state(self, vlan, state_to_wait_for):
        network_domain = self._get_network_domain()

        wait_poll_interval = self.module.params['wait_poll_interval']
        wait_time = self.module.params['wait_time']

        # Bizarre bug in libcloud when checking status after delete; socket.error is too generic to catch in this context so for now we don't even try.

        try:
            return self.driver.connection.wait_for_state(
                state_to_wait_for,
                self.driver.ex_get_vlan,
                wait_poll_interval,
                wait_time,
                vlan
            )

        except DimensionDataAPIException as api_exception:
            if api_exception.code != 'RESOURCE_NOT_FOUND':
                raise

            return DimensionDataVlan(
                id=vlan.id,
                status='NOT_FOUND',
                name='',
                description='',
                private_ipv4_range_address='',
                private_ipv4_range_size=0,
                ipv4_gateway='',
                ipv6_range_address='',
                ipv6_range_size=0,
                ipv6_gateway='',
                location=self.location,
                network_domain=network_domain
            )

    def _get_network_domain(self):
        """
        Retrieve the target network domain from the Cloud Control API.

        :return: The network domain.
        """

        try:
            return self.get_network_domain(
                self.network_domain_selector, self.location
            )
        except UnknownNetworkError:
            self.module.fail_json(
                msg='Cannot find network domain "{0}" in datacenter "{1}".'.format(
                    self.network_domain_selector, self.location
                )
            )

            return None


class InvalidVlanChangeError(Exception):
    """
    Error raised when an illegal change to VLAN state is attempted.
    """

    pass


class VlanDiff(object):
    """
    Represents differences between VLAN information (from CloudControl) and module parameters.
    """

    def __init__(self, vlan, module_params):
        """

        :param vlan: The VLAN information from CloudControl.
        :type vlan: DimensionDataVlan
        :param module_params: The module parameters.
        :type module_params: dict
        """

        self.vlan = vlan
        self.module_params = module_params

        self.name_changed = module_params['name'] != vlan.name
        self.description_changed = module_params['description'] != vlan.description
        self.private_ipv4_base_address_changed = module_params['private_ipv4_base_address'] != vlan.private_ipv4_range_address
        self.private_ipv4_prefix_size_changed = module_params['private_ipv4_prefix_size'] != vlan.private_ipv4_range_size

        # Is configured prefix size greater than or less than the actual prefix size?
        private_ipv4_prefix_size_difference = module_params['private_ipv4_prefix_size'] - vlan.private_ipv4_range_size
        self.private_ipv4_prefix_size_increased = private_ipv4_prefix_size_difference > 0
        self.private_ipv4_prefix_size_decreased = private_ipv4_prefix_size_difference < 0

    def has_changes(self):
        """
        Does the VlanDiff represent any changes between the VLAN and module configuration?

        :return: True, if there are change changes; otherwise, False.
        """

        return self.needs_edit() or self.needs_expand()

    def ensure_legal_change(self):
        """
        Ensure the change (if any) represented by the VlanDiff represents a legal change to VLAN state.

        - private_ipv4_base_address cannot be changed
        - private_ipv4_prefix_size must be greater than or equal to the VLAN's existing private_ipv4_range_size

        :raise InvalidVlanChangeError: The VlanDiff does not represent a legal change to VLAN state.
        """

        # Cannot change base address for private IPv4 network.
        if self.private_ipv4_base_address_changed:
            raise InvalidVlanChangeError('Cannot change the private IPV4 base address for an existing VLAN.')

        # Cannot shrink private IPv4 network (by increasing prefix size).
        if self.private_ipv4_prefix_size_increased:
            raise InvalidVlanChangeError('Cannot shrink the private IPV4 network for an existing VLAN (only expand is supported).')

    def needs_edit(self):
        """
        Is an Edit operation required to resolve the differences between the VLAN information and the module parameters?

        :return: True, if an Edit operation is required; otherwise, False.
        """

        return self.name_changed or self.description_changed

    def needs_expand(self):
        """
        Is an Expand operation required to resolve the differences between the VLAN information and the module parameters?

        The VLAN's network is expanded by reducing the size of its network prefix.

        :return: True, if an Expand operation is required; otherwise, False.
        """

        return self.private_ipv4_prefix_size_decreased


def vlan_to_dict(vlan):
    return {
        'id': vlan.id,
        'name': vlan.name,
        'description': vlan.description,
        'location': vlan.location.id,
        'private_ipv4_base_address': vlan.private_ipv4_range_address,
        'private_ipv4_prefix_size': vlan.private_ipv4_range_size,
        'private_ipv4_gateway_address': vlan.ipv4_gateway,
        'ipv6_base_address': vlan.ipv6_range_address,
        'ipv6_prefix_size': vlan.ipv6_range_size,
        'ipv6_gateway_address': vlan.ipv6_gateway,
        'status': vlan.status
    }


def main():
    module = DimensionDataVlanModule()

    if module.state == 'present':
        module.state_present()
    elif module.state == 'readonly':
        module.state_readonly()
    elif module.state == 'absent':
        module.state_absent()


if __name__ == '__main__':
    main()
