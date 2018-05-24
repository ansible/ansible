#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: na_ontap_ntp
short_description: Create/Delete/modify_version ONTAP NTP server
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: Suhas Bangalore Shekar (bsuhas@netapp.com), Archana Ganesan (garchana@netapp.com)
description:
- Create or delete or modify ntp server in ONTAP
options:
  state:
    description:
    - Whether the specified ntp server should exist or not.
    choices: ['present', 'absent']
    default: 'present'
  server_name:
    description:
    - The name of the ntp server to manage.
    required: True
  version:
    description:
    - give version for ntp server
    choices: ['auto', '3', '4']
    default: 'auto'
"""

EXAMPLES = """
    - name: Create NTP server
      na_ontap_ntp:
        state: present
        version: auto
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Delete NTP server
      na_ontap_ntp:
        state: absent
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapNTPServer(object):
    """ object initialize and class methods """
    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            server_name=dict(required=True, type='str'),
            version=dict(required=False, type='str', default='auto',
                         choices=['auto', '3', '4']),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.server_name = parameters['server_name']
        self.version = parameters['version']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_ntp_server(self):
        """
        Return details about the ntp server
        :param:
            name : Name of the server_name
        :return: Details about the ntp server. None if not found.
        :rtype: dict
        """
        ntp_iter = netapp_utils.zapi.NaElement('ntp-server-get-iter')
        ntp_info = netapp_utils.zapi.NaElement('ntp-server-info')
        ntp_info.add_new_child('server-name', self.server_name)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(ntp_info)

        ntp_iter.add_child_elem(query)
        result = self.server.invoke_successfully(ntp_iter, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:

            ntp_server_name = result.get_child_by_name('attributes-list').\
                get_child_by_name('ntp-server-info').\
                get_child_content('server-name')
            server_version = result.get_child_by_name('attributes-list').\
                get_child_by_name('ntp-server-info').\
                get_child_content('version')
            return_value = {
                'server-name': ntp_server_name,
                'version': server_version
            }

        return return_value

    def create_ntp_server(self):
        """
        create ntp server.
        """
        ntp_server_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'ntp-server-create', **{'server-name': self.server_name,
                                    'version': self.version
                                    })

        try:
            self.server.invoke_successfully(ntp_server_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating ntp server %s: %s'
                                  % (self.server_name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_ntp_server(self):
        """
        delete ntp server.
        """
        ntp_server_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'ntp-server-delete', **{'server-name': self.server_name})

        try:
            self.server.invoke_successfully(ntp_server_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting ntp server %s: %s'
                                  % (self.server_name, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_version(self):
        """
        modify the version.
        """
        ntp_modify_versoin = netapp_utils.zapi.NaElement.create_node_with_children(
            'ntp-server-modify',
            **{'server-name': self.server_name, 'version': self.version})
        try:
            self.server.invoke_successfully(ntp_modify_versoin,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying version for ntp server %s: %s'
                                  % (self.server_name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """Apply action to ntp-server"""

        changed = False
        ntp_modify = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_ntp", cserver)
        ntp_server_details = self.get_ntp_server()
        if ntp_server_details is not None:
            if self.state == 'absent':  # delete
                changed = True
            elif self.state == 'present' and self.version:
                # modify version
                if self.version != ntp_server_details['version']:
                    ntp_modify = True
                    changed = True
        else:
            if self.state == 'present':  # create
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if ntp_server_details is None:
                        self.create_ntp_server()
                    elif ntp_modify:
                        self.modify_version()
                elif self.state == 'absent':
                    self.delete_ntp_server()

        self.module.exit_json(changed=changed)


def main():
    """ Create object and call apply """
    ntp_obj = NetAppOntapNTPServer()
    ntp_obj.apply()


if __name__ == '__main__':
    main()
