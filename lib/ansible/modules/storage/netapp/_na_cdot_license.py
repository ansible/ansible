#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_license

short_description: Manage NetApp cDOT protocol and feature licenses
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (@timuster) <sumit4@netapp.com>

deprecated:
  removed_in: '2.11'
  why: Updated modules released with increased functionality
  alternative: Use M(na_ontap_license) instead.

description:
- Add or remove licenses on NetApp ONTAP.

options:

  remove_unused:
    description:
    - Remove licenses that have no controller affiliation in the cluster.
    type: bool

  remove_expired:
    description:
    - Remove licenses that have expired in the cluster.
    type: bool

  serial_number:
    description:
    - Serial number of the node associated with the license.
    - This parameter is used primarily when removing license for a specific service.
    - If this parameter is not provided, the cluster serial number is used by default.

  licenses:
    description:
    - List of licenses to add or remove.
    - Please note that trying to remove a non-existent license will throw an error.
    suboptions:
      base:
        description:
          - Cluster Base License
      nfs:
        description:
          - NFS License
      cifs:
        description:
          - CIFS License
      iscsi:
        description:
          - iSCSI License
      fcp:
        description:
          - FCP License
      cdmi:
        description:
          - CDMI License
      snaprestore:
        description:
          - SnapRestore License
      snapmirror:
        description:
          - SnapMirror License
      flexclone:
        description:
          - FlexClone License
      snapvault:
        description:
          - SnapVault License
      snaplock:
        description:
          - SnapLock License
      snapmanagersuite:
        description:
          - SnapManagerSuite License
      snapprotectapps:
        description:
          - SnapProtectApp License
      v_storageattach:
        description:
          - Virtual Attached Storage License

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

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppCDOTLicense(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            serial_number=dict(required=False, type='str', default=None),
            remove_unused=dict(default=False, type='bool'),
            remove_expired=dict(default=False, type='bool'),
            licenses=dict(default=False, type='dict'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=False
        )

        p = self.module.params

        # set up state variables
        self.serial_number = p['serial_number']
        self.remove_unused = p['remove_unused']
        self.remove_expired = p['remove_expired']
        self.licenses = p['licenses']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)

    def get_licensing_status(self):
        """
            Check licensing status

            :return: package (key) and licensing status (value)
            :rtype: dict
        """
        license_status = netapp_utils.zapi.NaElement('license-v2-status-list-info')
        result = None
        try:
            result = self.server.invoke_successfully(license_status,
                                                     enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error checking license status: %s" %
                                  to_native(e), exception=traceback.format_exc())

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
        license_delete = netapp_utils.zapi.NaElement('license-v2-delete')
        for package in remove_list:
            license_delete.add_new_child('package', package)

        if self.serial_number is not None:
            license_delete.add_new_child('serial-number', self.serial_number)

        try:
            self.server.invoke_successfully(license_delete,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error removing license %s" %
                                  to_native(e), exception=traceback.format_exc())

    def remove_unused_licenses(self):
        """
        Remove unused licenses
        """
        remove_unused = netapp_utils.zapi.NaElement('license-v2-delete-unused')
        try:
            self.server.invoke_successfully(remove_unused,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error removing unused licenses: %s" %
                                  to_native(e), exception=traceback.format_exc())

    def remove_expired_licenses(self):
        """
        Remove expired licenses
        """
        remove_expired = netapp_utils.zapi.NaElement('license-v2-delete-expired')
        try:
            self.server.invoke_successfully(remove_expired,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error removing expired licenses: %s" %
                                  to_native(e), exception=traceback.format_exc())

    def update_licenses(self):
        """
        Update licenses
        """
        # Remove unused and expired licenses, if requested.
        if self.remove_unused:
            self.remove_unused_licenses()

        if self.remove_expired:
            self.remove_expired_licenses()

        # Next, add/remove specific requested licenses.
        license_add = netapp_utils.zapi.NaElement('license-v2-add')
        codes = netapp_utils.zapi.NaElement('codes')
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
        if len(remove_list) != 0:
            self.remove_licenses(remove_list)

        # Add requested licenses
        if len(codes.get_children()) != 0:
            license_add.add_child_elem(codes)
            try:
                self.server.invoke_successfully(license_add,
                                                enable_tunneling=False)
            except netapp_utils.zapi.NaApiError as e:
                self.module.fail_json(msg="Error adding licenses: %s" %
                                      to_native(e), exception=traceback.format_exc())

    def apply(self):
        changed = False
        # Add / Update licenses.
        license_status = self.get_licensing_status()
        self.update_licenses()
        new_license_status = self.get_licensing_status()

        if license_status != new_license_status:
            changed = True

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTLicense()
    v.apply()


if __name__ == '__main__':
    main()
