#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_snapshot

short_description: Manage NetApp cDOT snapshots
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.5'
author: Marcel Juhnke <marcel.juhnke@accenture.com>

description:
- Create or delete snapshots on NetApp cDOT

options:

  state:
    description:
    - Whether the specified snapshot should exist or not.
    required: true
    choices: ['present', 'absent']

  name:
    description:
    - The name of the snapshot to manage.
    required: true

  volume_name:
    description:
    - The name of the containing volume.
    required: true

  vserver:
    description:
    - Name of the vserver to use.
    required: true
    default: None

'''

EXAMPLES = """

    - name: Create Snapshot Copy
      na_cdot_snapshot:
        state: present
        name: snap-keep-forever
        volume_name: vserver_root
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete Snapshot Copy
      na_cdot_snapshot:
        state: absent
        name: snap-keep-forever
        volume_name: vserver_root
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


class NetAppCDOTSnapshot(object):

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
            volume_name=dict(required=True, type='str'),
            vserver=dict(required=True, type='str', default=None),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['volume_name'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.vserver = p['vserver']
        self.volume_name = p['volume_name']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_snapshot(self):
        """
        Return details about the snapshot
        :param:
            name : Name of the smapshot
            volume_name: Name of the containing volume

        :return: Details about the snapshot. None if not found.
        :rtype: dict
        """
        snapshot_list = netapp_utils.zapi.NaElement('snapshot-get-iter')
        snapshot_info = netapp_utils.zapi.NaElement('snapshot-info')
        snapshot_info.add_new_child('name', self.name)
        snapshot_info.add_new_child('volume', self.volume_name)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(snapshot_info)

        snapshot_list.add_child_elem(query)

        result = self.server.invoke_successfully(snapshot_list, True)

        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            snapshot_info = result.get_child_by_name(
                'attributes-list').get_child_by_name(
                    'snapshot-info')
            # check if snapshot name & volume match
            returned_name = snapshot_info.get_child_content('name')
            returned_volume = snapshot_info.get_child_content('volume')

            if returned_name == self.name and returned_volume == self.volume_name:
                return_value = {
                    'name': self.name,
                    'volume_name': self.volume_name,
                }

        return return_value

    def create_snapshot(self):
        snapshot_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapshot-create', **{'volume': self.volume_name,
                                  'snapshot': self.name})

        try:
            self.server.invoke_successfully(snapshot_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error creating snapshot %s on %s: %s' % (
                self.name, self.volume_name, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_snapshot(self):
        snapshot_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'snapshot-delete', **{'volume': self.volume_name,
                                  'snapshot': self.name})

        try:
            self.server.invoke_successfully(snapshot_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error deleting snapshot %s on %s: %s' % (
                self.name, self.volume_name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        snapshot_exists = False
        snapshot_detail = self.get_snapshot()

        if snapshot_detail:
            snapshot_exists = True

            if self.state == 'absent':
                changed = True

        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not snapshot_exists:
                        self.create_snapshot()

                elif self.state == 'absent':
                    self.delete_snapshot()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTSnapshot()
    v.apply()

if __name__ == '__main__':
    main()
