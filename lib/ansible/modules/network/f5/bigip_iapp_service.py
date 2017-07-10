#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 F5 Networks Inc.
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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: bigip_iapp_service
short_description: Manages TCL iApp services on a BIG-IP.
description:
  - Manages TCL iApp services on a BIG-IP.
version_added: "2.4"
options:
  name:
    description:
      - The name of the iApp service that you want to deploy.
    required: True
  template:
    description:
      - The iApp template from which to instantiate a new service. This
        template must exist on your BIG-IP before you can successfully
        create a service. This parameter is required if the C(state)
        parameter is C(present).
  parameters:
    description:
      - A hash of all the required template variables for the iApp template.
        If your parameters are stored in a file (the more common scenario)
        it is recommended you use either the `file` or `template` lookups
        to supply the expected parameters.
  force:
    description:
      - Forces the updating of an iApp service even if the parameters to the
        service have not changed. This option is of particular importance if
        the iApp template that underlies the service has been updated in-place.
        This option is equivalent to re-configuring the iApp if that template
        has changed.
    default: False
  state:
    description:
      - When C(present), ensures that the iApp service is created and running.
        When C(absent), ensures that the iApp service has been removed.
    default: present
    choices:
      - present
      - absent
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires the deepdiff Python package on the host. This is as easy as pip
    install f5-sdk.
requirements:
  - f5-sdk
  - deepdiff
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Create HTTP iApp service from iApp template
  bigip_iapp_service:
      name: "foo-service"
      template: "f5.http"
      parameters: "{{ lookup('file', 'f5.http.parameters.json') }}"
      password: "secret"
      server: "lb.mydomain.com"
      state: "present"
      user: "admin"
  delegate_to: localhost

- name: Upgrade foo-service to v1.2.0rc4 of the f5.http template
  bigip_iapp_service:
      name: "foo-service"
      template: "f5.http.v1.2.0rc4"
      password: "secret"
      server: "lb.mydomain.com"
      state: "present"
      user: "admin"
  delegate_to: localhost

- name: Configure a service using parameters in YAML
  bigip_iapp_service:
      name: "tests"
      template: "web_frontends"
      password: "admin"
      server: "{{ inventory_hostname }}"
      server_port: "{{ bigip_port }}"
      validate_certs: "{{ validate_certs }}"
      state: "present"
      user: "admin"
      parameters:
          variables:
              - name: "var__vs_address"
                value: "1.1.1.1"
              - name: "pm__apache_servers_for_http"
                value: "2.2.2.1:80"
              - name: "pm__apache_servers_for_https"
                value: "2.2.2.2:80"
  delegate_to: localhost

- name: Re-configure a service whose underlying iApp was updated in place
  bigip_iapp_service:
      name: "tests"
      template: "web_frontends"
      password: "admin"
      force: yes
      server: "{{ inventory_hostname }}"
      server_port: "{{ bigip_port }}"
      validate_certs: "{{ validate_certs }}"
      state: "present"
      user: "admin"
      parameters:
          variables:
              - name: "var__vs_address"
                value: "1.1.1.1"
              - name: "pm__apache_servers_for_http"
                value: "2.2.2.1:80"
              - name: "pm__apache_servers_for_https"
                value: "2.2.2.2:80"
  delegate_to: localhost
