#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - Create/Delete/Initialize SnapMirror volume/vserver relationships
  - Modify schedule for a SnapMirror relationship
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_snapmirror
options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified relationship should exist or not.
    default: present
  source_volume:
    description:
      - Specifies the name of the source volume for the SnapMirror.
  destination_volume:
    description:
      - Specifies the name of the destination volume for the SnapMirror.
  source_vserver:
    description:
      - Name of the source vserver for the SnapMirror.
  destination_vserver:
    description:
      - Name of the destination vserver for the SnapMirror.
  source_path:
    description:
      - Specifies the source endpoint of the SnapMirror relationship.
  destination_path:
    description:
      - Specifies the destination endpoint of the SnapMirror relationship.
  relationship_type:
    choices: ['data_protection', 'load_sharing', 'vault', 'restore', 'transition_data_protection',
    'extended_data_protection']
    description:
      - Specify the type of SnapMirror relationship.
  schedule:
    description:
      - Specify the name of the current schedule, which is used to update the SnapMirror relationship.
      - Optional for create, modifiable.
  policy:
    description:
      - Specify the name of the SnapMirror policy that applies to this relationship.
    version_added: "2.8"
  source_hostname:
    description:
     - Source hostname or IP address.
     - Required for SnapMirror delete
  source_username:
    description:
     - Source username.
     - Optional if this is same as destination username.
  source_password:
    description:
     - Source password.
     - Optional if this is same as destination password.
