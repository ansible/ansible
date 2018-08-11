#!/usr/bin/python
#
# (c) 2018, Evert Mulder (base on manageiq_user.py by Daniel Korn <korndaniel1@gmail.com>)
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

module: manageiq_tenant

short_description: Management of tenants in ManageIQ.
extends_documentation_fragment: manageiq
version_added: '2.7'
author: Evert Mulder
description:
  - The manageiq_tenant module supports adding, updating and deleting tenants in ManageIQ.

options:
  state:
    description:
    - absent - tenant should not exist, present - tenant should be.
    choices: ['absent', 'present']
    default: 'present'
  name:
    description:
      - The tenant name.
    required: true
    default: null
  description:
    description:
    - The tenant description.
    required: true
    default: null
  parent_id:
    description:
    - The id of the parent tenant. If not supplied the root tenant is used.
    required: false
    default: null
  quotas:
    description:
    - The tenant quotas.
    - All parameters case sensitive.
    - 'Valid attributes are:'
    - ' - C(cpu_allocated) (int): use null to remove the quota.'
    - ' - C(mem_allocated) (GB): use null to remove the quota.'
    - ' - C(storage_allocated) (GB): use null to remove the quota.'
    - ' - C(vms_allocated) (int): use null to remove the quota.'
    - ' - C(templates_allocated) (int): use null to remove the quota.'
    required: false
    default: null
'''

EXAMPLES = '''
- name: Update the root tenant in ManageIQ
  manageiq_tenant:
    name: 'My Company'
    description: 'My company name'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Create a tenant in ManageIQ
  manageiq_tenant:
    name: 'Dep1'
    description: 'Manufacturing department'
    parent_id: 1
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Delete a tenant in ManageIQ
  manageiq_tenant:
    state: 'absent'
    name: 'Dep1'
    parent_id: 1
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Set tenant quota for cpu_allocated, mem_allocated, remove quota for vms_allocated
  manageiq_tenant:
    name: 'Dep1'
    parent_id: 1
    quotas:
      - cpu_allocated: 100
      - mem_allocated: 50
      - vms_allocated: null
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False


- name: Delete a tenant in ManageIQ using a token
  manageiq_tenant:
    state: 'absent'
    name: 'Dep1'
    parent_id: 1
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      token: 'sometoken'
      verify_ssl: False
'''

RETURN = '''
tenant:
  description: The tenant.
  returned: success
  type: complex
  contains:
    name:
      description: The tenant name
      returned: success
      type: string
    description:
      description: The tenant description
      returned: success
      type: string
    id:
      description: The tenant id
      returned: success
      type: int
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec


class ManageIQTenant(object):
    """
        Object to execute tenant management operations in manageiq.
    """

    def __init__(self, manageiq):
        self.manageiq = manageiq

        self.module = self.manageiq.module
        self.api_url = self.manageiq.api_url
        self.client = self.manageiq.client

    def tenant(self, name, parent_id):
        """ Search for tenant object by name and parent_id
            or the root tenant if no parent_is is supplied.
        Returns:
            the tenant, or None if tenant was not found.
        """

        if parent_id:

            tenants = self.client.collections.tenants.find_by(name=name)

            for tenant in tenants:
                tenant_parent_id = tenant['ancestry'].split("/")[-1]
                if int(tenant_parent_id) == parent_id:
                    return tenant

            return None
        else:
            return self.client.collections.tenants.find_by(ancestry=None)[0]

    def compare_tenant(self, tenant, name, description):
        """ Compare tenant fields with new field values.

        Returns:
            false if tenant fields have some difference from new fields, true o/w.
        """
        found_difference = (
            (name and tenant['name'] != name) or
            (description and tenant['description'] != description)
        )

        return not found_difference

    def delete_tenant(self, tenant):
        """ Deletes a tenant from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        try:
            url = '%s/tenants/%s' % (self.api_url, tenant['id'])
            result = self.client.post(url, action='delete')
        except Exception as e:
            self.module.fail_json(msg="failed to delete tenant %s: %s" % (tenant['name'], str(e)))

        return dict(changed=True, msg=result['message'])

    def edit_tenant(self, tenant, name, description):
        """ Edit a manageiq tenant.

        Returns:
            a short message describing the operation executed.
        """
        resource = dict(name=name, description=description, use_config_for_attributes=False)

        # check if we need to update ( compare_tenant is true is no difference found )
        if self.compare_tenant(tenant, name, description):
            return dict(
                changed=False,
                msg="tenant %s is not changed." % tenant['name'],
                tenant=tenant['_data'])

        # try to update tenant
        try:
            result = self.client.post(tenant['href'], action='edit', resource=resource)
        except Exception as e:
            self.module.fail_json(msg="failed to update tenant %s: %s" % (tenant['name'], str(e)))

        return dict(
            changed=True,
            msg="successfully updated the tenant with id %s" % (tenant['id']),
            tenant=result)

    def create_tenant(self, name, description, parent_id):
        """ Creates the tenant in manageiq.

        Returns:
            the created tenant id, name, created_on timestamp,
            updated_on timestamp.
        """
        # check for required arguments
        for key, value in dict(name=name, description=description, parent_id=parent_id).items():
            if value in (None, ''):
                self.module.fail_json(msg="missing required argument: %s" % key)

        url = '%s/tenants' % (self.api_url)

        resource = {'name': name, 'description': description, 'parent': {'id': parent_id}}

        try:
            result = self.client.post(url, action='create', resource=resource)
        except Exception as e:
            self.module.fail_json(msg="failed to create tenant %s: %s" % (name, str(e)))

        return dict(
            changed=True,
            msg="successfully created tenant %s with id " % name,
            tenant=result['results'])

    def tenant_quota(self, tenant, quota_key):
        """ Search for tenant quotas object by tenant and quota_key.
        Returns:
            the quotas for the tenant, or None if no tenant quotas were not found.
        """

        tenant_quotas = self.client.get("%s/quotas?expand=resources&filter[]=name=%s" % (tenant['href'], quota_key))

        return tenant_quotas['resources']

    def tenant_quotas(self, tenant):
        """ Search for tenant quotas object by tenant.
        Returns:
            the quotas for the tenant, or None if no tenant quotas were not found.
        """

        tenant_quotas = self.client.get("%s/quotas?expand=resources" % (tenant['href']))

        return tenant_quotas['resources']

    def update_tenant_quotas(self, tenant, quotas):
        """ Creates the tenant quotas in manageiq.

        Returns:
            result
        """

        changed = False
        messages = []
        for quota_key, quota_value in quotas.items():
            current_quota_filtered = self.tenant_quota(tenant, quota_key)
            if current_quota_filtered:
                current_quota = current_quota_filtered[0]
            else:
                current_quota = None

            if quota_value:
                # Change the byte values to GB
                if quota_key in ['storage_allocated', 'mem_allocated']:
                    quota_value_int = int(quota_value) * 1024 * 1024 * 1024
                else:
                    quota_value_int = int(quota_value)
                if current_quota:
                    res = self.edit_tenant_quota(tenant, current_quota, quota_key, quota_value_int)
                else:
                    res = self.create_tenant_quota(tenant, quota_key, quota_value_int)
            else:
                if current_quota:
                    res = self.delete_tenant_quota(tenant, current_quota)
                else:
                    res = dict(changed=False, msg="tenant quota %s does not exist" % quota_key)

            if res['changed']:
                changed = True

            messages.append(res['msg'])

        return dict(
            changed=changed,
            msg=', '.join(messages))

    def edit_tenant_quota(self, tenant, current_quota, quota_key, quota_value):
        """ Update the tenant quotas in manageiq.

        Returns:
            result
        """

        if current_quota['value'] == quota_value:
            return dict(
                changed=False,
                msg="tenant quota %s already has value %s" % (quota_key, quota_value))
        else:

            url = '%s/quotas/%s' % (tenant['href'], current_quota['id'])
            resource = {'value': quota_value}
            try:
                self.client.post(url, action='edit', resource=resource)
            except Exception as e:
                self.module.fail_json(msg="failed to update tenant quota %s: %s" % (quota_key, str(e)))

            return dict(
                changed=True,
                msg="successfully updated tenant quota %s" % quota_key)

    def create_tenant_quota(self, tenant, quota_key, quota_value):
        """ Creates the tenant quotas in manageiq.

        Returns:
            result
        """
        url = '%s/quotas' % (tenant['href'])
        resource = {'name': quota_key, 'value': quota_value}
        try:
            self.client.post(url, action='create', resource=resource)
        except Exception as e:
            self.module.fail_json(msg="failed to create tenant quota %s: %s" % (quota_key, str(e)))

        return dict(
            changed=True,
            msg="successfully created tenant quota %s" % quota_key)

    def delete_tenant_quota(self, tenant, quota):
        """ deletes the tenant quotas in manageiq.

        Returns:
            result
        """
        try:
            url = '%s/%s' % (tenant['href'], quota['id'])
            result = self.client.post(url, action='delete')
        except Exception as e:
            self.module.fail_json(msg="failed to delete tenant %s: %s" % (tenant['name'], str(e)))

        return dict(changed=True, msg=result['message'])


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        description=dict(required=True, type='str'),
        parent_id=dict(required=False, type='int'),
        state=dict(choices=['absent', 'present'], default='present'),
        quotas=dict(type='dict', default={})
    )
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    name = module.params['name']
    description = module.params['description']
    parent_id = module.params['parent_id']
    state = module.params['state']
    quotas = module.params['quotas']

    manageiq = ManageIQ(module)
    manageiq_tenant = ManageIQTenant(manageiq)

    tenant = manageiq_tenant.tenant(name, parent_id)

    # tenant should not exist
    if state == "absent":
        # if we have a tenant, delete it
        if tenant:
            res_args = manageiq_tenant.delete_tenant(tenant)
        # if we do not have a tenant, nothing to do
        else:
            res_args = dict(
                changed=False,
                msg="tenant %s: with parent: %i does not exist in manageiq" % (name, parent_id))

    # tenant should exist
    if state == "present":
        # if we have a tenant, edit it
        if tenant:
            res_args = manageiq_tenant.edit_tenant(tenant, name, description)

        # if we do not have a tenant, create it
        else:
            res_args = manageiq_tenant.create_tenant(name, description, parent_id)

        # quotas as supplied and we have a tenant
        if quotas:
            tenant_quotas_res = manageiq_tenant.update_tenant_quotas(res_args['tenant'], quotas)
            if tenant_quotas_res['changed']:
                res_args['changed'] = True
                res_args['tenant_quotas_msg'] = tenant_quotas_res['msg']

            # reload the tenant with the quota data
            tenant.reload(expand='resources', attributes=['tenant_quotas'])
            res_args['tenant'] = tenant._data

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
