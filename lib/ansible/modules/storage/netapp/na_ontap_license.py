#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_license

short_description: NetApp ONTAP protocol and feature licenses
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Add or remove licenses on NetApp ONTAP.

options:
  state:
    description:
    - Whether the specified license should exist or not.
    choices: ['present', 'absent']
    default: present

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
      Serial number of the node associated with the license.
      This parameter is used primarily when removing license for a specific service.

  license_names:
    description:
    - List of license-names to delete.
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

  license_codes:
    description:
    - List of license codes to be added.

'''


EXAMPLES = """
- name: Add licenses
  na_ontap_license:
    state: present
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
    serial_number: #################
    license_codes: CODE1,CODE2

- name: Remove licenses
  na_ontap_license:
    state: absent
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
    remove_unused: false
    remove_expired: true
    serial_number: #################
    license_names: nfs,cifs
"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


def local_cmp(a, b):
    """
        compares with only values and not keys, keys should be the same for both dicts
        :param a: dict 1
        :param b: dict 2
        :return: difference of values in both dicts
        """
    diff = [key for key in a if a[key] != b[key]]
    return len(diff)


class NetAppOntapLicense(object):
    '''ONTAP license class'''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            serial_number=dict(required=False, type='str'),
            remove_unused=dict(default=None, type='bool'),
            remove_expired=dict(default=None, type='bool'),
            license_codes=dict(default=None, type='list'),
            license_names=dict(default=None, type='list'),
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=False,
            required_if=[
                ('state', 'absent', ['serial_number', 'license_names'])]
        )
        parameters = self.module.params
        # set up state variables
        self.state = parameters['state']
        self.serial_number = parameters['serial_number']
        self.remove_unused = parameters['remove_unused']
        self.remove_expired = parameters['remove_expired']
        self.license_codes = parameters['license_codes']
        self.license_names = parameters['license_names']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_licensing_status(self):
        """
            Check licensing status

            :return: package (key) and licensing status (value)
            :rtype: dict
        """
        license_status = netapp_utils.zapi.NaElement(
            'license-v2-status-list-info')
        result = None
        try:
            result = self.server.invoke_successfully(license_status,
                                                     enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error checking license status: %s" %
                                  to_native(error), exception=traceback.format_exc())

        return_dictionary = {}
        license_v2_status = result.get_child_by_name('license-v2-status')
        if license_v2_status:
            for license_v2_status_info in license_v2_status.get_children():
                package = license_v2_status_info.get_child_content('package')
                status = license_v2_status_info.get_child_content('method')
                return_dictionary[package] = status

        return return_dictionary

    def remove_licenses(self, package_name):
        """
        Remove requested licenses
        :param:
          package_name: Name of the license to be deleted
        """
        license_delete = netapp_utils.zapi.NaElement('license-v2-delete')
        license_delete.add_new_child('serial-number', self.serial_number)
        license_delete.add_new_child('package', package_name)
        try:
            self.server.invoke_successfully(license_delete,
                                            enable_tunneling=False)
            return True
        except netapp_utils.zapi.NaApiError as error:
            # Error 15661 - Object not found
            if to_native(error.code) == "15661":
                return False
            else:
                self.module.fail_json(msg="Error removing license %s" %
                                      to_native(error), exception=traceback.format_exc())

    def remove_unused_licenses(self):
        """
        Remove unused licenses
        """
        remove_unused = netapp_utils.zapi.NaElement('license-v2-delete-unused')
        try:
            self.server.invoke_successfully(remove_unused,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error removing unused licenses: %s" %
                                  to_native(error), exception=traceback.format_exc())

    def remove_expired_licenses(self):
        """
        Remove expired licenses
        """
        remove_expired = netapp_utils.zapi.NaElement(
            'license-v2-delete-expired')
        try:
            self.server.invoke_successfully(remove_expired,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error removing expired licenses: %s" %
                                  to_native(error), exception=traceback.format_exc())

    def add_licenses(self):
        """
        Add licenses
        """
        license_add = netapp_utils.zapi.NaElement('license-v2-add')
        codes = netapp_utils.zapi.NaElement('codes')
        for code in self.license_codes:
            codes.add_new_child('license-code-v2', str(code.strip().lower()))
        license_add.add_child_elem(codes)
        try:
            self.server.invoke_successfully(license_add,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error adding licenses: %s" %
                                  to_native(error), exception=traceback.format_exc())

    def apply(self):
        '''Call add, delete or modify methods'''
        changed = False
        create_license = False
        remove_license = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_license", cserver)
        # Add / Update licenses.
        license_status = self.get_licensing_status()

        if self.state == 'absent':  # delete
            changed = True
        else:  # add or update
            if self.license_codes is not None:
                create_license = True
                changed = True
            if self.remove_unused is not None:
                remove_license = True
                changed = True
            if self.remove_expired is not None:
                remove_license = True
                changed = True
        if changed:
            if self.state == 'present':  # execute create
                if create_license:
                    self.add_licenses()
                if self.remove_unused is not None:
                    self.remove_unused_licenses()
                if self.remove_expired is not None:
                    self.remove_expired_licenses()
                if create_license or remove_license:
                    new_license_status = self.get_licensing_status()
                    if local_cmp(license_status, new_license_status) == 0:
                        changed = False
            else:  # execute delete
                license_deleted = False
                for package in self.license_names:
                    license_deleted |= self.remove_licenses(package)
                    changed = license_deleted

        self.module.exit_json(changed=changed)


def main():
    '''Apply license operations'''
    obj = NetAppOntapLicense()
    obj.apply()


if __name__ == '__main__':
    main()
