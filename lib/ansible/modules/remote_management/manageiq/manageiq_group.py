#!/usr/bin/python
#
# (c) 2018, Evert Mulder <evertmulder@gmail.com> (base on manageiq_user.py by Daniel Korn <korndaniel1@gmail.com>)
#
# This file is part of Ansible
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: manageiq_group

short_description: Management of groups in ManageIQ.
extends_documentation_fragment: manageiq
version_added: '2.8'
author: Evert Mulder (@evertmulder)
description:
  - The manageiq_group module supports adding, updating and deleting groups in ManageIQ.

options:
  state:
    description:
    - absent - group should not exist, present - group should be.
    choices: ['absent', 'present']
    default: 'present'
  description:
    description:
    - The group description.
    required: true
    default: null
  role_id:
    description:
    - The the group role id
    required: false
    default: null
  role:
    description:
    - The the group role name
    - The C(role_id) has precedence over the C(role) when supplied.
    required: false
    default: null
  tenant_id:
    description:
    - The tenant for the group identified by the tenant id.
    required: false
    default: null
  tenant:
    description:
    - The tenant for the group identified by the tenant name.
    - The C(tenant_id) has precedence over the C(tenant) when supplied.
    - Tenant names are case sensitive.
    required: false
    default: null
  managed_filters:
    description: The tag values per category
    type: dict
    required: false
    default: null
  managed_filters_merge_mode:
    description:
    - In merge mode existing categories are kept or updated, new categories are added.
    - In replace mode all categories will be replaced with the supplied C(managed_filters).
    choices: [ merge, replace ]
    default: replace
  belongsto_filters:
    description: A list of strings with a reference to the allowed host, cluster or folder
    type: list
    required: false
    default: null
  belongsto_filters_merge_mode:
    description:
    - In merge mode existing settings are merged with the supplied C(belongsto_filters).
    - In replace mode current values are replaced with the supplied C(belongsto_filters).
    choices: [ merge, replace ]
    default: replace
'''

EXAMPLES = '''
- name: Create a group in ManageIQ with the role EvmRole-user and tenant 'my_tenant'
  manageiq_group:
    description: 'MyGroup-user'
    role: 'EvmRole-user'
    tenant: 'my_tenant'
    manageiq_connection:
      url: 'https://manageiq_server'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: Create a group in ManageIQ with the role EvmRole-user and tenant with tenant_id 4
  manageiq_group:
    description: 'MyGroup-user'
    role: 'EvmRole-user'
    tenant_id: 4
    manageiq_connection:
      url: 'https://manageiq_server'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name:
  - Create or update a group in ManageIQ with the role EvmRole-user and tenant my_tenant.
  - Apply 3 prov_max_cpu and 2 department tags to the group.
  - Limit access to a cluster for the group.
  manageiq_group:
    description: 'MyGroup-user'
    role: 'EvmRole-user'
    tenant: my_tenant
    managed_filters:
      prov_max_cpu:
      - '1'
      - '2'
      - '4'
      department:
      - defense
      - engineering
    managed_filters_merge_mode: replace
    belongsto_filters:
    - "/belongsto/ExtManagementSystem|ProviderName/EmsFolder|Datacenters/EmsFolder|dc_name/EmsFolder|host/EmsCluster|Cluster name"
    belongsto_filters_merge_mode: merge
    manageiq_connection:
      url: 'https://manageiq_server'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: Delete a group in ManageIQ
  manageiq_group:
    state: 'absent'
    description: 'MyGroup-user'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'

- name: Delete a group in ManageIQ using a token
  manageiq_group:
    state: 'absent'
    description: 'MyGroup-user'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      token: 'sometoken'
'''

RETURN = '''
group:
  description: The group.
  returned: success
  type: complex
  contains:
    description:
      description: The group description
      returned: success
      type: str
    id:
      description: The group id
      returned: success
      type: int
    group_type:
      description: The group type, system or user
      returned: success
      type: str
    role:
      description: The group role name
      returned: success
      type: str
    tenant:
      description: The group tenant name
      returned: success
      type: str
    managed_filters:
      description: The tag values per category
      returned: success
      type: dict
    belongsto_filters:
      description: A list of strings with a reference to the allowed host, cluster or folder
      returned: success
      type: list
    created_on:
      description: Group creation date
      returned: success
      type: str
      example: 2018-08-12T08:37:55+00:00
    updated_on:
      description: Group update date
      returned: success
      type: int
      example: 2018-08-12T08:37:55+00:00
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec


