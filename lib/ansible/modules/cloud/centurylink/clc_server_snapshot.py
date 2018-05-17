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
module: clc_server_snapshot
short_description: Create, Delete and Restore server snapshots in CenturyLink Cloud.
description:
  - An Ansible module to Create, Delete and Restore server snapshots in CenturyLink Cloud.
version_added: "2.0"
options:
  server_ids:
    description:
      - The list of CLC server Ids.
    required: True
  expiration_days:
    description:
      - The number of days to keep the server snapshot before it expires.
    default: 7
    required: False
  state:
    description:
      - The state to insure that the provided resources are in.
    default: 'present'
    required: False
    choices: ['present', 'absent', 'restore']
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    type: bool
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

- name: Create server snapshot
  clc_server_snapshot:
    server_ids:
        - UC1TEST-SVR01
        - UC1TEST-SVR02
    expiration_days: 10
    wait: True
    state: present

- name: Restore server snapshot
  clc_server_snapshot:
    server_ids:
        - UC1TEST-SVR01
        - UC1TEST-SVR02
    wait: True
    state: restore

- name: Delete server snapshot
  clc_server_snapshot:
    server_ids:
        - UC1TEST-SVR01
        - UC1TEST-SVR02
    wait: True
    state: absent
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
'''

__version__ = '${version}'

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
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True

from ansible.module_utils.basic import AnsibleModule


class ClcSnapshot:

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
        p = self.module.params
        server_ids = p['server_ids']
        expiration_days = p['expiration_days']
        state = p['state']
        request_list = []
        changed = False
        changed_servers = []

        self._set_clc_credentials_from_env()
        if state == 'present':
            changed, request_list, changed_servers = self.ensure_server_snapshot_present(
                server_ids=server_ids,
                expiration_days=expiration_days)
        elif state == 'absent':
            changed, request_list, changed_servers = self.ensure_server_snapshot_absent(
                server_ids=server_ids)
        elif state == 'restore':
            changed, request_list, changed_servers = self.ensure_server_snapshot_restore(
                server_ids=server_ids)

        self._wait_for_requests_to_complete(request_list)
        return self.module.exit_json(
            changed=changed,
            server_ids=changed_servers)

    def ensure_server_snapshot_present(self, server_ids, expiration_days):
        """
        Ensures the given set of server_ids have the snapshots created
        :param server_ids: The list of server_ids to create the snapshot
        :param expiration_days: The number of days to keep the snapshot
        :return: (changed, request_list, changed_servers)
                 changed: A flag indicating whether any change was made
                 request_list: the list of clc request objects from CLC API call
                 changed_servers: The list of servers ids that are modified
        """
        request_list = []
        changed = False
        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.GetSnapshots()) == 0]
        for server in servers_to_change:
            changed = True
            if not self.module.check_mode:
                request = self._create_server_snapshot(server, expiration_days)
                request_list.append(request)
        changed_servers = [
            server.id for server in servers_to_change if server.id]
        return changed, request_list, changed_servers

    def _create_server_snapshot(self, server, expiration_days):
        """
        Create the snapshot for the CLC server
        :param server: the CLC server object
        :param expiration_days: The number of days to keep the snapshot
        :return: the create request object from CLC API Call
        """
        result = None
        try:
            result = server.CreateSnapshot(
                delete_existing=True,
                expiration_days=expiration_days)
        except CLCException as ex:
            self.module.fail_json(msg='Failed to create snapshot for server : {0}. {1}'.format(
                server.id, ex.response_text
            ))
        return result

    def ensure_server_snapshot_absent(self, server_ids):
        """
        Ensures the given set of server_ids have the snapshots removed
        :param server_ids: The list of server_ids to delete the snapshot
        :return: (changed, request_list, changed_servers)
                 changed: A flag indicating whether any change was made
                 request_list: the list of clc request objects from CLC API call
                 changed_servers: The list of servers ids that are modified
        """
        request_list = []
        changed = False
        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.GetSnapshots()) > 0]
        for server in servers_to_change:
            changed = True
            if not self.module.check_mode:
                request = self._delete_server_snapshot(server)
                request_list.append(request)
        changed_servers = [
            server.id for server in servers_to_change if server.id]
        return changed, request_list, changed_servers

    def _delete_server_snapshot(self, server):
        """
        Delete snapshot for the CLC server
        :param server: the CLC server object
        :return: the delete snapshot request object from CLC API
        """
        result = None
        try:
            result = server.DeleteSnapshot()
        except CLCException as ex:
            self.module.fail_json(msg='Failed to delete snapshot for server : {0}. {1}'.format(
                server.id, ex.response_text
            ))
        return result

    def ensure_server_snapshot_restore(self, server_ids):
        """
        Ensures the given set of server_ids have the snapshots restored
        :param server_ids: The list of server_ids to delete the snapshot
        :return: (changed, request_list, changed_servers)
                 changed: A flag indicating whether any change was made
                 request_list: the list of clc request objects from CLC API call
                 changed_servers: The list of servers ids that are modified
        """
        request_list = []
        changed = False
        servers = self._get_servers_from_clc(
            server_ids,
            'Failed to obtain server list from the CLC API')
        servers_to_change = [
            server for server in servers if len(
                server.GetSnapshots()) > 0]
        for server in servers_to_change:
            changed = True
            if not self.module.check_mode:
                request = self._restore_server_snapshot(server)
                request_list.append(request)
        changed_servers = [
            server.id for server in servers_to_change if server.id]
        return changed, request_list, changed_servers

    def _restore_server_snapshot(self, server):
        """
        Restore snapshot for the CLC server
        :param server: the CLC server object
        :return: the restore snapshot request object from CLC API
        """
        result = None
        try:
            result = server.RestoreSnapshot()
        except CLCException as ex:
            self.module.fail_json(msg='Failed to restore snapshot for server : {0}. {1}'.format(
                server.id, ex.response_text
            ))
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
                        msg='Unable to process server snapshot request')

    @staticmethod
    def define_argument_spec():
        """
        This function defines the dictionary object required for
        package module
        :return: the package dictionary object
        """
        argument_spec = dict(
            server_ids=dict(type='list', required=True),
            expiration_days=dict(default=7),
            wait=dict(default=True),
            state=dict(
                default='present',
                choices=[
                    'present',
                    'absent',
                    'restore']),
        )
        return argument_spec

    def _get_servers_from_clc(self, server_list, message):
        """
        Internal function to fetch list of CLC server objects from a list of server ids
        :param server_list: The list of server ids
        :param message: The error message to throw in case of any error
        :return the list of CLC server objects
        """
        try:
            return self.clc.v2.Servers(server_list).servers
        except CLCException as ex:
            return self.module.fail_json(msg=message + ': %s' % ex)

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
        argument_spec=ClcSnapshot.define_argument_spec(),
        supports_check_mode=True
    )
    clc_snapshot = ClcSnapshot(module)
    clc_snapshot.process_request()


if __name__ == '__main__':
    main()
