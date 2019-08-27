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

module: manageiq_tags

short_description: Management of resource tags in ManageIQ.
extends_documentation_fragment: manageiq
version_added: '2.5'
author: Daniel Korn (@dkorn)
description:
  - The manageiq_tags module supports adding, updating and deleting tags in ManageIQ.

options:
  state:
    description:
      - absent - tags should not exist,
      - present - tags should exist,
      - list - list current tags.
    choices: ['absent', 'present', 'list']
    default: 'present'
  tags:
    description:
      - tags - list of dictionaries, each includes 'name' and 'category' keys.
      - required if state is present or absent.
  resource_type:
    description:
      - the relevant resource type in manageiq
    required: true
    choices: ['provider', 'host', 'vm', 'blueprint', 'category', 'cluster',
        'data store', 'group', 'resource pool', 'service', 'service template',
        'template', 'tenant', 'user']
  resource_name:
    description:
      - the relevant resource name in manageiq
    required: true
'''

EXAMPLES = '''
- name: Create new tags for a provider in ManageIQ
  manageiq_tags:
    resource_name: 'EngLab'
    resource_type: 'provider'
    tags:
    - category: environment
      name: prod
    - category: owner
      name: prod_ops
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: Remove tags for a provider in ManageIQ
  manageiq_tags:
    state: absent
    resource_name: 'EngLab'
    resource_type: 'provider'
    tags:
    - category: environment
      name: prod
    - category: owner
      name: prod_ops
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: List current tags for a provider in ManageIQ
  manageiq_tags:
    state: list
    resource_name: 'EngLab'
    resource_type: 'provider'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec, manageiq_entities


def query_resource_id(manageiq, resource_type, resource_name):
    """ Query the resource name in ManageIQ.

    Returns:
        the resource id if it exists in manageiq, Fail otherwise.
    """
    resource = manageiq.find_collection_resource_by(resource_type, name=resource_name)
    if resource:
        return resource["id"]
    else:
        msg = "{resource_name} {resource_type} does not exist in manageiq".format(
            resource_name=resource_name, resource_type=resource_type)
        manageiq.module.fail_json(msg=msg)


class ManageIQTags(object):
    """
        Object to execute tags management operations of manageiq resources.
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

    def full_tag_name(self, tag):
        """ Returns the full tag name in manageiq
        """
        return '/managed/{tag_category}/{tag_name}'.format(
            tag_category=tag['category'],
            tag_name=tag['name'])

    def clean_tag_object(self, tag):
        """ Clean a tag object to have human readable form of:
        {
            full_name: STR,
            name: STR,
            display_name: STR,
            category: STR
        }
        """
        full_name = tag.get('name')
        categorization = tag.get('categorization', {})

        return dict(
            full_name=full_name,
            name=categorization.get('name'),
            display_name=categorization.get('display_name'),
            category=categorization.get('category', {}).get('name'))

    def query_resource_tags(self):
        """ Returns a set of the tag objects assigned to the resource
        """
        url = '{resource_url}/tags?expand=resources&attributes=categorization'
        try:
            response = self.client.get(url.format(resource_url=self.resource_url))
        except Exception as e:
            msg = "Failed to query {resource_type} tags: {error}".format(
                resource_type=self.resource_type,
                error=e)
            self.module.fail_json(msg=msg)

        resources = response.get('resources', [])

        # clean the returned rest api tag object to look like:
        # {full_name: STR, name: STR, display_name: STR, category: STR}
        tags = [self.clean_tag_object(tag) for tag in resources]

        return tags

    def tags_to_update(self, tags, action):
        """ Create a list of tags we need to update in ManageIQ.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        tags_to_post = []
        assigned_tags = self.query_resource_tags()

        # make a list of assigned full tag names strings
        # e.g. ['/managed/environment/prod', ...]
        assigned_tags_set = set([tag['full_name'] for tag in assigned_tags])

        for tag in tags:
            assigned = self.full_tag_name(tag) in assigned_tags_set

            if assigned and action == 'unassign':
                tags_to_post.append(tag)
            elif (not assigned) and action == 'assign':
                tags_to_post.append(tag)

        return tags_to_post

    def assign_or_unassign_tags(self, tags, action):
        """ Perform assign/unassign action
        """
        # get a list of tags needed to be changed
        tags_to_post = self.tags_to_update(tags, action)
        if not tags_to_post:
            return dict(
                changed=False,
                msg="Tags already {action}ed, nothing to do".format(action=action))

        # try to assign or unassign tags to resource
        url = '{resource_url}/tags'.format(resource_url=self.resource_url)
        try:
            response = self.client.post(url, action=action, resources=tags)
        except Exception as e:
            msg = "Failed to {action} tag: {error}".format(
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

        # successfully changed all needed tags
        return dict(
            changed=True,
            msg="Successfully {action}ed tags".format(action=action))


def main():
    actions = {'present': 'assign', 'absent': 'unassign', 'list': 'list'}
    argument_spec = dict(
        tags=dict(type='list'),
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
            ('state', 'present', ['tags']),
            ('state', 'absent', ['tags'])
        ],
    )

    tags = module.params['tags']
    resource_type_key = module.params['resource_type']
    resource_name = module.params['resource_name']
    state = module.params['state']

    # get the action and resource type
    action = actions[state]
    resource_type = manageiq_entities()[resource_type_key]

    manageiq = ManageIQ(module)

    # query resource id, fail if resource does not exist
    resource_id = query_resource_id(manageiq, resource_type, resource_name)

    manageiq_tags = ManageIQTags(manageiq, resource_type, resource_id)

    if action == 'list':
        # return a list of current tags for this object
        current_tags = manageiq_tags.query_resource_tags()
        res_args = dict(changed=False, tags=current_tags)
    else:
        # assign or unassign the tags
        res_args = manageiq_tags.assign_or_unassign_tags(tags, action)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
