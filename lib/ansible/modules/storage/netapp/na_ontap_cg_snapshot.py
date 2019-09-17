#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
short_description: NetApp ONTAP manage consistency group snapshot
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - Create consistency group snapshot for ONTAP volumes.
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_cg_snapshot
options:
  state:
    description:
      - If you want to create a snapshot.
    default: present
  vserver:
    required: true
    description:
      - Name of the vserver.
  volumes:
    required: true
    description:
      - A list of volumes in this filer that is part of this CG operation.
  snapshot:
    required: true
    description:
      - The provided name of the snapshot that is created in each volume.
  timeout:
    description:
      - Timeout selector.
    choices: ['urgent', 'medium', 'relaxed']
    default: medium
  snapmirror_label:
    description:
      - A human readable SnapMirror label to be attached with the consistency group snapshot copies.
version_added: "2.7"

'''

EXAMPLES = """
    - name:
      na_ontap_cg_snapshot:
        state: present
        vserver: vserver_name
        snapshot: snapshot name
        volumes: vol_name
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        hostname: "{{ netapp hostname }}"
"""

RETURN = """
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPCGSnapshot(object):
    """
    Methods to create CG snapshots
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, default='present'),
            vserver=dict(required=True, type='str'),
            volumes=dict(required=True, type='list'),
            snapshot=dict(required=True, type='str'),
            timeout=dict(required=False, type='str', choices=[
                'urgent', 'medium', 'relaxed'], default='medium'),
            snapmirror_label=dict(required=False, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up variables
        self.state = parameters['state']
        self.vserver = parameters['vserver']
        self.volumes = parameters['volumes']
        self.snapshot = parameters['snapshot']
        self.timeout = parameters['timeout']
        self.snapmirror_label = parameters['snapmirror_label']
        self.cgid = None

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)

    def does_snapshot_exist(self, volume):
        """
        This is duplicated from na_ontap_snapshot
        Checks to see if a snapshot exists or not
        :return: Return True if a snapshot exists, false if it doesn't
        """
        # TODO: Remove this method and import snapshot module and
        # call get after re-factoring __init__ across all the modules
        # we aren't importing now, since __init__ does a lot of Ansible setup
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-get-iter")
        desired_attr = netapp_utils.zapi.NaElement("desired-attributes")
        snapshot_info = netapp_utils.zapi.NaElement('snapshot-info')
        comment = netapp_utils.zapi.NaElement('comment')
        # add more desired attributes that are allowed to be modified
        snapshot_info.add_child_elem(comment)
        desired_attr.add_child_elem(snapshot_info)
        snapshot_obj.add_child_elem(desired_attr)
        # compose query
        query = netapp_utils.zapi.NaElement("query")
        snapshot_info_obj = netapp_utils.zapi.NaElement("snapshot-info")
        snapshot_info_obj.add_new_child("name", self.snapshot)
        snapshot_info_obj.add_new_child("volume", volume)
        query.add_child_elem(snapshot_info_obj)
        snapshot_obj.add_child_elem(query)
        result = self.server.invoke_successfully(snapshot_obj, True)
        return_value = None
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            attributes_list = result.get_child_by_name('attributes-list')
            snap_info = attributes_list.get_child_by_name('snapshot-info')
            return_value = {'comment': snap_info.get_child_content('comment')}
        return return_value

    def cgcreate(self):
        """
        Calls cg-start and cg-commit (when cg-start succeeds)
        """
        started = self.cg_start()
        if started:
            if self.cgid is not None:
                self.cg_commit()
            else:
                self.module.fail_json(msg="Error fetching CG ID for CG commit %s" % self.snapshot,
                                      exception=traceback.format_exc())
        return started

    def cg_start(self):
        """
        For the given list of volumes, creates cg-snapshot
        """
        snapshot_started = False
        cgstart = netapp_utils.zapi.NaElement("cg-start")
        cgstart.add_new_child("snapshot", self.snapshot)
        cgstart.add_new_child("timeout", self.timeout)
        volume_list = netapp_utils.zapi.NaElement("volumes")
        cgstart.add_child_elem(volume_list)
        for vol in self.volumes:
            snapshot_exists = self.does_snapshot_exist(vol)
            if snapshot_exists is None:
                snapshot_started = True
                volume_list.add_new_child("volume-name", vol)
        if snapshot_started:
            if self.snapmirror_label:
                cgstart.add_new_child("snapmirror-label",
                                      self.snapmirror_label)
            try:
                cgresult = self.server.invoke_successfully(
                    cgstart, enable_tunneling=True)
                if cgresult.get_child_by_name('cg-id'):
                    self.cgid = cgresult['cg-id']
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg="Error creating CG snapshot %s: %s" %
                                      (self.snapshot, to_native(error)),
                                      exception=traceback.format_exc())
        return snapshot_started

    def cg_commit(self):
        """
        When cg-start is successful, performs a cg-commit with the cg-id
        """
        cgcommit = netapp_utils.zapi.NaElement.create_node_with_children(
            'cg-commit', **{'cg-id': self.cgid})
        try:
            self.server.invoke_successfully(cgcommit,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error committing CG snapshot %s: %s" %
                                  (self.snapshot, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Applies action from playbook'''
        netapp_utils.ems_log_event("na_ontap_cg_snapshot", self.server)
        changed = self.cgcreate()
        self.module.exit_json(changed=changed)


def main():
    '''Execute action from playbook'''
    cg_obj = NetAppONTAPCGSnapshot()
    cg_obj.apply()


if __name__ == '__main__':
    main()
