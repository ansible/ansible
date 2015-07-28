#!/usr/bin/python

#
# Copyright (c) 2015 CenturyLink
#
# This file is part of Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>
#

DOCUMENTATION = '''
module: clc_firewall_policy
short_description: Create/delete/update firewall policies
description:
  - Create or delete or update firewall polices on Centurylink Cloud
version_added: "2.0"
options:
  location:
    description:
      - Target datacenter for the firewall policy
    required: True
  state:
    description:
      - Whether to create or delete the firewall policy
    default: present
    required: False
    choices: ['present', 'absent']
  source:
    description:
      - The list  of source addresses for traffic on the originating firewall.
        This is required when state is 'present"
    default: None
    required: False
  destination:
    description:
      - The list of destination addresses for traffic on the terminating firewall.
        This is required when state is 'present'
    default: None
    required: False
  ports:
    description:
      - The list of ports associated with the policy.
        TCP and UDP can take in single ports or port ranges.
    default: None
    required: False
    choices: ['any', 'icmp', 'TCP/123', 'UDP/123', 'TCP/123-456', 'UDP/123-456']
  firewall_policy_id:
    description:
      - Id of the firewall policy. This is required to update or delete an existing firewall policy
    default: None
    required: False
  source_account_alias:
    description:
      - CLC alias for the source account
    required: True
  destination_account_alias:
    description:
      - CLC alias for the destination account
    default: None
    required: False
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [True, False]
  enabled:
    description:
      - Whether the firewall policy is enabled or disabled
    default: True
    required: False
    choices: [True, False]
requirements:
    - python = 2.7
    - requests >= 2.5.0
    - clc-sdk
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
        state: absent
        firewall_policy_id: 'c62105233d7a4231bd2e91b9c791e43e1'
'''

__version__ = '${version}'

import urlparse
from time import sleep
from distutils.version import LooseVersion

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

try:
    import clc as clc_sdk
    from clc import CLCException
    from clc import APIFailedResponse
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True


class ClcFirewallPolicy:

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
        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')
        if requests.__version__ and LooseVersion(
                requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

        self._set_user_agent(self.clc)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            location=dict(required=True),
            source_account_alias=dict(required=True, default=None),
            destination_account_alias=dict(default=None),
            firewall_policy_id=dict(default=None),
            ports=dict(default=None, type='list'),
            source=dict(defualt=None, type='list'),
            destination=dict(defualt=None, type='list'),
            wait=dict(default=True),
            state=dict(default='present', choices=['present', 'absent']),
            enabled=dict(defualt=True, choices=[True, False])
        )
        return argument_spec

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        changed = False
        firewall_policy = None
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

        if state == 'absent':
            changed, firewall_policy_id, firewall_policy = self._ensure_firewall_policy_is_absent(
                source_account_alias, location, self.firewall_dict)

        elif state == 'present':
            changed, firewall_policy_id, firewall_policy = self._ensure_firewall_policy_is_present(
                source_account_alias, location, self.firewall_dict)

        return self.module.exit_json(
            changed=changed,
            firewall_policy_id=firewall_policy_id,
            firewall_policy=firewall_policy)

    @staticmethod
    def _get_policy_id_from_response(response):
        """
        Method to parse out the policy id from creation response
        :param response: response from firewall creation API call
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
        :param firewall_dict: dictionary of request parameters for firewall policy
        :return: (changed, firewall_policy_id, firewall_policy)
            changed: flag for if a change occurred
            firewall_policy_id: the firewall policy id that was created/updated
            firewall_policy: The firewall_policy object
        """
        firewall_policy = None
        firewall_policy_id = firewall_dict.get('firewall_policy_id')

        if firewall_policy_id is None:
            if not self.module.check_mode:
                response = self._create_firewall_policy(
                    source_account_alias,
                    location,
                    firewall_dict)
                firewall_policy_id = self._get_policy_id_from_response(
                    response)
            changed = True
        else:
            firewall_policy = self._get_firewall_policy(
                source_account_alias, location, firewall_policy_id)
            if not firewall_policy:
                return self.module.fail_json(
                    msg='Unable to find the firewall policy id : {0}'.format(
                        firewall_policy_id))
            changed = self._compare_get_request_with_dict(
                firewall_policy,
                firewall_dict)
            if not self.module.check_mode and changed:
                self._update_firewall_policy(
                    source_account_alias,
                    location,
                    firewall_policy_id,
                    firewall_dict)
        if changed and firewall_policy_id:
            firewall_policy = self._wait_for_requests_to_complete(
                source_account_alias,
                location,
                firewall_policy_id)
        return changed, firewall_policy_id, firewall_policy

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
            firewall_policy_id: the firewall policy id that was deleted
            response: response from CLC API call
        """
        changed = False
        response = []
        firewall_policy_id = firewall_dict.get('firewall_policy_id')
        result = self._get_firewall_policy(
            source_account_alias, location, firewall_policy_id)
        if result:
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
        Creates the firewall policy for the given account alias
        :param source_account_alias: the source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_dict: dictionary of request parameters for firewall policy
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
        except APIFailedResponse as e:
            return self.module.fail_json(
                msg="Unable to create firewall policy. %s" %
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
        :param firewall_policy_id: firewall policy id to delete
        :return: response: response from CLC API call
        """
        try:
            response = self.clc.v2.API.Call(
                'DELETE', '/v2-experimental/firewallPolicies/%s/%s/%s' %
                          (source_account_alias, location, firewall_policy_id))
        except APIFailedResponse as e:
            return self.module.fail_json(
                msg="Unable to delete the firewall policy id : {0}. {1}".format(
                    firewall_policy_id, str(e.response_text)))
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
        :param firewall_policy_id: firewall policy id to update
        :param firewall_dict: dictionary of request parameters for firewall policy
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
        except APIFailedResponse as e:
            return self.module.fail_json(
                msg="Unable to update the firewall policy id : {0}. {1}".format(
                    firewall_policy_id, str(e.response_text)))
        return response

    @staticmethod
    def _compare_get_request_with_dict(response, firewall_dict):
        """
        Helper method to compare the json response for getting the firewall policy with the request parameters
        :param response: response from the get method
        :param firewall_dict: dictionary of request parameters for firewall policy
        :return: changed: Boolean that returns true if there are differences between
                          the response parameters and the playbook parameters
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
        :return: response - The response from CLC API call
        """
        response = None
        try:
            response = self.clc.v2.API.Call(
                'GET', '/v2-experimental/firewallPolicies/%s/%s/%s' %
                (source_account_alias, location, firewall_policy_id))
        except APIFailedResponse as e:
            if e.response_status_code != 404:
                self.module.fail_json(
                    msg="Unable to fetch the firewall policy with id : {0}. {1}".format(
                        firewall_policy_id, str(e.response_text)))
        return response

    def _wait_for_requests_to_complete(
            self,
            source_account_alias,
            location,
            firewall_policy_id,
            wait_limit=50):
        """
        Waits until the CLC requests are complete if the wait argument is True
        :param source_account_alias: The source account alias for the firewall policy
        :param location: datacenter of the firewall policy
        :param firewall_policy_id: The firewall policy id
        :param wait_limit: The number of times to check the status for completion
        :return: the firewall_policy object
        """
        wait = self.module.params.get('wait')
        count = 0
        firewall_policy = None
        while wait:
            count += 1
            firewall_policy = self._get_firewall_policy(
                source_account_alias, location, firewall_policy_id)
            status = firewall_policy.get('status')
            if status == 'active' or count > wait_limit:
                wait = False
            else:
                # wait for 2 seconds
                sleep(2)
        return firewall_policy

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
