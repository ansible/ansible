#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
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
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

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
    - To unmount, use junction path C('').

  space_guarantee:
    description:
    - Space guarantee style for the volume.
    choices: ['none', 'file', 'volume']

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

  unix_permissions:
    description:
    - Unix permission bits in octal or symbolic format.
    - For example, 0 is equivalent to ------------, 777 is equivalent to ---rwxrwxrwx,both formats are accepted.
    - The valid octal value ranges between 0 and 777 inclusive.
    version_added: '2.8'

  snapshot_policy:
    description:
    - The name of the snapshot policy.
    - the default policy name is 'default'.
    version_added: '2.8'

  aggr_list:
    description:
    -  an array of names of aggregates to be used for FlexGroup constituents.
    version_added: '2.8'

  aggr_list_multiplier:
    description:
    -  The number of times to iterate over the aggregates listed with the aggr_list parameter when creating a FlexGroup.
    version_added: '2.8'

  auto_provision_as:
    description:
    - Automatically provision a FlexGroup volume.
    version_added: '2.8'
    choices: ['flexgroup']

  snapdir_access:
    description:
    - This is an advanced option, the default is False.
    - Enable the visible '.snapshot' directory that is normally present at system internal mount points.
    - This value also turns on access to all other '.snapshot' directories in the volume.
    type: bool
    version_added: '2.8'

  atime_update:
    description:
    - This is an advanced option, the default is True.
    - If false, prevent the update of inode access times when a file is read.
    - This value is useful for volumes with extremely high read traffic,
      since it prevents writes to the inode file for the volume from contending with reads from other files.
    - This field should be used carefully.
    - That is, use this field when you know in advance that the correct access time for inodes will not be needed for files on that volume.
    type: bool
    version_added: '2.8'

  wait_for_completion:
    description:
    - Set this parameter to 'true' for synchronous execution during create (wait until volume status is online)
    - Set this parameter to 'false' for asynchronous execution
    - For asynchronous, execution exits as soon as the request is sent, without checking volume status
    type: bool
    default: false
    version_added: '2.8'

  time_out:
    description:
    - time to wait for flexGroup creation, modification, or deletion in seconds.
    - Error out if task is not completed in defined time.
    - if 0, the request is asynchronous.
    - default is set to 3 minutes.
    default: 180
    version_added: '2.8'

  language:
    description:
    - Language to use for Volume
    - Default uses SVM language
    - Possible values   Language
    - c                 POSIX
    - ar                Arabic
    - cs                Czech
    - da                Danish
    - de                German
    - en                English
    - en_us             English (US)
    - es                Spanish
    - fi                Finnish
    - fr                French
    - he                Hebrew
    - hr                Croatian
    - hu                Hungarian
    - it                Italian
    - ja                Japanese euc-j
    - ja_v1             Japanese euc-j
    - ja_jp.pck         Japanese PCK (sjis)
    - ja_jp.932         Japanese cp932
    - ja_jp.pck_v2      Japanese PCK (sjis)
    - ko                Korean
    - no                Norwegian
    - nl                Dutch
    - pl                Polish
    - pt                Portuguese
    - ro                Romanian
    - ru                Russian
    - sk                Slovak
    - sl                Slovenian
    - sv                Swedish
    - tr                Turkish
    - zh                Simplified Chinese
    - zh.gbk            Simplified Chinese (GBK)
    - zh_tw             Traditional Chinese euc-tw
    - zh_tw.big5        Traditional Chinese Big 5
    - To use UTF-8 as the NFS character set, append '.UTF-8' to the language code
    version_added: '2.8'
