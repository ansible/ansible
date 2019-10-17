#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_volume_clone
short_description: NetApp ONTAP manage volume clones.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create NetApp ONTAP volume clones.
- A FlexClone License is required to use this module
options:
  state:
    description:
    - Whether volume clone should be created.
    choices: ['present']
    default: 'present'
  parent_volume:
    description:
    - The parent volume of the volume clone being created.
    required: true
    type: str
  name:
    description:
    - The name of the volume clone being created.
    required: true
    type: str
    aliases:
    - volume
  vserver:
    description:
    - Vserver in which the volume clone should be created.
    required: true
    type: str
  parent_snapshot:
    description:
    - Parent snapshot in which volume clone is created off.
    type: str
  parent_vserver:
    description:
    - Vserver of parent volume in which clone is created off.
    type: str
  qos_policy_group_name:
    description:
    - The qos-policy-group-name which should be set for volume clone.
    type: str
  space_reserve:
    description:
    - The space_reserve setting which should be used for the volume clone.
    choices: ['volume', 'none']
  volume_type:
    description:
    - The volume-type setting which should be used for the volume clone.
    choices: ['rw', 'dp']
  junction_path:
    version_added: '2.8'
    description:
    - Junction path of the volume.
    type: str
  uid:
    version_added: '2.9'
    description:
    - The UNIX user ID for the clone volume.
    type: int
  gid:
    version_added: '2.9'
    description:
    - The UNIX group ID for the clone volume.
    type: int
'''

EXAMPLES = """
    - name: create volume clone
      na_ontap_volume_clone:
        state: present
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        hostname: "{{ netapp hostname }}"
        vserver: vs_hack
        parent_volume: normal_volume
        name: clone_volume_7
        space_reserve: none
        parent_snapshot: backup1
        junction_path: /clone_volume_7
        uid: 1
        gid: 1
"""

RETURN = """
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils._text import to_native

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPVolumeClone(object):
    """
        Creates a volume clone
    """

    def __init__(self):
        """
            Initialize the NetAppOntapVolumeClone class
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present'], default='present'),
            parent_volume=dict(required=True, type='str'),
            name=dict(required=True, type='str', aliases=["volume"]),
            vserver=dict(required=True, type='str'),
            parent_snapshot=dict(required=False, type='str', default=None),
            parent_vserver=dict(required=False, type='str', default=None),
            qos_policy_group_name=dict(required=False, type='str', default=None),
            space_reserve=dict(required=False, choices=['volume', 'none'], default=None),
            volume_type=dict(required=False, choices=['rw', 'dp']),
            junction_path=dict(required=False, type='str', default=None),
            uid=dict(required=False, type='int'),
            gid=dict(required=False, type='int')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
            required_together=[
                ['uid', 'gid']
            ]
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])
        return

    def create_volume_clone(self):
        """
        Creates a new volume clone
        """
        clone_obj = netapp_utils.zapi.NaElement('volume-clone-create')
        clone_obj.add_new_child("parent-volume", self.parameters['parent_volume'])
        clone_obj.add_new_child("volume", self.parameters['volume'])
        if self.parameters.get('qos_policy_group_name'):
            clone_obj.add_new_child("qos-policy-group-name", self.parameters['qos_policy_group_name'])
        if self.parameters.get('space_reserve'):
            clone_obj.add_new_child("space-reserve", self.parameters['space_reserve'])
        if self.parameters.get('parent_snapshot'):
            clone_obj.add_new_child("parent-snapshot", self.parameters['parent_snapshot'])
        if self.parameters.get('parent_vserver'):
            clone_obj.add_new_child("parent-vserver", self.parameters['parent_vserver'])
        if self.parameters.get('volume_type'):
            clone_obj.add_new_child("volume-type", self.parameters['volume_type'])
        if self.parameters.get('junction_path'):
            clone_obj.add_new_child("junction-path", self.parameters['junction_path'])
        if self.parameters.get('uid'):
            clone_obj.add_new_child("uid", str(self.parameters['uid']))
            clone_obj.add_new_child("gid", str(self.parameters['gid']))
        try:
            self.server.invoke_successfully(clone_obj, True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error creating volume clone: %s: %s' %
                                      (self.parameters['volume'], to_native(exc)), exception=traceback.format_exc())

    def get_volume_clone(self):
        clone_obj = netapp_utils.zapi.NaElement('volume-clone-get')
        clone_obj.add_new_child("volume", self.parameters['volume'])
        try:
            results = self.server.invoke_successfully(clone_obj, True)
            if results.get_child_by_name('attributes'):
                attributes = results.get_child_by_name('attributes')
                info = attributes.get_child_by_name('volume-clone-info')
                parent_volume = info.get_child_content('parent-volume')
                # checking if clone volume name already used to create by same parent volume
                if parent_volume == self.parameters['parent_volume']:
                    return results
        except netapp_utils.zapi.NaApiError as error:
            # Error 15661 denotes an volume clone not being found.
            if to_native(error.code) == "15661":
                pass
            else:
                self.module.fail_json(msg='Error fetching volume clone information %s: %s' %
                                          (self.parameters['volume'], to_native(error)), exception=traceback.format_exc())
        return None

    def apply(self):
        """
        Run Module based on play book
        """
        netapp_utils.ems_log_event("na_ontap_volume_clone", self.server)
        current = self.get_volume_clone()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_volume_clone()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Creates the NetApp Ontap Volume Clone object and runs the correct play task
    """
    obj = NetAppONTAPVolumeClone()
    obj.apply()


if __name__ == '__main__':
    main()
