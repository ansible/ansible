#!/usr/bin/python
#
# Copyright (c) 2015 CenturyLink
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: clc_loadbalancer
short_description: Create, Delete shared loadbalancers in CenturyLink Cloud.
description:
  - An Ansible module to Create, Delete shared loadbalancers in CenturyLink Cloud.
version_added: "2.0"
options:
  name:
    description:
      - The name of the loadbalancer
    required: True
  description:
    description:
      - A description for the loadbalancer
  alias:
    description:
      - The alias of your CLC Account
    required: True
  location:
    description:
      - The location of the datacenter where the load balancer resides in
    required: True
  method:
    description:
      -The balancing method for the load balancer pool
    choices: ['leastConnection', 'roundRobin']
  persistence:
    description:
      - The persistence method for the load balancer
    choices: ['standard', 'sticky']
  port:
    description:
      - Port to configure on the public-facing side of the load balancer pool
    choices: [80, 443]
  nodes:
    description:
      - A list of nodes that needs to be added to the load balancer pool
    default: []
  status:
    description:
      - The status of the loadbalancer
    default: enabled
    choices: ['enabled', 'disabled']
  state:
    description:
      - Whether to create or delete the load balancer pool
    default: present
    choices: ['present', 'absent', 'port_absent', 'nodes_present', 'nodes_absent']
requirements:
    - python = 2.7
    - requests >= 2.5.0
    - clc-sdk
author: "CLC Runner (@clc-runner)"
notes:
    - To use this module, it is required to set the below environment variables which enables access to the
      Centurylink Cloud
          - CLC_V2_API_USERNAME, the account login id for the centurylink cloud
          - CLC_V2_API_PASSWORD, the account password for the centurylink cloud
    - Alternatively, the module accepts the API token and account alias. The API token can be generated using the
      CLC account login and password via the HTTP api call @ https://api.ctl.io/v2/authentication/login
          - CLC_V2_API_TOKEN, the API token generated from https://api.ctl.io/v2/authentication/login
          - CLC_ACCT_ALIAS, the account alias associated with the centurylink cloud
    - Users can set CLC_V2_API_URL to specify an endpoint for pointing to a different CLC environment.
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples
- name: Create Loadbalancer
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Create things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - ipAddress: 10.11.22.123
            privatePort: 80
        state: present

- name: Add node to an existing loadbalancer pool
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Create things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - ipAddress: 10.11.22.234
            privatePort: 80
        state: nodes_present

- name: Remove node from an existing loadbalancer pool
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Create things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - ipAddress: 10.11.22.234
            privatePort: 80
        state: nodes_absent

- name: Delete LoadbalancerPool
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Delete things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - ipAddress: 10.11.22.123
            privatePort: 80
        state: port_absent

- name: Delete Loadbalancer
  hosts: localhost
  connection: local
  tasks:
    - name: Actually Delete things
      clc_loadbalancer:
        name: test
        description: test
        alias: TEST
        location: WA1
        port: 443
        nodes:
          - ipAddress: 10.11.22.123
            privatePort: 80
        state: absent
'''

RETURN = '''
loadbalancer:
    description: The load balancer result object from CLC
    returned: success
    type: dict
    sample:
        {
           "description":"test-lb",
           "id":"ab5b18cb81e94ab9925b61d1ca043fb5",
           "ipAddress":"66.150.174.197",
           "links":[
              {
                 "href":"/v2/sharedLoadBalancers/wfad/wa1/ab5b18cb81e94ab9925b61d1ca043fb5",
                 "rel":"self",
                 "verbs":[
                    "GET",
                    "PUT",
                    "DELETE"
                 ]
              },
              {
                 "href":"/v2/sharedLoadBalancers/wfad/wa1/ab5b18cb81e94ab9925b61d1ca043fb5/pools",
                 "rel":"pools",
                 "verbs":[
                    "GET",
                    "POST"
                 ]
              }
           ],
           "name":"test-lb",
           "pools":[

           ],
           "status":"enabled"
        }
