#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
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
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

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
    choices: ['raid4', 'raid_dp', 'raid_tec']
    version_added: '2.7'

  unmount_volumes:
    type: bool
    description:
    - If set to "TRUE", this option specifies that all of the volumes hosted by the given aggregate are to be unmounted
    - before the offline operation is executed.
    - By default, the system will reject any attempt to offline an aggregate that hosts one or more online volumes.

  disks:
    type: list
    description:
    - Specific list of disks to use for the new aggregate.
    - To create a "mirrored" aggregate with a specific list of disks, both 'disks' and 'mirror_disks' options must be supplied.
      Additionally, the same number of disks must be supplied in both lists.
    version_added: '2.8'

  is_mirrored:
    type: bool
    description:
    - Specifies that the new aggregate be mirrored (have two plexes).
    - If set to true, then the indicated disks will be split across the two plexes. By default, the new aggregate will not be mirrored.
    - This option cannot be used when a specific list of disks is supplied with either the 'disks' or 'mirror_disks' options.
    version_added: '2.8'

  mirror_disks:
    type: list
    description:
    - List of mirror disks to use. It must contain the same number of disks specified in 'disks'.
    version_added: '2.8'

  spare_pool:
    description:
    - Specifies the spare pool from which to select spare disks to use in creation of a new aggregate.
    choices: ['Pool0', 'Pool1']
    version_added: '2.8'

  wait_for_online:
    description:
    - Set this parameter to 'true' for synchronous execution during create (wait until aggregate status is online)
    - Set this parameter to 'false' for asynchronous execution
    - For asynchronous, execution exits as soon as the request is sent, without checking aggregate status
    type: bool
    default: false
    version_added: '2.8'

  time_out:
    description:
      - time to wait for aggregate creation in seconds
      - default is set to 100 seconds
    default: 100
    version_added: "2.8"
'''

EXAMPLES = """
- name: Create Aggregates and wait 5 minutes until aggregate is online
  na_ontap_aggregate:
    state: present
    service_state: online
    name: ansibleAggr
    disk_count: 1
    wait_for_online: True
    time_out: 300
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
    from_name: ansibleAggr
    name: ansibleAggr2
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
import time
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
            name=dict(required=True, type='str'),
            disks=dict(required=False, type='list'),
            disk_count=dict(required=False, type='int', default=None),
            disk_size=dict(required=False, type='int'),
            disk_type=dict(required=False, choices=['ATA', 'BSAS', 'FCAL', 'FSAS', 'LUN', 'MSATA', 'SAS', 'SSD', 'VMDISK']),
            from_name=dict(required=False, type='str'),
            mirror_disks=dict(required=False, type='list'),
            nodes=dict(required=False, type='list'),
            is_mirrored=dict(required=False, type='bool'),
            raid_size=dict(required=False, type='int'),
            raid_type=dict(required=False, choices=['raid4', 'raid_dp', 'raid_tec']),
            service_state=dict(required=False, choices=['online', 'offline']),
            spare_pool=dict(required=False, choices=['Pool0', 'Pool1']),
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            unmount_volumes=dict(required=False, type='bool'),
            wait_for_online=dict(required=False, type='bool', default=False),
            time_out=dict(required=False, type='int', default=100)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('service_state', 'offline', ['unmount_volumes']),
            ],
            mutually_exclusive=[
                ('is_mirrored', 'disks'),
                ('is_mirrored', 'mirror_disks'),
                ('is_mirrored', 'spare_pool'),
                ('spare_pool', 'disks')
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        if self.parameters.get('mirror_disks') is not None and self.parameters.get('disks') is None:
            self.module.fail_json(mgs="mirror_disks require disks options to be set")
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
        result = None
        try:
            result = self.server.invoke_successfully(aggr_get_iter, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            # Error 13040 denotes an aggregate not being found.
            if to_native(error.code) == "13040":
                pass
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
        if self.parameters.get('is_mirrored'):
            options['is-mirrored'] = str(self.parameters['is_mirrored'])
        if self.parameters.get('spare_pool'):
            options['spare-pool'] = self.parameters['spare_pool']
        if self.parameters.get('raid_type'):
            options['raid-type'] = self.parameters['raid_type']
        aggr_create = netapp_utils.zapi.NaElement.create_node_with_children('aggr-create', **options)
        if self.parameters.get('nodes'):
            nodes_obj = netapp_utils.zapi.NaElement('nodes')
            aggr_create.add_child_elem(nodes_obj)
            for node in self.parameters['nodes']:
                nodes_obj.add_new_child('node-name', node)
        if self.parameters.get('disks'):
            disks_obj = netapp_utils.zapi.NaElement('disk-info')
            for disk in self.parameters.get('disks'):
                disks_obj.add_new_child('name', disk)
            aggr_create.add_child_elem(disks_obj)
        if self.parameters.get('mirror_disks'):
            mirror_disks_obj = netapp_utils.zapi.NaElement('disk-info')
            for disk in self.parameters.get('mirror_disks'):
                mirror_disks_obj.add_new_child('name', disk)
            aggr_create.add_child_elem(mirror_disks_obj)

        try:
            self.server.invoke_successfully(aggr_create, enable_tunneling=False)
            if self.parameters.get('wait_for_online'):
                # round off time_out
                retries = (self.parameters['time_out'] + 5) / 10
                current = self.get_aggr()
                status = None if current is None else current['service_state']
                while status != 'online' and retries > 0:
                    time.sleep(10)
                    retries = retries - 1
                    current = self.get_aggr()
                    status = None if current is None else current['service_state']
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
