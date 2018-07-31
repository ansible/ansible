#!/usr/bin/python
''' this is igroup module

 (c) 2018, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''

module: na_ontap_igroup
short_description: ONTAP iSCSI igroup configuration
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: chhaya gunawat (chhayag@netapp.com), Chris Archibald (carchi@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)

description:
    - create, destroy or rename Igroups and add or remove initiator in igroups.

options:
  state:
    description:
    - Whether the specified Igroup should exist or not.
    choices: ['present', 'absent']
    default: present

  name:
    description:
    - The name of the lun to manage.
    required: true

  initiator_group_type:
    description:
    - Type of the initiator group.
    - Required when C(state=present).
    choices: ['fcp', 'iscsi', 'mixed']

  new_name:
    description:
    - New name to be given to initiator group.

  ostype:
    description:
    - OS type of the initiators within the group.

  initiator:
    description:
    - WWPN, WWPN Alias, or iSCSI name of Initiator to add or remove.

  bind_portset:
    description:
    - Name of a current portset to bind to the newly created igroup.

  force_remove_initiator:
    description:
    -  Forcibly remove the initiator even if there are existing LUNs mapped to this initiator group.
    type: bool
    default: False

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = '''
    - name: Create Igroup
      na_ontap_igroup:
        state: present
        name: ansibleIgroup3
        initiator-group-type: iscsi
        ostype: linux
        initiator: iqn.1994-05.com.redhat:scspa0395855001.rtp.openenglab.netapp.com
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: rename Igroup
      na_ontap_igroup:
        state: absent
        name: ansibleIgroup3
        initiator-group-type: iscsi
        ostype: linux
        initiator: iqn.1994-05.com.redhat:scspa0395855001.rtp.openenglab.netapp.com
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: remove Igroup
      na_ontap_igroup:
        state: absent
        name: ansibleIgroup3
        initiator-group-type: iscsi
        ostype: linux
        initiator: iqn.1994-05.com.redhat:scspa0395855001.rtp.openenglab.netapp.com
        vserver: ansibleVServer
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


class NetAppOntapIgroup(object):

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            new_name=dict(required=False, type='str', default=None),
            ostype=dict(required=False, type='str'),
            initiator_group_type=dict(required=False, type='str',
                                      choices=['fcp', 'iscsi', 'mixed']),
            initiator=dict(required=False, type='str'),
            vserver=dict(required=True, type='str'),
            force_remove_initiator=dict(required=False, type='bool', default=False),
            bind_portset=dict(required=False, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        params = self.module.params

        # set up state variables
        self.state = params['state']
        self.name = params['name']
        self.ostype = params['ostype']
        self.initiator_group_type = params['initiator_group_type']
        self.initiator = params['initiator']
        self.vserver = params['vserver']
        self.new_name = params['new_name']
        self.force_remove_initiator = params['force_remove_initiator']
        self.bind_portset = params['bind_portset']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)

    def get_igroup(self):
        """
        Return details about the igroup
        :param:
            name : Name of the igroup

        :return: Details about the igroup. None if not found.
        :rtype: dict
        """
        igroup_info = netapp_utils.zapi.NaElement('igroup-get-iter')
        igroup_attributes = netapp_utils.zapi.NaElement('initiator-group-info')
        igroup_attributes.add_new_child('initiator-group-name', self.name)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(igroup_attributes)
        igroup_info.add_child_elem(query)
        result = self.server.invoke_successfully(igroup_info, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            igroup_attributes = result.get_child_by_name(
                'attributes-list').get_child_by_name(
                    'igroup-attributes')
            return_value = {
                'name': self.name,
            }

        return return_value

    def add_initiator(self):
        """
        Add the initiator.
        """
        options = {'initiator-group-name': self.name}

        if self.initiator is not None:
            options['initiator'] = self.initiator

        igroup_add = netapp_utils.zapi.NaElement.create_node_with_children(
            'igroup-add', **options)

        try:
            self.server.invoke_successfully(igroup_add,
                                            enable_tunneling=True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == "9008":
                # Error 9008 denotes Initiator group already contains initiator
                return False
            else:
                self.module.fail_json(msg='Error adding igroup initiator %s: %s' % (self.name, to_native(error)),
                                      exception=traceback.format_exc())

    def remove_initiator(self):
        """
        Remove the initiator.
        """
        options = {'initiator': self.initiator}

        options['initiator-group-name'] = self.name

        igroup_remove = netapp_utils.zapi.NaElement.create_node_with_children(
            'igroup-remove', **options)

        try:
            self.server.invoke_successfully(igroup_remove,
                                            enable_tunneling=True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == "9007":
                # Error 9007 denotes Initiator group does not contain initiator
                return False
            else:
                self.module.fail_json(msg='Error removing igroup initiator %s: %s' % (self.name, to_native(error)),
                                      exception=traceback.format_exc())

    def create_igroup(self):
        """
        Create the igroup.
        """
        options = {'initiator-group-name': self.name}
        if self.ostype is not None:
            options['os-type'] = self.ostype
        if self.initiator_group_type is not None:
            options['initiator-group-type'] = self.initiator_group_type
        if self.bind_portset is not None:
            options['bind-portset'] = self.bind_portset

        igroup_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'igroup-create', **options)

        try:
            self.server.invoke_successfully(igroup_create,
                                            enable_tunneling=True)
            self.add_initiator()
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error provisioning igroup %s: %s' % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_igroup(self):
        """
        Delete the igroup.
        """
        igroup_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'igroup-destroy', **{'initiator-group-name': self.name, 'force': 'true' if self.force_remove_initiator else 'false'})

        try:
            self.server.invoke_successfully(igroup_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting igroup %s: %s' % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def rename_igroup(self):
        """
        Rename the igroup.
        """
        igroup_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'igroup-rename', **{'initiator-group-name': self.name, 'initiator-group-new-name': str(
                self.new_name)})
        try:
            self.server.invoke_successfully(igroup_rename,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming igroup %s: %s' % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        igroup_exists = False
        rename_igroup = False
        initiator_changed = False
        check = False
        netapp_utils.ems_log_event("na_ontap_igroup", self.server)
        igroup_detail = self.get_igroup()

        if igroup_detail:
            igroup_exists = True
            if self.state == 'absent':
                changed = True

            elif self.state == 'present':
                if self.new_name is not None and self.new_name != self.name:
                    rename_igroup = True
                    changed = True
                if changed:
                    check = True
                if self.initiator:
                    changed = True
        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not igroup_exists:
                        self.create_igroup()
                    else:
                        if self.initiator:
                            initiator_changed = self.add_initiator()
                        if rename_igroup:
                            self.rename_igroup()
                        if (not check) and (not initiator_changed):
                            changed = False

                elif self.state == 'absent':
                    if self.initiator:
                        self.remove_initiator()
                    self.delete_igroup()

        self.module.exit_json(changed=changed)


def main():
    obj = NetAppOntapIgroup()
    obj.apply()


if __name__ == '__main__':
    main()
