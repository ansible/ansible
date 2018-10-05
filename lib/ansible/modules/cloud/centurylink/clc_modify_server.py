#!/usr/bin/python
#
# Copyright (c) 2015 CenturyLink
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: clc_modify_server
short_description: modify servers in CenturyLink Cloud.
description:
  - An Ansible module to modify servers in CenturyLink Cloud.
version_added: "2.0"
options:
  server_ids:
    description:
      - A list of server Ids to modify.
    required: True
  cpu:
    description:
      - How many CPUs to update on the server
  memory:
    description:
      - Memory (in GB) to set to the server.
  anti_affinity_policy_id:
    description:
      - The anti affinity policy id to be set for a hyper scale server.
        This is mutually exclusive with 'anti_affinity_policy_name'
  anti_affinity_policy_name:
    description:
      - The anti affinity policy name to be set for a hyper scale server.
        This is mutually exclusive with 'anti_affinity_policy_id'
  alert_policy_id:
    description:
      - The alert policy id to be associated to the server.
        This is mutually exclusive with 'alert_policy_name'
  alert_policy_name:
    description:
      - The alert policy name to be associated to the server.
        This is mutually exclusive with 'alert_policy_id'
  state:
    description:
      - The state to insure that the provided resources are in.
    default: 'present'
    choices: ['present', 'absent']
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    type: bool
    default: 'yes'
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

- name: set the cpu count to 4 on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    cpu: 4
    state: present

- name: set the memory to 8GB on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    memory: 8
    state: present

- name: set the anti affinity policy on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    anti_affinity_policy_name: 'aa_policy'
    state: present

- name: remove the anti affinity policy on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    anti_affinity_policy_name: 'aa_policy'
    state: absent

- name: add the alert policy on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    alert_policy_name: 'alert_policy'
    state: present

- name: remove the alert policy on a server
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    alert_policy_name: 'alert_policy'
    state: absent

- name: set the memory to 16GB and cpu to 8 core on a lust if servers
  clc_modify_server:
    server_ids:
        - UC1TESTSVR01
        - UC1TESTSVR02
    cpu: 8
    memory: 16
    state: present
'''

RETURN = '''
server_ids:
    description: The list of server ids that are changed
    returned: success
    type: list
    sample:
        [
            "UC1TEST-SVR01",
            "UC1TEST-SVR02"
        ]
servers:
    description: The list of server objects that are changed
    returned: success
    type: list
    sample:
        [
           {
              "changeInfo":{
                 "createdBy":"service.wfad",
                 "createdDate":1438196820,
                 "modifiedBy":"service.wfad",
                 "modifiedDate":1438196820
              },
              "description":"test-server",
              "details":{
                 "alertPolicies":[

                 ],
                 "cpu":1,
                 "customFields":[

                 ],
                 "diskCount":3,
                 "disks":[
                    {
                       "id":"0:0",
                       "partitionPaths":[

                       ],
                       "sizeGB":1
                    },
                    {
                       "id":"0:1",
                       "partitionPaths":[

                       ],
                       "sizeGB":2
                    },
                    {
                       "id":"0:2",
                       "partitionPaths":[

                       ],
                       "sizeGB":14
                    }
                 ],
                 "hostName":"",
                 "inMaintenanceMode":false,
                 "ipAddresses":[
                    {
                       "internal":"10.1.1.1"
                    }
                 ],
                 "memoryGB":1,
                 "memoryMB":1024,
                 "partitions":[

                 ],
                 "powerState":"started",
                 "snapshots":[

                 ],
                 "storageGB":17
              },
              "groupId":"086ac1dfe0b6411989e8d1b77c4065f0",
              "id":"test-server",
              "ipaddress":"10.120.45.23",
              "isTemplate":false,
              "links":[
                 {
                    "href":"/v2/servers/wfad/test-server",
                    "id":"test-server",
                    "rel":"self",
                    "verbs":[
                       "GET",
                       "PATCH",
                       "DELETE"
                    ]
                 },
                 {
                    "href":"/v2/groups/wfad/086ac1dfe0b6411989e8d1b77c4065f0",
                    "id":"086ac1dfe0b6411989e8d1b77c4065f0",
                    "rel":"group"
                 },
                 {
                    "href":"/v2/accounts/wfad",
                    "id":"wfad",
                    "rel":"account"
                 },
                 {
                    "href":"/v2/billing/wfad/serverPricing/test-server",
                    "rel":"billing"
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/publicIPAddresses",
                    "rel":"publicIPAddresses",
                    "verbs":[
                       "POST"
                    ]
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/credentials",
                    "rel":"credentials"
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/statistics",
                    "rel":"statistics"
                 },
                 {
                    "href":"/v2/servers/wfad/510ec21ae82d4dc89d28479753bf736a/upcomingScheduledActivities",
                    "rel":"upcomingScheduledActivities"
                 },
                 {
                    "href":"/v2/servers/wfad/510ec21ae82d4dc89d28479753bf736a/scheduledActivities",
                    "rel":"scheduledActivities",
                    "verbs":[
                       "GET",
                       "POST"
                    ]
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/capabilities",
                    "rel":"capabilities"
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/alertPolicies",
                    "rel":"alertPolicyMappings",
                    "verbs":[
                       "POST"
                    ]
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/antiAffinityPolicy",
                    "rel":"antiAffinityPolicyMapping",
                    "verbs":[
                       "PUT",
                       "DELETE"
                    ]
                 },
                 {
                    "href":"/v2/servers/wfad/test-server/cpuAutoscalePolicy",
                    "rel":"cpuAutoscalePolicyMapping",
                    "verbs":[
                       "PUT",
                       "DELETE"
                    ]
                 }
              ],
              "locationId":"UC1",
              "name":"test-server",
              "os":"ubuntu14_64Bit",
              "osType":"Ubuntu 14 64-bit",
              "status":"active",
              "storageType":"standard",
              "type":"standard"
           }
        ]
