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
  volume:
    description:
    - The name of the volume clone being created.
    required: true
  vserver:
    description:
    - Vserver in which the volume clone should be created.
    required: true
  parent_snapshot:
    description:
    - Parent snapshot in which volume clone is created off.
  parent_vserver:
    description:
    - Vserver of parent volume in which clone is created off.
  qos_policy_group_name:
    description:
    - The qos-policy-group-name which should be set for volume clone.
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
        volume: clone_volume_7
        space_reserve: none
        parent_snapshot: backup1
        junction_path: /clone_volume_7
"""

RETURN = """
"""

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapVolumeClone(object):
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
            volume=dict(required=True, type='str'),
            vserver=dict(required=True, type='str'),
            parent_snapshot=dict(required=False, type='str', default=None),
            parent_vserver=dict(required=False, type='str', default=None),
            qos_policy_group_name=dict(required=False, type='str', default=None),
            space_reserve=dict(required=False, choices=['volume', 'none'], default=None),
            volume_type=dict(required=False, choices=['rw', 'dp']),
            junction_path=dict(required=False, type='str', default=None)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.parent_snapshot = parameters['parent_snapshot']
        self.parent_volume = parameters['parent_volume']
        self.parent_vserver = parameters['parent_vserver']
        self.qos_policy_group_name = parameters['qos_policy_group_name']
        self.space_reserve = parameters['space_reserve']
        self.volume = parameters['volume']
        self.volume_type = parameters['volume_type']
        self.vserver = parameters['vserver']
        self.junction_path = parameters['junction_path']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)
        return

    def create_volume_clone(self):
        """
        Creates a new volume clone
        """
        clone_obj = netapp_utils.zapi.NaElement('volume-clone-create')
        clone_obj.add_new_child("parent-volume", self.parent_volume)
        clone_obj.add_new_child("volume", self.volume)
        if self.qos_policy_group_name:
            clone_obj.add_new_child("qos-policy-group-name", self.qos_policy_group_name)
        if self.space_reserve:
            clone_obj.add_new_child("space-reserve", self.space_reserve)
        if self.parent_snapshot:
            clone_obj.add_new_child("parent-snapshot", self.parent_snapshot)
        if self.parent_vserver:
            clone_obj.add_new_child("parent-vserver", self.parent_vserver)
        if self.volume_type:
            clone_obj.add_new_child("volume-type", self.volume_type)
        if self.junction_path:
            clone_obj.add_new_child("junction-path", self.junction_path)
        self.server.invoke_successfully(clone_obj, True)

    def does_volume_clone_exists(self):
        clone_obj = netapp_utils.zapi.NaElement('volume-clone-get')
        clone_obj.add_new_child("volume", self.volume)
        try:
            results = self.server.invoke_successfully(clone_obj, True)
        except netapp_utils.zapi.NaApiError:
            return False
        attributes = results.get_child_by_name('attributes')
        info = attributes.get_child_by_name('volume-clone-info')
        parent_volume = info.get_child_content('parent-volume')
        if parent_volume == self.parent_volume:
            return True
        self.module.fail_json(msg="Error clone %s already exists for parent %s" % (self.volume, parent_volume))

    def apply(self):
        """
        Run Module based on play book
        """
        changed = False
        netapp_utils.ems_log_event("na_ontap_volume_clone", self.server)
        existing_volume_clone = self.does_volume_clone_exists()
        if existing_volume_clone is False:  # create clone
            changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                self.create_volume_clone()

        self.module.exit_json(changed=changed)


def main():
    """
    Creates the NetApp Ontap Volume Clone object and runs the correct play task
    """
    obj = NetAppOntapVolumeClone()
    obj.apply()


if __name__ == '__main__':
    main()
