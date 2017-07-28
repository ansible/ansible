#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: sf_check_connections

short_description: Check connectivity to MVIP and SVIP.
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)
description:
- Used to test the management connection to the cluster.
- The test pings the MVIP and SVIP, and executes a simple API method to verify connectivity.

options:

  skip:
    description:
    - Skip checking connection to SVIP or MVIP.
    required: false
    choices: ['svip', 'mvip']
    default: None

  mvip:
    description:
    - Optionally, use to test connection of a different MVIP.
    - This is not needed to test the connection to the target cluster.
    required: false
    default: None

  svip:
    description:
    - Optionally, use to test connection of a different SVIP.
    - This is not needed to test the connection to the target cluster.
    required: false
    default: None

'''


EXAMPLES = """
   - name: Check connections to MVIP and SVIP
     sf_check_connections:
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


HAS_SF_SDK = netapp_utils.has_sf_sdk()


class SolidFireConnection(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            skip=dict(required=False, type='str', default=None, choices=['mvip', 'svip']),
            mvip=dict(required=False, type='str', default=None),
            svip=dict(required=False, type='str', default=None)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.skip = p['skip']
        self.mvip = p['mvip']
        self.svip = p['svip']

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.ElementFactory.create(p['hostname'], p['username'], p['password'], port=442)

    def check_mvip_connection(self):
        """
            Check connection to MVIP

            :return: true if connection was successful, false otherwise.
            :rtype: bool
        """
        try:
            test = self.sfe.test_connect_mvip(mvip=self.mvip)
            result = test.details.connected
            # Todo - Log details about the test
            return result

        except Exception as e:
            self.module.fail_json(msg='Error checking connection to MVIP: %s' % to_native(e), exception=traceback.format_exc())
            return False

    def check_svip_connection(self):
        """
            Check connection to SVIP

            :return: true if connection was successful, false otherwise.
            :rtype: bool
        """
        try:
            test = self.sfe.test_connect_svip(svip=self.svip)
            result = test.details.connected
            # Todo - Log details about the test
            return result

        except Exception as e:
            self.module.fail_json(msg='Error checking connection to SVIP: %s' % to_native(e), exception=traceback.format_exc())
            return False

    def check(self):

        failed = True
        msg = ''

        if self.skip is None:
            mvip_connection_established = self.check_mvip_connection()
            svip_connection_established = self.check_svip_connection()

            # Set failed and msg
            if not mvip_connection_established:
                failed = True
                msg = 'Connection to MVIP failed.'
            elif not svip_connection_established:
                failed = True
                msg = 'Connection to SVIP failed.'
            else:
                failed = False

        elif self.skip == 'mvip':
            svip_connection_established = self.check_svip_connection()

            # Set failed and msg
            if not svip_connection_established:
                failed = True
                msg = 'Connection to SVIP failed.'
            else:
                failed = False

        elif self.skip == 'svip':
            mvip_connection_established = self.check_mvip_connection()

            # Set failed and msg
            if not mvip_connection_established:
                failed = True
                msg = 'Connection to MVIP failed.'
            else:
                failed = False

        if failed:
            self.module.fail_json(msg=msg)
        else:
            self.module.exit_json()


def main():
    v = SolidFireConnection()
    v.check()

if __name__ == '__main__':
    main()
