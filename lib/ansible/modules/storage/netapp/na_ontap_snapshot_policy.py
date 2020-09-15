#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_snapshot_policy
short_description: NetApp ONTAP manage Snapshot Policy
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create/Modify/Delete ONTAP snapshot policies
options:
  state:
    description:
    - If you want to create, modify or delete a snapshot policy.
    choices: ['present', 'absent']
    default: present
  name:
    description:
      Name of the snapshot policy to be managed.
      The maximum string length is 256 characters.
    required: true
  enabled:
    description:
    - Status of the snapshot policy indicating whether the policy will be enabled or disabled.
    type: bool
  comment:
    description:
      A human readable comment attached with the snapshot.
      The size of the comment can be at most 255 characters.
  count:
    description:
      Retention count for the snapshots created by the schedule.
    type: list
  schedule:
    description:
    - Schedule to be added inside the policy.
    type: list
  snapmirror_label:
    description:
    - SnapMirror label assigned to each schedule inside the policy. Use an empty
      string ('') for no label.
    type: list
    required: false
    version_added: '2.9'
  vserver:
    description:
    - The name of the vserver to use. In a multi-tenanted environment, assigning a
      Snapshot Policy to a vserver will restrict its use to that vserver.
    required: false
    version_added: '2.9'
'''
EXAMPLES = """
    - name: Create Snapshot policy
      na_ontap_snapshot_policy:
        state: present
        name: ansible2
        schedule: hourly
        count: 150
        enabled: True
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        https: False

    - name: Create Snapshot policy with multiple schedules
      na_ontap_snapshot_policy:
        state: present
        name: ansible2
        schedule: ['hourly', 'daily', 'weekly', 'monthly', '5min']
        count: [1, 2, 3, 4, 5]
        enabled: True
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        https: False

    - name: Create Snapshot policy owned by a vserver
      na_ontap_snapshot_policy:
        state: present
        name: ansible3
        vserver: ansible
        schedule: ['hourly', 'daily', 'weekly', 'monthly', '5min']
        count: [1, 2, 3, 4, 5]
        snapmirror_label: ['hourly', 'daily', 'weekly', 'monthly', '']
        enabled: True
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        https: False

    - name: Modify Snapshot policy with multiple schedules
      na_ontap_snapshot_policy:
        state: present
        name: ansible2
        schedule: ['daily', 'weekly']
        count: [20, 30]
        snapmirror_label: ['daily', 'weekly']
        enabled: True
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        https: False

    - name: Delete Snapshot policy
      na_ontap_snapshot_policy:
        state: absent
        name: ansible2
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        https: False
"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapSnapshotPolicy(object):
    """
    Creates and deletes a Snapshot Policy
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            name=dict(required=True, type="str"),
            enabled=dict(required=False, type="bool"),
            # count is a list of integers
            count=dict(required=False, type="list", elements="int"),
            comment=dict(required=False, type="str"),
            schedule=dict(required=False, type="list", elements="str"),
            snapmirror_label=dict(required=False, type="list", elements="str"),
            vserver=dict(required=False, type="str")
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['enabled', 'count', 'schedule']),
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            if 'vserver' in self.parameters:
                self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])
            else:
                self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
        return

    def get_snapshot_policy(self):
        """
        Checks to see if a snapshot policy exists or not
        :return: Return policy details if a snapshot policy exists, None if it doesn't
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-policy-get-iter")
        # compose query
        query = netapp_utils.zapi.NaElement("query")
        snapshot_info_obj = netapp_utils.zapi.NaElement("snapshot-policy-info")
        snapshot_info_obj.add_new_child("policy", self.parameters['name'])
        if 'vserver' in self.parameters:
            snapshot_info_obj.add_new_child("vserver-name", self.parameters['vserver'])
        query.add_child_elem(snapshot_info_obj)
        snapshot_obj.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(snapshot_obj, True)
            if result.get_child_by_name('num-records') and \
                    int(result.get_child_content('num-records')) == 1:
                snapshot_policy = result.get_child_by_name('attributes-list').get_child_by_name('snapshot-policy-info')
                current = {}
                current['name'] = snapshot_policy.get_child_content('policy')
                current['vserver'] = snapshot_policy.get_child_content('vserver-name')
                current['enabled'] = False if snapshot_policy.get_child_content('enabled').lower() == 'false' else True
                current['comment'] = snapshot_policy.get_child_content('comment') or ''
                current['schedule'], current['count'], current['snapmirror_label'] = [], [], []
                if snapshot_policy.get_child_by_name('snapshot-policy-schedules'):
                    for schedule in snapshot_policy['snapshot-policy-schedules'].get_children():
                        current['schedule'].append(schedule.get_child_content('schedule'))
                        current['count'].append(int(schedule.get_child_content('count')))
                        snapmirror_label = schedule.get_child_content('snapmirror-label')
                        if snapmirror_label is None or snapmirror_label == '-':
                            snapmirror_label = ''
                        current['snapmirror_label'].append(snapmirror_label)
                return current
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg=to_native(error), exception=traceback.format_exc())
        return None

    def validate_parameters(self):
        """
        Validate if each schedule has a count associated
        :return: None
        """
        if 'count' not in self.parameters or 'schedule' not in self.parameters or \
                len(self.parameters['count']) > 5 or len(self.parameters['schedule']) > 5 or \
                len(self.parameters['count']) < 1 or len(self.parameters['schedule']) < 1 or \
                len(self.parameters['count']) != len(self.parameters['schedule']):
            self.module.fail_json(msg="Error: A Snapshot policy must have at least 1 "
                                      "schedule and can have up to a maximum of 5 schedules, with a count "
                                      "representing the maximum number of Snapshot copies for each schedule")

        if 'snapmirror_label' in self.parameters:
            if len(self.parameters['snapmirror_label']) != len(self.parameters['schedule']):
                self.module.fail_json(msg="Error: Each Snapshot Policy schedule must have an "
                                          "accompanying SnapMirror Label")

    def modify_snapshot_policy(self, current):
        """
        Modifies an existing snapshot policy
        """
        # Set up required variables to modify snapshot policy
        options = {'policy': self.parameters['name']}
        modify = False

        # Set up optional variables to modify snapshot policy
        if 'enabled' in self.parameters and self.parameters['enabled'] != current['enabled']:
            options['enabled'] = str(self.parameters['enabled'])
            modify = True
        if 'comment' in self.parameters and self.parameters['comment'] != current['comment']:
            options['comment'] = self.parameters['comment']
            modify = True

        if modify:
            snapshot_obj = netapp_utils.zapi.NaElement.create_node_with_children('snapshot-policy-modify', **options)
            try:
                self.server.invoke_successfully(snapshot_obj, True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg='Error modifying snapshot policy %s: %s' %
                                      (self.parameters['name'], to_native(error)),
                                      exception=traceback.format_exc())

    def modify_snapshot_policy_schedules(self, current):
        """
        Modify existing schedules in snapshot policy
        :return: None
        """
        self.validate_parameters()

        delete_schedules, modify_schedules, add_schedules = [], [], []

        if 'snapmirror_label' in self.parameters:
            snapmirror_labels = self.parameters['snapmirror_label']
        else:
            # User hasn't supplied any snapmirror labels.
            snapmirror_labels = [None] * len(self.parameters['schedule'])

        # Identify schedules for deletion
        for schedule in current['schedule']:
            schedule = schedule.strip()
            if schedule not in [item.strip() for item in self.parameters['schedule']]:
                options = {'policy': current['name'],
                           'schedule': schedule}
                delete_schedules.append(options)

        # Identify schedules to be modified or added
        for schedule, count, snapmirror_label in zip(self.parameters['schedule'], self.parameters['count'], snapmirror_labels):
            schedule = schedule.strip()
            if snapmirror_label is not None:
                snapmirror_label = snapmirror_label.strip()

            options = {'policy': current['name'],
                       'schedule': schedule}

            if schedule in current['schedule']:
                # Schedule exists. Only modify if it has changed.
                modify = False
                schedule_index = current['schedule'].index(schedule)

                if count != current['count'][schedule_index]:
                    options['new-count'] = str(count)
                    modify = True

                if snapmirror_label is not None:
                    if snapmirror_label != current['snapmirror_label'][schedule_index]:
                        options['new-snapmirror-label'] = snapmirror_label
                        modify = True

                if modify:
                    modify_schedules.append(options)
            else:
                # New schedule
                options['count'] = str(count)
                if snapmirror_label is not None and snapmirror_label != '':
                    options['snapmirror-label'] = snapmirror_label
                add_schedules.append(options)

        # Delete N-1 schedules no longer required. Must leave 1 schedule in policy
        # at any one time. Delete last one afterwards.
        while len(delete_schedules) > 1:
            options = delete_schedules.pop()
            self.modify_snapshot_policy_schedule(options, 'snapshot-policy-remove-schedule')

        # Modify schedules.
        while len(modify_schedules) > 0:
            options = modify_schedules.pop()
            self.modify_snapshot_policy_schedule(options, 'snapshot-policy-modify-schedule')

        # Add N-1 new schedules. Add last one after last schedule has been deleted.
        while len(add_schedules) > 1:
            options = add_schedules.pop()
            self.modify_snapshot_policy_schedule(options, 'snapshot-policy-add-schedule')

        # Delete last schedule no longer required.
        while len(delete_schedules) > 0:
            options = delete_schedules.pop()
            self.modify_snapshot_policy_schedule(options, 'snapshot-policy-remove-schedule')

        # Add last new schedule.
        while len(add_schedules) > 0:
            options = add_schedules.pop()
            self.modify_snapshot_policy_schedule(options, 'snapshot-policy-add-schedule')

    def modify_snapshot_policy_schedule(self, options, zapi):
        """
        Add, modify or remove a schedule to/from a snapshot policy
        """
        snapshot_obj = netapp_utils.zapi.NaElement.create_node_with_children(zapi, **options)
        try:
            self.server.invoke_successfully(snapshot_obj, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying snapshot policy schedule %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def create_snapshot_policy(self):
        """
        Creates a new snapshot policy
        """
        # set up required variables to create a snapshot policy
        self.validate_parameters()
        options = {'policy': self.parameters['name'],
                   'enabled': str(self.parameters['enabled']),
                   }

        if 'snapmirror_label' in self.parameters:
            snapmirror_labels = self.parameters['snapmirror_label']
        else:
            # User hasn't supplied any snapmirror labels.
            snapmirror_labels = [None] * len(self.parameters['schedule'])

        # zapi attribute for first schedule is schedule1, second is schedule2 and so on
        positions = [str(i) for i in range(1, len(self.parameters['schedule']) + 1)]
        for schedule, count, snapmirror_label, position in zip(self.parameters['schedule'], self.parameters['count'], snapmirror_labels, positions):
            schedule = schedule.strip()
            options['count' + position] = str(count)
            options['schedule' + position] = schedule
            if snapmirror_label is not None:
                snapmirror_label = snapmirror_label.strip()
                if snapmirror_label != '':
                    options['snapmirror-label' + position] = snapmirror_label
        snapshot_obj = netapp_utils.zapi.NaElement.create_node_with_children('snapshot-policy-create', **options)

        # Set up optional variables to create a snapshot policy
        if self.parameters.get('comment'):
            snapshot_obj.add_new_child("comment", self.parameters['comment'])
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating snapshot policy %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_snapshot_policy(self):
        """
        Deletes an existing snapshot policy
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-policy-delete")

        # Set up required variables to delete a snapshot policy
        snapshot_obj.add_new_child("policy", self.parameters['name'])
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting snapshot policy %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event(event_name, cserver)

    def apply(self):
        """
        Check to see which play we should run
        """
        self.asup_log_for_cserver("na_ontap_snapshot_policy")
        current = self.get_snapshot_policy()
        modify = None
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action is None and self.parameters['state'] == 'present':
            # Don't sort schedule/count/snapmirror_label lists as it can
            # mess up the intended parameter order.
            modify = self.na_helper.get_modified_attributes(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_snapshot_policy()
                elif cd_action == 'delete':
                    self.delete_snapshot_policy()
                if modify:
                    self.modify_snapshot_policy(current)
                    self.modify_snapshot_policy_schedules(current)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Creates and deletes a Snapshot Policy
    """
    obj = NetAppOntapSnapshotPolicy()
    obj.apply()


if __name__ == '__main__':
    main()
