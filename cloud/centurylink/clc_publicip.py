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
module: clc_publicip
short_description: Add and Delete public ips on servers in CenturyLink Cloud.
description:
  - An Ansible module to add or delete public ip addresses on an existing server or servers in CenturyLink Cloud.
options:
  protocol:
    descirption:
      - The protocol that the public IP will listen for.
    default: TCP
    required: False
  ports:
    description:
      - A list of ports to expose.
    required: True
  server_ids:
    description:
      - A list of servers to create public ips on.
    required: True
  state:
    description:
      - Determine wheteher to create or delete public IPs. If present module will not create a second public ip if one
        already exists.
    default: present
    choices: ['present', 'absent']
    required: False
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
    choices: [ True, False ]
    default: True
    required: False
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

- name: Add Public IP to Server
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create Public IP For Servers
      clc_publicip:
        protocol: 'TCP'
        ports:
            - 80
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        state: present
      register: clc

    - name: debug
      debug: var=clc

- name: Delete Public IP from Server
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create Public IP For Servers
      clc_publicip:
        server_ids:
            - UC1ACCTSRVR01
            - UC1ACCTSRVR02
        state: absent
      register: clc

    - name: debug
      debug: var=clc
'''

__version__ = '${version}'

import requests

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
    from clc import CLCException
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True


class ClcPublicIp(object):
    clc = clc_sdk
    module = None
    group_dict = {}

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module
        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

        self._set_user_agent(self.clc)

    def process_request(self):
        """
        Process the request - Main Code Path
        :param params: dictionary of module parameters
        :return: Returns with either an exit_json or fail_json
        """
        self._set_clc_credentials_from_env()
        params = self.module.params
        server_ids = params['server_ids']
        ports = params['ports']
        protocol = params['protocol']
        state = params['state']
        requests = []
        chagned_server_ids = []
        changed = False

        if state == 'present':
            changed, chagned_server_ids, requests = self.ensure_public_ip_present(
                server_ids=server_ids, protocol=protocol, ports=ports)
        elif state == 'absent':
            changed, chagned_server_ids, requests = self.ensure_public_ip_absent(
                server_ids=server_ids)
        else:
            return self.module.fail_json(msg="Unknown State: " + state)
        self._wait_for_requests_to_complete(requests)
        return self.module.exit_json(changed=changed,
                                     server_ids=chagned_server_ids)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            protocol=dict(default='TCP'),
            ports=dict(type='list'),
            wait=dict(type='bool', default=True),
            state=dict(default='present', choices=['present', 'absent']),
        )
        return argument_spec

    def ensure_public_ip_present(self, server_ids, protocol, ports):
        """
        Ensures the given server ids having the public ip available
        :param server_ids: the list of server ids
        :param protocol: the ip protocol
        :param ports: the list of ports to expose
        :return: (changed, changed_server_ids, results)
                  changed: A flag indicating if there is any change
                  changed_server_ids : the list of server ids that are changed
                  results: The result list from clc public ip call
        """
        changed = False
        results = []
        changed_server_ids = []
        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.PublicIPs().public_ips) == 0]
        ports_to_expose = [{'protocol': protocol, 'port': port}
                           for port in ports]
        for server in servers_to_change:
            if not self.module.check_mode:
                result = server.PublicIPs().Add(ports_to_expose)
                results.append(result)
            changed_server_ids.append(server.id)
            changed = True
        return changed, changed_server_ids, results

    def ensure_public_ip_absent(self, server_ids):
        """
        Ensures the given server ids having the public ip removed if there is any
        :param server_ids: the list of server ids
        :return: (changed, changed_server_ids, results)
                  changed: A flag indicating if there is any change
                  changed_server_ids : the list of server ids that are changed
                  results: The result list from clc public ip call
        """
        changed = False
        results = []
        changed_server_ids = []
        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.PublicIPs().public_ips) > 0]
        ips_to_delete = []
        for server in servers_to_change:
            for ip_address in server.PublicIPs().public_ips:
                ips_to_delete.append(ip_address)
        for server in servers_to_change:
            if not self.module.check_mode:
                for ip in ips_to_delete:
                    result = ip.Delete()
                    results.append(result)
            changed_server_ids.append(server.id)
            changed = True
        return changed, changed_server_ids, results

    def _wait_for_requests_to_complete(self, requests_lst):
        """
        Waits until the CLC requests are complete if the wait argument is True
        :param requests_lst: The list of CLC request objects
        :return: none
        """
        if not self.module.params['wait']:
            return
        for request in requests_lst:
            request.WaitUntilComplete()
            for request_details in request.requests:
                if request_details.Status() != 'succeeded':
                    self.module.fail_json(
                        msg='Unable to process public ip request')

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

    def _get_servers_from_clc(self, server_ids, message):
        """
        Gets list of servers form CLC api
        """
        try:
            return self.clc.v2.Servers(server_ids).servers
        except CLCException as exception:
            self.module.fail_json(msg=message + ': %s' % exception)

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
        argument_spec=ClcPublicIp._define_module_argument_spec(),
        supports_check_mode=True
    )
    clc_public_ip = ClcPublicIp(module)
    clc_public_ip.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
