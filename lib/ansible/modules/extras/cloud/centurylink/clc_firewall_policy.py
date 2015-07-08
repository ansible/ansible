#!/usr/bin/python

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
# Copyright 2015 CenturyLink Cloud
#
# Licensed under the Apache License, Version 2.0 (the "License");

# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# CenturyLink Cloud: http://www.CenturyLinkCloud.com
# API Documentation: https://www.centurylinkcloud.com/api-docs/v2/
#

DOCUMENTATION = '''
module: clc_firewall_policy
short_desciption: Create/delete/update firewall policies
description:
  - Create or delete or updated firewall polices on Centurylink Centurylink Cloud
options:
  location:
    description:
      - Target datacenter for the firewall policy
    default: None
    required: True
    aliases: []
  state:
    description:
      - Whether to create or delete the firewall policy
    default: present
    required: True
    choices: ['present', 'absent']
    aliases: []
  source:
    description:
      - Source addresses for traffic on the originating firewall
    default: None
    required: For Creation
    aliases: []
  destination:
    description:
      - Destination addresses for traffic on the terminating firewall
    default: None
    required: For Creation
    aliases: []
  ports:
    description:
      - types of ports associated with the policy. TCP & UDP can take in single ports or port ranges.
    default: None
    required: False
    choices: ['any', 'icmp', 'TCP/123', 'UDP/123', 'TCP/123-456', 'UDP/123-456']
    aliases: []
  firewall_policy_id:
    description:
      - Id of the firewall policy
    default: None
    required: False
    aliases: []
  source_account_alias:
    description:
      - CLC alias for the source account
    default: None
    required: True
    aliases: []
  destination_account_alias:
    description:
      - CLC alias for the destination account
    default: None
    required: False
    aliases: []
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [ True, False ]
    aliases: []
  enabled:
    description:
      - If the firewall policy is enabled or disabled
    default: true
    required: False
    choices: [ true, false ]
    aliases: []

'''

EXAMPLES = '''
---
- name: Create Firewall Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create / Verify an Firewall Policy at CenturyLink Cloud
      clc_firewall:
        source_account_alias: WFAD
        location: VA1
        state: present
        source: 10.128.216.0/24
        destination: 10.128.216.0/24
        ports: Any
        destination_account_alias: WFAD

---
- name: Delete Firewall Policy
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete an Firewall Policy at CenturyLink Cloud
      clc_firewall:
        source_account_alias: WFAD
        location: VA1
        state: present
        firewall_policy_id: c62105233d7a4231bd2e91b9c791eaae
'''

__version__ = '${version}'

import urlparse
from time import sleep
import requests

try:
    import clc as clc_sdk
    from clc import CLCException
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True


