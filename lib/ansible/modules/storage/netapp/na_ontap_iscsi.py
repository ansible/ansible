#!/usr/bin/python

# (c) 2017-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_iscsi

short_description: NetApp ONTAP manage iSCSI service
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- create, delete, start, stop iSCSI service on SVM.

options:

  state:
    description:
    - Whether the service should be present or deleted.
    choices: ['present', 'absent']
    default: present

  service_state:
    description:
    - Whether the specified service should running .
    choices: ['started', 'stopped']

  vserver:
    required: true
    description:
    - The name of the vserver to use.

'''

EXAMPLES = """
- name: Create iscsi service
  na_ontap_iscsi:
    state: present
    service_state: started
    vserver: ansibleVServer
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Stop Iscsi service
  na_ontap_iscsi:
    state: present
    service_state: stopped
    vserver: ansibleVServer
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Delete Iscsi service
  na_ontap_iscsi:
    state: absent
    vserver: ansibleVServer
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


class NetAppOntapISCSI(object):

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            service_state=dict(required=False, choices=[
                               'started', 'stopped'], default=None),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        params = self.module.params

        # set up state variables
        self.state = params['state']
        self.service_state = params['service_state']
        if self.state == 'present' and self.service_state is None:
            self.service_state = 'started'
        self.vserver = params['vserver']
        self.is_started = None

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)

    def get_iscsi(self):
        """
        Return details about the iscsi service

        :return: Details about the iscsi service
        :rtype: dict
        """
        iscsi_info = netapp_utils.zapi.NaElement('iscsi-service-get-iter')
        iscsi_attributes = netapp_utils.zapi.NaElement('iscsi-service-info')

        iscsi_attributes.add_new_child('vserver', self.vserver)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(iscsi_attributes)

        iscsi_info.add_child_elem(query)

        result = self.server.invoke_successfully(iscsi_info, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            iscsi = result.get_child_by_name(
                'attributes-list').get_child_by_name('iscsi-service-info')
            if iscsi:
                is_started = iscsi.get_child_content('is-available') == 'true'
                return_value = {
                    'is_started': is_started
                }

        return return_value

    def create_iscsi_service(self):
        """
        Create iscsi service and start if requested
        """
        iscsi_service = netapp_utils.zapi.NaElement.create_node_with_children(
            'iscsi-service-create',
            **{'start': 'true' if self.state == 'started' else 'false'
               })

        try:
            self.server.invoke_successfully(
                iscsi_service, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error creating iscsi service: % s"
                                  % (to_native(e)),
                                  exception=traceback.format_exc())

    def delete_iscsi_service(self):
        """
         Delete the iscsi service
        """
        if self.is_started:
            self.stop_iscsi_service()

        iscsi_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'iscsi-service-destroy')

        try:
            self.server.invoke_successfully(
                iscsi_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error deleting iscsi service \
                                  on vserver %s: %s"
                                  % (self.vserver, to_native(e)),
                                  exception=traceback.format_exc())

    def stop_iscsi_service(self):
        """
         Stop iscsi service
        """

        iscsi_stop = netapp_utils.zapi.NaElement.create_node_with_children(
            'iscsi-service-stop')

        try:
            self.server.invoke_successfully(iscsi_stop, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error Stopping iscsi service \
                                  on vserver %s: %s"
                                  % (self.vserver, to_native(e)),
                                  exception=traceback.format_exc())

    def start_iscsi_service(self):
        """
        Start iscsi service
        """
        iscsi_start = netapp_utils.zapi.NaElement.create_node_with_children(
            'iscsi-service-start')

        try:
            self.server.invoke_successfully(iscsi_start, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error starting iscsi service \
                                  on vserver %s: %s"
                                  % (self.vserver, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        property_changed = False
        iscsi_service_exists = False
        netapp_utils.ems_log_event("na_ontap_iscsi", self.server)
        iscsi_service_detail = self.get_iscsi()

        if iscsi_service_detail:
            self.is_started = iscsi_service_detail['is_started']
            iscsi_service_exists = True

            if self.state == 'absent':
                property_changed = True

            elif self.state == 'present':
                is_started = 'started' if self.is_started else 'stopped'
                property_changed = is_started != self.service_state

        else:
            if self.state == 'present':
                property_changed = True

        if property_changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not iscsi_service_exists:
                        self.create_iscsi_service()  # the service is stopped when initially created
                    if self.service_state == 'started':
                        self.start_iscsi_service()
                    if iscsi_service_exists and self.service_state == 'stopped':
                        self.stop_iscsi_service()

                elif self.state == 'absent':
                    self.delete_iscsi_service()

        changed = property_changed
        # TODO: include other details about the lun (size, etc.)
        self.module.exit_json(changed=changed)


def main():
    v = NetAppOntapISCSI()
    v.apply()


if __name__ == '__main__':
    main()
