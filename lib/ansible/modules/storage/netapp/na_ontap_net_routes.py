#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_net_routes
short_description: NetApp ONTAP network routes
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (ng-ansibleteam@netapp.com)
description:
- Modify ONTAP network routes.
options:
  state:
    description:
    - Whether you want to create or delete a network route.
    choices: ['present', 'absent']
    default: present
  vserver:
    description:
    - The name of the vserver.
    required: true
  destination:
    description:
    - Specify the route destination.
    - Example 10.7.125.5/20, fd20:13::/64.
    required: true
  gateway:
    description:
    - Specify the route gateway.
    - Example 10.7.125.1, fd20:13::1.
    required: true
  metric:
    description:
    - Specify the route metric.
    - If this field is not provided the default will be set to 20.
  new_destination:
    description:
    - Specify the new route destination.
  new_gateway:
    description:
    - Specify the new route gateway.
  new_metric:
    description:
    - Specify the new route metric.
'''

EXAMPLES = """
    - name: create route
      na_ontap_net_routes:
        state=present
        vserver={{ Vserver name }}
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        destination=10.7.125.5/20
        gateway=10.7.125.1
        metric=30
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapNetRoutes(object):
    """
    Create, Modifies and Destroys a Net Route
    """

    def __init__(self):
        """
        Initialize the Ontap Net Route class
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            destination=dict(required=True, type='str'),
            gateway=dict(required=True, type='str'),
            metric=dict(required=False, type='str'),
            new_destination=dict(required=False, type='str', default=None),
            new_gateway=dict(required=False, type='str', default=None),
            new_metric=dict(required=False, type='str', default=None),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])
        return

    def create_net_route(self, current_metric=None):
        """
        Creates a new Route
        """
        route_obj = netapp_utils.zapi.NaElement('net-routes-create')
        route_obj.add_new_child("destination", self.parameters['destination'])
        route_obj.add_new_child("gateway", self.parameters['gateway'])
        if current_metric is None and self.parameters.get('metric') is not None:
            metric = self.parameters['metric']
        else:
            metric = current_metric
        route_obj.add_new_child("metric", metric)
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating net route: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def delete_net_route(self):
        """
        Deletes a given Route
        """
        route_obj = netapp_utils.zapi.NaElement('net-routes-destroy')
        route_obj.add_new_child("destination", self.parameters['destination'])
        route_obj.add_new_child("gateway", self.parameters['gateway'])
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting net route: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def modify_net_route(self, current, desired):
        """
        Modify a net route
        """
        # return if there is nothing to change
        for key, val in desired.items():
            if val == current[key]:
                self.na_helper.changed = False
                return
        # delete and re-create with new params
        self.delete_net_route()
        route_obj = netapp_utils.zapi.NaElement('net-routes-create')
        for attribute in ['metric', 'destination', 'gateway']:
            if desired.get(attribute) is not None:
                value = desired[attribute]
            else:
                value = current[attribute]
            route_obj.add_new_child(attribute, value)
        try:
            result = self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            # restore the old route, create the route with the existing metric
            self.create_net_route(current['metric'])
            # return if desired route already exists
            if to_native(error.code) == '13001':
                return
            # Invalid value specified for any of the attributes
            self.module.fail_json(msg='Error modifying net route: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def get_net_route(self, params=None):
        """
        Checks to see if a route exist or not
        :return: NaElement object if a route exists, None otherwise
        """
        if params is not None:
            # we need at least on of the new_destination or new_gateway to fetch desired route
            if params.get('destination') is None and params.get('gateway') is None:
                return None
        current = dict()
        route_obj = netapp_utils.zapi.NaElement('net-routes-get')
        for attr in ['destination', 'gateway']:
            if params and params.get(attr) is not None:
                value = params[attr]
            else:
                value = self.parameters[attr]
            route_obj.add_new_child(attr, value)
        try:
            result = self.server.invoke_successfully(route_obj, True)
            route_info = result.get_child_by_name('attributes').get_child_by_name('net-vs-routes-info')
            current['destination'] = route_info.get_child_content('destination')
            current['gateway'] = route_info.get_child_content('gateway')
            current['metric'] = route_info.get_child_content('metric')
        except netapp_utils.zapi.NaApiError as error:
            # Error 13040 denotes a route doesn't exist.
            if to_native(error.code) == "15661":
                return None
            self.module.fail_json(msg='Error fetching net route: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())
        return current

    def is_modify_action(self, current, desired):
        """
        Get desired action to be applied for net routes
        Destination and gateway are unique params for a route and cannot be duplicated
        So if a route with desired destination or gateway exists already, we don't try to modify
        :param current: current details
        :param desired: desired details
        :return: create / delete / modify / None
        """
        if current is None and desired is None:
            # this is invalid
            # cannot modify a non existent resource
            return None
        if current is None and desired is not None:
            # idempotency or duplication
            # we need not create
            return False
        if current is not None and desired is not None:
            # we can't modify an ambiguous route (idempotency/duplication)
            return False
        return True

    def get_params_to_be_modified(self, current):
        """
        Get parameters and values that need to be modified
        :param current: current details
        :return: dict(), None
        """
        if current is None:
            return None
        desired = dict()
        if self.parameters.get('new_destination') is not None and \
                self.parameters['new_destination'] != current['destination']:
            desired['destination'] = self.parameters['new_destination']
        if self.parameters.get('new_gateway') is not None and \
                self.parameters['new_gateway'] != current['gateway']:
            desired['gateway'] = self.parameters['new_gateway']
        if self.parameters.get('new_metric') is not None and \
                self.parameters['new_metric'] != current['metric']:
            desired['metric'] = self.parameters['new_metric']
        return desired

    def apply(self):
        """
        Run Module based on play book
        """
        # changed = False
        netapp_utils.ems_log_event("na_ontap_net_routes", self.server)
        # route_exists = False
        current = self.get_net_route()
        modify, cd_action = None, None
        modify_params = {'destination': self.parameters.get('new_destination'),
                         'gateway': self.parameters.get('new_gateway'),
                         'metric': self.parameters.get('new_metric')}
        # if any new_* param is present in playbook, check for modify action
        if any(modify_params.values()):
            # get parameters that are eligible for modify
            d = self.get_net_route(modify_params)
            modify = self.na_helper.is_rename_action(current, d)
            if modify is None:
                self.module.fail_json(msg="Error modifying: route %s does not exist" % self.parameters['destination'])
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)

        if cd_action == 'create':
            self.create_net_route()
        elif cd_action == 'delete':
            self.delete_net_route()
        elif modify:
            self.modify_net_route(current, modify_params)

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Creates the NetApp Ontap Net Route object and runs the correct play task
    """
    obj = NetAppOntapNetRoutes()
    obj.apply()


if __name__ == '__main__':
    main()
