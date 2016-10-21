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

module: sf_cluster_pair_manager

short_description: Manage Cluster pairing
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)
description:
- Create, delete, or update Cluster pairs
    - auth_basic

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

    action:
        required: true
        description:
        - Create or Delete a cluster pair, or
        - create an encoded key from a cluster that is used to pair with another cluster.
        - Remember to run the Playbook in verbose mode, using -v, if you need the key to be displayed on the console.
        choices: ['create', 'delete', 'get_key']

    cluster_pairing_key:
        required: false
        note: required when action == create
        description:
        - A string of characters that is returned from the "StartClusterPairing" API method

    cluster_pair_id:
        required: false
        note: required when action == delete
        description:
        -  Unique identifier used to pair two clusters.

'''

EXAMPLES = """
   - name: Get Cluster Key
     sf_cluster_pair_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       action: get_key

   - name: Create Cluster Pair
     sf_cluster_pair_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       action: create
       cluster_pair_key: {{ cluster pair key }}

   - name: Delete Cluster Pair
     sf_cluster_pair_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       action: delete
       cluster_pair_id: {{ cluster pair id }}
"""

RETURN = """
msg:
    description: Successfully generated key
    returned: success
    type: string
    sample: '{"changed": true, "key": value}'

msg:
    description: Successful creation of cluster pair
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successful removal of cluster pair
    returned: success
    type: string
    sample: '{"changed": true}'

"""

import sys
import json
import logging
from traceback import format_exc

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.pycompat24 import get_exception

import socket
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from solidfire.factory import ElementFactory


class SolidFireClusterPairing(object):

    def __init__(self):

        self.module = AnsibleModule(
            argument_spec=dict(
                action=dict(required=True, choices=['create', 'delete', 'get_key']),

                cluster_pairing_key=dict(type='str', default=None),
                cluster_pair_id=dict(type='int', default=None),

                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('action', 'create', ['cluster_pairing_key']),
                ('action', 'delete', ['cluster_pair_id']),
            ],
            supports_check_mode=False
        )

        p = self.module.params

        # set up state variables
        self.action = p['action']
        self.cluster_pairing_key = p['cluster_pairing_key']
        self.cluster_pair_id = p['cluster_pair_id']

        self.generated_cluster_pairing_key = ""

        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']

        # create connection to solidfire cluster
        self.sfe = ElementFactory.create(self.hostname, self.username, self.password)

    def complete_cluster_pair(self):
        logger.debug('Creating cluster pair ')

        try:
            self.sfe.complete_cluster_pairing(cluster_pairing_key=self.cluster_pairing_key)

        except:
            err = get_exception()
            logger.exception('Error creating cluster pair : %s', str(err))
            raise

    def delete_cluster_pair(self):
        logger.debug('Deleting cluster pair %s', self.cluster_pair_id)

        try:
            self.sfe.remove_cluster_pair(cluster_pair_id=self.cluster_pair_id)

        except:
            err = get_exception()
            logger.exception('Error removing cluster pair %s: %s', self.cluster_pair_id, str(err))
            raise

    def start_cluster_pairing(self):

        #    Used to create an encoded key from a cluster that is used to pair with another
        #    cluster. The key created from this API method is used in the "complete_cluster_pairing" API method to
        #    establish a cluster pairing. You can pair a cluster with a maximum of four other SolidFire clusters.

        logger.debug('Start cluster pairing')

        try:
            result = self.sfe.start_cluster_pairing()
            self.generated_cluster_pairing_key = result.cluster_pairing_key

        except:
            err = get_exception()
            logger.exception('Error starting cluster pairing : %s', str(err))

    def apply(self):
        changed = False

        if self.action == 'create':
            self.complete_cluster_pair()
            changed = True

        elif self.action == 'delete':
            self.delete_cluster_pair()
            changed = True

        elif self.action == 'get_key':
            self.start_cluster_pairing()
            changed = False

        self.module.exit_json(changed=changed, cluster_pairing_key=self.generated_cluster_pairing_key)


def main():
    v = SolidFireClusterPairing()

    try:
        v.apply()
    except:
        err = get_exception()
        logger.debug("Exception in apply(): \n%s" % format_exc(err))
        raise

main()