'''

__version__ = '${version}'

import json
import os
from distutils.version import LooseVersion

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
    from clc import CLCException
    from clc import APIFailedResponse
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True

from ansible.module_utils.basic import AnsibleModule


class ClcModifyServer:
    clc = clc_sdk

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')
        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')
        if requests.__version__ and LooseVersion(
                requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

        self._set_user_agent(self.clc)

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        self._set_clc_credentials_from_env()

        p = self.module.params
        cpu = p.get('cpu')
        memory = p.get('memory')
        state = p.get('state')
        if state == 'absent' and (cpu or memory):
            return self.module.fail_json(
                msg='\'absent\' state is not supported for \'cpu\' and \'memory\' arguments')

        server_ids = p['server_ids']
        if not isinstance(server_ids, list):
            return self.module.fail_json(
                msg='server_ids needs to be a list of instances to modify: %s' %
                server_ids)

        (changed, server_dict_array, changed_server_ids) = self._modify_servers(
            server_ids=server_ids)

        self.module.exit_json(
            changed=changed,
            server_ids=changed_server_ids,
            servers=server_dict_array)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            state=dict(default='present', choices=['present', 'absent']),
            cpu=dict(),
            memory=dict(),
            anti_affinity_policy_id=dict(),
            anti_affinity_policy_name=dict(),
            alert_policy_id=dict(),
            alert_policy_name=dict(),
            wait=dict(type='bool', default=True)
        )
        mutually_exclusive = [
            ['anti_affinity_policy_id', 'anti_affinity_policy_name'],
            ['alert_policy_id', 'alert_policy_name']
        ]
        return {"argument_spec": argument_spec,
                "mutually_exclusive": mutually_exclusive}

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

    def _get_servers_from_clc(self, server_list, message):
        """
        Internal function to fetch list of CLC server objects from a list of server ids
        :param server_list: The list of server ids
        :param message: the error message to throw in case of any error
        :return the list of CLC server objects
        """
        try:
            return self.clc.v2.Servers(server_list).servers
        except CLCException as ex:
            return self.module.fail_json(msg=message + ': %s' % ex.message)

    def _modify_servers(self, server_ids):
        """
        modify the servers configuration on the provided list
        :param server_ids: list of servers to modify
        :return: a list of dictionaries with server information about the servers that were modified
        """
        p = self.module.params
        state = p.get('state')
        server_params = {
            'cpu': p.get('cpu'),
            'memory': p.get('memory'),
            'anti_affinity_policy_id': p.get('anti_affinity_policy_id'),
            'anti_affinity_policy_name': p.get('anti_affinity_policy_name'),
            'alert_policy_id': p.get('alert_policy_id'),
            'alert_policy_name': p.get('alert_policy_name'),
        }
        changed = False
        server_changed = False
        aa_changed = False
        ap_changed = False
        server_dict_array = []
        result_server_ids = []
        request_list = []
        changed_servers = []

        if not isinstance(server_ids, list) or len(server_ids) < 1:
            return self.module.fail_json(
                msg='server_ids should be a list of servers, aborting')

        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
        for server in servers:
            if state == 'present':
                server_changed, server_result = self._ensure_server_config(
                    server, server_params)
                if server_result:
                    request_list.append(server_result)
                aa_changed = self._ensure_aa_policy_present(
                    server,
                    server_params)
                ap_changed = self._ensure_alert_policy_present(
                    server,
                    server_params)
            elif state == 'absent':
                aa_changed = self._ensure_aa_policy_absent(
                    server,
                    server_params)
                ap_changed = self._ensure_alert_policy_absent(
                    server,
                    server_params)
            if server_changed or aa_changed or ap_changed:
                changed_servers.append(server)
                changed = True

        self._wait_for_requests(self.module, request_list)
        self._refresh_servers(self.module, changed_servers)

        for server in changed_servers:
            server_dict_array.append(server.data)
            result_server_ids.append(server.id)

        return changed, server_dict_array, result_server_ids

    def _ensure_server_config(
            self, server, server_params):
        """
        ensures the server is updated with the provided cpu and memory
        :param server: the CLC server object
        :param server_params: the dictionary of server parameters
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        cpu = server_params.get('cpu')
        memory = server_params.get('memory')
        changed = False
        result = None

        if not cpu:
            cpu = server.cpu
        if not memory:
            memory = server.memory
        if memory != server.memory or cpu != server.cpu:
            if not self.module.check_mode:
                result = self._modify_clc_server(
                    self.clc,
                    self.module,
                    server.id,
                    cpu,
                    memory)
            changed = True
        return changed, result

    @staticmethod
    def _modify_clc_server(clc, module, server_id, cpu, memory):
        """
        Modify the memory or CPU of a clc server.
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param server_id: id of the server to modify
        :param cpu: the new cpu value
        :param memory: the new memory value
        :return: the result of CLC API call
        """
        result = None
        acct_alias = clc.v2.Account.GetAlias()
        try:
            # Update the server configuration
            job_obj = clc.v2.API.Call('PATCH',
                                      'servers/%s/%s' % (acct_alias,
                                                         server_id),
                                      json.dumps([{"op": "set",
                                                   "member": "memory",
                                                   "value": memory},
                                                  {"op": "set",
                                                   "member": "cpu",
                                                   "value": cpu}]))
            result = clc.v2.Requests(job_obj)
        except APIFailedResponse as ex:
            module.fail_json(
                msg='Unable to update the server configuration for server : "{0}". {1}'.format(
                    server_id, str(ex.response_text)))
        return result

    @staticmethod
    def _wait_for_requests(module, request_list):
        """
        Block until server provisioning requests are completed.
        :param module: the AnsibleModule object
        :param request_list: a list of clc-sdk.Request instances
        :return: none
        """
        wait = module.params.get('wait')
        if wait:
            # Requests.WaitUntilComplete() returns the count of failed requests
            failed_requests_count = sum(
                [request.WaitUntilComplete() for request in request_list])

            if failed_requests_count > 0:
                module.fail_json(
                    msg='Unable to process modify server request')

    @staticmethod
    def _refresh_servers(module, servers):
        """
        Loop through a list of servers and refresh them.
        :param module: the AnsibleModule object
        :param servers: list of clc-sdk.Server instances to refresh
        :return: none
        """
        for server in servers:
            try:
                server.Refresh()
            except CLCException as ex:
                module.fail_json(msg='Unable to refresh the server {0}. {1}'.format(
                    server.id, ex.message
                ))

    def _ensure_aa_policy_present(
            self, server, server_params):
        """
        ensures the server is updated with the provided anti affinity policy
        :param server: the CLC server object
        :param server_params: the dictionary of server parameters
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        acct_alias = self.clc.v2.Account.GetAlias()

        aa_policy_id = server_params.get('anti_affinity_policy_id')
        aa_policy_name = server_params.get('anti_affinity_policy_name')
        if not aa_policy_id and aa_policy_name:
            aa_policy_id = self._get_aa_policy_id_by_name(
                self.clc,
                self.module,
                acct_alias,
                aa_policy_name)
        current_aa_policy_id = self._get_aa_policy_id_of_server(
            self.clc,
            self.module,
            acct_alias,
            server.id)

        if aa_policy_id and aa_policy_id != current_aa_policy_id:
            self._modify_aa_policy(
                self.clc,
                self.module,
                acct_alias,
                server.id,
                aa_policy_id)
            changed = True
        return changed

    def _ensure_aa_policy_absent(
            self, server, server_params):
        """
        ensures the provided anti affinity policy is removed from the server
        :param server: the CLC server object
        :param server_params: the dictionary of server parameters
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        acct_alias = self.clc.v2.Account.GetAlias()
        aa_policy_id = server_params.get('anti_affinity_policy_id')
        aa_policy_name = server_params.get('anti_affinity_policy_name')
        if not aa_policy_id and aa_policy_name:
            aa_policy_id = self._get_aa_policy_id_by_name(
                self.clc,
                self.module,
                acct_alias,
                aa_policy_name)
        current_aa_policy_id = self._get_aa_policy_id_of_server(
            self.clc,
            self.module,
            acct_alias,
            server.id)

        if aa_policy_id and aa_policy_id == current_aa_policy_id:
            self._delete_aa_policy(
                self.clc,
                self.module,
                acct_alias,
                server.id)
            changed = True
        return changed

    @staticmethod
    def _modify_aa_policy(clc, module, acct_alias, server_id, aa_policy_id):
        """
        modifies the anti affinity policy of the CLC server
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param acct_alias: the CLC account alias
        :param server_id: the CLC server id
        :param aa_policy_id: the anti affinity policy id
        :return: result: The result from the CLC API call
        """
        result = None
        if not module.check_mode:
            try:
                result = clc.v2.API.Call('PUT',
                                         'servers/%s/%s/antiAffinityPolicy' % (
                                             acct_alias,
                                             server_id),
                                         json.dumps({"id": aa_policy_id}))
            except APIFailedResponse as ex:
                module.fail_json(
                    msg='Unable to modify anti affinity policy to server : "{0}". {1}'.format(
                        server_id, str(ex.response_text)))
        return result

    @staticmethod
    def _delete_aa_policy(clc, module, acct_alias, server_id):
        """
        Delete the anti affinity policy of the CLC server
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param acct_alias: the CLC account alias
        :param server_id: the CLC server id
        :return: result: The result from the CLC API call
        """
        result = None
        if not module.check_mode:
            try:
                result = clc.v2.API.Call('DELETE',
                                         'servers/%s/%s/antiAffinityPolicy' % (
                                             acct_alias,
                                             server_id),
                                         json.dumps({}))
            except APIFailedResponse as ex:
                module.fail_json(
                    msg='Unable to delete anti affinity policy to server : "{0}". {1}'.format(
                        server_id, str(ex.response_text)))
        return result

    @staticmethod
    def _get_aa_policy_id_by_name(clc, module, alias, aa_policy_name):
        """
        retrieves the anti affinity policy id of the server based on the name of the policy
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param alias: the CLC account alias
        :param aa_policy_name: the anti affinity policy name
        :return: aa_policy_id: The anti affinity policy id
        """
        aa_policy_id = None
        try:
            aa_policies = clc.v2.API.Call(method='GET',
                                          url='antiAffinityPolicies/%s' % alias)
        except APIFailedResponse as ex:
            return module.fail_json(
                msg='Unable to fetch anti affinity policies from account alias : "{0}". {1}'.format(
                    alias, str(ex.response_text)))
        for aa_policy in aa_policies.get('items'):
            if aa_policy.get('name') == aa_policy_name:
                if not aa_policy_id:
                    aa_policy_id = aa_policy.get('id')
                else:
                    return module.fail_json(
                        msg='multiple anti affinity policies were found with policy name : %s' % aa_policy_name)
        if not aa_policy_id:
            module.fail_json(
                msg='No anti affinity policy was found with policy name : %s' % aa_policy_name)
        return aa_policy_id

    @staticmethod
    def _get_aa_policy_id_of_server(clc, module, alias, server_id):
        """
        retrieves the anti affinity policy id of the server based on the CLC server id
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param alias: the CLC account alias
        :param server_id: the CLC server id
        :return: aa_policy_id: The anti affinity policy id
        """
        aa_policy_id = None
        try:
            result = clc.v2.API.Call(
                method='GET', url='servers/%s/%s/antiAffinityPolicy' %
                (alias, server_id))
            aa_policy_id = result.get('id')
        except APIFailedResponse as ex:
            if ex.response_status_code != 404:
                module.fail_json(msg='Unable to fetch anti affinity policy for server "{0}". {1}'.format(
                    server_id, str(ex.response_text)))
        return aa_policy_id

    def _ensure_alert_policy_present(
            self, server, server_params):
        """
        ensures the server is updated with the provided alert policy
        :param server: the CLC server object
        :param server_params: the dictionary of server parameters
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False
        acct_alias = self.clc.v2.Account.GetAlias()
        alert_policy_id = server_params.get('alert_policy_id')
        alert_policy_name = server_params.get('alert_policy_name')
        if not alert_policy_id and alert_policy_name:
            alert_policy_id = self._get_alert_policy_id_by_name(
                self.clc,
                self.module,
                acct_alias,
                alert_policy_name)
        if alert_policy_id and not self._alert_policy_exists(
                server, alert_policy_id):
            self._add_alert_policy_to_server(
                self.clc,
                self.module,
                acct_alias,
                server.id,
                alert_policy_id)
            changed = True
        return changed

    def _ensure_alert_policy_absent(
            self, server, server_params):
        """
        ensures the alert policy is removed from the server
        :param server: the CLC server object
        :param server_params: the dictionary of server parameters
        :return: (changed, group) -
            changed: Boolean whether a change was made
            result: The result from the CLC API call
        """
        changed = False

        acct_alias = self.clc.v2.Account.GetAlias()
        alert_policy_id = server_params.get('alert_policy_id')
        alert_policy_name = server_params.get('alert_policy_name')
        if not alert_policy_id and alert_policy_name:
            alert_policy_id = self._get_alert_policy_id_by_name(
                self.clc,
                self.module,
                acct_alias,
                alert_policy_name)

        if alert_policy_id and self._alert_policy_exists(
                server, alert_policy_id):
            self._remove_alert_policy_to_server(
                self.clc,
                self.module,
                acct_alias,
                server.id,
                alert_policy_id)
            changed = True
        return changed

    @staticmethod
    def _add_alert_policy_to_server(
            clc, module, acct_alias, server_id, alert_policy_id):
        """
        add the alert policy to CLC server
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param acct_alias: the CLC account alias
        :param server_id: the CLC server id
        :param alert_policy_id: the alert policy id
        :return: result: The result from the CLC API call
        """
        result = None
        if not module.check_mode:
            try:
                result = clc.v2.API.Call('POST',
                                         'servers/%s/%s/alertPolicies' % (
                                             acct_alias,
                                             server_id),
                                         json.dumps({"id": alert_policy_id}))
            except APIFailedResponse as ex:
                module.fail_json(msg='Unable to set alert policy to the server : "{0}". {1}'.format(
                    server_id, str(ex.response_text)))
        return result

    @staticmethod
    def _remove_alert_policy_to_server(
            clc, module, acct_alias, server_id, alert_policy_id):
        """
        remove the alert policy to the CLC server
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param acct_alias: the CLC account alias
        :param server_id: the CLC server id
        :param alert_policy_id: the alert policy id
        :return: result: The result from the CLC API call
        """
        result = None
        if not module.check_mode:
            try:
                result = clc.v2.API.Call('DELETE',
                                         'servers/%s/%s/alertPolicies/%s'
                                         % (acct_alias, server_id, alert_policy_id))
            except APIFailedResponse as ex:
                module.fail_json(msg='Unable to remove alert policy from the server : "{0}". {1}'.format(
                    server_id, str(ex.response_text)))
        return result

    @staticmethod
    def _get_alert_policy_id_by_name(clc, module, alias, alert_policy_name):
        """
        retrieves the alert policy id of the server based on the name of the policy
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param alias: the CLC account alias
        :param alert_policy_name: the alert policy name
        :return: alert_policy_id: The alert policy id
        """
        alert_policy_id = None
        try:
            alert_policies = clc.v2.API.Call(method='GET',
                                             url='alertPolicies/%s' % alias)
        except APIFailedResponse as ex:
            return module.fail_json(msg='Unable to fetch alert policies for account : "{0}". {1}'.format(
                alias, str(ex.response_text)))
        for alert_policy in alert_policies.get('items'):
            if alert_policy.get('name') == alert_policy_name:
                if not alert_policy_id:
                    alert_policy_id = alert_policy.get('id')
                else:
                    return module.fail_json(
                        msg='multiple alert policies were found with policy name : %s' % alert_policy_name)
        return alert_policy_id

    @staticmethod
    def _alert_policy_exists(server, alert_policy_id):
        """
        Checks if the alert policy exists for the server
        :param server: the clc server object
        :param alert_policy_id: the alert policy
        :return: True: if the given alert policy id associated to the server, False otherwise
        """
        result = False
        alert_policies = server.alertPolicies
        if alert_policies:
            for alert_policy in alert_policies:
                if alert_policy.get('id') == alert_policy_id:
                    result = True
        return result

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

    argument_dict = ClcModifyServer._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_modify_server = ClcModifyServer(module)
    clc_modify_server.process_request()


if __name__ == '__main__':
    main()
