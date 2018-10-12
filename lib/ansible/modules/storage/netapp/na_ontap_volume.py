#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_volume

short_description: NetApp ONTAP manage volumes.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (ng-ansibleteam@netapp.com)

description:
- Create or destroy or modify volumes on NetApp ONTAP.

options:

  state:
    description:
    - Whether the specified volume should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  name:
    description:
    - The name of the volume to manage.
    required: true

  vserver:
    description:
    - Name of the vserver to use.
    required: true

  from_name:
    description:
    - Name of the existing volume to be renamed to name.
    version_added: '2.7'

  is_infinite:
    type: bool
    description:
      Set True if the volume is an Infinite Volume.
      Deleting an infinite volume is asynchronous.

  is_online:
    type: bool
    description:
    - Whether the specified volume is online, or not.
    default: True

  aggregate_name:
    description:
    - The name of the aggregate the flexvol should exist on.
    - Required when C(state=present).

  size:
    description:
    - The size of the volume in (size_unit). Required when C(state=present).

  size_unit:
    description:
    - The unit used to interpret the size parameter.
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: gb

  type:
    description:
    - The volume type, either read-write (RW) or data-protection (DP).

  policy:
    description:
    - Name of the export policy.

  junction_path:
    description:
    - Junction path of the volume.

  space_guarantee:
    description:
    - Space guarantee style for the volume.
    choices: ['none', 'volume']

  percent_snapshot_space:
    description:
    - Amount of space reserved for snapshot copies of the volume.

  volume_security_style:
    description:
    - The security style associated with this volume.
    choices: ['mixed', 'ntfs', 'unified', 'unix']
    default: 'mixed'

  encrypt:
    type: bool
    description:
    - Whether or not to enable Volume Encryption.
    default: False
    version_added: '2.7'

  efficiency_policy:
    description:
    - Allows a storage efficiency policy to be set on volume creation.
    version_added: '2.7'

