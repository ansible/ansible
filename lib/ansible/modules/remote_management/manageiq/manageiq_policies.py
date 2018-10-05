#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Daniel Korn <korndaniel1@gmail.com>
# (c) 2017, Yaacov Zamir <yzamir@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''

module: manageiq_policies

short_description: Management of resource policy_profiles in ManageIQ.
extends_documentation_fragment: manageiq
version_added: '2.5'
author: Daniel Korn (@dkorn)
description:
  - The manageiq_policies module supports adding and deleting policy_profiles in ManageIQ.

options:
  state:
    description:
      - absent - policy_profiles should not exist,
      - present - policy_profiles should exist,
      - list - list current policy_profiles and policies.
    choices: ['absent', 'present', 'list']
    default: 'present'
  policy_profiles:
    description:
      - list of dictionaries, each includes the policy_profile 'name' key.
      - required if state is present or absent.
  resource_type:
    description:
      - the type of the resource to which the profile should be [un]assigned
    required: true
    choices: ['provider', 'host', 'vm', 'blueprint', 'category', 'cluster',
        'data store', 'group', 'resource pool', 'service', 'service template',
        'template', 'tenant', 'user']
  resource_name:
    description:
      - the name of the resource to which the profile should be [un]assigned
    required: true
'''

EXAMPLES = '''
- name: Assign new policy_profile for a provider in ManageIQ
  manageiq_policies:
    resource_name: 'EngLab'
    resource_type: 'provider'
    policy_profiles:
      - name: openscap profile
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Unassign a policy_profile for a provider in ManageIQ
  manageiq_policies:
    state: absent
    resource_name: 'EngLab'
    resource_type: 'provider'
    policy_profiles:
      - name: openscap profile
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: List current policy_profile and policies for a provider in ManageIQ
  manageiq_policies:
    state: list
    resource_name: 'EngLab'
    resource_type: 'provider'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False
'''

RETURN = '''
manageiq_policies:
    description:
      - List current policy_profile and policies for a provider in ManageIQ
    returned: always
    type: dict
    sample: '{
        "changed": false,
        "profiles": [
            {
                "policies": [
                    {
                        "active": true,
                        "description": "OpenSCAP",
                        "name": "openscap policy"
                    },
                    {
                        "active": true,
                        "description": "Analyse incoming container images",
                        "name": "analyse incoming container images"
                    },
                    {
                        "active": true,
                        "description": "Schedule compliance after smart state analysis",
                        "name": "schedule compliance after smart state analysis"
                    }
                ],
                "profile_description": "OpenSCAP profile",
                "profile_name": "openscap profile"
            }
        ]
    }'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec, manageiq_entities