class ManageIQgroup(object):
    """
        Object to execute group management operations in manageiq.
    """

    def __init__(self, manageiq):
        self.manageiq = manageiq

        self.module = self.manageiq.module
        self.api_url = self.manageiq.api_url
        self.client = self.manageiq.client

    def group(self, description):
        """ Search for group object by description.
        Returns:
            the group, or None if group was not found.
        """
        groups = self.client.collections.groups.find_by(description=description)
        if len(groups) == 0:
            return None
        else:
            return groups[0]

    def tenant(self, tenant_id, tenant_name):
        """ Search for tenant entity by name or id
        Returns:
            the tenant entity, None if no id or name was supplied
        """

        if tenant_id:
            tenant = self.client.get_entity('tenants', tenant_id)
            if not tenant:
                self.module.fail_json(msg="Tenant with id '%s' not found in manageiq" % str(tenant_id))
            return tenant
        else:
            if tenant_name:
                tenant_res = self.client.collections.tenants.find_by(name=tenant_name)
                if not tenant_res:
                    self.module.fail_json(msg="Tenant '%s' not found in manageiq" % tenant_name)
                if len(tenant_res) > 1:
                    self.module.fail_json(msg="Multiple tenants found in manageiq with name '%s" % tenant_name)
                tenant = tenant_res[0]
                return tenant
            else:
                # No tenant name or tenant id supplied
                return None

    def role(self, role_id, role_name):
        """ Search for a role object by name or id.
        Returns:
            the role entity, None no id or name was supplied

            the role, or send a module Fail signal if role not found.
        """
        if role_id:
            role = self.client.get_entity('roles', role_id)
            if not role:
                self.module.fail_json(msg="Role with id '%s' not found in manageiq" % str(role_id))
            return role
        else:
            if role_name:
                role_res = self.client.collections.roles.find_by(name=role_name)
                if not role_res:
                    self.module.fail_json(msg="Role '%s' not found in manageiq" % role_name)
                if len(role_res) > 1:
                    self.module.fail_json(msg="Multiple roles found in manageiq with name '%s" % role_name)
                return role_res[0]
            else:
                # No role name or role id supplied
                return None

    @staticmethod
    def merge_dict_values(norm_current_values, norm_updated_values):
        """ Create an merged update object for manageiq group filters.

            The input dict contain the tag values per category.
            If the new values contain the category, all tags for that category are replaced
            If the new values do not contain the category, the existing tags are kept

        Returns:
            the nested array with the merged values, used in the update post body
        """

        # If no updated values are supplied, in merge mode, the original values must be returned
        # otherwise the existing tag filters will be removed.
        if norm_current_values and (not norm_updated_values):
            return norm_current_values

        # If no existing tag filters exist, use the user supplied values
        if (not norm_current_values) and norm_updated_values:
            return norm_updated_values

        # start with norm_current_values's keys and values
        res = norm_current_values.copy()
        # replace res with norm_updated_values's keys and values
        res.update(norm_updated_values)
        return res

    def delete_group(self, group):
        """ Deletes a group from manageiq.

        Returns:
            a dict of:
            changed: boolean indicating if the entity was updated.
            msg: a short message describing the operation executed.
        """
        try:
            url = '%s/groups/%s' % (self.api_url, group['id'])
            self.client.post(url, action='delete')
        except Exception as e:
            self.module.fail_json(msg="failed to delete group %s: %s" % (group['description'], str(e)))

        return dict(
            changed=True,
            msg="deleted group %s with id %i" % (group['description'], group['id']))

    def edit_group(self, group, description, role, tenant, norm_managed_filters, managed_filters_merge_mode,
                   belongsto_filters, belongsto_filters_merge_mode):
        """ Edit a manageiq group.

        Returns:
            a dict of:
            changed: boolean indicating if the entity was updated.
            msg: a short message describing the operation executed.
        """

        if role or norm_managed_filters or belongsto_filters:
            group.reload(attributes=['miq_user_role_name', 'entitlement'])

        try:
            current_role = group['miq_user_role_name']
        except AttributeError:
            current_role = None

        changed = False
        resource = {}

        if description and group['description'] != description:
            resource['description'] = description
            changed = True

        if tenant and group['tenant_id'] != tenant['id']:
            resource['tenant'] = dict(id=tenant['id'])
            changed = True

        if role and current_role != role['name']:
            resource['role'] = dict(id=role['id'])
            changed = True

        if norm_managed_filters or belongsto_filters:

            # Only compare if filters are supplied
            entitlement = group['entitlement']

            if 'filters' not in entitlement:
                # No existing filters exist, use supplied filters
                managed_tag_filters_post_body = self.normalized_managed_tag_filters_to_miq(norm_managed_filters)
                resource['filters'] = {'managed': managed_tag_filters_post_body, "belongsto": belongsto_filters}
                changed = True
            else:
                current_filters = entitlement['filters']
                new_filters = self.edit_group_edit_filters(current_filters,
                                                           norm_managed_filters, managed_filters_merge_mode,
                                                           belongsto_filters, belongsto_filters_merge_mode)
                if new_filters:
                    resource['filters'] = new_filters
                    changed = True

        if not changed:
            return dict(
                changed=False,
                msg="group %s is not changed." % group['description'])

        # try to update group
        try:
            self.client.post(group['href'], action='edit', resource=resource)
            changed = True
        except Exception as e:
            self.module.fail_json(msg="failed to update group %s: %s" % (group['name'], str(e)))

        return dict(
            changed=changed,
            msg="successfully updated the group %s with id %s" % (group['description'], group['id']))

    def edit_group_edit_filters(self, current_filters, norm_managed_filters, managed_filters_merge_mode,
                                belongsto_filters, belongsto_filters_merge_mode):
        """ Edit a manageiq group filters.

        Returns:
            None if no the group was not updated
            If the group was updated the post body part for updating the group
        """
        filters_updated = False
        new_filters_resource = {}

        # Process belongsto filters
        if 'belongsto' in current_filters:
            current_belongsto_set = set(current_filters['belongsto'])
        else:
            current_belongsto_set = set()

        if belongsto_filters:
            new_belongsto_set = set(belongsto_filters)
        else:
            new_belongsto_set = set()

        if current_belongsto_set == new_belongsto_set:
            new_filters_resource['belongsto'] = current_filters['belongsto']
        else:
            if belongsto_filters_merge_mode == 'merge':
                current_belongsto_set.update(new_belongsto_set)
                new_filters_resource['belongsto'] = list(current_belongsto_set)
            else:
                new_filters_resource['belongsto'] = list(new_belongsto_set)
            filters_updated = True

        # Process belongsto managed filter tags
        # The input is in the form dict with keys are the categories and the tags are supplied string array
        # ManageIQ, the current_managed, uses an array of arrays. One array of categories.
        # We normalize the user input from a dict with arrays to a dict of sorted arrays
        # We normalize the current manageiq array of arrays also to a dict of sorted arrays so we can compare
        norm_current_filters = self.manageiq_filters_to_sorted_dict(current_filters)

        if norm_current_filters == norm_managed_filters:
            new_filters_resource['managed'] = current_filters['managed']
        else:
            if managed_filters_merge_mode == 'merge':
                merged_dict = self.merge_dict_values(norm_current_filters, norm_managed_filters)
                new_filters_resource['managed'] = self.normalized_managed_tag_filters_to_miq(merged_dict)
            else:
                new_filters_resource['managed'] = self.normalized_managed_tag_filters_to_miq(norm_managed_filters)
            filters_updated = True

        if not filters_updated:
            return None

        return new_filters_resource

    def create_group(self, description, role, tenant, norm_managed_filters, belongsto_filters):
        """ Creates the group in manageiq.

        Returns:
            the created group id, name, created_on timestamp,
            updated_on timestamp.
        """
        # check for required arguments
        for key, value in dict(description=description).items():
            if value in (None, ''):
                self.module.fail_json(msg="missing required argument: %s" % key)

        url = '%s/groups' % self.api_url

        resource = {'description': description}

        if role is not None:
            resource['role'] = dict(id=role['id'])

        if tenant is not None:
            resource['tenant'] = dict(id=tenant['id'])

        if norm_managed_filters or belongsto_filters:
            managed_tag_filters_post_body = self.normalized_managed_tag_filters_to_miq(norm_managed_filters)
            resource['filters'] = {'managed': managed_tag_filters_post_body, "belongsto": belongsto_filters}

        try:
            result = self.client.post(url, action='create', resource=resource)
        except Exception as e:
            self.module.fail_json(msg="failed to create group %s: %s" % (description, str(e)))

        return dict(
            changed=True,
            msg="successfully created group %s" % description,
            group_id=result['results'][0]['id']
        )

    @staticmethod
    def normalized_managed_tag_filters_to_miq(norm_managed_filters):
        if not norm_managed_filters:
            return None

        return list(norm_managed_filters.values())

    @staticmethod
    def manageiq_filters_to_sorted_dict(current_filters):
        if 'managed' not in current_filters:
            return None

        res = {}
        for tag_list in current_filters['managed']:
            tag_list.sort()
            key = tag_list[0].split('/')[2]
            res[key] = tag_list

        return res

    @staticmethod
    def normalize_user_managed_filters_to_sorted_dict(managed_filters, module):
        if not managed_filters:
            return None

        res = {}
        for cat_key in managed_filters:
            cat_array = []
            if not isinstance(managed_filters[cat_key], list):
                module.fail_json(msg='Entry "{0}" of managed_filters must be a list!'.format(cat_key))
            for tags in managed_filters[cat_key]:
                miq_managed_tag = "/managed/" + cat_key + "/" + tags
                cat_array.append(miq_managed_tag)
            # Do not add empty categories. ManageIQ will remove all categories that are not supplied
            if cat_array:
                cat_array.sort()
                res[cat_key] = cat_array
        return res

    @staticmethod
    def create_result_group(group):
        """ Creates the ansible result object from a manageiq group entity

        Returns:
            a dict with the group id, description, role, tenant, filters, group_type, created_on, updated_on
        """
        try:
            role_name = group['miq_user_role_name']
        except AttributeError:
            role_name = None

        managed_filters = None
        belongsto_filters = None
        if 'filters' in group['entitlement']:
            filters = group['entitlement']['filters']
            if 'belongsto' in filters:
                belongsto_filters = filters['belongsto']
            if 'managed' in filters:
                managed_filters = {}
                for tag_list in filters['managed']:
                    key = tag_list[0].split('/')[2]
                    tags = []
                    for t in tag_list:
                        tags.append(t.split('/')[3])
                    managed_filters[key] = tags

        return dict(
            id=group['id'],
            description=group['description'],
            role=role_name,
            tenant=group['tenant']['name'],
            managed_filters=managed_filters,
            belongsto_filters=belongsto_filters,
            group_type=group['group_type'],
            created_on=group['created_on'],
            updated_on=group['updated_on'],
        )


