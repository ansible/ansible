#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_volume

short_description: Manage NetApp cDOT volumes
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy volumes on NetApp cDOT

options:

  state:
    description:
    - Whether the specified volume should exist or not.
    required: true
    choices: ['present', 'absent']

  name:
    description:
    - The name of the volume to manage.
    required: true

  infinite:
    description:
    - Set True if the volume is an Infinite Volume.
    choices: ['True', 'False']
    default: 'False'

  online:
    description:
    - Whether the specified volume is online, or not.
    choices: ['True', 'False']
    default: 'True'

  aggregate_name:
    description:
    - The name of the aggregate the flexvol should exist on. Required when C(state=present).

  size:
    description:
    - The size of the volume in (size_unit). Required when C(state=present).

  size_unit:
    description:
    - The unit used to interpret the size parameter.
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: 'gb'

  vserver:
    description:
    - Name of the vserver to use.
    required: true
    default: None

'''

EXAMPLES = """

    - name: Create FlexVol
      na_cdot_volume:
        state: present
        name: ansibleVolume
        infinite: False
        aggregate_name: aggr1
        size: 20
        size_unit: mb
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Make FlexVol offline
      na_cdot_volume:
        state: present
        name: ansibleVolume
        infinite: False
        online: False
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


class NetAppCDOTVolume(object):

    def __init__(self):

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

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            is_infinite=dict(required=False, type='bool', default=False, aliases=['infinite']),
            is_online=dict(required=False, type='bool', default=True, aliases=['online']),
            size=dict(type='int'),
            size_unit=dict(default='gb',
                           choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                    'pb', 'eb', 'zb', 'yb'], type='str'),
            aggregate_name=dict(type='str'),
            vserver=dict(required=True, type='str', default=None),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['aggregate_name', 'size'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.is_infinite = p['is_infinite']
        self.is_online = p['is_online']
        self.size_unit = p['size_unit']
        self.vserver = p['vserver']

        if p['size'] is not None:
            self.size = p['size'] * self._size_unit_map[self.size_unit]
        else:
            self.size = None
        self.aggregate_name = p['aggregate_name']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module, vserver=self.vserver)

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
        volume_id_attributes = netapp_utils.zapi.NaElement('volume-id-attributes')
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
            is_online = None
            if current_state == "online":
                is_online = True
            elif current_state == "offline":
                is_online = False
            return_value = {
                'name': self.name,
                'size': current_size,
                'is_online': is_online,
            }

        return return_value

    def create_volume(self):
        volume_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'volume-create', **{'volume': self.name,
                                'containing-aggr-name': self.aggregate_name,
                                'size': str(self.size)})

        try:
            self.server.invoke_successfully(volume_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error provisioning volume %s of size %s: %s' % (self.name, self.size, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_volume(self):
        if self.is_infinite:
            volume_delete = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-destroy-async', **{'volume-name': self.name})
        else:
            volume_delete = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-destroy', **{'name': self.name, 'unmount-and-offline':
                                     'true'})

        try:
            self.server.invoke_successfully(volume_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error deleting volume %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def rename_volume(self):
        """
        Rename the volume.

        Note: 'is_infinite' needs to be set to True in order to rename an
        Infinite Volume.
        """
        if self.is_infinite:
            volume_rename = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-rename-async',
                **{'volume-name': self.name, 'new-volume-name': str(
                    self.name)})
        else:
            volume_rename = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-rename', **{'volume': self.name, 'new-volume-name': str(
                    self.name)})
        try:
            self.server.invoke_successfully(volume_rename,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error renaming volume %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def resize_volume(self):
        """
        Re-size the volume.

        Note: 'is_infinite' needs to be set to True in order to rename an
        Infinite Volume.
        """
        if self.is_infinite:
            volume_resize = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-size-async',
                **{'volume-name': self.name, 'new-size': str(
                    self.size)})
        else:
            volume_resize = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-size', **{'volume': self.name, 'new-size': str(
                    self.size)})
        try:
            self.server.invoke_successfully(volume_resize,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error re-sizing volume %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def change_volume_state(self):
        """
        Change volume's state (offline/online).

        Note: 'is_infinite' needs to be set to True in order to change the
        state of an Infinite Volume.
        """
        state_requested = None
        if self.is_online:
            # Requested state is 'online'.
            state_requested = "online"
            if self.is_infinite:
                volume_change_state = netapp_utils.zapi.NaElement.create_node_with_children(
                    'volume-online-async',
                    **{'volume-name': self.name})
            else:
                volume_change_state = netapp_utils.zapi.NaElement.create_node_with_children(
                    'volume-online',
                    **{'name': self.name})
        else:
            # Requested state is 'offline'.
            state_requested = "offline"
            if self.is_infinite:
                volume_change_state = netapp_utils.zapi.NaElement.create_node_with_children(
                    'volume-offline-async',
                    **{'volume-name': self.name})
            else:
                volume_change_state = netapp_utils.zapi.NaElement.create_node_with_children(
                    'volume-offline',
                    **{'name': self.name})
        try:
            self.server.invoke_successfully(volume_change_state,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error changing the state of volume %s to %s: %s' %
                                  (self.name, state_requested, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        volume_exists = False
        rename_volume = False
        resize_volume = False
        volume_detail = self.get_volume()

        if volume_detail:
            volume_exists = True

            if self.state == 'absent':
                changed = True

            elif self.state == 'present':
                if str(volume_detail['size']) != str(self.size):
                    resize_volume = True
                    changed = True
                if (volume_detail['is_online'] is not None) and (volume_detail['is_online'] != self.is_online):
                    changed = True
                    if self.is_online is False:
                        # Volume is online, but requested state is offline
                        pass
                    else:
                        # Volume is offline but requested state is online
                        pass

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
                        if volume_detail['is_online'] is not \
                                None and volume_detail['is_online'] != \
                                self.is_online:
                            self.change_volume_state()
                        # Ensure re-naming is the last change made.
                        if rename_volume:
                            self.rename_volume()

                elif self.state == 'absent':
                    self.delete_volume()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTVolume()
    v.apply()

if __name__ == '__main__':
    main()
