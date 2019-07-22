#!/usr/bin/python

# (c) 2018 Piotr Olczak <piotr.olczak@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
module: na_ontap_motd
author: Piotr Olczak (@dprts) <polczak@redhat.com>
extends_documentation_fragment:
    - netapp.na_ontap
short_description: Setup motd on cDOT
description:
    - This module allows you to manipulate motd on cDOT
version_added: "2.7"
requirements:
    - netapp_lib
options:
    state:
        description:
        - If C(state=present) sets MOTD given in I(message) C(state=absent) removes it.
        choices: ['present', 'absent']
        default: present
    message:
        description:
        - MOTD Text message, required when C(state=present).
    vserver:
        description:
        - The name of the SVM motd should be set for.
        required: true
    show_cluster_motd:
        description:
        - Set to I(false) if Cluster-level Message of the Day should not be shown
        type: bool
        default: True

'''

EXAMPLES = '''

- name: Set Cluster-Level MOTD
  na_ontap_motd:
    vserver: my_ontap_cluster
    message: "Cluster wide MOTD"
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
    state: present
    https: true

- name: Set MOTD for I(rhev_nfs_krb) SVM, do not show Cluster-Level MOTD
  na_ontap_motd:
    vserver: rhev_nfs_krb
    message: "Access to rhev_nfs_krb is also restricted"
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
    state: present
    show_cluster_motd: False
    https: true

'''

RETURN = '''

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

try:
    import xmltodict
    HAS_XMLTODICT_LIB = True
except ImportError:
    HAS_XMLTODICT_LIB = False


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class CDotMotd(object):

    def __init__(self):
        argument_spec = netapp_utils.na_ontap_host_argument_spec()
        argument_spec.update(dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            vserver=dict(required=True, type='str'),
            message=dict(default='', type='str'),
            show_cluster_motd=dict(default=True, type='bool')
        ))

        self.module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_XMLTODICT_LIB is False:
            self.module.fail_json(msg="the python xmltodict module is required")

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")

        self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def _create_call(self):
        api_call = netapp_utils.zapi.NaElement('vserver-motd-modify-iter')
        api_call.add_new_child('message', self.parameters['message'])
        api_call.add_new_child('is-cluster-message-enabled', 'true' if self.parameters['show_cluster_motd'] else 'false')
        query = netapp_utils.zapi.NaElement('query')
        motd_info = netapp_utils.zapi.NaElement('vserver-motd-info')
        motd_info.add_new_child('vserver', self.parameters['vserver'])
        query.add_child_elem(motd_info)
        api_call.add_child_elem(query)
        return api_call

    def commit_changes(self):
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_motd", cserver)
        if self.parameters['state'] == 'absent':
            # Just make sure it is empty
            self.parameters['message'] = ''

        call = self._create_call()

        try:
            _call_result = self.server.invoke_successfully(call, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as err:
            self.module.fail_json(msg="Error calling API %s: %s" %
                                  ('vserver-motd-modify-iter', to_native(err)), exception=traceback.format_exc())

        _dict_num_succeeded = xmltodict.parse(
            _call_result.get_child_by_name('num-succeeded').to_string(),
            xml_attribs=False)

        num_succeeded = int(_dict_num_succeeded['num-succeeded'])

        changed = bool(num_succeeded >= 1)

        result = {'state': self.parameters['state'], 'changed': changed}
        self.module.exit_json(**result)


def main():
    ansible_call = CDotMotd()
    ansible_call.commit_changes()


if __name__ == '__main__':
    main()
