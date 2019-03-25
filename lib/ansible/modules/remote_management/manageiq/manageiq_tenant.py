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
version_added: '2.8'
author: Evert Mulder (@evertmulder)
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
    - The C(parent_id) takes president over C(parent) when supplied
    required: false
    default: null
  parent:
    description:
    - The name of the parent tenant. If not supplied and no C(parent_id) is supplied the root tenant is used.
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
      validate_certs: False

- name: Create a tenant in ManageIQ
  manageiq_tenant:
    name: 'Dep1'
    description: 'Manufacturing department'
    parent_id: 1
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: Delete a tenant in ManageIQ
  manageiq_tenant:
    state: 'absent'
    name: 'Dep1'
    parent_id: 1
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

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
      validate_certs: False


- name: Delete a tenant in ManageIQ using a token
  manageiq_tenant:
    state: 'absent'
    name: 'Dep1'
    parent_id: 1
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      token: 'sometoken'
      validate_certs: False
'''

RETURN = '''
tenant:
  description: The tenant.
  returned: success
  type: complex
  contains:
    id:
      description: The tenant id
      returned: success
      type: int
    name:
      description: The tenant name
      returned: success
      type: str
    description:
      description: The tenant description
      returned: success
      type: str
    parent_id:
      description: The id of the parent tenant
      returned: success
      type: int
    quotas:
      description: List of tenant quotas
      returned: success
      type: list
      sample:
        cpu_allocated: 100
        mem_allocated: 50
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

    def tenant(self, name, parent_id, parent):
        """ Search for tenant object by name and parent_id or parent
            or the root tenant if no parent or parent_id is supplied.
        Returns:
            the parent tenant, None for the root tenant
            the tenant or None if tenant was not found.
        """

        if parent_id:
            parent_tenant_res = self.client.collections.tenants.find_by(id=parent_id)
            if not parent_tenant_res:
                self.module.fail_json(msg="Parent tenant with id '%s' not found in manageiq" % str(parent_id))
            parent_tenant = parent_tenant_res[0]
            tenants = self.client.collections.tenants.find_by(name=name)

            for tenant in tenants:
                try:
                    ancestry = tenant['ancestry']
                except AttributeError:
                    ancestry = None

                if ancestry:
                    tenant_parent_id = int(ancestry.split("/")[-1])
                    if int(tenant_parent_id) == parent_id:
                        return parent_tenant, tenant

            return parent_tenant, None
        else:
            if parent:
                parent_tenant_res = self.client.collections.tenants.find_by(name=parent)
                if not parent_tenant_res:
                    self.module.fail_json(msg="Parent tenant '%s' not found in manageiq" % parent)

                if len(parent_tenant_res) > 1:
                    self.module.fail_json(msg="Multiple parent tenants not found in manageiq with name '%s" % parent)

                parent_tenant = parent_tenant_res[0]
                parent_id = parent_tenant['id']
                tenants = self.client.collections.tenants.find_by(name=name)

                for tenant in tenants:
                    try:
                        ancestry = tenant['ancestry']
                    except AttributeError:
                        ancestry = None

                    if ancestry:
                        tenant_parent_id = int(ancestry.split("/")[-1])
                        if tenant_parent_id == parent_id:
                            return parent_tenant, tenant

                return parent_tenant, None
            else:
                # No parent or parent id supplied we select the root tenant
                return None, self.client.collections.tenants.find_by(ancestry=None)[0]

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
            dict with `msg` and `changed`
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
            dict with `msg` and `changed`
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
            msg="successfully updated the tenant with id %s" % (tenant['id']))

    def create_tenant(self, name, description, parent_tenant):
        """ Creates the tenant in manageiq.

        Returns:
            dict with `msg`, `changed` and `tenant_id`
        """
        parent_id = parent_tenant['id']
        # check for required arguments
        for key, value in dict(name=name, description=description, parent_id=parent_id).items():
            if value in (None, ''):
                self.module.fail_json(msg="missing required argument: %s" % key)

        url = '%s/tenants' % self.api_url

        resource = {'name': name, 'description': description, 'parent': {'id': parent_id}}

        try:
            result = self.client.post(url, action='create', resource=resource)
            tenant_id = result['results'][0]['id']
        except Exception as e:
            self.module.fail_json(msg="failed to create tenant %s: %s" % (name, str(e)))

        return dict(
            changed=True,
            msg="successfully created tenant '%s' with id '%s'" % (name, tenant_id),
            tenant_id=tenant_id)

    def tenant_quota(self, tenant, quota_key):
        """ Search for tenant quota object by tenant and quota_key.
        Returns:
            the quota for the tenant, or None if the tenant quota was not found.
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
            dict with `msg` and `changed`
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
                    res = dict(changed=False, msg="tenant quota '%s' does not exist" % quota_key)

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
            result = self.client.post(quota['href'], action='delete')
        except Exception as e:
            self.module.fail_json(msg="failed to delete tenant quota '%s': %s" % (quota['name'], str(e)))

        return dict(changed=True, msg=result['message'])

    def create_tenant_response(self, tenant, parent_tenant):
        """ Creates the ansible result object from a manageiq tenant entity

        Returns:
            a dict with the tenant id, name, description, parent id,
            quota's
        """
        tenant_quotas = self.create_tenant_quotas_response(tenant['tenant_quotas'])

        try:
            ancestry = tenant['ancestry']
            tenant_parent_id = int(ancestry.split("/")[-1])
        except AttributeError:
            # The root tenant does not return the ancestry attribute
            tenant_parent_id = None

        return dict(
            id=tenant['id'],
            name=tenant['name'],
            description=tenant['description'],
            parent_id=tenant_parent_id,
            quotas=tenant_quotas
        )

    @staticmethod
    def create_tenant_quotas_response(tenant_quotas):
        """ Creates the ansible result object from a manageiq tenant_quotas entity

        Returns:
            a dict with the applied quotas, name and value
        """

        if not tenant_quotas:
            return {}

        result = {}
        for quota in tenant_quotas:
            if quota['unit'] == 'bytes':
                value = float(quota['value']) / (1024 * 1024 * 1024)
            else:
                value = quota['value']
            result[quota['name']] = value
        return result


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        description=dict(required=True, type='str'),
        parent_id=dict(required=False, type='int'),
        parent=dict(required=False, type='str'),
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
    parent = module.params['parent']
    state = module.params['state']
    quotas = module.params['quotas']

    manageiq = ManageIQ(module)
    manageiq_tenant = ManageIQTenant(manageiq)

    parent_tenant, tenant = manageiq_tenant.tenant(name, parent_id, parent)

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
            res_args = manageiq_tenant.create_tenant(name, description, parent_tenant)
            tenant = manageiq.client.get_entity('tenants', res_args['tenant_id'])

        # quotas as supplied and we have a tenant
        if quotas:
            tenant_quotas_res = manageiq_tenant.update_tenant_quotas(tenant, quotas)
            if tenant_quotas_res['changed']:
                res_args['changed'] = True
                res_args['tenant_quotas_msg'] = tenant_quotas_res['msg']

        tenant.reload(expand='resources', attributes=['tenant_quotas'])
        res_args['tenant'] = manageiq_tenant.create_tenant_response(tenant, parent_tenant)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
