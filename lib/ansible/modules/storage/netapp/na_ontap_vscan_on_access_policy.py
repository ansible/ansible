#!/usr/bin/python

# (c) 2018-2019, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_vscan_on_access_policy
short_description: NetApp ONTAP Vscan on access policy configuration.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Configure on access policy for Vscan (virus scan)
options:
  state:
    description:
    - Whether a Vscan on Access policy is present or not
    choices: ['present', 'absent']
    default: present

  vserver:
    description:
    - the name of the data vserver to use.
    required: true

  policy_name:
    description:
    - The name of the policy
    required: true

  file_ext_to_exclude:
    description:
    - File extensions for which On-Access scanning must not be performed.

  file_ext_to_include:
    description:
    - File extensions for which On-Access scanning is considered. The default value is '*', which means that all files are considered for scanning except
    - those which are excluded from scanning.

  filters:
    description:
    - A list of filters which can be used to define the scope of the On-Access policy more precisely. The filters can be added in any order. Possible values
    - scan_ro_volume  Enable scans for read-only volume,
    - scan_execute_access  Scan only files opened with execute-access (CIFS only)

  is_scan_mandatory:
    description:
    - Specifies whether access to a file is allowed if there are no external virus-scanning servers available for virus scanning. It is true if not provided at
     the time of creating a policy.
    type: bool

  max_file_size:
    description:
    - Max file-size (in bytes) allowed for scanning. The default value of 2147483648 (2GB) is taken if not provided at the time of creating a policy.

  paths_to_exclude:
    description:
    - File paths for which On-Access scanning must not be performed.

  scan_files_with_no_ext:
    description:
    - Specifies whether files without any extension are considered for scanning or not.
    default: True
