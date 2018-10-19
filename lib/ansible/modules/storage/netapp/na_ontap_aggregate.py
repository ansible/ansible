#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_aggregate

short_description: NetApp ONTAP manage aggregates.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (ng-ansibleteam@netapp.com)

description:
- Create, delete, or manage aggregates on ONTAP.

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

  from_name:
    description:
    - Name of the aggregate to be renamed.
    version_added: '2.7'

  nodes:
    description:
    - Node(s) for the aggregate to be created on.  If no node specified, mgmt lif home will be used.
    - If multiple nodes specified an aggr stripe will be made.

  disk_type:
    description:
    - Type of disk to use to build aggregate
    choices: ['ATA', 'BSAS', 'FCAL', 'FSAS', 'LUN', 'MSATA', 'SAS', 'SSD', 'VMDISK']
    version_added: '2.7'

  disk_count:
    description:
    - Number of disks to place into the aggregate, including parity disks.
    - The disks in this newly-created aggregate come from the spare disk pool.
    - The smallest disks in this pool join the aggregate first, unless the C(disk-size) argument is provided.
    - Either C(disk-count) or C(disks) must be supplied. Range [0..2^31-1].
    - Required when C(state=present).

  disk_size:
    description:
    - Disk size to use in 4K block size.  Disks within 10% of specified size will be used.
    version_added: '2.7'

  raid_size:
    description:
    - Sets the maximum number of drives per raid group.
    version_added: '2.7'

  raid_type:
    description:
    - Specifies the type of RAID groups to use in the new aggregate.
    - The default value is raid4 on most platforms.
    version_added: '2.7'

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
from ansible.module_utils.netapp_module import NetAppModule

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
            from_name=dict(required=False, type='str'),
            disk_count=dict(required=False, type='int', default=None),
            disk_type=dict(required=False, choices=['ATA', 'BSAS', 'FCAL', 'FSAS', 'LUN', 'MSATA', 'SAS', 'SSD',
                                                    'VMDISK']),
            raid_type=dict(required=False, type='str'),
            disk_size=dict(required=False, type='int'),
            nodes=dict(required=False, type='list'),
            raid_size=dict(required=False, type='int'),
            unmount_volumes=dict(required=False, type='bool'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('service_state', 'offline', ['unmount_volumes'])
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def aggr_get_iter(self, name):
        """
        Return aggr-get-iter query results
        :param name: Name of the aggregate
        :return: NaElement if aggregate found, None otherwise
        """

        aggr_get_iter = netapp_utils.zapi.NaElement('aggr-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-attributes', **{'aggregate-name': name})
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        aggr_get_iter.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(aggr_get_iter, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            # Error 13040 denotes an aggregate not being found.
            if to_native(error.code) == "13040":
                return None
            else:
                self.module.fail_json(msg=to_native(error), exception=traceback.format_exc())
        return result

    def get_aggr(self, name=None):
        """
        Fetch details if aggregate exists.
        :param name: Name of the aggregate to be fetched
        :return:
            Dictionary of current details if aggregate found
            None if aggregate is not found
        """
        if name is None:
            name = self.parameters['name']
        aggr_get = self.aggr_get_iter(name)
        if (aggr_get and aggr_get.get_child_by_name('num-records') and
                int(aggr_get.get_child_content('num-records')) >= 1):
            current_aggr = dict()
            attr = aggr_get.get_child_by_name('attributes-list').get_child_by_name('aggr-attributes')
            current_aggr['service_state'] = attr.get_child_by_name('aggr-raid-attributes').get_child_content('state')
            return current_aggr
        return None

    def aggregate_online(self):
        """
        Set state of an offline aggregate to online
        :return: None
        """
        online_aggr = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-online', **{'aggregate': self.parameters['name'],
                              'force-online': 'true'})
        try:
            self.server.invoke_successfully(online_aggr,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error changing the state of aggregate %s to %s: %s' %
                                  (self.parameters['name'], self.parameters['service_state'], to_native(error)),
                                  exception=traceback.format_exc())

    def aggregate_offline(self):
        """
        Set state of an online aggregate to offline
        :return: None
        """
        offline_aggr = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-offline', **{'aggregate': self.parameters['name'],
                               'force-offline': 'false',
                               'unmount-volumes': str(self.parameters['unmount_volumes'])})
        try:
            self.server.invoke_successfully(offline_aggr, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error changing the state of aggregate %s to %s: %s' %
                                  (self.parameters['name'], self.parameters['service_state'], to_native(error)),
                                  exception=traceback.format_exc())

    def create_aggr(self):
        """
        Create aggregate
        :return: None
        """
        if not self.parameters.get('disk_count'):
            self.module.fail_json(msg='Error provisioning aggregate %s: \
                                             disk_count is required' % self.parameters['name'])
        options = {'aggregate': self.parameters['name'],
                   'disk-count': str(self.parameters['disk_count'])
                   }
        if self.parameters.get('disk_type'):
            options['disk-type'] = self.parameters['disk_type']
        if self.parameters.get('raid_size'):
            options['raid-size'] = str(self.parameters['raid_size'])
        if self.parameters.get('raid_type'):
            options['raid-type'] = self.parameters['raid_type']
        if self.parameters.get('disk_size'):
            options['disk-size'] = str(self.parameters['disk_size'])
        aggr_create = netapp_utils.zapi.NaElement.create_node_with_children('aggr-create', **options)
        if self.parameters.get('nodes'):
            nodes_obj = netapp_utils.zapi.NaElement('nodes')
            aggr_create.add_child_elem(nodes_obj)
            for node in self.parameters['nodes']:
                nodes_obj.add_new_child('node-name', node)

        try:
            self.server.invoke_successfully(aggr_create, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error provisioning aggregate %s: %s"
                                      % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_aggr(self):
        """
        Delete aggregate.
        :return: None
        """
        aggr_destroy = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-destroy', **{'aggregate': self.parameters['name']})

        try:
            self.server.invoke_successfully(aggr_destroy,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error removing aggregate %s: %s" % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def rename_aggregate(self):
        """
        Rename aggregate.
        """
        aggr_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-rename', **{'aggregate': self.parameters['from_name'],
                              'new-aggregate-name': self.parameters['name']})

        try:
            self.server.invoke_successfully(aggr_rename, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error renaming aggregate %s: %s"
                                      % (self.parameters['from_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_aggr(self, modify):
        """
        Modify state of the aggregate
        :param modify: dictionary of parameters to be modified
        :return: None
        """
        if modify['service_state'] == 'offline':
            self.aggregate_offline()
        elif modify['service_state'] == 'online':
            self.aggregate_online()

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
        Apply action to the aggregate
        :return: None
        """
        self.asup_log_for_cserver("na_ontap_aggregate")

        current = self.get_aggr()
        # rename and create are mutually exclusive
        rename, cd_action = None, None
        if self.parameters.get('from_name'):
            rename = self.na_helper.is_rename_action(self.get_aggr(self.parameters['from_name']), current)
            if rename is None:
                self.module.fail_json(msg="Error renaming: aggregate %s does not exist" % self.parameters['from_name'])
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_aggregate()
                elif cd_action == 'create':
                    self.create_aggr()
                elif cd_action == 'delete':
                    self.delete_aggr()
                elif modify:
                    self.modify_aggr(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Create Aggregate class instance and invoke apply
    :return: None
    """
    obj_aggr = NetAppOntapAggregate()
    obj_aggr.apply()


if __name__ == '__main__':
    main()