class ManageIQPolicies(object):
    """
        Object to execute policies management operations of manageiq resources.
    """

    def __init__(self, manageiq, resource_type, resource_id):
        self.manageiq = manageiq

        self.module = self.manageiq.module
        self.api_url = self.manageiq.api_url
        self.client = self.manageiq.client

        self.resource_type = resource_type
        self.resource_id = resource_id
        self.resource_url = '{api_url}/{resource_type}/{resource_id}'.format(
            api_url=self.api_url,
            resource_type=resource_type,
            resource_id=resource_id)

    def query_profile_href(self, profile):
        """ Add or Update the policy_profile href field

        Example:
            {name: STR, ...} => {name: STR, href: STR}
        """
        resource = self.manageiq.find_collection_resource_or_fail(
            "policy_profiles", **profile)
        return dict(name=profile['name'], href=resource['href'])

    def query_resource_profiles(self):
        """ Returns a set of the profile objects objects assigned to the resource
        """
        url = '{resource_url}/policy_profiles?expand=resources'
        try:
            response = self.client.get(url.format(resource_url=self.resource_url))
        except Exception as e:
            msg = "Failed to query {resource_type} policies: {error}".format(
                resource_type=self.resource_type,
                error=e)
            self.module.fail_json(msg=msg)

        resources = response.get('resources', [])

        # clean the returned rest api profile object to look like:
        # {profile_name: STR, profile_description: STR, policies: ARR<POLICIES>}
        profiles = [self.clean_profile_object(profile) for profile in resources]

        return profiles

    def query_profile_policies(self, profile_id):
        """ Returns a set of the policy objects assigned to the resource
        """
        url = '{api_url}/policy_profiles/{profile_id}?expand=policies'
        try:
            response = self.client.get(url.format(api_url=self.api_url, profile_id=profile_id))
        except Exception as e:
            msg = "Failed to query {resource_type} policies: {error}".format(
                resource_type=self.resource_type,
                error=e)
            self.module.fail_json(msg=msg)

        resources = response.get('policies', [])

        # clean the returned rest api policy object to look like:
        # {name: STR, description: STR, active: BOOL}
        policies = [self.clean_policy_object(policy) for policy in resources]

        return policies

    def clean_policy_object(self, policy):
        """ Clean a policy object to have human readable form of:
        {
            name: STR,
            description: STR,
            active: BOOL
        }
        """
        name = policy.get('name')
        description = policy.get('description')
        active = policy.get('active')

        return dict(
            name=name,
            description=description,
            active=active)

    def clean_profile_object(self, profile):
        """ Clean a profile object to have human readable form of:
        {
            profile_name: STR,
            profile_description: STR,
            policies: ARR<POLICIES>
        }
        """
        profile_id = profile['id']
        name = profile.get('name')
        description = profile.get('description')
        policies = self.query_profile_policies(profile_id)

        return dict(
            profile_name=name,
            profile_description=description,
            policies=policies)

    def profiles_to_update(self, profiles, action):
        """ Create a list of policies we need to update in ManageIQ.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        profiles_to_post = []
        assigned_profiles = self.query_resource_profiles()

        # make a list of assigned full profile names strings
        # e.g. ['openscap profile', ...]
        assigned_profiles_set = set([profile['profile_name'] for profile in assigned_profiles])

        for profile in profiles:
            assigned = profile.get('name') in assigned_profiles_set

            if (action == 'unassign' and assigned) or (action == 'assign' and not assigned):
                # add/update the policy profile href field
                # {name: STR, ...} => {name: STR, href: STR}
                profile = self.query_profile_href(profile)
                profiles_to_post.append(profile)

        return profiles_to_post

    def assign_or_unassign_profiles(self, profiles, action):
        """ Perform assign/unassign action
        """
        # get a list of profiles needed to be changed
        profiles_to_post = self.profiles_to_update(profiles, action)
        if not profiles_to_post:
            return dict(
                changed=False,
                msg="Profiles {profiles} already {action}ed, nothing to do".format(
                    action=action,
                    profiles=profiles))

        # try to assign or unassign profiles to resource
        url = '{resource_url}/policy_profiles'.format(resource_url=self.resource_url)
        try:
            response = self.client.post(url, action=action, resources=profiles_to_post)
        except Exception as e:
            msg = "Failed to {action} profile: {error}".format(
                action=action,
                error=e)
            self.module.fail_json(msg=msg)

        # check all entities in result to be successfull
        for result in response['results']:
            if not result['success']:
                msg = "Failed to {action}: {message}".format(
                    action=action,
                    message=result['message'])
                self.module.fail_json(msg=msg)

        # successfully changed all needed profiles
        return dict(
            changed=True,
            msg="Successfully {action}ed profiles: {profiles}".format(
                action=action,
                profiles=profiles))


def main():
    actions = {'present': 'assign', 'absent': 'unassign', 'list': 'list'}
    argument_spec = dict(
        policy_profiles=dict(type='list'),
        resource_name=dict(required=True, type='str'),
        resource_type=dict(required=True, type='str',
                           choices=manageiq_entities().keys()),
        state=dict(required=False, type='str',
                   choices=['present', 'absent', 'list'], default='present'),
    )
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['policy_profiles']),
            ('state', 'absent', ['policy_profiles'])
        ],
    )

    policy_profiles = module.params['policy_profiles']
    resource_type_key = module.params['resource_type']
    resource_name = module.params['resource_name']
    state = module.params['state']

    # get the action and resource type
    action = actions[state]
    resource_type = manageiq_entities()[resource_type_key]

    manageiq = ManageIQ(module)

    # query resource id, fail if resource does not exist
    resource_id = manageiq.find_collection_resource_or_fail(resource_type, name=resource_name)['id']

    manageiq_policies = ManageIQPolicies(manageiq, resource_type, resource_id)

    if action == 'list':
        # return a list of current profiles for this object
        current_profiles = manageiq_policies.query_resource_profiles()
        res_args = dict(changed=False, profiles=current_profiles)
    else:
        # assign or unassign the profiles
        res_args = manageiq_policies.assign_or_unassign_profiles(policy_profiles, action)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
