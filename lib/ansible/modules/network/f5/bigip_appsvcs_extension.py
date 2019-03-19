#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_appsvcs_extension
short_description: Manage application service deployments
description:
  - Manages application service deployments via the App Services Extension functionality
    in BIG-IP.
version_added: 2.7
options:
  content:
    description:
      - Declaration of tenants configured on the system.
      - This parameter is most often used along with the C(file) or C(template) lookup plugins.
        Refer to the examples section for correct usage.
      - For anything advanced or with formatting consider using the C(template) lookup.
      - This can additionally be used for specifying application service configurations
        directly in YAML, however that is not an encouraged practice and, if used at all,
        should only be used for the absolute smallest of configurations to prevent your
        Playbooks from becoming too large.
      - If you C(content) includes encrypted values (such as ciphertexts, passphrases, etc),
        the returned C(changed) value will always be true.
      - If you are using the C(to_nice_json) filter, it will cause this module to fail because
        the purpose of that filter is to format the JSON to be human-readable and this process
        includes inserting "extra characters that break JSON validators.
    type: raw
    required: True
  tenants:
    description:
      - A list of tenants that you want to remove.
      - This parameter is only relevant when C(state) is C(absent). It will be ignored when
        C(state) is C(present).
      - A value of C(all) will remove all tenants.
      - Tenants can be specified as a list as well to remove only specific tenants.
    type: raw
  force:
    description:
      - Force updates a declaration.
      - This parameter should be used in cases where your declaration includes items that
        are encrypted or in cases (such as WAF Policies) where you want a large reload to take place.
    type: bool
    default: no
  state:
    description:
      - When C(state) is C(present), ensures the configuration exists.
      - When C(state) is C(absent), ensures that the configuration is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Deploy an app service configuration
  bigip_appsvcs_extension:
    content: "{{ lookup('file', '/path/to/appsvcs.json') }}"
    state: present
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove all app service configurations
  bigip_appsvcs_extension:
    tenants: all
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove tenants T1 and T2 from app service configurations
  bigip_appsvcs_extension:
    tenants:
      - T1
      - T2
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
action:
  description:
    - The action performed.
  returned: changed
  type: str
  sample: deploy
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six import string_types

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec


try:
    import json
except ImportError:
    import simplejson as json


