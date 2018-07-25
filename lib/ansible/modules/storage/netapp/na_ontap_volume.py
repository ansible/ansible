#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_ontap_volume

short_description: Manage NetApp ONTAP volumes.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author:
- Sumit Kumar (sumit4@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)

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

  new_name:
    description:
    - New name of the volume to be renamed.

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
            new_name=dict(required=False, type='str'),
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
                                       default='mixed')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.name = parameters['name']
        self.new_name = parameters['new_name']
        self.is_infinite = parameters['is_infinite']
        self.is_online = parameters['is_online']
        self.size_unit = parameters['size_unit']
        self.vserver = parameters['vserver']
        self.type = parameters['type']
        self.policy = parameters['policy']
        self.junction_path = parameters['junction_path']
        self.space_guarantee = parameters['space_guarantee']
        self.percent_snapshot_space = parameters['percent_snapshot_space']
        self.aggregate_name = parameters['aggregate_name']
        self.volume_security_style = parameters['volume_security_style']

        if parameters['size'] is not None:
            self.size = parameters['size'] * \
                self._size_unit_map[self.size_unit]
        else:
            self.size = None

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)
            self.cluster = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_volume(self):
        """
        Return details about the volume
        :param:
            name : Name of the volume

        :return: Details about the volume. None if not found.
        :rtype: dict
        """
        volume_info = netapp_utils.zapi.NaElement('volume-get-iter')
        volume_attributes = netapp_utils.zapi.NaElement('volume-attributes')
        volume_id_attributes = netapp_utils.zapi.NaElement(
            'volume-id-attributes')
        volume_id_attributes.add_new_child('name', self.name)
        volume_attributes.add_child_elem(volume_id_attributes)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(volume_attributes)

        volume_info.add_child_elem(query)

        result = self.server.invoke_successfully(volume_info, True)

        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            volume_attributes = result.get_child_by_name(
                'attributes-list').get_child_by_name(
                    'volume-attributes')
            # Get volume's current size
            volume_space_attributes = volume_attributes.get_child_by_name(
                'volume-space-attributes')
            current_size = volume_space_attributes.get_child_content('size')

            # Get volume's state (online/offline)
            volume_state_attributes = volume_attributes.get_child_by_name(
                'volume-state-attributes')
            current_state = volume_state_attributes.get_child_content('state')
            volume_id_attributes = volume_attributes.get_child_by_name(
                'volume-id-attributes')
            aggregate_name = volume_id_attributes.get_child_content(
                'containing-aggregate-name')
            junction_path = volume_id_attributes.get_child_content(
                'junction-path')
            volume_type = volume_id_attributes.get_child_content('type')
            volume_export_attributes = volume_attributes.get_child_by_name(
                'volume-export-attributes')
            policy = volume_export_attributes.get_child_content('policy')
            space_guarantee = volume_space_attributes.get_child_content(
                'space-guarantee')
            percent_snapshot_space = volume_space_attributes.get_child_by_name(
                'percentage-snapshot-reserve')

            is_online = None
            if current_state == "online":
                is_online = True
            elif current_state == "offline":
                is_online = False
            return_value = {
                'name': self.name,
                'size': current_size,
                'is_online': is_online,
                'aggregate_name': aggregate_name,
                'policy': policy,
                'space_guarantee': space_guarantee,
                'percent_snapshot_space': percent_snapshot_space,
                'type': volume_type,
                'junction_path': junction_path

            }

        return return_value

    def create_volume(self):
        '''Create ONTAP volume'''
        if self.aggregate_name is None:
            self.module.fail_json(msg='Error provisioning volume %s: \
                                  aggregate_name is required'
                                  % self.name)
        options = {'volume': self.name,
                   'containing-aggr-name': self.aggregate_name,
                   'size': str(self.size)}
        if self.percent_snapshot_space is not None:
            options['percentage-snapshot-reserve'] = self.percent_snapshot_space
        if self.type is not None:
            options['volume-type'] = self.type
        if self.policy is not None:
            options['export-policy'] = self.policy
        if self.junction_path is not None:
            options['junction-path'] = self.junction_path
        if self.space_guarantee is not None:
            options['space-reserve'] = self.space_guarantee
        if self.volume_security_style is not None:
            options['volume-security-style'] = self.volume_security_style

        volume_create = netapp_utils.zapi\
            .NaElement.create_node_with_children(
                'volume-create', **options)
        try:
            self.server.invoke_successfully(volume_create,
                                            enable_tunneling=True)
            self.ems_log_event("create")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error provisioning volume %s \
                                  of size %s: %s'
                                  % (self.name, self.size, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_volume(self):
        '''Delete ONTAP volume'''
        if self.is_infinite:
            volume_delete = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-destroy-async', **{'volume-name': self.name})
        else:
            volume_delete = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-destroy', **{'name': self.name,
                                         'unmount-and-offline': 'true'})
        try:
            self.server.invoke_successfully(volume_delete,
                                            enable_tunneling=True)
            self.ems_log_event("delete")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting volume %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def move_volume(self):
        '''Move volume from source aggregate to destination aggregate'''
        volume_move = netapp_utils.zapi\
            .NaElement.create_node_with_children(
                'volume-move-start', **{'source-volume': self.name,
                                        'vserver': self.vserver,
                                        'dest-aggr': self.aggregate_name})
        try:
            self.cluster.invoke_successfully(volume_move,
                                             enable_tunneling=True)
            self.ems_log_event("move")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error moving volume %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def rename_volume(self):
        """
        Rename the volume.

        Note: 'is_infinite' needs to be set to True in order to rename an
        Infinite Volume.
        """
        if self.is_infinite:
            volume_rename = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-rename-async',
                    **{'volume-name': self.name, 'new-volume-name': str(
                        self.new_name)})
        else:
            volume_rename = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-rename', **{'volume': self.name,
                                        'new-volume-name': str(self.new_name)})
        try:
            self.server.invoke_successfully(volume_rename,
                                            enable_tunneling=True)
            self.ems_log_event("rename")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming volume %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def resize_volume(self):
        """
        Re-size the volume.

        Note: 'is_infinite' needs to be set to True in order to rename an
        Infinite Volume.
        """
        if self.is_infinite:
            volume_resize = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-size-async',
                    **{'volume-name': self.name, 'new-size': str(
                        self.size)})
        else:
            volume_resize = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-size', **{'volume': self.name, 'new-size': str(
                        self.size)})
        try:
            self.server.invoke_successfully(volume_resize,
                                            enable_tunneling=True)
            self.ems_log_event("resize")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error re-sizing volume %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def change_volume_state(self):
        """
        Change volume's state (offline/online).

        """
        state_requested = None
        if self.is_online:
            # Requested state is 'online'.
            state_requested = "online"
            if self.is_infinite:
                volume_change_state = netapp_utils.zapi\
                    .NaElement.create_node_with_children(
                        'volume-online-async',
                        **{'volume-name': self.name})
            else:
                volume_change_state = netapp_utils.zapi\
                    .NaElement.create_node_with_children(
                        'volume-online',
                        **{'name': self.name})
        else:
            # Requested state is 'offline'.
            state_requested = "offline"
            volume_unmount = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-unmount', **{'volume-name': self.name})
            if self.is_infinite:
                volume_change_state = netapp_utils.zapi\
                    .NaElement.create_node_with_children(
                        'volume-offline-async',
                        **{'volume-name': self.name})
            else:
                volume_change_state = netapp_utils.zapi\
                    .NaElement.create_node_with_children(
                        'volume-offline',
                        **{'name': self.name})
        try:
            if state_requested == "offline":
                self.server.invoke_successfully(volume_unmount,
                                                enable_tunneling=True)
            self.server.invoke_successfully(volume_change_state,
                                            enable_tunneling=True)
            self.ems_log_event("change")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error changing the state of \
                                  volume %s to %s: %s'
                                  % (self.name, state_requested,
                                     to_native(error)),
                                  exception=traceback.format_exc())

    def volume_modify(self):
        """
        modify volume parameter 'policy'
        """
        vol_mod_iter = netapp_utils.zapi.NaElement('volume-modify-iter')
        attributes = netapp_utils.zapi.NaElement('attributes')
        vol_mod_attributes = netapp_utils.zapi.NaElement('volume-attributes')
        if self.policy is not None:
            vol_export_attributes = netapp_utils.zapi.NaElement(
                'volume-export-attributes')
            vol_export_attributes.add_new_child('policy', self.policy)
            vol_mod_attributes.add_child_elem(vol_export_attributes)
        if self.space_guarantee is not None:
            vol_space_attributes = netapp_utils.zapi.NaElement(
                'volume-space-attributes')
            vol_space_attributes.add_new_child(
                'space-guarantee', self.space_guarantee)
            vol_mod_attributes.add_child_elem(vol_space_attributes)
        attributes.add_child_elem(vol_mod_attributes)
        query = netapp_utils.zapi.NaElement('query')
        vol_query_attributes = netapp_utils.zapi.NaElement('volume-attributes')
        vol_id_attributes = netapp_utils.zapi.NaElement('volume-id-attributes')
        vol_id_attributes.add_new_child('name', self.name)
        vol_query_attributes.add_child_elem(vol_id_attributes)
        query.add_child_elem(vol_query_attributes)
        vol_mod_iter.add_child_elem(attributes)
        vol_mod_iter.add_child_elem(query)

        try:
            self.server.invoke_successfully(vol_mod_iter,
                                            enable_tunneling=True)
            self.ems_log_event("modify")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying volume %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Call create/modify/delete operations'''
        changed = False
        volume_exists = False
        rename_volume = False
        resize_volume = False
        move_volume = False
        modify_volume = False
        state_change = False
        volume_detail = self.get_volume()
        if volume_detail:
            volume_exists = True

            if self.state == 'absent':
                changed = True
            elif self.state == 'present':
                if self.aggregate_name is not None and \
                        volume_detail['aggregate_name'] != self.aggregate_name:
                    move_volume = True
                    changed = True
                if self.size is not None and \
                        str(volume_detail['size']) != str(self.size):
                    resize_volume = True
                    changed = True
                if (volume_detail['is_online'] is not None) and \
                        (volume_detail['is_online'] != self.is_online):
                    state_change = True
                    changed = True
                if self.new_name is not None and \
                        self.name != self.new_name:
                    rename_volume = True
                    changed = True
                if self.policy is not None and \
                        self.policy != volume_detail['policy']:
                    modify_volume = True
                    changed = True
                if self.space_guarantee is not None and \
                        self.space_guarantee != volume_detail['space_guarantee']:
                    modify_volume = True
                    changed = True
        else:
            if self.state == 'present':
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not volume_exists:
                        self.create_volume()
                    else:
                        if resize_volume:
                            self.resize_volume()
                        if state_change:
                            self.change_volume_state()
                        if modify_volume:
                            self.volume_modify()
                        # Ensure re-naming is the last change made.
                        if rename_volume:
                            self.rename_volume()
                        # Ensure volume move  is the very last change made.
                        if move_volume:
                            self.move_volume()

                elif self.state == 'absent':
                    self.delete_volume()

        self.module.exit_json(changed=changed)

    def ems_log_event(self, state):
        '''Autosupport log event'''
        if state == 'create':
            message = "A Volume has been created, size: " + \
                str(self.size) + str(self.size_unit)
        elif state == 'delete':
            message = "A Volume has been deleted"
        elif state == 'move':
            message = "A Volume has been moved"
        elif state == 'rename':
            message = "A Volume has been renamed"
        elif state == 'resize':
            message = "A Volume has been resized to: " + \
                str(self.size) + str(self.size_unit)
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
