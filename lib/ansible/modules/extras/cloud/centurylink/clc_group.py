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
module: clc_group
short_desciption: Create/delete Server Groups at Centurylink Cloud
description:
  - Create or delete Server Groups at Centurylink Centurylink Cloud
options:
  name:
    description:
      - The name of the Server Group
  description:
    description:
      - A description of the Server Group
  parent:
    description:
      - The parent group of the server group
  location:
    description:
      - Datacenter to create the group in
  state:
    description:
      - Whether to create or delete the group
    default: present
    choices: ['present', 'absent']

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
            changed, group, response = self._ensure_group_is_absent(
                group_name=group_name, parent_name=parent_name)

        else:
            changed, group, response = self._ensure_group_is_present(
                group_name=group_name, parent_name=parent_name, group_description=group_description)


        self.module.exit_json(changed=changed, group=group_name)

    #
    #  Functions to define the Ansible module and its arguments
    #

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
            alias=dict(default=None),
            custom_fields=dict(type='list', default=[]),
            server_ids=dict(type='list', default=[]),
            state=dict(default='present', choices=['present', 'absent']))

        return argument_spec

    #
    #   Module Behavior Functions
    #

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
                for g in group:
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
        group, parent = self.group_dict.get(group_name)
        response = group.Delete()
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
        results = []
        groups = []
        group = group_name

        parent_exists = self._group_exists(group_name=parent, parent_name=None)
        child_exists = self._group_exists(group_name=group_name, parent_name=parent)

        if parent_exists and child_exists:
            group, parent = self.group_dict[group_name]
            changed = False
        elif parent_exists and not child_exists:
            if not self.module.check_mode:
                groups.append(group_name)
                for g in groups:
                    group = self._create_group(
                        group=group,
                        parent=parent,
                        description=description)
                    results.append(group)
            changed = True
        else:
            self.module.fail_json(
                msg="parent group: " +
                parent +
                " does not exist")

        return changed, group, results

    def _create_group(self, group, parent, description):
        """
        Create the provided server group
        :param group: clc_sdk.Group - the group to create
        :param parent: clc_sdk.Parent - the parent group for {group}
        :param description: string - a text description of the group
        :return: clc_sdk.Group - the created group
        """

        (parent, grandparent) = self.group_dict[parent]
        return parent.Create(name=group, description=description)

    #
    #   Utility Functions
    #

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

    def _get_group_tree_for_datacenter(self, datacenter=None, alias=None):
        """
        Walk the tree of groups for a datacenter
        :param datacenter: string - the datacenter to walk (ex: 'UC1')
        :param alias: string - the account alias to search. Defaults to the current user's account
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
    module = AnsibleModule(argument_spec=ClcGroup._define_module_argument_spec(), supports_check_mode=True)

    clc_group = ClcGroup(module)
    clc_group.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