'''

EXAMPLES = """

    - name: Create FlexVol
      na_ontap_volume:
        state: present
        name: ansibleVolume12
        is_infinite: False
        aggregate_name: ansible_aggr
        size: 100
        size_unit: mb
        space_guarantee: none
        policy: default
        percent_snapshot_space: 60
        vserver: ansibleVServer
        wait_for_completion: True
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Volume Delete
      na_ontap_volume:
        state: absent
        name: ansibleVolume12
        aggregate_name: ansible_aggr
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

    - name: Create flexGroup volume manually
      na_ontap_volume:
        state: present
        name: ansibleVolume
        is_infinite: False
        aggr_list: "{{ aggr_list }}"
        aggr_list_multiplier: 2
        size: 200
        size_unit: mb
        space_guarantee: none
        policy: default
        vserver: "{{ vserver }}"
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        https: False
        unix_permissions: 777
        snapshot_policy: default
        time_out: 0

    - name: Create flexGroup volume auto provision as flex group
      na_ontap_volume:
        state: present
        name: ansibleVolume
        is_infinite: False
        auto_provision_as: flexgroup
        size: 200
        size_unit: mb
        space_guarantee: none
        policy: default
        vserver: "{{ vserver }}"
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        https: False
        unix_permissions: 777
        snapshot_policy: default
        time_out: 0

"""

RETURN = """
"""

import time
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
            space_guarantee=dict(choices=['none', 'file', 'volume'], default=None),
            percent_snapshot_space=dict(type='int', default=None),
            volume_security_style=dict(choices=['mixed',
                                                'ntfs', 'unified', 'unix'],
                                       default='mixed'),
            encrypt=dict(required=False, type='bool', default=False),
            efficiency_policy=dict(required=False, type='str'),
            unix_permissions=dict(required=False, type='str'),
            snapshot_policy=dict(required=False, type='str'),
            aggr_list=dict(required=False, type='list'),
            aggr_list_multiplier=dict(required=False, type='int'),
            snapdir_access=dict(required=False, type='bool'),
            atime_update=dict(required=False, type='bool'),
            auto_provision_as=dict(choices=['flexgroup'], required=False, type='str'),
            wait_for_completion=dict(required=False, type='bool', default=False),
            time_out=dict(required=False, type='int', default=180),
            language=dict(type='str', required=False)
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.volume_style = None

        if self.parameters.get('size'):
            self.parameters['size'] = self.parameters['size'] * \
                self._size_unit_map[self.parameters['size_unit']]
        # ONTAP will return True and False as the string true and false.
        if 'snapdir_access' in self.parameters:
            self.parameters['snapdir_access'] = str(self.parameters['snapdir_access']).lower()
        if 'atime_update' in self.parameters:
            self.parameters['atime_update'] = str(self.parameters['atime_update']).lower()
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

            volume_attributes = volume_get_iter['attributes-list']['volume-attributes']
            volume_space_attributes = volume_attributes['volume-space-attributes']
            volume_state_attributes = volume_attributes['volume-state-attributes']
            volume_id_attributes = volume_attributes['volume-id-attributes']
            volume_export_attributes = volume_attributes['volume-export-attributes']
            volume_security_unix_attributes = volume_attributes['volume-security-attributes']['volume-security-unix-attributes']
            volume_snapshot_attributes = volume_attributes['volume-snapshot-attributes']
            volume_performance_attributes = volume_attributes['volume-performance-attributes']
            # Get volume's state (online/offline)
            current_state = volume_state_attributes['state']
            is_online = (current_state == "online")

            return_value = {
                'name': vol_name,
                'size': int(volume_space_attributes['size']),
                'is_online': is_online,
                'policy': volume_export_attributes['policy'],
                'unix_permissions': volume_security_unix_attributes['permissions'],
                'snapshot_policy': volume_snapshot_attributes['snapshot-policy']

            }
            if volume_space_attributes.get_child_by_name('percentage-snapshot-reserve'):
                return_value['percent_snapshot_space'] = volume_space_attributes['percentage-snapshot-reserve']
            if volume_id_attributes.get_child_by_name('containing-aggregate-name'):
                return_value['aggregate_name'] = volume_id_attributes['containing-aggregate-name']
            else:
                return_value['aggregate_name'] = None
            if volume_id_attributes.get_child_by_name('junction-path'):
                return_value['junction_path'] = volume_id_attributes['junction-path']
            else:
                return_value['junction_path'] = ''
            if volume_id_attributes.get_child_by_name('style-extended'):
                return_value['style_extended'] = volume_id_attributes['style-extended']
            else:
                return_value['style_extended'] = None
            if volume_space_attributes.get_child_by_name('space-guarantee'):
                return_value['space_guarantee'] = volume_space_attributes['space-guarantee']
            else:
                return_value['space_guarantee'] = None
            if volume_snapshot_attributes.get_child_by_name('snapdir-access-enabled'):
                return_value['snapdir_access'] = volume_snapshot_attributes['snapdir-access-enabled']
            else:
                return_value['snapdir_access'] = None
            if volume_performance_attributes.get_child_by_name('is-atime-update-enabled'):
                return_value['atime_update'] = volume_performance_attributes['is-atime-update-enabled']
            else:
                return_value['atime_update'] = None

        return return_value

    def create_volume(self):
        '''Create ONTAP volume'''
        if self.volume_style == 'flexGroup':
            self.create_volume_async()
        else:
            options = self.create_volume_options()
            volume_create = netapp_utils.zapi.NaElement.create_node_with_children('volume-create', **options)
            try:
                self.server.invoke_successfully(volume_create, enable_tunneling=True)
                if self.parameters.get('wait_for_completion'):
                    # round off time_out
                    retries = (self.parameters['time_out'] + 5) // 10
                    current = self.get_volume()
                    is_online = None if current is None else current['is_online']
                    while not is_online and retries > 0:
                        time.sleep(10)
                        retries = retries - 1
                        current = self.get_volume()
                        is_online = None if current is None else current['is_online']
                self.ems_log_event("volume-create")
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg='Error provisioning volume %s of size %s: %s'
                                      % (self.parameters['name'], self.parameters['size'], to_native(error)),
                                      exception=traceback.format_exc())

        if self.parameters.get('efficiency_policy'):
            self.assign_efficiency_policy()

    def create_volume_async(self):
        '''
        create volume async.
        '''
        options = self.create_volume_options()
        volume_create = netapp_utils.zapi.NaElement.create_node_with_children('volume-create-async', **options)
        if self.parameters.get('aggr_list'):
            aggr_list_obj = netapp_utils.zapi.NaElement('aggr-list')
            volume_create.add_child_elem(aggr_list_obj)
            for aggr in self.parameters['aggr_list']:
                aggr_list_obj.add_new_child('aggr-name', aggr)
        try:
            result = self.server.invoke_successfully(volume_create, enable_tunneling=True)
            self.ems_log_event("volume-create")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error provisioning volume %s of size %s: %s'
                                  % (self.parameters['name'], self.parameters['size'], to_native(error)),
                                  exception=traceback.format_exc())
        self.check_invoke_result(result, 'create')

        if self.parameters.get('efficiency_policy'):
            self.assign_efficiency_policy_async()

    def create_volume_options(self):
        options = {}
        if self.volume_style == 'flexGroup':
            options['volume-name'] = self.parameters['name']
            if self.parameters.get('aggr_list_multiplier'):
                options['aggr-list-multiplier'] = str(self.parameters['aggr_list_multiplier'])
            if self.parameters.get('auto_provision_as'):
                options['auto-provision-as'] = self.parameters['auto_provision_as']
            if self.parameters.get('space_guarantee'):
                options['space-guarantee'] = self.parameters['space_guarantee']
            if self.parameters.get('size'):
                options['size'] = str(self.parameters['size'])
        else:
            options['volume'] = self.parameters['name']
            options['size'] = str(self.parameters['size'])
            if self.parameters.get('aggregate_name') is None:
                self.module.fail_json(msg='Error provisioning volume %s: aggregate_name is required'
                                      % self.parameters['name'])
            options['containing-aggr-name'] = self.parameters['aggregate_name']
            if self.parameters.get('space_guarantee'):
                options['space-reserve'] = self.parameters['space_guarantee']

        if self.parameters.get('snapshot_policy'):
            options['snapshot-policy'] = self.parameters['snapshot_policy']
        if self.parameters.get('unix_permissions'):
            options['unix-permissions'] = self.parameters['unix_permissions']
        if self.parameters.get('volume_security_style'):
            options['volume-security-style'] = self.parameters['volume_security_style']
        if self.parameters.get('policy'):
            options['export-policy'] = self.parameters['policy']
        if self.parameters.get('junction_path'):
            options['junction-path'] = self.parameters['junction_path']
        if self.parameters.get('type'):
            options['volume-type'] = self.parameters['type']
        if self.parameters.get('percent_snapshot_space'):
            options['percentage-snapshot-reserve'] = self.parameters['percent_snapshot_space']
        if self.parameters.get('language'):
            options['language-code'] = self.parameters['language']
        return options

    def delete_volume(self):
        '''Delete ONTAP volume'''
        if self.parameters.get('is_infinite') or self.volume_style == 'flexGroup':
            volume_delete = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-destroy-async', **{'volume-name': self.parameters['name'], 'unmount-and-offline': 'true'})
        else:
            volume_delete = netapp_utils.zapi\
                .NaElement.create_node_with_children(
                    'volume-destroy', **{'name': self.parameters['name'],
                                         'unmount-and-offline': 'true'})
        try:
            result = self.server.invoke_successfully(volume_delete, enable_tunneling=True)
            if self.parameters.get('is_infinite') or self.volume_style == 'flexGroup':
                self.check_invoke_result(result, 'delete')
            self.ems_log_event("volume-delete")
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
        Infinite Volume. Use time_out parameter to set wait time for rename completion.
        """
        vol_rename_zapi, vol_name_zapi = ['volume-rename-async', 'volume-name'] if self.parameters['is_infinite']\
            else ['volume-rename', 'volume']
        volume_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            vol_rename_zapi, **{vol_name_zapi: self.parameters['from_name'],
                                'new-volume-name': str(self.parameters['name'])})
        try:
            result = self.server.invoke_successfully(volume_rename, enable_tunneling=True)
            if vol_rename_zapi == 'volume-rename-async':
                self.check_invoke_result(result, 'rename')
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
        vol_size_zapi, vol_name_zapi = ['volume-size-async', 'volume-name']\
            if (self.parameters['is_infinite'] or self.volume_style == 'flexGroup')\
            else ['volume-size', 'volume']
        volume_resize = netapp_utils.zapi.NaElement.create_node_with_children(
            vol_size_zapi, **{vol_name_zapi: self.parameters['name'],
                              'new-size': str(self.parameters['size'])})
        try:
            result = self.server.invoke_successfully(volume_resize, enable_tunneling=True)
            if vol_size_zapi == 'volume-size-async':
                self.check_invoke_result(result, 'resize')
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
            vol_state_zapi, vol_name_zapi, action = ['volume-online-async', 'volume-name', 'online']\
                if (self.parameters['is_infinite'] or self.volume_style == 'flexGroup')\
                else ['volume-online', 'name', 'online']
        else:   # Desired state is offline, setup zapi APIs respectively
            vol_state_zapi, vol_name_zapi, action = ['volume-offline-async', 'volume-name', 'offline']\
                if (self.parameters['is_infinite'] or self.volume_style == 'flexGroup')\
                else ['volume-offline', 'name', 'offline']
            volume_unmount = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-unmount', **{'volume-name': self.parameters['name']})
        volume_change_state = netapp_utils.zapi.NaElement.create_node_with_children(
            vol_state_zapi, **{vol_name_zapi: self.parameters['name']})
        try:
            if not self.parameters['is_online']:  # Unmount before offline
                self.server.invoke_successfully(volume_unmount, enable_tunneling=True)
            result = self.server.invoke_successfully(volume_change_state, enable_tunneling=True)
            if self.volume_style == 'flexGroup' or self.parameters['is_infinite']:
                self.check_invoke_result(result, action)
            self.ems_log_event("change-state")
        except netapp_utils.zapi.NaApiError as error:
            state = "online" if self.parameters['is_online'] else "offline"
            self.module.fail_json(msg='Error changing the state of volume %s to %s: %s'
                                  % (self.parameters['name'], state, to_native(error)),
                                  exception=traceback.format_exc())

    def volume_modify_attributes(self):
        """
        modify volume parameter 'policy','unix_permissions','snapshot_policy','space_guarantee','percent_snapshot_space'
        """
        # TODO: refactor this method
        vol_mod_iter = None
        if self.volume_style == 'flexGroup' or self.parameters['is_infinite']:
            vol_mod_iter = netapp_utils.zapi.NaElement('volume-modify-iter-async')
        else:
            vol_mod_iter = netapp_utils.zapi.NaElement('volume-modify-iter')
        attributes = netapp_utils.zapi.NaElement('attributes')
        vol_mod_attributes = netapp_utils.zapi.NaElement('volume-attributes')
        vol_space_attributes = netapp_utils.zapi.NaElement('volume-space-attributes')
        if self.parameters.get('policy'):
            vol_export_attributes = netapp_utils.zapi.NaElement(
                'volume-export-attributes')
            vol_export_attributes.add_new_child('policy', self.parameters['policy'])
            vol_mod_attributes.add_child_elem(vol_export_attributes)
        if self.parameters.get('space_guarantee'):
            vol_space_attributes.add_new_child(
                'space-guarantee', self.parameters['space_guarantee'])
            vol_mod_attributes.add_child_elem(vol_space_attributes)
        if self.parameters.get('percent_snapshot_space'):
            vol_space_attributes.add_new_child(
                'percentage-snapshot-reserve', str(self.parameters['percent_snapshot_space']))
            vol_mod_attributes.add_child_elem(vol_space_attributes)
        if self.parameters.get('unix_permissions'):
            vol_unix_permissions_attributes = netapp_utils.zapi.NaElement(
                'volume-security-unix-attributes')
            vol_unix_permissions_attributes.add_new_child('permissions', self.parameters['unix_permissions'])
            vol_security_attributes = netapp_utils.zapi.NaElement(
                'volume-security-attributes')
            vol_security_attributes.add_child_elem(vol_unix_permissions_attributes)
            vol_mod_attributes.add_child_elem(vol_security_attributes)
        if self.parameters.get('snapshot_policy') or self.parameters.get('snapdir_access'):
            vol_snapshot_policy_attributes = netapp_utils.zapi.NaElement('volume-snapshot-attributes')
            if self.parameters.get('snapshot_policy'):
                vol_snapshot_policy_attributes.add_new_child('snapshot-policy', self.parameters['snapshot_policy'])
            if self.parameters.get('snapdir_access'):
                vol_snapshot_policy_attributes.add_new_child('snapdir-access-enabled', self.parameters.get('snapdir_access'))
            vol_mod_attributes.add_child_elem(vol_snapshot_policy_attributes)
        if self.parameters.get('atime_update'):
            vol_performance_attributes = netapp_utils.zapi.NaElement('volume-performance-attributes')
            vol_performance_attributes.add_new_child('is-atime-update-enabled', self.parameters.get('atime_update'))
            vol_mod_attributes.add_child_elem(vol_performance_attributes)
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
            if self.volume_style == 'flexGroup' or self.parameters['is_infinite']:
                success = result.get_child_by_name('success-list')
                success = success.get_child_by_name('volume-modify-iter-async-info')
                results = dict()
                for key in ('status', 'jobid'):
                    if success.get_child_by_name(key):
                        results[key] = success[key]
                status = results.get('status')
                if status == 'in_progress' and 'jobid' in results:
                    if self.parameters['time_out'] == 0:
                        return
                    error = self.check_job_status(results['jobid'])
                    if error is None:
                        return
                    else:
                        self.module.fail_json(msg='Error when modify volume: %s' % error)
                self.module.fail_json(msg='Unexpected error when modify volume: results is: %s' % repr(results))
            # handle error if modify space, policy, or unix-permissions parameter fails
            if failures is not None:
                if failures.get_child_by_name('volume-modify-iter-info') is not None:
                    return_info = 'volume-modify-iter-info'
                    error_msg = failures.get_child_by_name(return_info).get_child_content('error-message')
                    self.module.fail_json(msg="Error modifying volume %s: %s"
                                          % (self.parameters['name'], error_msg),
                                          exception=traceback.format_exc())
                elif failures.get_child_by_name('volume-modify-iter-async-info') is not None:
                    return_info = 'volume-modify-iter-async-info'
                    error_msg = failures.get_child_by_name(return_info).get_child_content('error-message')
                    self.module.fail_json(msg="Error modifying volume %s: %s"
                                          % (self.parameters['name'], error_msg),
                                          exception=traceback.format_exc())
            self.ems_log_event("volume-modify")
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying volume %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def volume_mount(self):
        """
        Mount an existing volume in specified junction_path
        :return: None
        """
        vol_mount = netapp_utils.zapi.NaElement('volume-mount')
        vol_mount.add_new_child('volume-name', self.parameters['name'])
        vol_mount.add_new_child('junction-path', self.parameters['junction_path'])
        try:
            self.server.invoke_successfully(vol_mount, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error mounting volume %s on path %s: %s'
                                      % (self.parameters['name'], self.parameters['junction_path'],
                                         to_native(error)), exception=traceback.format_exc())

    def volume_unmount(self):
        """
        Unmount an existing volume
        :return: None
        """
        vol_unmount = netapp_utils.zapi.NaElement.create_node_with_children(
            'volume-unmount', **{'volume-name': self.parameters['name']})
        try:
            self.server.invoke_successfully(vol_unmount, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error unmounting volume %s: %s'
                                      % (self.parameters['name'], to_native(error)), exception=traceback.format_exc())

    def modify_volume(self, modify):
        for attribute in modify.keys():
            if attribute == 'size':
                self.resize_volume()
            if attribute == 'is_online':
                self.change_volume_state()
            if attribute == 'aggregate_name':
                self.move_volume()
            if attribute in ['space_guarantee', 'policy', 'unix_permissions',
                             'snapshot_policy', 'percent_snapshot_space', 'snapdir_access', 'atime_update']:
                self.volume_modify_attributes()
            if attribute == 'junction_path':
                if modify.get('junction_path') == '':
                    self.volume_unmount()
                else:
                    self.volume_mount()

    def compare_chmod_value(self, current):
        """
        compare current unix_permissions to desire unix_permissions.
        :return: True if the same, False it not the same or desire unix_permissions is not valid.
        """
        desire = self.parameters
        if current is None:
            return False
        octal_value = ''
        unix_permissions = desire['unix_permissions']
        if unix_permissions.isdigit():
            return int(current['unix_permissions']) == int(unix_permissions)
        else:
            if len(unix_permissions) != 12:
                return False
            if unix_permissions[:3] != '---':
                return False
            for i in range(3, len(unix_permissions), 3):
                if unix_permissions[i] not in ['r', '-'] or unix_permissions[i + 1] not in ['w', '-']\
                        or unix_permissions[i + 2] not in ['x', '-']:
                    return False
                group_permission = self.char_to_octal(unix_permissions[i:i + 3])
                octal_value += str(group_permission)
            return int(current['unix_permissions']) == int(octal_value)

    def char_to_octal(self, chars):
        """
        :param chars: Characters to be converted into octal values.
        :return: octal value of the individual group permission.
        """
        total = 0
        if chars[0] == 'r':
            total += 4
        if chars[1] == 'w':
            total += 2
        if chars[2] == 'x':
            total += 1
        return total

    def get_volume_style(self, current):
        if current is None:
            if self.parameters.get('aggr_list') or self.parameters.get('aggr_list_multiplier') or self.parameters.get('auto_provision_as'):
                return 'flexGroup'
        else:
            if current.get('style_extended'):
                if current['style_extended'] == 'flexgroup':
                    return 'flexGroup'
                else:
                    return current['style_extended']
        return None

    def get_job(self, jobid, server):
        """
        Get job details by id
        """
        job_get = netapp_utils.zapi.NaElement('job-get')
        job_get.add_new_child('job-id', jobid)
        try:
            result = server.invoke_successfully(job_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == "15661":
                # Not found
                return None
            self.module.fail_json(msg='Error fetching job info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        results = dict()
        job_info = result.get_child_by_name('attributes').get_child_by_name('job-info')
        results = {
            'job-progress': job_info['job-progress'],
            'job-state': job_info['job-state']
        }
        if job_info.get_child_by_name('job-completion') is not None:
            results['job-completion'] = job_info['job-completion']
        else:
            results['job-completion'] = None
        return results

    def check_job_status(self, jobid):
        """
        Loop until job is complete
        """
        server = self.server
        sleep_time = 5
        time_out = self.parameters['time_out']
        results = self.get_job(jobid, server)

        while time_out > 0:
            results = self.get_job(jobid, server)
            # If running as cluster admin, the job is owned by cluster vserver
            # rather than the target vserver.
            if results is None and server == self.server:
                results = netapp_utils.get_cserver(self.server)
                server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
                continue
            if results is None:
                error = 'cannot locate job with id: %d' % int(jobid)
                break
            if results['job-state'] in ('queued', 'running'):
                time.sleep(sleep_time)
                time_out -= sleep_time
                continue
            if results['job-state'] in ('success', 'failure'):
                break
            else:
                self.module.fail_json(msg='Unexpected job status in: %s' % repr(results))

        if results is not None:
            if results['job-state'] == 'success':
                error = None
            elif results['job-state'] in ('queued', 'running'):
                error = 'job completion exceeded expected timer of: %s seconds' % \
                        self.parameters['time_out']
            else:
                if results['job-completion'] is not None:
                    error = results['job-completion']
                else:
                    error = results['job-progress']
        return error

    def check_invoke_result(self, result, action):
        '''
        check invoked api call back result.
        '''
        results = dict()
        for key in ('result-status', 'result-jobid'):
            if result.get_child_by_name(key):
                results[key] = result[key]
        status = results.get('result-status')
        if status == 'in_progress' and 'result-jobid' in results:
            if self.parameters['time_out'] == 0:
                return
            error = self.check_job_status(results['result-jobid'])
            if error is None:
                return
            else:
                self.module.fail_json(msg='Error when %s volume: %s' % (action, error))
        if status == 'failed':
            self.module.fail_json(msg='Operation failed when %s volume.' % action)

    def assign_efficiency_policy(self):
        options = {'path': '/vol/' + self.parameters['name']}
        efficiency_enable = netapp_utils.zapi.NaElement.create_node_with_children('sis-enable', **options)
        try:
            self.server.invoke_successfully(efficiency_enable, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error enable efficiency on volume %s: %s'
                                      % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

        options['policy-name'] = self.parameters['efficiency_policy']
        efficiency_start = netapp_utils.zapi.NaElement.create_node_with_children('sis-set-config', **options)
        try:
            self.server.invoke_successfully(efficiency_start, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error setting up an efficiency policy %s on volume %s: %s'
                                      % (self.parameters['efficiency_policy'], self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def assign_efficiency_policy_async(self):
        options = {'volume-name': self.parameters['name']}
        efficiency_enable = netapp_utils.zapi.NaElement.create_node_with_children('sis-enable-async', **options)
        try:
            result = self.server.invoke_successfully(efficiency_enable, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error enable efficiency on volume %s: %s'
                                      % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        self.check_invoke_result(result, 'enable efficiency on')

        options['policy-name'] = self.parameters['efficiency_policy']
        efficiency_start = netapp_utils.zapi.NaElement.create_node_with_children('sis-set-config-async', **options)
        try:
            result = self.server.invoke_successfully(efficiency_start, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error setting up an efficiency policy on volume %s: %s'
                                      % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        self.check_invoke_result(result, 'set efficiency policy on')

    def apply(self):
        '''Call create/modify/delete operations'''
        current = self.get_volume()
        self.volume_style = self.get_volume_style(current)
        # rename and create are mutually exclusive
        rename, cd_action = None, None
        if self.parameters.get('from_name'):
            rename = self.na_helper.is_rename_action(self.get_volume(self.parameters['from_name']), current)
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if self.parameters.get('unix_permissions'):
            # current stores unix_permissions' numeric value.
            # unix_permission in self.parameter can be either numeric or character.
            if self.compare_chmod_value(current):
                del self.parameters['unix_permissions']
        if self.parameters.get('percent_snapshot_space'):
            self.parameters['percent_snapshot_space'] = str(self.parameters['percent_snapshot_space'])
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_volume()
                if cd_action == 'create':
                    self.create_volume()
                    # if we create, and modify only variable are set (snapdir_access or atime_update) we need to run a modify
                    if 'snapdir_access' in self.parameters or 'atime_update' in self.parameters:
                        self.volume_modify_attributes()
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
        elif state == 'volume-delete':
            message = "A Volume has been deleted"
        elif state == 'volume-move':
            message = "A Volume has been moved"
        elif state == 'volume-rename':
            message = "A Volume has been renamed"
        elif state == 'volume-resize':
            message = "A Volume has been resized to: " + \
                str(self.parameters['size']) + str(self.parameters['size_unit'])
        elif state == 'volume-change':
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
