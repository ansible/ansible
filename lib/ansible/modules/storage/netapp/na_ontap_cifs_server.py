#!/usr/bin/python
""" this is cifs_server module

 (c) 2018-2019, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'certified'
}

DOCUMENTATION = '''
---
module: na_ontap_cifs_server
short_description: NetApp ONTAP CIFS server configuration
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Creating / deleting and modifying the CIFS server .

options:

  state:
    description:
    - Whether the specified cifs_server should exist or not.
    default: present
    choices: ['present', 'absent']

  service_state:
    description:
    - CIFS Server Administrative Status.
    choices: ['stopped', 'started']

  name:
    description:
    - Specifies the cifs_server name.
    required: true
    aliases: ['cifs_server_name']

  admin_user_name:
    description:
    - Specifies the cifs server admin username.

  admin_password:
    description:
    - Specifies the cifs server admin password.

  domain:
    description:
    - The Fully Qualified Domain Name of the Windows Active Directory this CIFS server belongs to.

  workgroup:
    description:
    -  The NetBIOS name of the domain or workgroup this CIFS server belongs to.

  ou:
    description:
    - The Organizational Unit (OU) within the Windows Active Directory
      this CIFS server belongs to.
    version_added: '2.7'

  force:
    type: bool
    description:
    - If this is set and a machine account with the same name as
      specified in 'name' exists in the Active Directory, it
      will be overwritten and reused.
    version_added: '2.7'

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = '''
    - name: Create cifs_server
      na_ontap_cifs_server:
        state: present
        vserver: svm1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete cifs_server
      na_ontap_cifs_server:
        state: absent
        name: data2
        vserver: svm1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

'''

RETURN = '''
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapcifsServer(object):
    """
    object to describe  cifs_server info
    """

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            service_state=dict(required=False, choices=['stopped', 'started']),
            name=dict(required=True, type='str', aliases=['cifs_server_name']),
            workgroup=dict(required=False, type='str', default=None),
            domain=dict(required=False, type='str'),
            admin_user_name=dict(required=False, type='str'),
            admin_password=dict(required=False, type='str', no_log=True),
            ou=dict(required=False, type='str'),
            force=dict(required=False, type='bool'),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        params = self.module.params

        # set up state variables
        self.state = params['state']
        self.cifs_server_name = params['cifs_server_name']
        self.workgroup = params['workgroup']
        self.domain = params['domain']
        self.vserver = params['vserver']
        self.service_state = params['service_state']
        self.admin_user_name = params['admin_user_name']
        self.admin_password = params['admin_password']
        self.ou = params['ou']
        self.force = params['force']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_cifs_server(self):
        """
        Return details about the CIFS-server
        :param:
            name : Name of the name of the cifs_server

        :return: Details about the cifs_server. None if not found.
        :rtype: dict
        """
        cifs_server_info = netapp_utils.zapi.NaElement('cifs-server-get-iter')
        cifs_server_attributes = netapp_utils.zapi.NaElement('cifs-server-config')
        cifs_server_attributes.add_new_child('cifs-server', self.cifs_server_name)
        cifs_server_attributes.add_new_child('vserver', self.vserver)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(cifs_server_attributes)
        cifs_server_info.add_child_elem(query)
        result = self.server.invoke_successfully(cifs_server_info, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            cifs_server_attributes = result.get_child_by_name('attributes-list').\
                get_child_by_name('cifs-server-config')
            return_value = {
                'cifs_server_name': self.cifs_server_name,
                'administrative-status': cifs_server_attributes.get_child_content('administrative-status')
            }

        return return_value

    def create_cifs_server(self):
        """
        calling zapi to create cifs_server
        """
        options = {'cifs-server': self.cifs_server_name, 'administrative-status': 'up'
                   if self.service_state == 'started' else 'down'}
        if self.workgroup is not None:
            options['workgroup'] = self.workgroup
        if self.domain is not None:
            options['domain'] = self.domain
        if self.admin_user_name is not None:
            options['admin-username'] = self.admin_user_name
        if self.admin_password is not None:
            options['admin-password'] = self.admin_password
        if self.ou is not None:
            options['organizational-unit'] = self.ou
        if self.force is not None:
            options['force-account-overwrite'] = str(self.force).lower()

        cifs_server_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-server-create', **options)

        try:
            self.server.invoke_successfully(cifs_server_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error Creating cifs_server %s: %s' %
                                  (self.cifs_server_name, to_native(exc)), exception=traceback.format_exc())

    def delete_cifs_server(self):
        """
        calling zapi to create cifs_server
        """
        if self.cifs_server_name == 'up':
            self.modify_cifs_server(admin_status='down')

        cifs_server_delete = netapp_utils.zapi.NaElement.create_node_with_children('cifs-server-delete')

        try:
            self.server.invoke_successfully(cifs_server_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error deleting cifs_server %s: %s' % (self.cifs_server_name, to_native(exc)),
                                  exception=traceback.format_exc())

    def modify_cifs_server(self, admin_status):
        """
        RModify the cifs_server.
        """
        cifs_server_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-server-modify', **{'cifs-server': self.cifs_server_name,
                                     'administrative-status': admin_status, 'vserver': self.vserver})
        try:
            self.server.invoke_successfully(cifs_server_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying cifs_server %s: %s' % (self.cifs_server_name, to_native(e)),
                                  exception=traceback.format_exc())

    def start_cifs_server(self):
        """
        RModify the cifs_server.
        """
        cifs_server_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-server-start')
        try:
            self.server.invoke_successfully(cifs_server_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying cifs_server %s: %s' % (self.cifs_server_name, to_native(e)),
                                  exception=traceback.format_exc())

    def stop_cifs_server(self):
        """
        RModify the cifs_server.
        """
        cifs_server_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-server-stop')
        try:
            self.server.invoke_successfully(cifs_server_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying cifs_server %s: %s' % (self.cifs_server_name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        calling all cifs_server features
        """

        changed = False
        cifs_server_exists = False
        netapp_utils.ems_log_event("na_ontap_cifs_server", self.server)
        cifs_server_detail = self.get_cifs_server()

        if cifs_server_detail:
            cifs_server_exists = True

            if self.state == 'present':
                administrative_status = cifs_server_detail['administrative-status']
                if self.service_state == 'started' and administrative_status == 'down':
                    changed = True
                if self.service_state == 'stopped' and administrative_status == 'up':
                    changed = True
            else:
                # we will delete the CIFs server
                changed = True
        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not cifs_server_exists:
                        self.create_cifs_server()

                    elif self.service_state == 'stopped':
                        self.stop_cifs_server()

                    elif self.service_state == 'started':
                        self.start_cifs_server()

                elif self.state == 'absent':
                    self.delete_cifs_server()

        self.module.exit_json(changed=changed)


def main():
    cifs_server = NetAppOntapcifsServer()
    cifs_server.apply()


if __name__ == '__main__':
    main()
