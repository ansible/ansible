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
module: clc_group
short_description: Create/delete Server Groups at Centurylink Cloud
description:
  - Create or delete Server Groups at Centurylink Centurylink Cloud
version_added: "2.0"
options:
  name:
    description:
      - The name of the Server Group
    required: True
  description:
    description:
      - A description of the Server Group
    required: False
  parent:
    description:
      - The parent group of the server group. If parent is not provided, it creates the group at top level.
    required: False
  location:
    description:
      - Datacenter to create the group in. If location is not provided, the group gets created in the default datacenter
        associated with the account
    required: False
  state:
    description:
      - Whether to create or delete the group
    default: present
    choices: ['present', 'absent']
  wait:
    description:
      - Whether to wait for the tasks to finish before returning.
    choices: [ True, False ]
    default: True
    required: False
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

# Create a Server Group

---
- name: Create Server Group
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create / Verify a Server Group at CenturyLink Cloud
      clc_group:
        name: 'My Cool Server Group'
        parent: 'Default Group'
        state: present
      register: clc

    - name: debug
      debug: var=clc

# Delete a Server Group

---
- name: Delete Server Group
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete / Verify Absent a Server Group at CenturyLink Cloud
      clc_group:
        name: 'My Cool Server Group'
        parent: 'Default Group'
        state: absent
      register: clc

    - name: debug
      debug: var=clc

'''

RETURN = '''
group:
    description: The group information
    returned: success
    type: dict
    sample:
        {
           "changeInfo":{
              "createdBy":"service.wfad",
              "createdDate":"2015-07-29T18:52:47Z",
              "modifiedBy":"service.wfad",
              "modifiedDate":"2015-07-29T18:52:47Z"
           },
           "customFields":[

           ],
           "description":"test group",
           "groups":[

           ],
           "id":"bb5f12a3c6044ae4ad0a03e73ae12cd1",
           "links":[
              {
                 "href":"/v2/groups/wfad",
                 "rel":"createGroup",
                 "verbs":[
                    "POST"
                 ]
              },
              {
                 "href":"/v2/servers/wfad",
                 "rel":"createServer",
                 "verbs":[
                    "POST"
                 ]
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1",
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
                 "rel":"parentGroup"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/defaults",
                 "rel":"defaults",
                 "verbs":[
                    "GET",
                    "POST"
                 ]
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/billing",
                 "rel":"billing"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/archive",
                 "rel":"archiveGroupAction"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/statistics",
                 "rel":"statistics"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/upcomingScheduledActivities",
                 "rel":"upcomingScheduledActivities"
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/horizontalAutoscalePolicy",
                 "rel":"horizontalAutoscalePolicyMapping",
                 "verbs":[
                    "GET",
                    "PUT",
                    "DELETE"
                 ]
              },
              {
                 "href":"/v2/groups/wfad/bb5f12a3c6044ae4ad0a03e73ae12cd1/scheduledActivities",
                 "rel":"scheduledActivities",
                 "verbs":[
                    "GET",
                    "POST"
                 ]
              }
           ],
           "locationId":"UC1",
           "name":"test group",
           "status":"active",
           "type":"default"
        }
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


