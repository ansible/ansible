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
module: clc_blueprint_package
short_desciption: deploys a blue print package on a set of servers in CenturyLink Cloud.
description:
  - An Ansible module to deploy blue print package on a set of servers in CenturyLink Cloud.
options:
  server_ids:
    description:
      - A list of server Ids to deploy the blue print package.
    default: []
    required: True
    aliases: []
  package_id:
    description:
      - The package id of the blue print.
    default: None
    required: True
    aliases: []
  package_params:
    description:
      - The dictionary of arguments required to deploy the blue print.
    default: {}
    required: False
    aliases: []
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

- name: Deploy package
      clc_blueprint_package:
        server_ids:
            - UC1WFSDANS01
            - UC1WFSDANS02
        package_id: 77abb844-579d-478d-3955-c69ab4a7ba1a
        package_params: {}
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


class ClcBlueprintPackage():

    clc = clc_sdk
    module = None

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
        :return: Returns with either an exit_json or fail_json
        """
        p = self.module.params

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

        self._set_clc_credentials_from_env()

        server_ids = p['server_ids']
        package_id = p['package_id']
        package_params = p['package_params']
        state = p['state']
        if state == 'present':
            changed, changed_server_ids, requests = self.ensure_package_installed(
                server_ids, package_id, package_params)
            if not self.module.check_mode:
                self._wait_for_requests_to_complete(requests)
        self.module.exit_json(changed=changed, server_ids=changed_server_ids)

    @staticmethod
    def define_argument_spec():
        """
        This function defnines the dictionary object required for
        package module
        :return: the package dictionary object
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            package_id=dict(required=True),
            package_params=dict(type='dict', default={}),
            wait=dict(default=True),
            state=dict(default='present', choices=['present'])
        )
        return argument_spec

    def ensure_package_installed(self, server_ids, package_id, package_params):
        """
        Ensure the package is installed in the given list of servers
        :param server_ids: the server list where the package needs to be installed
        :param package_id: the package id
        :param package_params: the package arguments
        :return: (changed, server_ids)
                    changed: A flag indicating if a change was made
                    server_ids: The list of servers modfied
        """
        changed = False
        requests = []
        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to get servers from CLC')
        try:
            for server in servers:
                request = self.clc_install_package(
                    server,
                    package_id,
                    package_params)
                requests.append(request)
                changed = True
        except CLCException as ex:
            self.module.fail_json(
                msg='Failed while installing package : %s with Error : %s' %
                (package_id, ex))
        return changed, server_ids, requests

    def clc_install_package(self, server, package_id, package_params):
        """
        Read all servers from CLC and executes each package from package_list
        :param server_list: The target list of servers where the packages needs to be installed
        :param package_list: The list of packages to be installed
        :return: (changed, server_ids)
                    changed: A flag indicating if a change was made
                    server_ids: The list of servers modfied
        """
        result = None
        if not self.module.check_mode:
            result = server.ExecutePackage(
                package_id=package_id,
                parameters=package_params)
        return result

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
                        msg='Unable to process package install request')

    def _get_servers_from_clc(self, server_list, message):
        """
        Internal function to fetch list of CLC server objects from a list of server ids
        :param the list server ids
        :return the list of CLC server objects
        """
        try:
            return self.clc.v2.Servers(server_list).servers
        except CLCException as ex:
            self.module.fail_json(msg=message + ': %s' % ex)

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
    Main function
    :return: None
    """
    module = AnsibleModule(
        argument_spec=ClcBlueprintPackage.define_argument_spec(),
        supports_check_mode=True
    )
    clc_blueprint_package = ClcBlueprintPackage(module)
    clc_blueprint_package.process_request()

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
