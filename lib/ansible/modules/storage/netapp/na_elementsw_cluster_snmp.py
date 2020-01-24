#!/usr/bin/python
# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

'''
Element Software Configure SNMP
'''
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_elementsw_cluster_snmp

short_description: Configure Element SW Cluster SNMP
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Configure Element Software cluster SNMP.

options:

    state:
        description:
        - This module enables you to enable SNMP on cluster nodes. When you enable SNMP, \
          the action applies to all nodes in the cluster, and the values that are passed replace, \
          in whole, all values set in any previous call to this module.
        choices: ['present', 'absent']
        default: 'present'

    snmp_v3_enabled:
        description:
        - Which version of SNMP has to be enabled.
        type: bool

    networks:
        description:
        - List of networks and what type of access they have to the SNMP servers running on the cluster nodes.
        - This parameter is required if SNMP v3 is disabled.
        suboptions:
            access:
                description:
                - ro for read-only access.
                - rw for read-write access.
                - rosys for read-only access to a restricted set of system information.
                choices: ['ro', 'rw', 'rosys']
            cidr:
                description:
                - A CIDR network mask. This network mask must be an integer greater than or equal to 0, \
                  and less than or equal to 32. It must also not be equal to 31.
            community:
                description:
                - SNMP community string.
            network:
                description:
                - This parameter along with the cidr variable is used to control which network the access and \
                  community string apply to.
                - The special value of 'default' is used to specify an entry that applies to all networks.
                - The cidr mask is ignored when network value is either a host name or default.

    usm_users:
        description:
        - List of users and the type of access they have to the SNMP servers running on the cluster nodes.
        - This parameter is required if SNMP v3 is enabled.
        suboptions:
            access:
                description:
                - rouser for read-only access.
                - rwuser for read-write access.
                - rosys for read-only access to a restricted set of system information.
                choices: ['rouser', 'rwuser', 'rosys']
            name:
                description:
                - The name of the user. Must contain at least one character, but no more than 32 characters.
                - Blank spaces are not allowed.
            password:
                description:
                - The password of the user. Must be between 8 and 255 characters long (inclusive).
                - Blank spaces are not allowed.
                - Required if 'secLevel' is 'auth' or 'priv.'
            passphrase:
                description:
                - The passphrase of the user. Must be between 8 and 255 characters long (inclusive).
                - Blank spaces are not allowed.
                - Required if 'secLevel' is 'priv.'
            secLevel:
                description:
                - To define the security level of a user.
                choices: ['noauth', 'auth', 'priv']