class ClcGroup(object):

    clc = None
    root_group = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.group_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')
        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')
        if requests.__version__ and LooseVersion(requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

        self._set_user_agent(self.clc)

    def process_request(self):
        """
        Execute the main code path, and handle the request
        :return: none
        """
        location = self.module.params.get('location')
        group_name = self.module.params.get('name')
        parent_name = self.module.params.get('parent')
        group_description = self.module.params.get('description')
        state = self.module.params.get('state')

        self._set_clc_credentials_from_env()
        self.group_dict = self._get_group_tree_for_datacenter(
            datacenter=location)

        if state == "absent":
            changed, group, requests = self._ensure_group_is_absent(
                group_name=group_name, parent_name=parent_name)
            if requests:
                self._wait_for_requests_to_complete(requests)
        else:
            changed, group = self._ensure_group_is_present(
                group_name=group_name, parent_name=parent_name, group_description=group_description)
        try:
            group = group.data
        except AttributeError:
            group = group_name
        self.module.exit_json(changed=changed, group=group)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(required=True),
            description=dict(default=None),
            parent=dict(default=None),
            location=dict(default=None),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(type='bool', default=True))

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

    def _ensure_group_is_absent(self, group_name, parent_name):
        """
        Ensure that group_name is absent by deleting it if necessary
        :param group_name: string - the name of the clc server group to delete
        :param parent_name: string - the name of the parent group for group_name
        :return: changed, group
        """
        changed = False
        group = []
        results = []

        if self._group_exists(group_name=group_name, parent_name=parent_name):
            if not self.module.check_mode:
                group.append(group_name)
                result = self._delete_group(group_name)
                results.append(result)
            changed = True
        return changed, group, results

    def _delete_group(self, group_name):
        """
        Delete the provided server group
        :param group_name: string - the server group to delete
        :return: none
        """
        response = None
        group, parent = self.group_dict.get(group_name)
        try:
            response = group.Delete()
        except CLCException as ex:
            self.module.fail_json(msg='Failed to delete group :{0}. {1}'.format(
                group_name, ex.response_text
            ))
        return response

    def _ensure_group_is_present(
            self,
            group_name,
            parent_name,
            group_description):
        """
        Checks to see if a server group exists, creates it if it doesn't.
        :param group_name: the name of the group to validate/create
        :param parent_name: the name of the parent group for group_name
        :param group_description: a short description of the server group (used when creating)
        :return: (changed, group) -
            changed:  Boolean- whether a change was made,
            group:  A clc group object for the group
        """
        assert self.root_group, "Implementation Error: Root Group not set"
        parent = parent_name if parent_name is not None else self.root_group.name
        description = group_description
        changed = False
        group = group_name

        parent_exists = self._group_exists(group_name=parent, parent_name=None)
        child_exists = self._group_exists(
            group_name=group_name,
            parent_name=parent)

        if parent_exists and child_exists:
            group, parent = self.group_dict[group_name]
            changed = False
        elif parent_exists and not child_exists:
            if not self.module.check_mode:
                group = self._create_group(
                    group=group,
                    parent=parent,
                    description=description)
            changed = True
        else:
            self.module.fail_json(
                msg="parent group: " +
                parent +
                " does not exist")

        return changed, group

    def _create_group(self, group, parent, description):
        """
        Create the provided server group
        :param group: clc_sdk.Group - the group to create
        :param parent: clc_sdk.Parent - the parent group for {group}
        :param description: string - a text description of the group
        :return: clc_sdk.Group - the created group
        """
        response = None
        (parent, grandparent) = self.group_dict[parent]
        try:
            response = parent.Create(name=group, description=description)
        except CLCException as ex:
            self.module.fail_json(msg='Failed to create group :{0}. {1}'.format(
                group, ex.response_text))
        return response

    def _group_exists(self, group_name, parent_name):
        """
        Check to see if a group exists
        :param group_name: string - the group to check
        :param parent_name: string - the parent of group_name
        :return: boolean - whether the group exists
        """
        result = False
        if group_name in self.group_dict:
            (group, parent) = self.group_dict[group_name]
            if parent_name is None or parent_name == parent.name:
                result = True
        return result

    def _get_group_tree_for_datacenter(self, datacenter=None):
        """
        Walk the tree of groups for a datacenter
        :param datacenter: string - the datacenter to walk (ex: 'UC1')
        :return: a dictionary of groups and parents
        """
        self.root_group = self.clc.v2.Datacenter(
            location=datacenter).RootGroup()
        return self._walk_groups_recursive(
            parent_group=None,
            child_group=self.root_group)

    def _walk_groups_recursive(self, parent_group, child_group):
        """
        Walk a parent-child tree of groups, starting with the provided child group
        :param parent_group: clc_sdk.Group - the parent group to start the walk
        :param child_group: clc_sdk.Group - the child group to start the walk
        :return: a dictionary of groups and parents
        """
        result = {str(child_group): (child_group, parent_group)}
        groups = child_group.Subgroups().groups
        if len(groups) > 0:
            for group in groups:
                if group.type != 'default':
                    continue

                result.update(self._walk_groups_recursive(child_group, group))
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
                        msg='Unable to process group request')

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
        argument_spec=ClcGroup._define_module_argument_spec(),
        supports_check_mode=True)

    clc_group = ClcGroup(module)
    clc_group.process_request()


if __name__ == '__main__':
    main()