class Parameters(AnsibleF5Parameters):
    api_map = {
        'class': 'class_name',
        'patchBody': 'patch_body',
        'resourceTimeout': 'resource_timeout',
        'targetTimeout': 'target_timeout',
        'targetTokens': 'target_tokens',
        'targetPassphrase': 'target_passphrase',
        'targetUsername': 'target_username',
        'targetPort': 'target_port',
        'targetHost': 'target_host',
        'retrieveAge': 'retrieve_age',
        'logLevel': 'log_level',
        'historyLimit': 'history_limit',
        'syncToGroup': 'sync_to_group',
        'redeployUpdateMode': 'redeploy_update_mode',
        'redeployAge': 'redeploy_age',
    }

    api_attributes = [
        'class',
        'action',
        'persist',
        'declaration',
        'patchBody',
        'resourceTimeout',
        'targetTimeout',
        'targetTokens',
        'targetPassphrase',
        'targetUsername',
        'targetPort',
        'targetHost',
        'retrieveAge',
        'trace',
        'logLevel',
        'historyLimit',
        'syncToGroup',
        'redeployUpdateMode',
        'redeployAge',
    ]

    returnables = [
        'class_name',
        'action',
        'persist',
        'declaration',
        'patch_body',
        'resource_timeout',
        'target_timeout',
        'target_tokens',
        'target_passphrase',
        'target_username',
        'target_port',
        'target_host',
        'retrieve_age',
        'trace',
        'log_level',
        'history_limit',
        'sync_to_group',
        'redeploy_update_mode',
        'redeploy_age',
    ]

    updatables = [
        'class_name',
        'action',
        'persist',
        'declaration',
        'patch_body',
        'resource_timeout',
        'target_timeout',
        'target_tokens',
        'target_passphrase',
        'target_username',
        'target_port',
        'target_host',
        'retrieve_age',
        'trace',
        'log_level',
        'history_limit',
        'sync_to_group',
        'redeploy_update_mode',
        'redeploy_age',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def content(self):
        if self._values['content'] is None:
            return None
        if isinstance(self._values['content'], string_types):
            return json.loads(self._values['content'] or 'null')
        else:
            return self._values['content']

    @property
    def class_name(self):
        return self._values['content'].get('class', None)

    @property
    def action(self):
        return self._values['content'].get('action', None)

    @property
    def declaration(self):
        return self._values['content'].get('declaration', None)

    @property
    def persist(self):
        if self._values['content']:
            return self._values['content'].get('persist', None)
        elif self.param_persist:
            return self.param_persist
        return None

    @property
    def param_persist(self):
        if self._values['parameters'] is None:
            return None
        result = self._values['parameters'].get('persist', None)
        return result

    @property
    def tenants(self):
        if self._values['tenants'] in [None, 'all']:
            return ''
        if isinstance(self._values['tenants'], list):
            return ','.join(self._values['tenants'])


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    @property
    def declaration(self):
        return None

    @property
    def target_passphrase(self):
        return None

    @property
    def class_name(self):
        return None

    @property
    def persist(self):
        return None


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


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def present(self):
        if self.exists():
            return False
        return self.upsert()

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.tenant_exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def upsert(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        if self.want.content == 'all':
            raise F5ModuleError(
                "'all' keyword cannot be used when 'state' is 'present'."
            )
        self.upsert_on_device()
        return True

    def _get_errors_from_response(self, messages):
        results = []
        if 'results' not in messages:
            if 'message' in messages:
                results.append(messages['message'])
            if 'errors' in messages:
                results += messages['errors']
        else:
            for message in messages['results']:
                if 'message' in message and message['message'] == 'declaration failed':
                    results.append(message['response'])
                if 'errors' in message:
                    results += message['errors']
        return results

    def upsert_on_device(self):
        uri = 'https://{0}:{1}/mgmt/shared/appsvcs/declare/'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=self.want.content)

        if resp.status != 200:
            result = resp.json()
            errors = self._get_errors_from_response(result)
            if errors:
                message = "{0}".format('. '.join(errors))
                raise F5ModuleError(message)
            raise F5ModuleError(resp.content)
        else:
            result = resp.json()
            errors = self._get_errors_from_response(result)
            if errors:
                message = "{0}".format('. '.join(errors))
                raise F5ModuleError(message)

    def ignore_changes(self, obj):
        if isinstance(obj, dict):
            if 'passphrase' in obj:
                obj['passphrase']['ignoreChanges'] = True
            if 'class' in obj and obj['class'] == 'WAF_Policy':
                obj['ignoreChanges'] = True
            return dict((k, self.ignore_changes(v)) for k, v in iteritems(obj))
        else:
            return obj

    def exists(self):
        declaration = {}
        if self.want.content is None:
            raise F5ModuleError(
                "Empty content cannot be specified when 'state' is 'present'."
            )
        try:
            declaration.update(self.want.content)
        except ValueError:
            raise F5ModuleError(
                "The provided 'content' could not be converted into valid json. If you "
                "are using the 'to_nice_json' filter, please remove it."
            )
        declaration['action'] = 'dry-run'

        # This deals with cases where you're comparing a passphrase.
        #
        # Passphrases will always cause an idepotent operation to register
        # a change. Therefore, by specifying "force", you are instructing
        # the module to **not** ignore the passphrase.
        #
        # This will cause the module to not append ignore clauses to the
        # classes that support them.
        if not self.want.force:
            self.ignore_changes(declaration)

        uri = "https://{0}:{1}/mgmt/shared/appsvcs/declare/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=declaration)
        try:
            response = resp.json()
        except ValueError:
            return False
        try:
            if response['results'][0]['message'] == 'no change':
                return True
        except KeyError:
            return False

    def tenant_exists(self):
        uri = "https://{0}:{1}/mgmt/shared/appsvcs/declare/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.tenants
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'statusCode' in response and response['statusCode'] == 404:
            return False
        return True

    def absent(self):
        if self.tenant_exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = 'https://{0}:{1}/mgmt/shared/appsvcs/declare/{2}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.tenants
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            content=dict(type='raw'),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            tenants=dict(type='raw'),
            force=dict(type='bool', default='no')
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['state', 'present', ['content']]
        ]
        self.mutually_exclusive = [
            ['content', 'tenants']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