def main():
    argument_spec = dict(
        description=dict(required=True, type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
        role_id=dict(required=False, type='int'),
        role=dict(required=False, type='str'),
        tenant_id=dict(required=False, type='int'),
        tenant=dict(required=False, type='str'),
        managed_filters=dict(required=False, type='dict'),
        managed_filters_merge_mode=dict(required=False, choices=['merge', 'replace'], default='replace'),
        belongsto_filters=dict(required=False, type='list', elements='str'),
        belongsto_filters_merge_mode=dict(required=False, choices=['merge', 'replace'], default='replace'),
    )
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    description = module.params['description']
    state = module.params['state']
    role_id = module.params['role_id']
    role_name = module.params['role']
    tenant_id = module.params['tenant_id']
    tenant_name = module.params['tenant']
    managed_filters = module.params['managed_filters']
    managed_filters_merge_mode = module.params['managed_filters_merge_mode']
    belongsto_filters = module.params['belongsto_filters']
    belongsto_filters_merge_mode = module.params['belongsto_filters_merge_mode']

    manageiq = ManageIQ(module)
    manageiq_group = ManageIQgroup(manageiq)

    group = manageiq_group.group(description)

    # group should not exist
    if state == "absent":
        # if we have a group, delete it
        if group:
            res_args = manageiq_group.delete_group(group)
        # if we do not have a group, nothing to do
        else:
            res_args = dict(
                changed=False,
                msg="group %s: does not exist in manageiq" % description)

    # group should exist
    if state == "present":

        tenant = manageiq_group.tenant(tenant_id, tenant_name)
        role = manageiq_group.role(role_id, role_name)
        norm_managed_filters = manageiq_group.normalize_user_managed_filters_to_sorted_dict(managed_filters, module)
        # if we have a group, edit it
        if group:
            res_args = manageiq_group.edit_group(group, description, role, tenant,
                                                 norm_managed_filters, managed_filters_merge_mode,
                                                 belongsto_filters, belongsto_filters_merge_mode)

        # if we do not have a group, create it
        else:
            res_args = manageiq_group.create_group(description, role, tenant, norm_managed_filters, belongsto_filters)
            group = manageiq.client.get_entity('groups', res_args['group_id'])

        group.reload(expand='resources', attributes=['miq_user_role_name', 'tenant', 'entitlement'])
        res_args['group'] = manageiq_group.create_result_group(group)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