class ClcFirewallPolicy():

    clc = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.firewall_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

        self._set_user_agent(self.clc)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            location=dict(required=True, defualt=None),
            source_account_alias=dict(required=True, default=None),
            destination_account_alias=dict(default=None),
            firewall_policy_id=dict(default=None),
            ports=dict(default=None, type='list'),
            source=dict(defualt=None, type='list'),
            destination=dict(defualt=None, type='list'),
            wait=dict(default=True),
            state=dict(default='present', choices=['present', 'absent']),
            enabled=dict(defualt=None)
        )
        return argument_spec

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        location = self.module.params.get('location')
        source_account_alias = self.module.params.get('source_account_alias')
        destination_account_alias = self.module.params.get(
            'destination_account_alias')
        firewall_policy_id = self.module.params.get('firewall_policy_id')
        ports = self.module.params.get('ports')
        source = self.module.params.get('source')
        destination = self.module.params.get('destination')
        wait = self.module.params.get('wait')
        state = self.module.params.get('state')
        enabled = self.module.params.get('enabled')

        self.firewall_dict = {
            'location': location,
            'source_account_alias': source_account_alias,
            'destination_account_alias': destination_account_alias,
            'firewall_policy_id': firewall_policy_id,
            'ports': ports,
            'source': source,
            'destination': destination,
            'wait': wait,
            'state': state,
            'enabled': enabled}

        self._set_clc_credentials_from_env()
        requests = []

        if state == 'absent':
            changed, firewall_policy_id, response = self._ensure_firewall_policy_is_absent(
                source_account_alias, location, self.firewall_dict)

        elif state == 'present':
            changed, firewall_policy_id, response = self._ensure_firewall_policy_is_present(
                source_account_alias, location, self.firewall_dict)
        else:
            return self.module.fail_json(msg="Unknown State: " + state)

        return self.module.exit_json(
            changed=changed,
            firewall_policy_id=firewall_policy_id)

    @staticmethod
    def _get_policy_id_from_response(response):
        """
        Method to parse out the policy id from creation response
        :param response: response from firewall creation control
        :return: policy_id: firewall policy id from creation call
        """
        url = response.get('links')[0]['href']
        path = urlparse.urlparse(url).path
        path_list = os.path.split(path)
        policy_id = path_list[-1]
        return policy_id

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

    def _ensure_firewall_policy_is_present(
            self,
            source_account_alias,
            location,
            firewall_dict):
        """
        Ensures that a given firewall policy is present
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_dict: dictionary or request parameters for firewall policy creation
        :return: (changed, firewall_policy, response)
            changed: flag for if a change occurred
            firewall_policy: policy that was changed
            response: response from CLC API call
        """
        changed = False
        response = {}
        firewall_policy_id = firewall_dict.get('firewall_policy_id')

        if firewall_policy_id is None:
            if not self.module.check_mode:
                response = self._create_firewall_policy(
                    source_account_alias,
                    location,
                    firewall_dict)
                firewall_policy_id = self._get_policy_id_from_response(
                    response)
                self._wait_for_requests_to_complete(
                    firewall_dict.get('wait'),
                    source_account_alias,
                    location,
                    firewall_policy_id)
            changed = True
        else:
            get_before_response, success = self._get_firewall_policy(
                source_account_alias, location, firewall_policy_id)
            if not success:
                return self.module.fail_json(
                    msg='Unable to find the firewall policy id : %s' %
                    firewall_policy_id)
            changed = self._compare_get_request_with_dict(
                get_before_response,
                firewall_dict)
            if not self.module.check_mode and changed:
                response = self._update_firewall_policy(
                    source_account_alias,
                    location,
                    firewall_policy_id,
                    firewall_dict)
                self._wait_for_requests_to_complete(
                    firewall_dict.get('wait'),
                    source_account_alias,
                    location,
                    firewall_policy_id)
        return changed, firewall_policy_id, response

    def _ensure_firewall_policy_is_absent(
            self,
            source_account_alias,
            location,
            firewall_dict):
        """
        Ensures that a given firewall policy is removed if present
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_dict: firewall policy to delete
        :return: (changed, firewall_policy_id, response)
            changed: flag for if a change occurred
            firewall_policy_id: policy that was changed
            response: response from CLC API call
        """
        changed = False
        response = []
        firewall_policy_id = firewall_dict.get('firewall_policy_id')
        result, success = self._get_firewall_policy(
            source_account_alias, location, firewall_policy_id)
        if success:
            if not self.module.check_mode:
                response = self._delete_firewall_policy(
                    source_account_alias,
                    location,
                    firewall_policy_id)
            changed = True
        return changed, firewall_policy_id, response

    def _create_firewall_policy(
            self,
            source_account_alias,
            location,
            firewall_dict):
        """
        Ensures that a given firewall policy is present
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_dict: dictionary or request parameters for firewall policy creation
        :return: response from CLC API call
        """
        payload = {
            'destinationAccount': firewall_dict.get('destination_account_alias'),
            'source': firewall_dict.get('source'),
            'destination': firewall_dict.get('destination'),
            'ports': firewall_dict.get('ports')}
        try:
            response = self.clc.v2.API.Call(
                'POST', '/v2-experimental/firewallPolicies/%s/%s' %
                        (source_account_alias, location), payload)
        except self.clc.APIFailedResponse as e:
            return self.module.fail_json(
                msg="Unable to successfully create firewall policy. %s" %
                    str(e.response_text))
        return response

    def _delete_firewall_policy(
            self,
            source_account_alias,
            location,
            firewall_policy_id):
        """
        Deletes a given firewall policy for an account alias in a datacenter
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_policy_id: firewall policy to delete
        :return: response: response from CLC API call
        """
        try:
            response = self.clc.v2.API.Call(
                'DELETE', '/v2-experimental/firewallPolicies/%s/%s/%s' %
                          (source_account_alias, location, firewall_policy_id))
        except self.clc.APIFailedResponse as e:
            return self.module.fail_json(
                msg="Unable to successfully delete firewall policy. %s" %
                    str(e.response_text))
        return response

    def _update_firewall_policy(
            self,
            source_account_alias,
            location,
            firewall_policy_id,
            firewall_dict):
        """
        Updates a firewall policy for a given datacenter and account alias
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_policy_id: firewall policy to delete
        :param firewall_dict: dictionary or request parameters for firewall policy creation
        :return: response: response from CLC API call
        """
        try:
            response = self.clc.v2.API.Call(
                'PUT',
                '/v2-experimental/firewallPolicies/%s/%s/%s' %
                (source_account_alias,
                 location,
                 firewall_policy_id),
                firewall_dict)
        except self.clc.APIFailedResponse as e:
            return self.module.fail_json(
                msg="Unable to successfully update firewall policy. %s" %
                    str(e.response_text))
        return response

    @staticmethod
    def _compare_get_request_with_dict(response, firewall_dict):
        """
        Helper method to compare the json response for getting the firewall policy with the request parameters
        :param response: response from the get method
        :param firewall_dict: dictionary or request parameters for firewall policy creation
        :return: changed: Boolean that returns true if there are differences between the response parameters and the playbook parameters
        """

        changed = False

        response_dest_account_alias = response.get('destinationAccount')
        response_enabled = response.get('enabled')
        response_source = response.get('source')
        response_dest = response.get('destination')
        response_ports = response.get('ports')

        request_dest_account_alias = firewall_dict.get(
            'destination_account_alias')
        request_enabled = firewall_dict.get('enabled')
        if request_enabled is None:
            request_enabled = True
        request_source = firewall_dict.get('source')
        request_dest = firewall_dict.get('destination')
        request_ports = firewall_dict.get('ports')

        if (
            response_dest_account_alias and str(response_dest_account_alias) != str(request_dest_account_alias)) or (
            response_enabled != request_enabled) or (
            response_source and response_source != request_source) or (
                response_dest and response_dest != request_dest) or (
                    response_ports and response_ports != request_ports):
            changed = True
        return changed

    def _get_firewall_policy(
            self,
            source_account_alias,
            location,
            firewall_policy_id):
        """
        Get back details for a particular firewall policy
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_policy_id: id of the firewall policy to get
        :return: response from CLC API call
        """
        response = []
        success = False
        try:
            response = self.clc.v2.API.Call(
                'GET', '/v2-experimental/firewallPolicies/%s/%s/%s' %
                (source_account_alias, location, firewall_policy_id))
            success = True
        except:
            pass
        return response, success

    def _wait_for_requests_to_complete(
            self,
            wait,
            source_account_alias,
            location,
            firewall_policy_id):
        """
        Waits until the CLC requests are complete if the wait argument is True
        :param requests_lst: The list of CLC request objects
        :return: none
        """
        if wait:
            response, success = self._get_firewall_policy(
                source_account_alias, location, firewall_policy_id)
            if response.get('status') == 'pending':
                sleep(2)
                self._wait_for_requests_to_complete(
                    wait,
                    source_account_alias,
                    location,
                    firewall_policy_id)
            return None

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
    module = AnsibleModule(
        argument_spec=ClcFirewallPolicy._define_module_argument_spec(),
        supports_check_mode=True)

    clc_firewall = ClcFirewallPolicy(module)
    clc_firewall.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
