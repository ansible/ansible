#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_iapp_service
short_description: Manages TCL iApp services on a BIG-IP
description:
  - Manages TCL iApp services on a BIG-IP.
  - If you are looking for the API that is communicated with on the BIG-IP,
    the one the is used is C(/mgmt/tm/sys/application/service/). There are a
    couple of APIs in a BIG-IP that might seem like they are relevant to iApp
    Services, but the API mentioned here is the one that is used.
version_added: 2.4
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
      - These parameters typically consist of the C(lists), C(tables), and
        C(variables) fields.
  force:
    description:
      - Forces the updating of an iApp service even if the parameters to the
        service have not changed. This option is of particular importance if
        the iApp template that underlies the service has been updated in-place.
        This option is equivalent to re-configuring the iApp if that template
        has changed.
    default: no
    type: bool
  state:
    description:
      - When C(present), ensures that the iApp service is created and running.
        When C(absent), ensures that the iApp service has been removed.
    default: present
    choices:
      - present
      - absent
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
  strict_updates:
    description:
      - Indicates whether the application service is tied to the template,
        so when the template is updated, the application service changes to
        reflect the updates.
      - When C(yes), disallows any updates to the resources that the iApp
        service has created, if they are not updated directly through the
        iApp.
      - When C(no), allows updates outside of the iApp.
      - If this option is specified in the Ansible task, it will take precedence
        over any similar setting in the iApp Server payload that you provide in
        the C(parameters) field.
    default: yes
    type: bool
    version_added: 2.5
  traffic_group:
    description:
      - The traffic group for the iApp service. When creating a new service, if
        this value is not specified, the default of C(/Common/traffic-group-1)
        will be used.
      - If this option is specified in the Ansible task, it will take precedence
        over any similar setting in the iApp Server payload that you provide in
        the C(parameters) field.
    version_added: 2.5
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create HTTP iApp service from iApp template
  bigip_iapp_service:
    name: foo-service
    template: f5.http
    parameters: "{{ lookup('file', 'f5.http.parameters.json') }}"
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Upgrade foo-service to v1.2.0rc4 of the f5.http template
  bigip_iapp_service:
    name: foo-service
    template: f5.http.v1.2.0rc4
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Configure a service using parameters in YAML
  bigip_iapp_service:
    name: tests
    template: web_frontends
    password: admin
    server: "{{ inventory_hostname }}"
    server_port: "{{ bigip_port }}"
    validate_certs: "{{ validate_certs }}"
    state: present
    user: admin
    parameters:
      variables:
        - name: var__vs_address
          value: 1.1.1.1
        - name: pm__apache_servers_for_http
          value: 2.2.2.1:80
        - name: pm__apache_servers_for_https
          value: 2.2.2.2:80
  delegate_to: localhost

- name: Re-configure a service whose underlying iApp was updated in place
  bigip_iapp_service:
    name: tests
    template: web_frontends
    password: admin
    force: yes
    server: "{{ inventory_hostname }}"
    server_port: "{{ bigip_port }}"
    validate_certs: "{{ validate_certs }}"
    state: present
    user: admin
    parameters:
      variables:
        - name: var__vs_address
          value: 1.1.1.1
        - name: pm__apache_servers_for_http
          value: 2.2.2.1:80
        - name: pm__apache_servers_for_https
          value: 2.2.2.2:80
  delegate_to: localhost

- name: Try to remove the iApp template before the associated Service is removed
  bigip_iapp_template:
    name: web_frontends
    state: absent
  register: result
  failed_when:
    - result is not success
    - "'referenced by one or more applications' not in result.msg"

- name: Configure a service using more complicated parameters
  bigip_iapp_service:
    name: tests
    template: web_frontends
    password: admin
    server: "{{ inventory_hostname }}"
    server_port: "{{ bigip_port }}"
    validate_certs: "{{ validate_certs }}"
    state: present
    user: admin
    parameters:
      variables:
        - name: var__vs_address
          value: 1.1.1.1
        - name: pm__apache_servers_for_http
          value: 2.2.2.1:80
        - name: pm__apache_servers_for_https
          value: 2.2.2.2:80
      lists:
        - name: irules__irules
          value:
            - foo
            - bar
      tables:
        - name: basic__snatpool_members
        - name: net__snatpool_members
        - name: optimizations__hosts
        - name: pool__hosts
          columnNames:
            - name
          rows:
            - row:
                - internal.company.bar
        - name: pool__members
          columnNames:
            - addr
            - port
            - connection_limit
          rows:
            - row:
                - "none"
                - 80
                - 0
        - name: server_pools__servers
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'strictUpdates': 'strict_updates',
        'trafficGroup': 'traffic_group',
    }

    returnables = []

    api_attributes = [
        'tables', 'variables', 'template', 'lists', 'deviceGroup',
        'inheritedDevicegroup', 'inheritedTrafficGroup', 'trafficGroup',
        'strictUpdates'
    ]

    updatables = ['tables', 'variables', 'lists', 'strict_updates', 'traffic_group']

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
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
        result = dict(
            tables=self.tables,
            variables=self.variables,
            lists=self.lists
        )
        return result

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
        if 'strictUpdates' in value:
            self.strictUpdates = value['strictUpdates']

    @property
    def template(self):
        if self._values['template'] is None:
            return None
        return fq_name(self.partition, self._values['template'])

    @template.setter
    def template(self, value):
        self._values['template'] = value

    @property
    def strict_updates(self):
        if self._values['strict_updates'] is None and self.strictUpdates is None:
            return None

        # Specifying the value overrides any associated value in the payload
        elif self._values['strict_updates'] is True:
            return 'enabled'
        elif self._values['strict_updates'] is False:
            return 'disabled'

        # This will be automatically `None` if it was not set by the
        # `parameters` setter
        elif self.strictUpdates:
            return self.strictUpdates
        else:
            return self._values['strict_updates']

    @property
    def traffic_group(self):
        if self._values['traffic_group'] is None and self.trafficGroup is None:
            return None

        # Specifying the value overrides any associated value in the payload
        elif self._values['traffic_group']:
            result = fq_name(self.partition, self._values['traffic_group'])

        # This will be automatically `None` if it was not set by the
        # `parameters` setter
        elif self.trafficGroup:
            result = fq_name(self.partition, self.trafficGroup)
        else:
            result = fq_name(self.partition, self._values['traffic_group'])
        if result.startswith('/Common/'):
            return result
        else:
            raise F5ModuleError(
                "Traffic groups can only exist in /Common"
            )


class Changes(Parameters):
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def traffic_group(self):
        if self.want.traffic_group != self.have.traffic_group:
            return self.want.traffic_group


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Changes()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = Changes(params=changed)
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
        if self.want.traffic_group is None and self.want.trafficGroup is None:
            self.want.update({'traffic_group': '/Common/traffic-group-1'})
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update() and not self.want.force:
            return False
        if self.module.check_mode:
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
        return Parameters(params=result)

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
        if self.module.check_mode:
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
        argument_spec = dict(
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
                default='no',
                type='bool'
            ),
            strict_updates=dict(
                type='bool',
                default='yes'
            ),
            traffic_group=dict(),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