'''

EXAMPLES = """
    - name: Create Vscan On Access Policy
      na_ontap_vscan_on_access_policy:
        state: present
        username: '{{ netapp_username }}'
        password: '{{ netapp_password }}'
        hostname: '{{ netapp_hostname }}'
        vserver: carchi-vsim2
        policy_name: carchi_policy
        file_ext_to_exclude: ['exe', 'yml']
    - name: modify Vscan on Access Policy
      na_ontap_vscan_on_access_policy:
        state: present
        username: '{{ netapp_username }}'
        password: '{{ netapp_password }}'
        hostname: '{{ netapp_hostname }}'
        vserver: carchi-vsim2
        policy_name: carchi_policy
        file_ext_to_exclude: ['exe', 'yml', 'py']
    - name: Delete On Access Policy
      na_ontap_vscan_on_access_policy:
        state: absent
        username: '{{ netapp_username }}'
        password: '{{ netapp_password }}'
        hostname: '{{ netapp_hostname }}'
        vserver: carchi-vsim2
        policy_name: carchi_policy
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapVscanOnAccessPolicy(object):
    """
    Create/Modify/Delete a Vscan OnAccess policy
    """
    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            policy_name=dict(required=True, type='str'),
            file_ext_to_exclude=dict(required=False, type="list"),
            file_ext_to_include=dict(required=False, type="list"),
            filters=dict(required=False, type="list"),
            is_scan_mandatory=dict(required=False, type='bool', default=False),
            max_file_size=dict(required=False, type="int"),
            paths_to_exclude=dict(required=False, type="list"),
            scan_files_with_no_ext=dict(required=False, type=bool, default=True)
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        parameters = self.module.params
        self.state = parameters['state']
        self.vserver = parameters['vserver']
        self.policy_name = parameters['policy_name']
        self.file_ext_to_exclude = parameters['file_ext_to_exclude']
        self.file_ext_to_include = parameters['file_ext_to_include']
        self.filters = parameters['filters']
        self.is_scan_mandatory = parameters['is_scan_mandatory']
        self.max_file_size = parameters['max_file_size']
        self.paths_to_exclude = parameters['paths_to_exclude']
        self.scan_files_with_no_ext = parameters['scan_files_with_no_ext']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)

    def exists_access_policy(self, policy_obj=None):
        """
        Check if a Vscan Access policy exists
        :return: True if Exist, False if it does not
        """
        if policy_obj is None:
            policy_obj = self.return_on_access_policy()
        if policy_obj:
            return True
        else:
            return False

    def return_on_access_policy(self):
        """
        Return a Vscan on Access Policy
        :return: None if there is no access policy, return the policy if there is
        """
        access_policy_obj = netapp_utils.zapi.NaElement('vscan-on-access-policy-get-iter')
        access_policy_info = netapp_utils.zapi.NaElement('vscan-on-access-policy-info')
        access_policy_info.add_new_child('policy-name', self.policy_name)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(access_policy_info)
        access_policy_obj.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(access_policy_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error searching Vscan on Access Policy %s: %s' %
                                      (self.policy_name, to_native(error)), exception=traceback.format_exc())
        if result.get_child_by_name('num-records'):
            if int(result.get_child_content('num-records')) == 1:
                return result
            elif int(result.get_child_content('num-records')) > 1:
                self.module.fail_json(msg='Mutiple Vscan on Access Policy matching %s:' % self.policy_name)
        return None

    def create_on_access_policy(self):
        """
        Create a Vscan on Access policy
        :return: none
        """
        access_policy_obj = netapp_utils.zapi.NaElement('vscan-on-access-policy-create')
        access_policy_obj.add_new_child('policy-name', self.policy_name)
        access_policy_obj.add_new_child('protocol', 'cifs')
        access_policy_obj = self._fill_in_access_policy(access_policy_obj)

        try:
            self.server.invoke_successfully(access_policy_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating Vscan on Access Policy %s: %s' %
                                      (self.policy_name, to_native(error)), exception=traceback.format_exc())

    def delete_on_access_policy(self):
        """
        Delete a Vscan On Access Policy
        :return:
        """
        access_policy_obj = netapp_utils.zapi.NaElement('vscan-on-access-policy-delete')
        access_policy_obj.add_new_child('policy-name', self.policy_name)
        try:
            self.server.invoke_successfully(access_policy_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error Deleting Vscan on Access Policy %s: %s' %
                                      (self.policy_name, to_native(error)), exception=traceback.format_exc())

    def modify_on_access_policy(self):
        """
        Modify a Vscan On Access policy
        :return: nothing
        """
        access_policy_obj = netapp_utils.zapi.NaElement('vscan-on-access-policy-modify')
        access_policy_obj.add_new_child('policy-name', self.policy_name)
        access_policy_obj = self._fill_in_access_policy(access_policy_obj)
        try:
            self.server.invoke_successfully(access_policy_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error Modifying Vscan on Access Policy %s: %s' %
                                      (self.policy_name, to_native(error)), exception=traceback.format_exc())

    def _fill_in_access_policy(self, access_policy_obj):
        if self.is_scan_mandatory is not None:
            access_policy_obj.add_new_child('is-scan-mandatory', str(self.is_scan_mandatory).lower())
        if self.max_file_size:
            access_policy_obj.add_new_child('max-file-size', str(self.max_file_size))
        if self.scan_files_with_no_ext is not None:
            access_policy_obj.add_new_child('scan-files-with-no-ext', str(self.scan_files_with_no_ext))
        if self.file_ext_to_exclude:
            ext_obj = netapp_utils.zapi.NaElement('file-ext-to-exclude')
            access_policy_obj.add_child_elem(ext_obj)
            for extension in self.file_ext_to_exclude:
                ext_obj.add_new_child('file-extension', extension)
        if self.file_ext_to_include:
            ext_obj = netapp_utils.zapi.NaElement('file-ext-to-include')
            access_policy_obj.add_child_elem(ext_obj)
            for extension in self.file_ext_to_include:
                ext_obj.add_new_child('file-extension', extension)
        if self.filters:
            ui_filter_obj = netapp_utils.zapi.NaElement('filters')
            access_policy_obj.add_child_elem(ui_filter_obj)
            for filter in self.filters:
                ui_filter_obj.add_new_child('vscan-on-access-policy-ui-filter', filter)
        if self.paths_to_exclude:
            path_obj = netapp_utils.zapi.NaElement('paths-to-exclude')
            access_policy_obj.add_child_elem(path_obj)
            for path in self.paths_to_exclude:
                path_obj.add_new_child('file-path', path)
        return access_policy_obj

    def has_policy_changed(self):
        results = self.return_on_access_policy()
        if results is None:
            return False
        try:
            policy_obj = results.get_child_by_name('attributes-list').get_child_by_name('vscan-on-access-policy-info')
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error Accessing on access policy %s: %s' %
                                      (self.policy_name, to_native(error)), exception=traceback.format_exc())
        if self.is_scan_mandatory is not None:
            if str(self.is_scan_mandatory).lower() != policy_obj.get_child_content('is-scan-mandatory'):
                return True
        if self.max_file_size:
            if self.max_file_size != int(policy_obj.get_child_content('max-file-size')):
                return True
        if self.scan_files_with_no_ext is not None:
            if str(self.scan_files_with_no_ext).lower() != policy_obj.get_child_content('scan-files-with-no-ext'):
                return True
        if self.file_ext_to_exclude:
            # if no file-ext-to-exclude are given at creation, XML will not have a file-ext-to-exclude
            if policy_obj.get_child_by_name('file-ext-to-exclude') is None:
                return True
            current_to_exclude = []
            for each in policy_obj.get_child_by_name('file-ext-to-exclude').get_children():
                current_to_exclude.append(each.get_content())
            k = self._diff(self.file_ext_to_exclude, current_to_exclude)
            # If the diff returns something the lists don't match and the policy has changed
            if k:
                return True
        if self.file_ext_to_include:
            # if no file-ext-to-include are given at creation, XML will not have a file-ext-to-include
            if policy_obj.get_child_by_name('file-ext-to-include') is None:
                return True
            current_to_include = []
            for each in policy_obj.get_child_by_name('file-ext-to-include').get_children():
                current_to_include.append(each.get_content())
            k = self._diff(self.file_ext_to_include, current_to_include)
            # If the diff returns something the lists don't match and the policy has changed
            if k:
                return True
        if self.filters:
            if policy_obj.get_child_by_name('filters') is None:
                return True
            current_filters = []
            for each in policy_obj.get_child_by_name('filters').get_children():
                current_filters.append(each.get_content())
            k = self._diff(self.filters, current_filters)
            # If the diff returns something the lists don't match and the policy has changed
            if k:
                return True
        if self.paths_to_exclude:
            if policy_obj.get_child_by_name('paths-to-exclude') is None:
                return True
            current_paths_to_exlude = []
            for each in policy_obj.get_child_by_name('paths-to-exclude').get_children():
                current_paths_to_exlude.append(each.get_content())
            k = self._diff(self.paths_to_exclude, current_paths_to_exlude)
            # If the diff returns something the lists don't match and the policy has changed
            if k:
                return True
        return False

    def _diff(self, li1, li2):
        """
        :param li1: list 1
        :param li2: list 2
        :return: a list contain items that are not on both lists
        """
        li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2]
        return li_dif

    def apply(self):
        netapp_utils.ems_log_event("na_ontap_vscan_on_access_policy", self.server)
        changed = False
        policy_obj = self.return_on_access_policy()
        if self.state == 'present':
            if not self.exists_access_policy(policy_obj):
                if not self.module.check_mode:
                    self.create_on_access_policy()
                changed = True
            else:
                # Check if anything has changed first.
                if self.has_policy_changed():
                    if not self.module.check_mode:
                        self.modify_on_access_policy()
                    changed = True
        if self.state == 'absent':
            if self.exists_access_policy(policy_obj):
                if not self.module.check_mode:
                    self.delete_on_access_policy()
                changed = True
        self.module.exit_json(changed=changed)


def main():
    """
    Execute action from playbook
    """
    command = NetAppOntapVscanOnAccessPolicy()
    command.apply()


if __name__ == '__main__':
    main()
