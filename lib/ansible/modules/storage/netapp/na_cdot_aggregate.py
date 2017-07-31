#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_aggregate

short_description: Manage NetApp cDOT aggregates.
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy aggregates on NetApp cDOT.

options:

  state:
    required: true
    description:
    - Whether the specified aggregate should exist or not.
    choices: ['present', 'absent']

  name:
    required: true
    description:
    - The name of the aggregate to manage.

  disk_count:
    description:
    - Number of disks to place into the aggregate, including parity disks.
    - The disks in this newly-created aggregate come from the spare disk pool.
    - The smallest disks in this pool join the aggregate first, unless the C(disk-size) argument is provided.
    - Either C(disk-count) or C(disks) must be supplied. Range [0..2^31-1].
    - Required when C(state=present).

'''

EXAMPLES = """
- name: Manage Aggregates
  na_cdot_aggregate:
    state: present
    name: ansibleAggr
    disk_count: 1
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Manage Aggregates
  na_cdot_aggregate:
    state: present
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


class NetAppCDOTAggregate(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            disk_count=dict(required=False, type='int'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['disk_count'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.disk_count = p['disk_count']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)

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
        except netapp_utils.zapi.NaApiError as e:
            # Error 13040 denotes an aggregate not being found.
            if to_native(e.code) == "13040":
                return False
            else:
                self.module.fail_json(msg=to_native(e), exception=traceback.format_exc())

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return True
        else:
            return False

    def create_aggr(self):
        aggr_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-create', **{'aggregate': self.name,
                              'disk-count': str(self.disk_count)})

        try:
            self.server.invoke_successfully(aggr_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error provisioning aggregate %s: %s" % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_aggr(self):
        aggr_destroy = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-destroy', **{'aggregate': self.name})

        try:
            self.server.invoke_successfully(aggr_destroy,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error removing aggregate %s: %s" % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def rename_aggregate(self):
        aggr_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-rename', **{'aggregate': self.name,
                              'new-aggregate-name':
                                  self.name})

        try:
            self.server.invoke_successfully(aggr_rename,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error renaming aggregate %s: %s" % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        aggregate_exists = self.get_aggr()
        rename_aggregate = False

        # check if anything needs to be changed (add/delete/update)

        if aggregate_exists:
            if self.state == 'absent':
                changed = True

            elif self.state == 'present':
                if self.name is not None and not self.name == \
                        self.name:
                    rename_aggregate = True
                    changed = True

        else:
            if self.state == 'present':
                # Aggregate does not exist, but requested state is present.
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not aggregate_exists:
                        self.create_aggr()

                    else:
                        if rename_aggregate:
                            self.rename_aggregate()

                elif self.state == 'absent':
                    self.delete_aggr()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTAggregate()
    v.apply()


if __name__ == '__main__':
    main()
