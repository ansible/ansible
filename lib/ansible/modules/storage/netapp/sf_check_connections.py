#!/usr/bin/python
# (c) 2016, NetApp, Inc
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

#!/usr/bin/python

DOCUMENTATION = '''

module: sf_check_connections

short_description: Check connectivity to MVIP and SVIP.

description:
- Used to test the management connection to the cluster.
The test pings the MVIP and SVIP, and executes a simple API method to verify connectivity.

options:

  hostname:
    required: true
    description:
    - hostname

  username:
    required: true
    description:
    - username

  password:
    required: true
    description:
    - password

  skip:
    required: false
    description:
    - Skip checking connection to SVIP or MVIP.
    choices: ['svip', 'mvip']

  mvip:
    required: false
    description:
    -   Optionally, use to test connection of a different MVIP.
        This is not needed to test the connection to the target cluster.

  svip:
    required: false
    description:
    -   Optionally, use to test connection of a different SVIP.
        This is not needed to test the connection to the target cluster.

'''

import sys
import json
import logging
from traceback import format_exc

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

import socket
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from solidfire.factory import ElementFactory


class SolidFireConnection(object):

    def __init__(self):
        logger.debug('Init %s', self.__class__.__name__)

        self.module = AnsibleModule(
            argument_spec=dict(
                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
                skip=dict(required=False, type='str', default=None, choices=['mvip', 'svip']),
                mvip=dict(required=False, type='str', default=None),
                svip=dict(required=False, type='str', default=None)
            ),
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']
        self.skip = p['skip']
        self.mvip = p['mvip']
        self.svip = p['svip']

        # create connection to solidfire cluster
        # self.sfe = ElementFactory.create(self.hostname, self.username, self.password)
        self.sfe = None

    def establish_connection(self):
        """
            Establish connection to SolidFire cluster

            :return: true if connection was successful.
            :rtype: bool
        """
        try:
            self.sfe = ElementFactory.create(self.hostname, self.username, self.password, port=442)
            return True

        except Exception as e:
            logger.exception('Error establishing connection to SolidFire cluster: %s',
                             e)
            return False

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
            logger.exception('Error checking connection to MVIP: %s',
                             e)
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
            logger.exception('Error checking connection to SVIP: %s',
                             e)
            return False

    def check(self):

        failed = True
        msg = ''

        self.establish_connection()

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

    try:
        v.check()
    except Exception as e:
        logger.debug("Exception in check(): \n%s" % format_exc(e))
        raise

main()
