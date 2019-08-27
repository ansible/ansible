#!/usr/bin/python

# (c) 2018-2019, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_vscan
short_description: NetApp ONTAP Vscan enable/disable.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
notes:
- on demand task, on_access_policy and scanner_pools must be set up before running this module
description:
- Enable and Disable Vscan
options:
  enable:
    description:
    - Whether to enable to disable a Vscan
    type: bool
    default: True

  vserver:
    description:
    - the name of the data vserver to use.
    required: true
    type: str
'''

EXAMPLES = """
    - name: Enable Vscan
      na_ontap_vscan:
        enable: True
        username: '{{ netapp_username }}'
        password: '{{ netapp_password }}'
        hostname: '{{ netapp_hostname }}'
        vserver: trident_svm

    - name: Disable Vscan
      na_ontap_vscan:
        enable: False
        username: '{{ netapp_username }}'
        password: '{{ netapp_password }}'
        hostname: '{{ netapp_hostname }}'
        vserver: trident_svm
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp import OntapRestAPI
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapVscan(object):
    def __init__(self):
        self.use_rest = False
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            enable=dict(type='bool', default=True),
            vserver=dict(required=True, type='str'),
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        # API should be used for ONTAP 9.6 or higher, Zapi for lower version
        self.restApi = OntapRestAPI(self.module)
        if self.restApi.is_rest():
            self.use_rest = True
        else:
            if HAS_NETAPP_LIB is False:
                self.module.fail_json(msg="the python NetApp-Lib module is required")
            else:
                self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def get_vscan(self):
        if self.use_rest:
            params = {'fields': 'svm,enabled',
                      "svm.name": self.parameters['vserver']}
            api = "protocols/vscan"
            message, error = self.restApi.get(api, params)
            if error:
                self.module.fail_json(msg=error)
            return message['records'][0]
        else:
            vscan_status_iter = netapp_utils.zapi.NaElement('vscan-status-get-iter')
            vscan_status_info = netapp_utils.zapi.NaElement('vscan-status-info')
            vscan_status_info.add_new_child('vserver', self.parameters['vserver'])
            query = netapp_utils.zapi.NaElement('query')
            query.add_child_elem(vscan_status_info)
            vscan_status_iter.add_child_elem(query)
            try:
                result = self.server.invoke_successfully(vscan_status_iter, True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg='Error getting Vscan info for Vserver %s: %s' %
                                          (self.parameters['vserver'], to_native(error)),
                                      exception=traceback.format_exc())
            if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
                return result.get_child_by_name('attributes-list').get_child_by_name('vscan-status-info')

    def enable_vscan(self, uuid=None):
        if self.use_rest:
            params = {"svm.name": self.parameters['vserver']}
            data = {"enabled": self.parameters['enable']}
            api = "protocols/vscan/" + uuid
            message, error = self.restApi.patch(api, data, params)
            if error is not None:
                self.module.fail_json(msg=error)
                # self.module.fail_json(msg=repr(self.restApi.errors), log=repr(self.restApi.debug_logs))
        else:
            vscan_status_obj = netapp_utils.zapi.NaElement("vscan-status-modify")
            vscan_status_obj.add_new_child('is-vscan-enabled', str(self.parameters['enable']))
            try:
                self.server.invoke_successfully(vscan_status_obj, True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg="Error Enable/Disabling Vscan: %s" % to_native(error), exception=traceback.format_exc())

    def asup_log(self):
        if self.use_rest:
            # TODO: logging for Rest
            return
        else:
            # Either we are using ZAPI, or REST failed when it should not
            try:
                netapp_utils.ems_log_event("na_ontap_vscan", self.server)
            except Exception:
                # TODO: we may fail to connect to REST or ZAPI, the line below shows REST issues only
                # self.module.fail_json(msg=repr(self.restApi.errors), log=repr(self.restApi.debug_logs))
                pass

    def apply(self):
        changed = False
        self.asup_log()
        current = self.get_vscan()
        if self.use_rest:
            if current['enabled'] != self.parameters['enable']:
                if not self.module.check_mode:
                    self.enable_vscan(current['svm']['uuid'])
                changed = True
        else:
            if current.get_child_content('is-vscan-enabled') != str(self.parameters['enable']).lower():
                if not self.module.check_mode:
                    self.enable_vscan()
                changed = True
        self.module.exit_json(changed=changed)


def main():
    """
    Execute action from playbook
    """
    command = NetAppOntapVscan()
    command.apply()


if __name__ == '__main__':
    main()
