#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_net_routes
short_description: Manage NetApp Ontap network routes
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author:
- Chris Archibald (carchi@netapp.com), Kevin Hutton (khutton@netapp.com)
description:
- Modify a Ontap network routes
options:
  state:
    description:
    - Whether you want to create or delete a network route
    choices: ['present', 'absent']
    default: present
  vserver:
    description:
    - The name of the vserver
    required: true
  destination:
    description:
    - Specify the route destination. Example 10.7.125.5/20, fd20:13::/64
    required: true
  gateway:
    description:
    - Specify the route gateway. Example 10.7.125.1, fd20:13::1
    required: true
  metric:
    description:
    - Specify the route metric.
    - If this field is not provided the default will be set to 30
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
            metric=dict(required=False, type='str', default=None),
            new_destination=dict(required=False, type='str', default=None),
            new_gateway=dict(required=False, type='str', default=None),
            new_metric=dict(required=False, type='str', default=None),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.vserver = parameters['vserver']
        self.destination = parameters['destination']
        self.gateway = parameters['gateway']
        self.metric = parameters['metric']
        self.new_destination = parameters['new_destination']
        self.new_gateway = parameters['new_destination']
        self.new_metric = parameters['new_metric']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)
        return

    def create_net_route(self):
        """
        Creates a new Route
        """
        route_obj = netapp_utils.zapi.NaElement('net-routes-create')
        route_obj.add_new_child("destination", self.destination)
        route_obj.add_new_child("gateway", self.gateway)
        if self.metric:
            route_obj.add_new_child("metric", self.metric)
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
        route_obj.add_new_child("destination", self.destination)
        route_obj.add_new_child("gateway", self.gateway)
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting net route: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def modify_net_route(self):
        """
        Modify a net route
        """
        self.delete_net_route()
        route_obj = netapp_utils.zapi.NaElement('net-routes-create')
        if self.new_destination:
            route_obj.add_new_child("destination", self.new_destination)
        else:
            route_obj.add_new_child("destination", self.destination)
        if self.new_gateway:
            route_obj.add_new_child("gateway", self.new_gateway)
        else:
            route_obj.add_new_child("gateway", self.gateway)
        if self.new_metric:
            route_obj.add_new_child("metric", self.new_metric)
        else:
            route_obj.add_new_child("metric", self.metric)
        # if anything goes wrong creating the new net route,
        # restore the old one
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError:
            self.create_net_route()

    def does_route_exists(self):
        """
        Checks to see if a route exist or not
        :return: True if a route exists, False if it does not
        """
        route_obj = netapp_utils.zapi.NaElement('net-routes-get')
        route_obj.add_new_child("destination", self.destination)
        route_obj.add_new_child("gateway", self.gateway)
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError:
            return False
        return True

    def apply(self):
        """
        Run Module based on play book
        """
        changed = False
        netapp_utils.ems_log_event("na_ontap_net_routes", self.server)
        route_exists = False
        existing_route = self.does_route_exists()

        if existing_route:
            route_exists = True
            if self.state == 'absent':
                changed = True
            elif self.state == 'present':
                if self.new_destination or \
                        self.new_gateway or self.new_metric:
                    changed = True
        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if not route_exists:
                    if self.state == 'present':
                        self.create_net_route()
                else:
                    if self.state == 'present':
                        self.modify_net_route()
                    elif self.state == 'absent':
                        self.delete_net_route()

        self.module.exit_json(changed=changed)


def main():
    """
    Creates the NetApp Ontap Net Route object and runs the correct play task
    """
    obj = NetAppOntapNetRoutes()
    obj.apply()


if __name__ == '__main__':
    main()
