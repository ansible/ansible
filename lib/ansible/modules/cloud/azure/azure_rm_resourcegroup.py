#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_resourcegroup
version_added: "2.1"
short_description: Manage Azure resource groups
description:
    - Create, update and delete a resource group.
options:
    force_delete_nonempty:
        description:
            - Remove a resource group and all associated resources.
            - Use with I(state=absent) to delete a resource group that contains resources.
        type: bool
        aliases:
            - force
        default: 'no'
    location:
        description:
            - Azure location for the resource group. Required when creating a new resource group.
            - Cannot be changed once resource group is created.
    name:
        description:
            - Name of the resource group.
        required: true
    state:
        description:
            - Assert the state of the resource group. Use C(present) to create or update and C(absent) to delete.
            - When C(absent) a resource group containing resources will not be removed unless the I(force) option is used.
        default: present
        choices:
            - absent
            - present
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)

'''

EXAMPLES = '''
    - name: Create a resource group
      azure_rm_resourcegroup:
        name: myResourceGroup
        location: westus
        tags:
            testing: testing
            delete: never

    - name: Delete a resource group
      azure_rm_resourcegroup:
        name: myResourceGroup
        state: absent

    - name: Delete a resource group including resources it contains
      azure_rm_resourcegroup:
        name: myResourceGroup
        force_delete_nonempty: yes
        state: absent
'''
RETURN = '''
contains_resources:
    description:
        - Whether or not the resource group contains associated resources.
    returned: always
    type: bool
    sample: True
state:
    description:
        - Current state of the resource group.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup"
        location:
            description:
                - Azure location for the resource group.
            returned: always
            type: str
            sample: westus
        name:
            description:
                - The resource group name.
            returned: always
            type: str
            sample: Testing
        provisioning_state:
            description:
                - Provisioning state of the resource group.
            returned: always
            type: str
            sample: Succeeded
        tags:
            description:
                - The resource group's tags.
            returned: always
            type: dict
            sample: {
                    "delete": "on-exit",
                    "testing": "no"
                    }
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, normalize_location_name


def resource_group_to_dict(rg):
    return dict(
        id=rg.id,
        name=rg.name,
        location=rg.location,
        tags=rg.tags,
        provisioning_state=rg.properties.provisioning_state
    )


class AzureRMResourceGroup(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            force_delete_nonempty=dict(type='bool', default=False, aliases=['force'])
        )

        self.name = None
        self.state = None
        self.location = None
        self.tags = None
        self.force_delete_nonempty = None

        self.results = dict(
            changed=False,
            contains_resources=False,
            state=dict(),
        )

        super(AzureRMResourceGroup, self).__init__(self.module_arg_spec,
                                                   supports_check_mode=True,
                                                   supports_tags=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        results = dict()
        changed = False
        rg = None
        contains_resources = False

        try:
            self.log('Fetching resource group {0}'.format(self.name))
            rg = self.rm_client.resource_groups.get(self.name)
            self.check_provisioning_state(rg, self.state)
            contains_resources = self.resources_exist()

            results = resource_group_to_dict(rg)
            if self.state == 'absent':
                self.log("CHANGED: resource group {0} exists but requested state is 'absent'".format(self.name))
                changed = True
            elif self.state == 'present':
                update_tags, results['tags'] = self.update_tags(results['tags'])
                self.log("update tags %s" % update_tags)
                self.log("new tags: %s" % str(results['tags']))
                if update_tags:
                    changed = True

                if self.location and normalize_location_name(self.location) != results['location']:
                    self.fail("Resource group '{0}' already exists in location '{1}' and cannot be "
                              "moved.".format(self.name, results['location']))
        except CloudError:
            self.log('Resource group {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: resource group {0} does not exist but requested state is "
                         "'present'".format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results
        self.results['contains_resources'] = contains_resources

        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                if not rg:
                    # Create resource group
                    self.log("Creating resource group {0}".format(self.name))
                    if not self.location:
                        self.fail("Parameter error: location is required when creating a resource group.")
                    if self.name_exists():
                        self.fail("Error: a resource group with the name {0} already exists in your subscription."
                                  .format(self.name))
                    params = self.rm_models.ResourceGroup(
                        location=self.location,
                        tags=self.tags
                    )
                else:
                    # Update resource group
                    params = self.rm_models.ResourceGroup(
                        location=results['location'],
                        tags=results['tags']
                    )
                self.results['state'] = self.create_or_update_resource_group(params)
            elif self.state == 'absent':
                if contains_resources and not self.force_delete_nonempty:
                    self.fail("Error removing resource group {0}. Resources exist within the group. "
                              "Use `force_delete_nonempty` to force delete. "
                              "To list resources under {0}, use `azure_rm_resourcegroup_facts` module with `list_resources` option.".format(self.name))
                self.delete_resource_group()

        return self.results

    def create_or_update_resource_group(self, params):
        try:
            result = self.rm_client.resource_groups.create_or_update(self.name, params)
        except Exception as exc:
            self.fail("Error creating or updating resource group {0} - {1}".format(self.name, str(exc)))
        return resource_group_to_dict(result)

    def delete_resource_group(self):
        try:
            poller = self.rm_client.resource_groups.delete(self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error delete resource group {0} - {1}".format(self.name, str(exc)))

        # The delete operation doesn't return anything.
        # If we got here, assume all is good
        self.results['state']['status'] = 'Deleted'
        return True

    def resources_exist(self):
        found = False
        try:
            response = self.rm_client.resources.list_by_resource_group(self.name)
        except AttributeError:
            response = self.rm_client.resource_groups.list_resources(self.name)
        except Exception as exc:
            self.fail("Error checking for resource existence in {0} - {1}".format(self.name, str(exc)))

        for item in response:
            found = True
            break
        return found

    def name_exists(self):
        try:
            exists = self.rm_client.resource_groups.check_existence(self.name)
        except Exception as exc:
            self.fail("Error checking for existence of name {0} - {1}".format(self.name, str(exc)))
        return exists


def main():
    AzureRMResourceGroup()


if __name__ == '__main__':
    main()