'''

EXAMPLES = """

  - name: configure SnmpNetwork
    tags:
    - elementsw_cluster_snmp
    na_elementsw_cluster_snmp:
      hostname: "{{ elementsw_hostname }}"
      username: "{{ elementsw_username }}"
      password: "{{ elementsw_password }}"
      state: present
      snmp_v3_enabled: True
      usm_users:
        access: rouser
        name: testuser
        password: ChangeMe123
        passphrase: ChangeMe123
        secLevel: auth
      networks:
        access: ro
        cidr: 24
        community: TestNetwork
        network: 192.168.0.1

  - name: Disable SnmpNetwork
    tags:
    - elementsw_cluster_snmp
    na_elementsw_cluster_snmp:
      hostname: "{{ elementsw_hostname }}"
      username: "{{ elementsw_username }}"
      password: "{{ elementsw_password }}"
      state: absent

"""

RETURN = """

msg:
    description: Success message
    returned: success
    type: str

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule
from ansible.module_utils.netapp_module import NetAppModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class ElementSWClusterSnmp(object):
    """
    Element Software Configure Element SW Cluster SnmpNetwork
    """
    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()

        self.argument_spec.update(dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            snmp_v3_enabled=dict(type='bool'),
            networks=dict(
                type='dict',
                options=dict(
                    access=dict(type='str', choices=['ro', 'rw', 'rosys']),
                    cidr=dict(type='int', default=None),
                    community=dict(type='str', default=None),
                    network=dict(type='str', default=None)
                )
            ),
            usm_users=dict(
                type='dict',
                options=dict(
                    access=dict(type='str', choices=['rouser', 'rwuser', 'rosys']),
                    name=dict(type='str', default=None),
                    password=dict(type='str', default=None),
                    passphrase=dict(type='str', default=None),
                    secLevel=dict(type='str', choices=['auth', 'noauth', 'priv'])
                )
            ),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['snmp_v3_enabled']),
                ('snmp_v3_enabled', True, ['usm_users']),
                ('snmp_v3_enabled', False, ['networks'])
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if self.parameters.get('state') == "present":
            if self.parameters.get('usm_users') is not None:
                # Getting the configuration details to configure SNMP Version3
                self.access_usm = self.parameters.get('usm_users')['access']
                self.name = self.parameters.get('usm_users')['name']
                self.password = self.parameters.get('usm_users')['password']
                self.passphrase = self.parameters.get('usm_users')['passphrase']
                self.secLevel = self.parameters.get('usm_users')['secLevel']
            if self.parameters.get('networks') is not None:
                # Getting the configuration details to configure SNMP Version2
                self.access_network = self.parameters.get('networks')['access']
                self.cidr = self.parameters.get('networks')['cidr']
                self.community = self.parameters.get('networks')['community']
                self.network = self.parameters.get('networks')['network']

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def enable_snmp(self):
        """
        enable snmp feature
        """
        try:
            self.sfe.enable_snmp(snmp_v3_enabled=self.parameters.get('snmp_v3_enabled'))
        except Exception as exception_object:
            self.module.fail_json(msg='Error enabling snmp feature %s' % to_native(exception_object),
                                  exception=traceback.format_exc())

    def disable_snmp(self):
        """
        disable snmp feature
        """
        try:
            self.sfe.disable_snmp()
        except Exception as exception_object:
            self.module.fail_json(msg='Error disabling snmp feature %s' % to_native(exception_object),
                                  exception=traceback.format_exc())

    def configure_snmp(self, actual_networks, actual_usm_users):
        """
        Configure snmp
        """
        try:
            self.sfe.set_snmp_acl(networks=[actual_networks], usm_users=[actual_usm_users])

        except Exception as exception_object:
            self.module.fail_json(msg='Error Configuring snmp feature %s' % to_native(exception_object.message),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Cluster SNMP configuration
        """
        changed = False
        result_message = None
        update_required = False
        version_change = False
        is_snmp_enabled = self.sfe.get_snmp_state().enabled

        if is_snmp_enabled is True:
            # IF SNMP is already enabled
            if self.parameters.get('state') == 'absent':
                # Checking for state change(s) here, and applying it later in the code allows us to support
                # check_mode
                changed = True

            elif self.parameters.get('state') == 'present':
                # Checking if SNMP configuration needs to be updated,
                is_snmp_v3_enabled = self.sfe.get_snmp_state().snmp_v3_enabled

                if is_snmp_v3_enabled != self.parameters.get('snmp_v3_enabled'):
                    # Checking if there any version changes required
                    version_change = True
                    changed = True

                if is_snmp_v3_enabled is True:
                    # Checking If snmp configuration for usm_users needs modification
                    if len(self.sfe.get_snmp_info().usm_users) == 0:
                        # If snmp is getting configured for first time
                        update_required = True
                        changed = True
                    else:
                        for usm_user in self.sfe.get_snmp_info().usm_users:
                            if usm_user.access != self.access_usm or usm_user.name != self.name or usm_user.password != self.password or \
                               usm_user.passphrase != self.passphrase or usm_user.sec_level != self.secLevel:
                                update_required = True
                                changed = True
                else:
                    # Checking If snmp configuration for networks needs modification
                    for snmp_network in self.sfe.get_snmp_info().networks:
                        if snmp_network.access != self.access_network or snmp_network.cidr != self.cidr or \
                           snmp_network.community != self.community or snmp_network.network != self.network:
                            update_required = True
                            changed = True

        else:
            if self.parameters.get('state') == 'present':
                changed = True

        result_message = ""

        if changed:
            if self.module.check_mode is True:
                result_message = "Check mode, skipping changes"

            else:
                if self.parameters.get('state') == "present":
                    # IF snmp is not enabled, then enable and configure snmp
                    if self.parameters.get('snmp_v3_enabled') is True:
                        # IF SNMP is enabled with version 3
                        usm_users = {'access': self.access_usm,
                                     'name': self.name,
                                     'password': self.password,
                                     'passphrase': self.passphrase,
                                     'secLevel': self.secLevel}
                        networks = None
                    else:
                        # IF SNMP is enabled with version 2
                        usm_users = None
                        networks = {'access': self.access_network,
                                    'cidr': self.cidr,
                                    'community': self.community,
                                    'network': self.network}

                    if is_snmp_enabled is False or version_change is True:
                        # Enable and configure snmp
                        self.enable_snmp()
                        self.configure_snmp(networks, usm_users)
                        result_message = "SNMP is enabled and configured"

                    elif update_required is True:
                        # If snmp is already enabled, update the configuration if required
                        self.configure_snmp(networks, usm_users)
                        result_message = "SNMP is configured"

                elif is_snmp_enabled is True and self.parameters.get('state') == "absent":
                    # If snmp is enabled and state is absent, disable snmp
                    self.disable_snmp()
                    result_message = "SNMP is disabled"

        self.module.exit_json(changed=changed, msg=result_message)


def main():
    """
    Main function
    """
    na_elementsw_cluster_snmp = ElementSWClusterSnmp()
    na_elementsw_cluster_snmp.apply()


if __name__ == '__main__':
    main()
