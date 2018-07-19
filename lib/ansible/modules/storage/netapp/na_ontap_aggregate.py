#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_ontap_aggregate

short_description: Manage NetApp ONTAP aggregates.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: Sumit Kumar (sumit4@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)

description:
- Create or destroy aggregates on NetApp cDOT.

options:

  state:
    description:
    - Whether the specified aggregate should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  service_state:
    description:
    - Whether the specified aggregate should be enabled or disabled. Creates aggregate if doesnt exist.
    choices: ['online', 'offline']

  name:
    required: true
    description:
    - The name of the aggregate to manage.

  rename:
    description:
    - The name of the aggregate that replaces the current name.

  nodes:
    description:
    - List of node for the aggregate

  disk_count:
    description:
    - Number of disks to place into the aggregate, including parity disks.
    - The disks in this newly-created aggregate come from the spare disk pool.
    - The smallest disks in this pool join the aggregate first, unless the C(disk-size) argument is provided.
    - Either C(disk-count) or C(disks) must be supplied. Range [0..2^31-1].
    - Required when C(state=present).

  unmount_volumes:
    type: bool
    description:
    - If set to "TRUE", this option specifies that all of the volumes hosted by the given aggregate are to be unmounted
    - before the offline operation is executed.
    - By default, the system will reject any attempt to offline an aggregate that hosts one or more online volumes.

'''

EXAMPLES = """
- name: Create Aggregates
  na_ontap_aggregate:
    state: present
    service_state: online
    name: ansibleAggr
    disk_count: 1
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Manage Aggregates
  na_ontap_aggregate:
    state: present
    service_state: offline
    unmount_volumes: true
    name: ansibleAggr
    disk_count: 1
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Rename Aggregates
  na_ontap_aggregate:
    state: present
    service_state: online
    name: ansibleAggr
    rename: ansibleAggr2
    disk_count: 1
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Delete Aggregates
  na_ontap_aggregate:
    state: absent
    service_state: offline
    unmount_volumes: true
    name: ansibleAggr
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


class NetAppOntapAggregate(object):
    ''' object initialize and class methods '''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            service_state=dict(required=False, choices=['online', 'offline']),
            name=dict(required=True, type='str'),
            rename=dict(required=False, type='str'),
            disk_count=dict(required=False, type='int', default=None),
            nodes=dict(required=False, type='list'),
            unmount_volumes=dict(required=False, type='bool'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('service_state', 'offline', ['unmount_volumes'])
            ],
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.service_state = parameters['service_state']
        self.name = parameters['name']
        self.rename = parameters['rename']
        self.disk_count = parameters['disk_count']
        self.nodes = parameters['nodes']
        self.unmount_volumes = parameters['unmount_volumes']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_aggr(self):
        """
        Checks if aggregate exists.

        :return:
            True if aggregate found
            False if aggregate is not found
        :rtype: bool
        """

        aggr_get_iter = netapp_utils.zapi.NaElement('aggr-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-attributes', **{'aggregate-name': self.name})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        aggr_get_iter.add_child_elem(query)

        try:
            result = self.server.invoke_successfully(aggr_get_iter,
                                                     enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            # Error 13040 denotes an aggregate not being found.
            if to_native(error.code) == "13040":
                return False
            else:
                self.module.fail_json(msg=to_native(
                    error), exception=traceback.format_exc())

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return True
        return False

    def aggregate_online(self):
        """
        enable aggregate (online).
        """
        online_aggr = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-online', **{'aggregate': self.name,
                              'force-online': 'true'})
        try:
            self.server.invoke_successfully(online_aggr,
                                            enable_tunneling=True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == "13060":
                # Error 13060 denotes aggregate is already online
                return False
            else:
                self.module.fail_json(msg='Error changing the state of aggregate %s to %s: %s' %
                                      (self.name, self.service_state,
                                       to_native(error)),
                                      exception=traceback.format_exc())

    def aggregate_offline(self):
        """
        disable aggregate (offline).
        """
        offline_aggr = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-offline', **{'aggregate': self.name,
                               'force-offline': 'false',
                               'unmount-volumes': str(self.unmount_volumes)})
        try:
            self.server.invoke_successfully(offline_aggr,
                                            enable_tunneling=True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == "13042":
                # Error 13042 denotes aggregate is already offline
                return False
            else:
                self.module.fail_json(msg='Error changing the state of aggregate %s to %s: %s' %
                                      (self.name, self.service_state,
                                       to_native(error)),
                                      exception=traceback.format_exc())

    def create_aggr(self):
        """
        create aggregate.
        """
        aggr_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-create', **{'aggregate': self.name,
                              'disk-count': str(self.disk_count)})
        if self.nodes is not None:
            nodes_obj = netapp_utils.zapi.NaElement('nodes')
            aggr_create.add_child_elem(nodes_obj)
            for node in self.nodes:
                nodes_obj.add_new_child('node-name', node)
        try:
            self.server.invoke_successfully(aggr_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error provisioning aggregate %s: %s" % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_aggr(self):
        """
        delete aggregate.
        """
        aggr_destroy = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-destroy', **{'aggregate': self.name})

        try:
            self.server.invoke_successfully(aggr_destroy,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error removing aggregate %s: %s" % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def rename_aggregate(self):
        """
        rename aggregate.
        """
        aggr_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-rename', **{'aggregate': self.name,
                              'new-aggregate-name':
                                  self.rename})

        try:
            self.server.invoke_successfully(aggr_rename,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error renaming aggregate %s: %s" % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Apply action to aggregate'''
        changed = False
        size_changed = False
        aggregate_exists = self.get_aggr()
        rename_aggregate = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_aggregate", cserver)

        # check if anything needs to be changed (add/delete/update)

        if aggregate_exists:
            if self.state == 'absent':
                changed = True

            elif self.state == 'present':
                if self.service_state:
                    changed = True
                if self.rename is not None and self.name != \
                        self.rename:
                    rename_aggregate = True
                    changed = True

        else:
            if self.state == 'present':
                # Aggregate does not exist, but requested state is present.
                if (self.rename is None) and self.disk_count:
                    changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not aggregate_exists:
                        self.create_aggr()
                        if self.service_state == 'offline':
                            self.aggregate_offline()
                    else:
                        if self.service_state == 'online':
                            size_changed = self.aggregate_online()
                        elif self.service_state == 'offline':
                            size_changed = self.aggregate_offline()
                        if rename_aggregate:
                            self.rename_aggregate()
                        if not size_changed and not rename_aggregate:
                            changed = False

                elif self.state == 'absent':
                    if self.service_state == 'offline':
                        self.aggregate_offline()
                    self.delete_aggr()
        self.module.exit_json(changed=changed)


def main():
    ''' Create object and call apply '''
    obj_aggr = NetAppOntapAggregate()
    obj_aggr.apply()


if __name__ == '__main__':
    main()