short_description: "NetApp ONTAP Manage SnapMirror"
version_added: "2.7"
'''

EXAMPLES = """

    - name: Create SnapMirror
      na_ontap_snapmirror:
        state: present
        source_volume: test_src
        destination_volume: test_dest
        source_vserver: ansible_src
        destination_vserver: ansible_dest
        schedule: hourly
        policy: MirrorAllSnapshots
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete SnapMirror
      na_ontap_snapmirror:
        state: absent
        destination_path: <path>
        source_hostname: "{{ source_hostname }}"
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Set schedule to NULL
      na_ontap_snapmirror:
        state: present
        destination_path: <path>
        schedule: ""
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Release SnapMirror
      na_ontap_snapmirror:
        state: release
        destination_path: <path>
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
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPSnapmirror(object):
    """
    Class with Snapmirror methods
    """

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            source_vserver=dict(required=False, type='str'),
            destination_vserver=dict(required=False, type='str'),
            source_volume=dict(required=False, type='str'),
            destination_volume=dict(required=False, type='str'),
            source_path=dict(required=False, type='str'),
            destination_path=dict(required=False, type='str'),
            schedule=dict(required=False, type='str'),
            policy=dict(required=False, type='str'),
            relationship_type=dict(required=False, type='str',
                                   choices=['data_protection', 'load_sharing',
                                            'vault', 'restore',
                                            'transition_data_protection',
                                            'extended_data_protection']
                                   ),
            source_hostname=dict(required=False, type='str'),
            source_username=dict(required=False, type='str'),
            source_password=dict(required=False, type='str', no_log=True)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_together=(['source_volume', 'destination_volume'],
                               ['source_vserver', 'destination_vserver']),
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # setup later if required
        self.source_server = None
        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def snapmirror_get_iter(self):
        """
        Compose NaElement object to query current SnapMirror relations using destination-path
        SnapMirror relation for a destination path is unique
        :return: NaElement object for SnapMirror-get-iter
        """
        snapmirror_get_iter = netapp_utils.zapi.NaElement('snapmirror-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        snapmirror_info = netapp_utils.zapi.NaElement('snapmirror-info')
        snapmirror_info.add_new_child('destination-location', self.parameters['destination_path'])
        query.add_child_elem(snapmirror_info)
        snapmirror_get_iter.add_child_elem(query)
        return snapmirror_get_iter

    def snapmirror_get(self):
        """
        Get current SnapMirror relations
        :return: Dictionary of current SnapMirror details if query successful, else None
        """
        snapmirror_get_iter = self.snapmirror_get_iter()
        snap_info = dict()
        try:
            result = self.server.invoke_successfully(snapmirror_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching snapmirror info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) > 0:
            snapmirror_info = result.get_child_by_name('attributes-list').get_child_by_name(
                'snapmirror-info')
            snap_info['mirror_state'] = snapmirror_info.get_child_content('mirror-state')
            snap_info['status'] = snapmirror_info.get_child_content('relationship-status')
            snap_info['schedule'] = snapmirror_info.get_child_content('schedule')
            snap_info['policy'] = snapmirror_info.get_child_content('policy')
            if snap_info['schedule'] is None:
                snap_info['schedule'] = ""
            return snap_info
        return None

    def check_if_remote_volume_exists(self):
        """
        Validate existence of source volume
        :return: True if volume exists, False otherwise
        """
        self.set_source_cluster_connection()
        # do a get volume to check if volume exists or not
        volume_info = netapp_utils.zapi.NaElement('volume-get-iter')
        volume_attributes = netapp_utils.zapi.NaElement('volume-attributes')
        volume_id_attributes = netapp_utils.zapi.NaElement('volume-id-attributes')
        volume_id_attributes.add_new_child('name', self.parameters['source_volume'])
        # if source_volume is present, then source_vserver is also guaranteed to be present
        volume_id_attributes.add_new_child('vserver-name', self.parameters['source_vserver'])
        volume_attributes.add_child_elem(volume_id_attributes)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(volume_attributes)
        volume_info.add_child_elem(query)
        try:
            result = self.source_server.invoke_successfully(volume_info, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching source volume details %s : %s'
                                      % (self.parameters['source_volume'], to_native(error)),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) > 0:
            return True
        return False

    def snapmirror_create(self):
        """
        Create a SnapMirror relationship
        """
        if self.parameters.get('source_hostname') and self.parameters.get('source_volume'):
            if not self.check_if_remote_volume_exists():
                self.module.fail_json(msg='Source volume does not exist. Please specify a volume that exists')
        options = {'source-location': self.parameters['source_path'],
                   'destination-location': self.parameters['destination_path']}
        snapmirror_create = netapp_utils.zapi.NaElement.create_node_with_children('snapmirror-create', **options)
        if self.parameters.get('relationship_type'):
            snapmirror_create.add_new_child('relationship-type', self.parameters['relationship_type'])
        if self.parameters.get('schedule'):
            snapmirror_create.add_new_child('schedule', self.parameters['schedule'])
        if self.parameters.get('policy'):
            snapmirror_create.add_new_child('policy', self.parameters['policy'])
        try:
            self.server.invoke_successfully(snapmirror_create, enable_tunneling=True)
            self.snapmirror_initialize()
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating SnapMirror %s' % to_native(error),
                                  exception=traceback.format_exc())

    def set_source_cluster_connection(self):
        """
        Setup ontap ZAPI server connection for source hostname
        :return: None
        """
        if self.parameters.get('source_username'):
            self.module.params['username'] = self.parameters['source_username']
        if self.parameters.get('source_password'):
            self.module.params['password'] = self.parameters['source_password']
        self.module.params['hostname'] = self.parameters['source_hostname']
        self.source_server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def delete_snapmirror(self):
        """
        Delete a SnapMirror relationship
        #1. Quiesce the SnapMirror relationship at destination
        #2. Break the SnapMirror relationship at the destination
        #3. Release the SnapMirror at source
        #4. Delete SnapMirror at destination
        """
        if not self.parameters.get('source_hostname'):
            self.module.fail_json(msg='Missing parameters for delete: Please specify the '
                                      'source cluster hostname to release the SnapMirror relation')
        self.set_source_cluster_connection()
        self.snapmirror_quiesce()
        if self.parameters.get('relationship_type') and \
                self.parameters.get('relationship_type') not in ['load_sharing', 'vault']:
            self.snapmirror_break()
        if self.get_destination():
            self.snapmirror_release()
        self.snapmirror_delete()

    def snapmirror_quiesce(self):
        """
        Quiesce SnapMirror relationship - disable all future transfers to this destination
        """
        options = {'destination-location': self.parameters['destination_path']}

        snapmirror_quiesce = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapmirror-quiesce', **options)
        try:
            self.server.invoke_successfully(snapmirror_quiesce,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error Quiescing SnapMirror : %s'
                                      % (to_native(error)),
                                  exception=traceback.format_exc())

    def snapmirror_delete(self):
        """
        Delete SnapMirror relationship at destination cluster
        """
        options = {'destination-location': self.parameters['destination_path']}

        snapmirror_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapmirror-destroy', **options)
        try:
            self.server.invoke_successfully(snapmirror_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting SnapMirror : %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def snapmirror_break(self):
        """
        Break SnapMirror relationship at destination cluster
        """
        options = {'destination-location': self.parameters['destination_path']}
        snapmirror_break = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapmirror-break', **options)
        try:
            self.server.invoke_successfully(snapmirror_break,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error breaking SnapMirror relationship : %s'
                                      % (to_native(error)),
                                  exception=traceback.format_exc())

    def snapmirror_release(self):
        """
        Release SnapMirror relationship from source cluster
        """
        options = {'destination-location': self.parameters['destination_path']}
        snapmirror_release = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapmirror-release', **options)
        try:
            self.source_server.invoke_successfully(snapmirror_release,
                                                   enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error releasing SnapMirror relationship : %s'
                                      % (to_native(error)),
                                  exception=traceback.format_exc())

    def snapmirror_abort(self):
        """
        Abort a SnapMirror relationship in progress
        """
        options = {'destination-location': self.parameters['destination_path']}
        snapmirror_abort = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapmirror-abort', **options)
        try:
            self.server.invoke_successfully(snapmirror_abort,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error aborting SnapMirror relationship : %s'
                                      % (to_native(error)),
                                  exception=traceback.format_exc())

    def snapmirror_initialize(self):
        """
        Initialize SnapMirror based on relationship type
        """
        current = self.snapmirror_get()
        if current['mirror_state'] != 'snapmirrored':
            initialize_zapi = 'snapmirror-initialize'
            if self.parameters.get('relationship_type') and self.parameters['relationship_type'] == 'load_sharing':
                initialize_zapi = 'snapmirror-initialize-ls-set'
                options = {'source-location': self.parameters['source_path']}
            else:
                options = {'destination-location': self.parameters['destination_path']}
            snapmirror_init = netapp_utils.zapi.NaElement.create_node_with_children(
                initialize_zapi, **options)
            try:
                self.server.invoke_successfully(snapmirror_init,
                                                enable_tunneling=True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg='Error initializing SnapMirror : %s'
                                          % (to_native(error)),
                                      exception=traceback.format_exc())

    def snapmirror_modify(self, modify):
        """
        Modify SnapMirror schedule or policy
        """
        options = {'destination-location': self.parameters['destination_path']}
        snapmirror_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapmirror-modify', **options)
        if modify.get('schedule') is not None:
            snapmirror_modify.add_new_child('schedule', modify.get('schedule'))
        if modify.get('policy'):
            snapmirror_modify.add_new_child('policy', modify.get('policy'))
        try:
            self.server.invoke_successfully(snapmirror_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying SnapMirror schedule or policy : %s'
                                      % (to_native(error)),
                                  exception=traceback.format_exc())

    def snapmirror_update(self):
        """
        Update data in destination endpoint
        """
        options = {'destination-location': self.parameters['destination_path']}
        snapmirror_update = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapmirror-update', **options)
        try:
            result = self.server.invoke_successfully(snapmirror_update,
                                                     enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error updating SnapMirror : %s'
                                      % (to_native(error)),
                                  exception=traceback.format_exc())

    def check_parameters(self):
        """
        Validate parameters and fail if one or more required params are missing
        Update source and destination path from vserver and volume parameters
        """
        if self.parameters['state'] == 'present'\
                and (self.parameters.get('source_path') or self.parameters.get('destination_path')):
            if not self.parameters.get('destination_path') or not self.parameters.get('source_path'):
                self.module.fail_json(msg='Missing parameters: Source path or Destination path')
        elif self.parameters.get('source_volume'):
            if not self.parameters.get('source_vserver') or not self.parameters.get('destination_vserver'):
                self.module.fail_json(msg='Missing parameters: source vserver or destination vserver or both')
            self.parameters['source_path'] = self.parameters['source_vserver'] + ":" + self.parameters['source_volume']
            self.parameters['destination_path'] = self.parameters['destination_vserver'] + ":" +\
                self.parameters['destination_volume']
        elif self.parameters.get('source_vserver'):
            self.parameters['source_path'] = self.parameters['source_vserver'] + ":"
            self.parameters['destination_path'] = self.parameters['destination_vserver'] + ":"

    def get_destination(self):
        result = None
        release_get = netapp_utils.zapi.NaElement('snapmirror-get-destination-iter')
        query = netapp_utils.zapi.NaElement('query')
        snapmirror_dest_info = netapp_utils.zapi.NaElement('snapmirror-destination-info')
        snapmirror_dest_info.add_new_child('destination-location', self.parameters['destination_path'])
        query.add_child_elem(snapmirror_dest_info)
        release_get.add_child_elem(query)
        try:
            result = self.source_server.invoke_successfully(release_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching snapmirror destinations info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) > 0:
            return True
        return None

    def apply(self):
        """
        Apply action to SnapMirror
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_snapmirror", cserver)
        self.check_parameters()
        current = self.snapmirror_get()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if cd_action == 'create':
            self.snapmirror_create()
        elif cd_action == 'delete':
            if current['status'] == 'transferring':
                self.snapmirror_abort()
            else:
                self.delete_snapmirror()
        else:
            if modify:
                self.snapmirror_modify(modify)
            # check for initialize
            if current and current['mirror_state'] != 'snapmirrored':
                self.snapmirror_initialize()
                # set changed explicitly for initialize
                self.na_helper.changed = True
            # Update when create is called again, or modify is being called
            if self.parameters['state'] == 'present':
                self.snapmirror_update()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """Execute action"""
    community_obj = NetAppONTAPSnapmirror()
    community_obj.apply()


if __name__ == '__main__':
    main()
