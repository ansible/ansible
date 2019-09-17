#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_fcp
short_description: NetApp ONTAP Start, Stop and Enable FCP services.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Start, Stop and Enable FCP services.
options:
  state:
    description:
    - Whether the FCP should be enabled or not.
    choices: ['present', 'absent']
    default: present

  status:
    description:
    - Whether the FCP should be up or down
    choices: ['up', 'down']
    default: up

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = """
    - name: create FCP
      na_ontap_fcp:
        state: present
        status: down
        hostname: "{{hostname}}"
        username: "{{username}}"
        password: "{{password}}"
        vserver:  "{{vservername}}"
"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapFCP(object):
    """
    Enable and Disable FCP
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            status=dict(required=False, choices=['up', 'down'], default='up')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])
        return

    def create_fcp(self):
        """
        Create's and Starts an FCP
        :return: none
        """
        try:
            self.server.invoke_successfully(netapp_utils.zapi.NaElement('fcp-service-create'), True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating FCP: %s' %
                                  (to_native(error)),
                                  exception=traceback.format_exc())

    def start_fcp(self):
        """
        Starts an existing FCP
        :return: none
        """
        try:
            self.server.invoke_successfully(netapp_utils.zapi.NaElement('fcp-service-start'), True)
        except netapp_utils.zapi.NaApiError as error:
            # Error 13013 denotes fcp service already started.
            if to_native(error.code) == "13013":
                return None
            else:
                self.module.fail_json(msg='Error starting FCP %s' % (to_native(error)),
                                      exception=traceback.format_exc())

    def stop_fcp(self):
        """
        Steps an Existing FCP
        :return: none
        """
        try:
            self.server.invoke_successfully(netapp_utils.zapi.NaElement('fcp-service-stop'), True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error Stopping FCP %s' %
                                      (to_native(error)),
                                  exception=traceback.format_exc())

    def destroy_fcp(self):
        """
        Destroys an already stopped FCP
        :return:
        """
        try:
            self.server.invoke_successfully(netapp_utils.zapi.NaElement('fcp-service-destroy'), True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error destroying FCP %s' %
                                      (to_native(error)),
                                  exception=traceback.format_exc())

    def get_fcp(self):
        fcp_obj = netapp_utils.zapi.NaElement('fcp-service-get-iter')
        fcp_info = netapp_utils.zapi.NaElement('fcp-service-info')
        fcp_info.add_new_child('vserver', self.parameters['vserver'])
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(fcp_info)
        fcp_obj.add_child_elem(query)
        result = self.server.invoke_successfully(fcp_obj, True)
        # There can only be 1 FCP per vserver. If true, one is set up, else one isn't set up
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:
            return True
        else:
            return False

    def current_status(self):
        try:
            status = self.server.invoke_successfully(netapp_utils.zapi.NaElement('fcp-service-status'), True)
            return status.get_child_content('is-available') == 'true'
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error destroying FCP: %s' %
                                      (to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_fcp", cserver)
        exists = self.get_fcp()
        changed = False
        if self.parameters['state'] == 'present':
            if exists:
                if self.parameters['status'] == 'up':
                    if not self.current_status():
                        self.start_fcp()
                        changed = True
                else:
                    if self.current_status():
                        self.stop_fcp()
                        changed = True
            else:
                self.create_fcp()
                if self.parameters['status'] == 'up':
                    self.start_fcp()
                elif self.parameters['status'] == 'down':
                    self.stop_fcp()
                changed = True
        else:
            if exists:
                if self.current_status():
                    self.stop_fcp()
                self.destroy_fcp()
                changed = True
        self.module.exit_json(changed=changed)


def main():
    """
    Start, Stop and Enable FCP services.
    """
    obj = NetAppOntapFCP()
    obj.apply()


if __name__ == '__main__':
    main()