'''

__version__ = '${version}'

import json
import os
import traceback
from time import sleep
from distutils.version import LooseVersion

REQUESTS_IMP_ERR = None
try:
    import requests
except ImportError:
    REQUESTS_IMP_ERR = traceback.format_exc()
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
CLC_IMP_ERR = None
try:
    import clc as clc_sdk
    from clc import APIFailedResponse
except ImportError:
    CLC_IMP_ERR = traceback.format_exc()
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class ClcLoadBalancer:

    clc = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.lb_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(msg=missing_required_lib('clc-sdk'), exception=CLC_IMP_ERR)
        if not REQUESTS_FOUND:
            self.module.fail_json(msg=missing_required_lib('requests'), exception=REQUESTS_IMP_ERR)
        if requests.__version__ and LooseVersion(
                requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

        self._set_user_agent(self.clc)

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        changed = False
        result_lb = None
        loadbalancer_name = self.module.params.get('name')
        loadbalancer_alias = self.module.params.get('alias')
        loadbalancer_location = self.module.params.get('location')
        loadbalancer_description = self.module.params.get('description')
        loadbalancer_port = self.module.params.get('port')
        loadbalancer_method = self.module.params.get('method')
        loadbalancer_persistence = self.module.params.get('persistence')
        loadbalancer_nodes = self.module.params.get('nodes')
        loadbalancer_status = self.module.params.get('status')
        state = self.module.params.get('state')

        if loadbalancer_description is None:
            loadbalancer_description = loadbalancer_name

        self._set_clc_credentials_from_env()

        self.lb_dict = self._get_loadbalancer_list(
            alias=loadbalancer_alias,
            location=loadbalancer_location)

        if state == 'present':
            changed, result_lb, lb_id = self.ensure_loadbalancer_present(
                name=loadbalancer_name,
                alias=loadbalancer_alias,
                location=loadbalancer_location,
                description=loadbalancer_description,
                status=loadbalancer_status)
            if loadbalancer_port:
                changed, result_pool, pool_id = self.ensure_loadbalancerpool_present(
                    lb_id=lb_id,
                    alias=loadbalancer_alias,
                    location=loadbalancer_location,
                    method=loadbalancer_method,
                    persistence=loadbalancer_persistence,
                    port=loadbalancer_port)

                if loadbalancer_nodes:
                    changed, result_nodes = self.ensure_lbpool_nodes_set(
                        alias=loadbalancer_alias,
                        location=loadbalancer_location,
                        name=loadbalancer_name,
                        port=loadbalancer_port,
                        nodes=loadbalancer_nodes)
        elif state == 'absent':
            changed, result_lb = self.ensure_loadbalancer_absent(
                name=loadbalancer_name,
                alias=loadbalancer_alias,
                location=loadbalancer_location)

        elif state == 'port_absent':
            changed, result_lb = self.ensure_loadbalancerpool_absent(
                alias=loadbalancer_alias,
                location=loadbalancer_location,
                name=loadbalancer_name,
                port=loadbalancer_port)

        elif state == 'nodes_present':
            changed, result_lb = self.ensure_lbpool_nodes_present(
                alias=loadbalancer_alias,
                location=loadbalancer_location,
                name=loadbalancer_name,
                port=loadbalancer_port,
                nodes=loadbalancer_nodes)

        elif state == 'nodes_absent':
            changed, result_lb = self.ensure_lbpool_nodes_absent(
                alias=loadbalancer_alias,
                location=loadbalancer_location,
                name=loadbalancer_name,
                port=loadbalancer_port,
                nodes=loadbalancer_nodes)

        self.module.exit_json(changed=changed, loadbalancer=result_lb)

    def ensure_loadbalancer_present(
            self, name, alias, location, description, status):
        """
        Checks to see if a load balancer exists and creates one if it does not.
        :param name: Name of loadbalancer
        :param alias: Alias of account
        :param location: Datacenter
        :param description: Description of loadbalancer
        :param status: Enabled / Disabled
        :return: (changed, result, lb_id)
            changed: Boolean whether a change was made
            result: The result object from the CLC load balancer request
            lb_id: The load balancer id
        """
        changed = False
        result = name
        lb_id = self._loadbalancer_exists(name=name)
        if not lb_id:
            if not self.module.check_mode:
                result = self.create_loadbalancer(name=name,
                                                  alias=alias,
                                                  location=location,
                                                  description=description,
                                                  status=status)
                lb_id = result.get('id')
            changed = True

        return changed, result, lb_id

    def ensure_loadbalancerpool_present(
            self, lb_id, alias, location, method, persistence, port):
        """
        Checks to see if a load balancer pool exists and creates one if it does not.
        :param lb_id: The loadbalancer id
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param method: the load balancing method
        :param persistence: the load balancing persistence type
        :param port: the port that the load balancer will listen on
        :return: (changed, group, pool_id) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
            pool_id: The string id of the load balancer pool
        """
        changed = False
        result = port
        if not lb_id:
            return changed, None, None
        pool_id = self._loadbalancerpool_exists(
            alias=alias,
            location=location,
            port=port,
            lb_id=lb_id)
        if not pool_id:
            if not self.module.check_mode:
                result = self.create_loadbalancerpool(
                    alias=alias,
                    location=location,
                    lb_id=lb_id,
                    method=method,
                    persistence=persistence,
                    port=port)
                pool_id = result.get('id')
            changed = True

        return changed, result, pool_id

    def ensure_loadbalancer_absent(self, name, alias, location):
        """
        Checks to see if a load balancer exists and deletes it if it does
        :param name: Name of the load balancer
        :param alias: Alias of account
        :param location: Datacenter
        :return: (changed, result)
            changed: Boolean whether a change was made
            result: The result from the CLC API Call
        """
        changed = False
        result = name
        lb_exists = self._loadbalancer_exists(name=name)
        if lb_exists:
            if not self.module.check_mode:
                result = self.delete_loadbalancer(alias=alias,
                                                  location=location,
                                                  name=name)
            changed = True
        return changed, result

    def ensure_loadbalancerpool_absent(self, alias, location, name, port):
        """
        Checks to see if a load balancer pool exists and deletes it if it does
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param name: the name of the load balancer
        :param port: the port that the load balancer listens on
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        result = None
        lb_exists = self._loadbalancer_exists(name=name)
        if lb_exists:
            lb_id = self._get_loadbalancer_id(name=name)
            pool_id = self._loadbalancerpool_exists(
                alias=alias,
                location=location,
                port=port,
                lb_id=lb_id)
            if pool_id:
                changed = True
                if not self.module.check_mode:
                    result = self.delete_loadbalancerpool(
                        alias=alias,
                        location=location,
                        lb_id=lb_id,
                        pool_id=pool_id)
            else:
                result = "Pool doesn't exist"
        else:
            result = "LB Doesn't Exist"
        return changed, result

    def ensure_lbpool_nodes_set(self, alias, location, name, port, nodes):
        """
        Checks to see if the provided list of nodes exist for the pool
         and set the nodes if any in the list those doesn't exist
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param name: the name of the load balancer
        :param port: the port that the load balancer will listen on
        :param nodes: The list of nodes to be updated to the pool
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        result = {}
        changed = False
        lb_exists = self._loadbalancer_exists(name=name)
        if lb_exists:
            lb_id = self._get_loadbalancer_id(name=name)
            pool_id = self._loadbalancerpool_exists(
                alias=alias,
                location=location,
                port=port,
                lb_id=lb_id)
            if pool_id:
                nodes_exist = self._loadbalancerpool_nodes_exists(alias=alias,
                                                                  location=location,
                                                                  lb_id=lb_id,
                                                                  pool_id=pool_id,
                                                                  nodes_to_check=nodes)
                if not nodes_exist:
                    changed = True
                    result = self.set_loadbalancernodes(alias=alias,
                                                        location=location,
                                                        lb_id=lb_id,
                                                        pool_id=pool_id,
                                                        nodes=nodes)
            else:
                result = "Pool doesn't exist"
        else:
            result = "Load balancer doesn't Exist"
        return changed, result

    def ensure_lbpool_nodes_present(self, alias, location, name, port, nodes):
        """
        Checks to see if the provided list of nodes exist for the pool and add the missing nodes to the pool
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param name: the name of the load balancer
        :param port: the port that the load balancer will listen on
        :param nodes: the list of nodes to be added
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        lb_exists = self._loadbalancer_exists(name=name)
        if lb_exists:
            lb_id = self._get_loadbalancer_id(name=name)
            pool_id = self._loadbalancerpool_exists(
                alias=alias,
                location=location,
                port=port,
                lb_id=lb_id)
            if pool_id:
                changed, result = self.add_lbpool_nodes(alias=alias,
                                                        location=location,
                                                        lb_id=lb_id,
                                                        pool_id=pool_id,
                                                        nodes_to_add=nodes)
            else:
                result = "Pool doesn't exist"
        else:
            result = "Load balancer doesn't Exist"
        return changed, result

    def ensure_lbpool_nodes_absent(self, alias, location, name, port, nodes):
        """
        Checks to see if the provided list of nodes exist for the pool and removes them if found any
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param name: the name of the load balancer
        :param port: the port that the load balancer will listen on
        :param nodes: the list of nodes to be removed
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        lb_exists = self._loadbalancer_exists(name=name)
        if lb_exists:
            lb_id = self._get_loadbalancer_id(name=name)
            pool_id = self._loadbalancerpool_exists(
                alias=alias,
                location=location,
                port=port,
                lb_id=lb_id)
            if pool_id:
                changed, result = self.remove_lbpool_nodes(alias=alias,
                                                           location=location,
                                                           lb_id=lb_id,
                                                           pool_id=pool_id,
                                                           nodes_to_remove=nodes)
            else:
                result = "Pool doesn't exist"
        else:
            result = "Load balancer doesn't Exist"
        return changed, result

    def create_loadbalancer(self, name, alias, location, description, status):
        """
        Create a loadbalancer w/ params
        :param name: Name of loadbalancer
        :param alias: Alias of account
        :param location: Datacenter
        :param description: Description for loadbalancer to be created
        :param status: Enabled / Disabled
        :return: result: The result from the CLC API call
        """
        result = None
        try:
            result = self.clc.v2.API.Call('POST',
                                          '/v2/sharedLoadBalancers/%s/%s' % (alias,
                                                                             location),
                                          json.dumps({"name": name,
                                                      "description": description,
                                                      "status": status}))
            sleep(1)
        except APIFailedResponse as e:
            self.module.fail_json(
                msg='Unable to create load balancer "{0}". {1}'.format(
                    name, str(e.response_text)))
        return result

    def create_loadbalancerpool(
            self, alias, location, lb_id, method, persistence, port):
        """
        Creates a pool on the provided load balancer
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param method: the load balancing method
        :param persistence: the load balancing persistence type
        :param port: the port that the load balancer will listen on
        :return: result: The result from the create API call
        """
        result = None
        try:
            result = self.clc.v2.API.Call(
                'POST', '/v2/sharedLoadBalancers/%s/%s/%s/pools' %
                (alias, location, lb_id), json.dumps(
                    {
                        "port": port, "method": method, "persistence": persistence
                    }))
        except APIFailedResponse as e:
            self.module.fail_json(
                msg='Unable to create pool for load balancer id "{0}". {1}'.format(
                    lb_id, str(e.response_text)))
        return result

    def delete_loadbalancer(self, alias, location, name):
        """
        Delete CLC loadbalancer
        :param alias: Alias for account
        :param location: Datacenter
        :param name: Name of the loadbalancer to delete
        :return: result: The result from the CLC API call
        """
        result = None
        lb_id = self._get_loadbalancer_id(name=name)
        try:
            result = self.clc.v2.API.Call(
                'DELETE', '/v2/sharedLoadBalancers/%s/%s/%s' %
                (alias, location, lb_id))
        except APIFailedResponse as e:
            self.module.fail_json(
                msg='Unable to delete load balancer "{0}". {1}'.format(
                    name, str(e.response_text)))
        return result

    def delete_loadbalancerpool(self, alias, location, lb_id, pool_id):
        """
        Delete the pool on the provided load balancer
        :param alias: The account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param pool_id: the id string of the load balancer pool
        :return: result: The result from the delete API call
        """
        result = None
        try:
            result = self.clc.v2.API.Call(
                'DELETE', '/v2/sharedLoadBalancers/%s/%s/%s/pools/%s' %
                (alias, location, lb_id, pool_id))
        except APIFailedResponse as e:
            self.module.fail_json(
                msg='Unable to delete pool for load balancer id "{0}". {1}'.format(
                    lb_id, str(e.response_text)))
        return result

    def _get_loadbalancer_id(self, name):
        """
        Retrieves unique ID of loadbalancer
        :param name: Name of loadbalancer
        :return: Unique ID of the loadbalancer
        """
        id = None
        for lb in self.lb_dict:
            if lb.get('name') == name:
                id = lb.get('id')
        return id

    def _get_loadbalancer_list(self, alias, location):
        """
        Retrieve a list of loadbalancers
        :param alias: Alias for account
        :param location: Datacenter
        :return: JSON data for all loadbalancers at datacenter
        """
        result = None
        try:
            result = self.clc.v2.API.Call(
                'GET', '/v2/sharedLoadBalancers/%s/%s' % (alias, location))
        except APIFailedResponse as e:
            self.module.fail_json(
                msg='Unable to fetch load balancers for account: {0}. {1}'.format(
                    alias, str(e.response_text)))
        return result

    def _loadbalancer_exists(self, name):
        """
        Verify a loadbalancer exists
        :param name: Name of loadbalancer
        :return: False or the ID of the existing loadbalancer
        """
        result = False

        for lb in self.lb_dict:
            if lb.get('name') == name:
                result = lb.get('id')
        return result

    def _loadbalancerpool_exists(self, alias, location, port, lb_id):
        """
        Checks to see if a pool exists on the specified port on the provided load balancer
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param port: the port to check and see if it exists
        :param lb_id: the id string of the provided load balancer
        :return: result: The id string of the pool or False
        """
        result = False
        try:
            pool_list = self.clc.v2.API.Call(
                'GET', '/v2/sharedLoadBalancers/%s/%s/%s/pools' %
                (alias, location, lb_id))
        except APIFailedResponse as e:
            return self.module.fail_json(
                msg='Unable to fetch the load balancer pools for for load balancer id: {0}. {1}'.format(
                    lb_id, str(e.response_text)))
        for pool in pool_list:
            if int(pool.get('port')) == int(port):
                result = pool.get('id')
        return result

    def _loadbalancerpool_nodes_exists(
            self, alias, location, lb_id, pool_id, nodes_to_check):
        """
        Checks to see if a set of nodes exists on the specified port on the provided load balancer
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the provided load balancer
        :param pool_id: the id string of the load balancer pool
        :param nodes_to_check: the list of nodes to check for
        :return: result: True / False indicating if the given nodes exist
        """
        result = False
        nodes = self._get_lbpool_nodes(alias, location, lb_id, pool_id)
        for node in nodes_to_check:
            if not node.get('status'):
                node['status'] = 'enabled'
            if node in nodes:
                result = True
            else:
                result = False
        return result

    def set_loadbalancernodes(self, alias, location, lb_id, pool_id, nodes):
        """
        Updates nodes to the provided pool
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param pool_id: the id string of the pool
        :param nodes: a list of dictionaries containing the nodes to set
        :return: result: The result from the CLC API call
        """
        result = None
        if not lb_id:
            return result
        if not self.module.check_mode:
            try:
                result = self.clc.v2.API.Call('PUT',
                                              '/v2/sharedLoadBalancers/%s/%s/%s/pools/%s/nodes'
                                              % (alias, location, lb_id, pool_id), json.dumps(nodes))
            except APIFailedResponse as e:
                self.module.fail_json(
                    msg='Unable to set nodes for the load balancer pool id "{0}". {1}'.format(
                        pool_id, str(e.response_text)))
        return result

    def add_lbpool_nodes(self, alias, location, lb_id, pool_id, nodes_to_add):
        """
        Add nodes to the provided pool
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param pool_id: the id string of the pool
        :param nodes_to_add: a list of dictionaries containing the nodes to add
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        result = {}
        nodes = self._get_lbpool_nodes(alias, location, lb_id, pool_id)
        for node in nodes_to_add:
            if not node.get('status'):
                node['status'] = 'enabled'
            if node not in nodes:
                changed = True
                nodes.append(node)
        if changed is True and not self.module.check_mode:
            result = self.set_loadbalancernodes(
                alias,
                location,
                lb_id,
                pool_id,
                nodes)
        return changed, result

    def remove_lbpool_nodes(
            self, alias, location, lb_id, pool_id, nodes_to_remove):
        """
        Removes nodes from the provided pool
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param pool_id: the id string of the pool
        :param nodes_to_remove: a list of dictionaries containing the nodes to remove
        :return: (changed, result) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        result = {}
        nodes = self._get_lbpool_nodes(alias, location, lb_id, pool_id)
        for node in nodes_to_remove:
            if not node.get('status'):
                node['status'] = 'enabled'
            if node in nodes:
                changed = True
                nodes.remove(node)
        if changed is True and not self.module.check_mode:
            result = self.set_loadbalancernodes(
                alias,
                location,
                lb_id,
                pool_id,
                nodes)
        return changed, result

    def _get_lbpool_nodes(self, alias, location, lb_id, pool_id):
        """
        Return the list of nodes available to the provided load balancer pool
        :param alias: the account alias
        :param location: the datacenter the load balancer resides in
        :param lb_id: the id string of the load balancer
        :param pool_id: the id string of the pool
        :return: result: The list of nodes
        """
        result = None
        try:
            result = self.clc.v2.API.Call('GET',
                                          '/v2/sharedLoadBalancers/%s/%s/%s/pools/%s/nodes'
                                          % (alias, location, lb_id, pool_id))
        except APIFailedResponse as e:
            self.module.fail_json(
                msg='Unable to fetch list of available nodes for load balancer pool id: {0}. {1}'.format(
                    pool_id, str(e.response_text)))
        return result

    @staticmethod
    def define_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            description=dict(default=None),
            location=dict(required=True),
            alias=dict(required=True),
            port=dict(choices=[80, 443]),
            method=dict(choices=['leastConnection', 'roundRobin']),
            persistence=dict(choices=['standard', 'sticky']),
            nodes=dict(type='list', default=[]),
            status=dict(default='enabled', choices=['enabled', 'disabled']),
            state=dict(
                default='present',
                choices=[
                    'present',
                    'absent',
                    'port_absent',
                    'nodes_present',
                    'nodes_absent'])
        )
        return argument_spec

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        api_url = env.get('CLC_V2_API_URL', False)

        if api_url:
            self.clc.defaults.ENDPOINT_URL_V2 = api_url

        if v2_api_token and clc_alias:
            self.clc._LOGIN_TOKEN_V2 = v2_api_token
            self.clc._V2_ENABLED = True
            self.clc.ALIAS = clc_alias
        elif v2_api_username and v2_api_passwd:
            self.clc.v2.SetCredentials(
                api_username=v2_api_username,
                api_passwd=v2_api_passwd)
        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")

    @staticmethod
    def _set_user_agent(clc):
        if hasattr(clc, 'SetRequestsSession'):
            agent_string = "ClcAnsibleModule/" + __version__
            ses = requests.Session()
            ses.headers.update({"Api-Client": agent_string})
            ses.headers['User-Agent'] += " " + agent_string
            clc.SetRequestsSession(ses)


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(argument_spec=ClcLoadBalancer.define_argument_spec(),
                           supports_check_mode=True)
    clc_loadbalancer = ClcLoadBalancer(module)
    clc_loadbalancer.process_request()


if __name__ == '__main__':
    main()