'''

EXAMPLES = """

    - name: Create FlexVol
      na_ontap_volume:
        state: present
        name: ansibleVolume
        is_infinite: False
        aggregate_name: aggr1
        size: 20
        size_unit: mb
        junction_path: /ansibleVolume11
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Make FlexVol offline
      na_ontap_volume:
        state: present
        name: ansibleVolume
        is_infinite: False
        is_online: False
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

"""

RETURN = """
"""

import traceback

import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapVolume(object):
    '''Class with volume operations'''

    def __init__(self):
        '''Initialize module parameters'''
        self._size_unit_map = dict(
            bytes=1,
            b=1,
            kb=1024,
            mb=1024 ** 2,
            gb=1024 ** 3,
            tb=1024 ** 4,
            pb=1024 ** 5,
            eb=1024 ** 6,
            zb=1024 ** 7,
            yb=1024 ** 8
        )

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            vserver=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
            is_infinite=dict(required=False, type='bool',
                             default=False),
            is_online=dict(required=False, type='bool',
                           default=True),
            size=dict(type='int', default=None),
            size_unit=dict(default='gb',
                           choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                    'pb', 'eb', 'zb', 'yb'], type='str'),
            aggregate_name=dict(type='str', default=None),
            type=dict(type='str', default=None),
            policy=dict(type='str', default=None),
            junction_path=dict(type='str', default=None),
            space_guarantee=dict(choices=['none', 'volume'], default=None),
            percent_snapshot_space=dict(type='str', default=None),
            volume_security_style=dict(choices=['mixed',
                                                'ntfs', 'unified', 'unix'],
                                       default='mixed'),
            encrypt=dict(required=False, type='bool', default=False),
            efficiency_policy=dict(required=False, type='str'),
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if self.parameters.get('size'):
            self.parameters['size'] = self.parameters['size'] * \
                self._size_unit_map[self.parameters['size_unit']]
        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.parameters['vserver'])
            self.cluster = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def volume_get_iter(self, vol_name=None):
        """
        Return volume-get-iter query results
        :param vol_name: name of the volume
        :return: NaElement
        """
        volume_info = netapp_utils.zapi.NaElement('volume-get-iter')
        volume_attributes = netapp_utils.zapi.NaElement('volume-attributes')
        volume_id_attributes = netapp_utils.zapi.NaElement('volume-id-attributes')
        volume_id_attributes.add_new_child('name', vol_name)
        volume_attributes.add_child_elem(volume_id_attributes)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(volume_attributes)
        volume_info.add_child_elem(query)

        try:
            result = self.server.invoke_successfully(volume_info, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching volume %s : %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        return result

    def get_volume(self, vol_name=None):
        """
        Return details about the volume
        :param:
            name : Name of the volume

        :return: Details about the volume. None if not found.
        :rtype: dict
        """
        if vol_name is None:
            vol_name = self.parameters['name']
        volume_get_iter = self.volume_get_iter(vol_name)
        return_value = None
        if volume_get_iter.get_child_by_name('num-records') and \
                int(volume_get_iter.get_child_content('num-records')) > 0:

            volume_attributes = volume_get_iter.get_child_by_name(
                'attributes-list').get_child_by_name(
                    'volume-attributes')
            # Get volume's current size
            volume_space_attributes = volume_attributes.get_child_by_name(
                'volume-space-attributes')
            current_size = int(volume_space_attributes.get_child_content('size'))

            # Get volume's state (online/offline)
            volume_state_attributes = volume_attributes.get_child_by_name(
                'volume-state-attributes')
            current_state = volume_state_attributes.get_child_content('state')
            volume_id_attributes = volume_attributes.get_child_by_name(
                'volume-id-attributes')
            aggregate_name = volume_id_attributes.get_child_content(
                'containing-aggregate-name')
            volume_export_attributes = volume_attributes.get_child_by_name(
                'volume-export-attributes')
            policy = volume_export_attributes.get_child_content('policy')
            space_guarantee = volume_space_attributes.get_child_content(
                'space-guarantee')

            is_online = (current_state == "online")
            return_value = {
                'name': vol_name,
                'size': current_size,
                'is_online': is_online,
                'aggregate_name': aggregate_name,
                'policy': policy,
                'space_guarantee': space_guarantee,
            }

        return return_value

    def create_volume(self):
        '''Create ONTAP volume'''
        if self.parameters.get('aggregate_name') is None:
            self.module.fail_json(msg='Error provisioning volume %s: \
                                  aggregate_name is required'
                                  % self.parameters['name'])
        options = {'volume': self.parameters['name'],
                   'containing-aggr-name': self.parameters['aggregate_name'],
                   'size': str(self.parameters['size'])}
        if self.parameters.get('percent_snapshot_space'):
            options['percentage-snapshot-reserve'] = self.parameters['percent_snapshot_space']
        if self.parameters.get('type'):
            options['volume-type'] = self.parameters['type']
        if self.parameters.get('policy'):
            options['export-policy'] = self.parameters['policy']
        if self.parameters.get('junction_path'):
            options['junction-path'] = self.parameters['junction_path']
        if self.parameters.get('space_guarantee'):
            options['space-reserve'] = self.parameters['space_guarantee']
        if self.parameters.get('volume_security_style'):
            options['volume-security-style'] = self.parameters['volume_security_style']
        volume_create = netapp_utils.zapi.NaElement.create_node_with_children('volume-create', **options)
        try:
            self.server.invoke_successfully(volume_create,
                                            enable_tunneling=True)
            self.ems_log_event("volume-create")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error provisioning volume %s \
                                  of size %s: %s'
                                  % (self.parameters['name'], self.parameters['size'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_volume(self):
        '''Delete ONTAP volume'''
        if self.parameters.get('is_infinite'):
            volume_delete = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-destroy-async', **{'volume-name': self.parameters['name']})
        else:
            volume_delete = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-destroy', **{'name': self.parameters['name'],
                                         'unmount-and-offline': 'true'})
        try:
            self.server.invoke_successfully(volume_delete, enable_tunneling=True)
            self.ems_log_event("delete")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting volume %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def move_volume(self):
        '''Move volume from source aggregate to destination aggregate'''
        volume_move = netapp_utils.zapi.NaElement.create_node_with_children(
            'volume-move-start', **{'source-volume': self.parameters['name'],
                                    'vserver': self.parameters['vserver'],
                                    'dest-aggr': self.parameters['aggregate_name']})
        try:
            self.cluster.invoke_successfully(volume_move,
                                             enable_tunneling=True)
            self.ems_log_event("volume-move")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error moving volume %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def rename_volume(self):
        """
        Rename the volume.

        Note: 'is_infinite' needs to be set to True in order to rename an
        Infinite Volume.
        """
        vol_rename_zapi, vol_name_zapi = ['volume-rename-async', 'volume-name'] if self.parameters['is_infinite']\
            else ['volume-rename', 'volume']
        volume_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            vol_rename_zapi, **{vol_name_zapi: self.parameters['from_name'],
                                'new-volume-name': str(self.parameters['name'])})
        try:
            self.server.invoke_successfully(volume_rename,
                                            enable_tunneling=True)
            self.ems_log_event("volume-rename")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming volume %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def resize_volume(self):
        """
        Re-size the volume.

        Note: 'is_infinite' needs to be set to True in order to rename an
        Infinite Volume.
        """
        vol_size_zapi, vol_name_zapi = ['volume-size-async', 'volume-name'] if self.parameters['is_infinite']\
            else ['volume-size', 'volume']
        volume_resize = netapp_utils.zapi.NaElement.create_node_with_children(
            vol_size_zapi, **{vol_name_zapi: self.parameters['name'],
                              'new-size': str(self.parameters['size'])})
        try:
            self.server.invoke_successfully(volume_resize, enable_tunneling=True)
            self.ems_log_event("volume-resize")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error re-sizing volume %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def change_volume_state(self):
        """
        Change volume's state (offline/online).
        """
        if self.parameters['is_online']:    # Desired state is online, setup zapi APIs respectively
            vol_state_zapi, vol_name_zapi = ['volume-online-async', 'volume-name'] if self.parameters['is_infinite']\
                else ['volume-online', 'name']
        else:   # Desired state is offline, setup zapi APIs respectively
            vol_state_zapi, vol_name_zapi = ['volume-offline-async', 'volume-name'] if self.parameters['is_infinite']\
                else ['volume-offline', 'name']
            volume_unmount = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-unmount', **{'volume-name': self.parameters['name']})
        volume_change_state = netapp_utils.zapi.NaElement.create_node_with_children(
            vol_state_zapi, **{vol_name_zapi: self.parameters['name']})
        try:
            if not self.parameters['is_online']:  # Unmount before offline
                self.server.invoke_successfully(volume_unmount, enable_tunneling=True)
            self.server.invoke_successfully(volume_change_state, enable_tunneling=True)
            self.ems_log_event("change-state")
        except netapp_utils.zapi.NaApiError as error:
            state = "online" if self.parameters['is_online'] else "offline"
            self.module.fail_json(msg='Error changing the state of volume %s to %s: %s'
                                  % (self.parameters['name'], state, to_native(error)),
                                  exception=traceback.format_exc())

    def volume_modify_policy_space(self):
        """
        modify volume parameter 'policy' or 'space_guarantee'
        """
        # TODO: refactor this method
        vol_mod_iter = netapp_utils.zapi.NaElement('volume-modify-iter')
        attributes = netapp_utils.zapi.NaElement('attributes')
        vol_mod_attributes = netapp_utils.zapi.NaElement('volume-attributes')
        if self.parameters.get('policy'):
            vol_export_attributes = netapp_utils.zapi.NaElement(
                'volume-export-attributes')
            vol_export_attributes.add_new_child('policy', self.parameters['policy'])
            vol_mod_attributes.add_child_elem(vol_export_attributes)
        if self.parameters.get('space_guarantee'):
            vol_space_attributes = netapp_utils.zapi.NaElement(
                'volume-space-attributes')
            vol_space_attributes.add_new_child(
                'space-guarantee', self.parameters['space_guarantee'])
            vol_mod_attributes.add_child_elem(vol_space_attributes)
        attributes.add_child_elem(vol_mod_attributes)
        query = netapp_utils.zapi.NaElement('query')
        vol_query_attributes = netapp_utils.zapi.NaElement('volume-attributes')
        vol_id_attributes = netapp_utils.zapi.NaElement('volume-id-attributes')
        vol_id_attributes.add_new_child('name', self.parameters['name'])
        vol_query_attributes.add_child_elem(vol_id_attributes)
        query.add_child_elem(vol_query_attributes)
        vol_mod_iter.add_child_elem(attributes)
        vol_mod_iter.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(vol_mod_iter, enable_tunneling=True)
            failures = result.get_child_by_name('failure-list')
            # handle error if modify space or policy parameter fails
            if failures is not None and failures.get_child_by_name('volume-modify-iter-info') is not None:
                error_msg = failures.get_child_by_name('volume-modify-iter-info').get_child_content('error-message')
                self.module.fail_json(msg="Error modifying volume %s: %s"
                                      % (self.parameters['name'], error_msg),
                                      exception=traceback.format_exc())
            self.ems_log_event("volume-modify")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying volume %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_volume(self, modify):
        for attribute in modify.keys():
            if attribute == 'size':
                self.resize_volume()
            elif attribute == 'is_online':
                self.change_volume_state()
            elif attribute == 'aggregate_name':
                self.move_volume()
            else:
                self.volume_modify_policy_space()

    def apply(self):
        '''Call create/modify/delete operations'''
        current = self.get_volume()
        # rename and create are mutually exclusive
        rename, cd_action = None, None
        if self.parameters.get('from_name'):
            rename = self.na_helper.is_rename_action(self.get_volume(self.parameters['from_name']), current)
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_volume()
                if cd_action == 'create':
                    self.create_volume()
                elif cd_action == 'delete':
                    self.delete_volume()
                elif modify:
                    self.modify_volume(modify)
        self.module.exit_json(changed=self.na_helper.changed)

    def ems_log_event(self, state):
        '''Autosupport log event'''
        if state == 'create':
            message = "A Volume has been created, size: " + \
                str(self.parameters['size']) + str(self.parameters['size_unit'])
        elif state == 'delete':
            message = "A Volume has been deleted"
        elif state == 'move':
            message = "A Volume has been moved"
        elif state == 'rename':
            message = "A Volume has been renamed"
        elif state == 'resize':
            message = "A Volume has been resized to: " + \
                str(self.parameters['size']) + str(self.parameters['size_unit'])
        elif state == 'change':
            message = "A Volume state has been changed"
        else:
            message = "na_ontap_volume has been called"
        netapp_utils.ems_log_event(
            "na_ontap_volume", self.server, event=message)


def main():
    '''Apply volume operations from playbook'''
    obj = NetAppOntapVolume()
    obj.apply()


if __name__ == '__main__':
    main()
