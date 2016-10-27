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

DOCUMENTATION = '''

module: na_cdot_license

short_description: Manage NetApp cDOT protocol and feature licenses
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Add or remove licenses on NetApp cDOT
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

  remove_unused:
    required: false
    description:
    - Remove licenses that have no controller affiliation in the cluster.
    choices: ['true', 'false']

  remove_expired:
    required: false
    description:
    - Remove licenses that have expired in the cluster.
    choices: ['true', 'false']

  serial_number:
    required: false
    description:
    - Serial number of the node associated with the license. This parameter
    - is used primarily when removing license for a specific service. If this
    - parameter is not provided, the cluster serial number is used by default.

  licenses:
    required: false
    description:
    - List of licenses to add or remove.
    
    - Please note that trying to remove a non-existent license will throw an error.
    valid_options:
        - base                : Cluster Base License,
        - nfs                 : NFS License,
        - cifs                : CIFS License,
        - iscsi               : iSCSI License,
        - fcp                 : FCP License,
        - cdmi                : CDMI License,
        - snaprestore         : SnapRestore License,
        - snapmirror          : SnapMirror License,
        - flexclone           : FlexClone License,
        - snapvault           : SnapVault License,
        - snaplock            : SnapLock License,
        - snapmanagersuite    : SnapManagerSuite License,
        - snapprotectapps     : SnapProtectApp License,
        - v_storageattach     : Virtual Attached Storage License

'''


EXAMPLES = """

    - name: Add licenses
          na_cdot_license:
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"
            serial_number: #################
            licenses:
              nfs: #################
              cifs: #################
              iscsi: #################
              fcp: #################
              snaprestore: #################
              flexclone: #################

    - name: Remove licenses
          na_cdot_license:
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"
            remove_unused: false
            remove_expired: true
            serial_number: #################
            licenses:
              nfs: remove
"""

RETURN = """
msg:
    description: Successfully added licenses
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successfully removed licenses
    returned: success
    type: string
    sample: '{"changed": true}'

"""

import sys
import json
import logging
from itertools import ifilter
from traceback import format_exc

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

import socket
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from netapp_lib.api.zapi import zapi
from netapp_lib.api.zapi import errors as zapi_errors

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NetAppCDOTLicense(object):

    def __init__(self):
        logger.debug('Init %s', self.__class__.__name__)

        self.module = AnsibleModule(
            argument_spec=dict(
                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
                serial_number=dict(required=False, type='str', default=None),
                remove_unused=dict(default=False, type='bool'),
                remove_expired=dict(default=False, type='bool'),
                licenses=dict(default=False, type='dict'),
            ),
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']
        self.serial_number = p['serial_number']
        self.remove_unused = p['remove_unused']
        self.remove_expired = p['remove_expired']
        self.licenses = p['licenses']

        # set up zapi
        self.server = zapi.NaServer(self.hostname)
        self.server.set_username(self.username)
        self.server.set_password(self.password)
        # Todo : Remove hardcoded values.
        self.server.set_api_version(major=1,
                                    minor=21)
        self.server.set_port(80)
        self.server.set_server_type('FILER')
        self.server.set_transport_type('HTTP')

    def get_licensing_status(self):
        """
            Check licensing status

            :return: package (key) and licensing status (value)
            :rtype: dict
        """
        license_status = zapi.NaElement('license-v2-status-list-info')
        result = None
        try:
            result = self.server.invoke_successfully(license_status,
                                                     enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error checking license status: %s',
                             zapi.NaApiError.message)
            raise

        return_dictionary = {}
        license_v2_status = result.get_child_by_name('license-v2-status')
        if license_v2_status:
            for license_v2_status_info in license_v2_status.get_children():
                package = license_v2_status_info.get_child_content('package')
                status = license_v2_status_info.get_child_content('method')
                return_dictionary[package] = status

        return return_dictionary

    def remove_licenses(self, remove_list):
        """
        Remove requested licenses
        :param:
            remove_list : List of packages to remove

        """
        license_delete = zapi.NaElement('license-v2-delete')
        for package in remove_list:
            license_delete.add_new_child('package', package)

        if self.serial_number is not None:
            license_delete.add_new_child('serial-number', self.serial_number)

        try:
            self.server.invoke_successfully(license_delete,
                                            enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error removing license : %s',
                             zapi.NaApiError.message)
            raise

    def remove_unused_licenses(self):
        """
        Remove unused licenses
        """
        remove_unused = zapi.NaElement('license-v2-delete-unused')
        try:
            self.server.invoke_successfully(remove_unused,
                                            enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error removing unused licenses : %s',
                             zapi.NaApiError.message)
            raise

    def remove_expired_licenses(self):
        """
        Remove expired licenses
        """
        remove_expired = zapi.NaElement('license-v2-delete-expired')
        try:
            self.server.invoke_successfully(remove_expired,
                                            enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error removing expired licenses : %s',
                             zapi.NaApiError.message)
            raise

    def update_licenses(self):
        """
        Update licenses
        """
        logger.debug('Updating licenses')

        # Remove unused and expired licenses, if requested.
        if self.remove_unused:
            self.remove_unused_licenses()

        if self.remove_expired:
            self.remove_expired_licenses()

        # Next, add/remove specific requested licenses.
        license_add = zapi.NaElement('license-v2-add')
        codes = zapi.NaElement('codes')
        remove_list = []
        for key, value in self.licenses.items():
            str_value = str(value)
            # Make sure license is not an empty string.
            if str_value and str_value.strip():
                if str_value.lower() == 'remove':
                    remove_list.append(str(key).lower())
                else:
                    codes.add_new_child('license-code-v2', str_value)

        # Remove requested licenses.
        if not len(remove_list) == 0:
            self.remove_licenses(remove_list)

        # Add requested licenses
        if not len(codes.get_children()) == 0:
            license_add.add_child_elem(codes)
            try:
                self.server.invoke_successfully(license_add,
                                                enable_tunneling=False)
            except zapi.NaApiError, e:
                logger.exception('Error adding licenses : %s',
                                 zapi.NaApiError.message)
                raise

    def apply(self):
        changed = False
        # Add / Update licenses.
        license_status = self.get_licensing_status()
        self.update_licenses()
        new_license_status = self.get_licensing_status()

        if not license_status == new_license_status:
            changed = True

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTLicense()

    try:
        v.apply()
    except Exception, e:
        logger.debug("Exception in apply(): \n%s" % format_exc(e))
        raise

main()