'''

RETURN = '''
# only common fields returned
'''

from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iteritems,
    iControlUnexpectedHTTPError
)
from deepdiff import DeepDiff


class Parameters(AnsibleF5Parameters):
    returnables = []
    api_attributes = [
        'tables', 'variables', 'template', 'lists', 'deviceGroup',
        'inheritedDevicegroup', 'inheritedTrafficGroup', 'trafficGroup'
    ]
    updatables = ['tables', 'variables', 'lists']

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result

    @property
    def tables(self):
        result = []
        if not self._values['tables']:
            return None
        tables = self._values['tables']
        for table in tables:
            tmp = dict()
            name = table.get('name', None)
            if name is None:
                raise F5ModuleError(
                    "One of the provided tables does not have a name"
                )
            tmp['name'] = str(name)
            columns = table.get('columnNames', None)
            if columns:
                tmp['columnNames'] = [str(x) for x in columns]
                # You cannot have rows without columns
                rows = table.get('rows', None)
                if rows:
                    tmp['rows'] = []
                    for row in rows:
                        tmp['rows'].append(dict(row=[str(x) for x in row['row']]))
            result.append(tmp)
        result = sorted(result, key=lambda k: k['name'])
        return result

    @tables.setter
    def tables(self, value):
        self._values['tables'] = value

    @property
    def variables(self):
        result = []
        if not self._values['variables']:
            return None
        variables = self._values['variables']
        for variable in variables:
            tmp = dict((str(k), str(v)) for k, v in iteritems(variable))
            if 'encrypted' not in tmp:
                # BIG-IP will inject an 'encrypted' key if you don't provide one.
                # If you don't provide one, then we give you the default 'no', by
                # default.
                tmp['encrypted'] = 'no'
            if 'value' not in tmp:
                tmp['value'] = ''

            # This seems to happen only on 12.0.0
            elif tmp['value'] == 'none':
                tmp['value'] = ''
            result.append(tmp)
        result = sorted(result, key=lambda k: k['name'])
        return result

    @variables.setter
    def variables(self, value):
        self._values['variables'] = value

    @property
    def lists(self):
        result = []
        if not self._values['lists']:
            return None
        lists = self._values['lists']
        for list in lists:
            tmp = dict((str(k), str(v)) for k, v in iteritems(list) if k != 'value')
            if 'encrypted' not in list:
                # BIG-IP will inject an 'encrypted' key if you don't provide one.
                # If you don't provide one, then we give you the default 'no', by
                # default.
                tmp['encrypted'] = 'no'
            if 'value' in list:
                if len(list['value']) > 0:
                    # BIG-IP removes empty values entries, so mimic this behavior
                    # for user-supplied values.
                    tmp['value'] = [str(x) for x in list['value']]
            result.append(tmp)
        result = sorted(result, key=lambda k: k['name'])
        return result

    @lists.setter
    def lists(self, value):
        self._values['lists'] = value

    @property
    def parameters(self):
        return dict(
            tables=self.tables,
            variables=self.variables,
            lists=self.lists
        )

    @parameters.setter
    def parameters(self, value):
        if value is None:
            return
        if 'tables' in value:
            self.tables = value['tables']
        if 'variables' in value:
            self.variables = value['variables']
        if 'lists' in value:
            self.lists = value['lists']
        if 'deviceGroup' in value:
            self.deviceGroup = value['deviceGroup']
        if 'inheritedDevicegroup' in value:
            self.inheritedDevicegroup = value['inheritedDevicegroup']
        if 'inheritedTrafficGroup' in value:
            self.inheritedTrafficGroup = value['inheritedTrafficGroup']
        if 'trafficGroup' in value:
            self.trafficGroup = value['trafficGroup']

    @property
    def template(self):
        if self._values['template'] is None:
            return None
        if self._values['template'].startswith("/" + self.partition):
            return self._values['template']
        elif self._values['template'].startswith("/"):
            return self._values['template']
        else:
            return '/{0}/{1}'.format(
                self.partition, self._values['template']
            )

    @template.setter
    def template(self, value):
        self._values['template'] = value


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(changed)

    def _update_changed_options(self):
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = str(DeepDiff(attr1, attr2))
        if changed:
            self.changes = Parameters(changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def exists(self):
        result = self.client.api.tm.sys.application.services.service.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
        self.create_on_device()
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update() and not self.want.force:
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update_on_device(self):
        params = self.want.api_params()
        params['execute-action'] = 'definition'
        resource = self.client.api.tm.sys.application.services.service.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.update(**params)

    def read_current_from_device(self):
        result = self.client.api.tm.sys.application.services.service.load(
            name=self.want.name,
            partition=self.want.partition
        ).to_dict()
        result.pop('_meta_data', None)
        return Parameters(result)

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.sys.application.services.service.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the iApp service")
        return True

    def remove_from_device(self):
        resource = self.client.api.tm.sys.application.services.service.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(required=True),
            template=dict(),
            parameters=dict(
                type='dict'
            ),
            state=dict(
                default='present',
                choices=['absent', 'present']
            ),
            force=dict(
                default=False,
                type='bool'
            )
        )
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
