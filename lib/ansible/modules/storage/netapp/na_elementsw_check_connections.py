#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_check_connections

short_description: NetApp Element Software Check connectivity to MVIP and SVIP.
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Used to test the management connection to the cluster.
- The test pings the MVIP and SVIP, and executes a simple API method to verify connectivity.

options:

  skip:
    description:
    - Skip checking connection to SVIP or MVIP.
    choices: ['svip', 'mvip']

  mvip:
    description:
    - Optionally, use to test connection of a different MVIP.
    - This is not needed to test the connection to the target cluster.

  svip:
    description:
    - Optionally, use to test connection of a different SVIP.
    - This is not needed to test the connection to the target cluster.

'''


EXAMPLES = """
   - name: Check connections to MVIP and SVIP
     na_elementsw_check_connections:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule


HAS_SF_SDK = netapp_utils.has_sf_sdk()


class NaElementSWConnection(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            skip=dict(required=False, type='str', default=None, choices=['mvip', 'svip']),
            mvip=dict(required=False, type='str', default=None),
            svip=dict(required=False, type='str', default=None)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('skip', 'svip', ['mvip']),
                ('skip', 'mvip', ['svip'])
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.module.params.copy()
        self.msg = ""

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the ElementSW Python SDK")
        else:
            self.elem = netapp_utils.create_sf_connection(self.module, port=442)

    def check_mvip_connection(self):
        """
            Check connection to MVIP

            :return: true if connection was successful, false otherwise.
            :rtype: bool
        """
        try:
            test = self.elem.test_connect_mvip(mvip=self.parameters['mvip'])
            # Todo - Log details about the test
            return test.details.connected

        except Exception as e:
            self.msg += 'Error checking connection to MVIP: %s' % to_native(e)
            return False

    def check_svip_connection(self):
        """
            Check connection to SVIP

            :return: true if connection was successful, false otherwise.
            :rtype: bool
        """
        try:
            test = self.elem.test_connect_svip(svip=self.parameters['svip'])
            # Todo - Log details about the test
            return test.details.connected
        except Exception as e:
            self.msg += 'Error checking connection to SVIP: %s' % to_native(e)
            return False

    def apply(self):
        passed = False
        if self.parameters.get('skip') is None:
            # Set failed and msg
            passed = self.check_mvip_connection()
            # check if both connections have passed
            passed &= self.check_svip_connection()
        elif self.parameters['skip'] == 'mvip':
            passed |= self.check_svip_connection()
        elif self.parameters['skip'] == 'svip':
            passed |= self.check_mvip_connection()
        if not passed:
            self.module.fail_json(msg=self.msg)
        else:
            self.module.exit_json()


def main():
    connect_obj = NaElementSWConnection()
    connect_obj.apply()


if __name__ == '__main__':
    main()
