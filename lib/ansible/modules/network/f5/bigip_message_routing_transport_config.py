#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_message_routing_transport_config
short_description: Manages configuration for an outgoing connection
description:
  - Manages configuration for an outgoing connection in BIG-IP message routing.
version_added: 2.9
options:
  name:
    description:
      - Specifies the name of the transport config to manage.
    type: str
    required: True
  description:
    description:
      - The user defined description of the transport config.
    type: str
  profiles:
    description:
      - Specifies a list profiles for the outgoing connection to use to direct and manage traffic.
    type: list
  src_addr_translation:
    description:
      - Specifies the type of source address translation enabled for the transport config and the pool
        that the source address translation will use.
    suboptions:
      type:
        description:
          - Specifies the type of source address translation associated with the specified transport config.
          - When set to C(snat) the C(pool) parameter needs to contain a name for a valid LSN or SNAT pool.
        type: str
        choices:
          - snat
          - none
          - automap
      pool:
        description:
          - Specifies the name of a LSN or SNAT pool used by the specified transport config.
          - "Name can also be specified in C(fullPath) format: C(/Common/foobar)"
          - When C(type) is C(none) or C(automap) the pool parameter will be replaced by C(none) keyword,
            thus any defined C(pool) parameter will be ignored.
        type: str
    type: dict
  src_port:
    description:
      - Specifies the source port to be used for the connection being created.
      - If no value is specified an ephemeral port is chosen for the connection being created.
      - The accepted range is between 0 and 65535 inclusive.
    type: int
  rules:
    description:
      - The iRules you want run on this transport config. iRules help automate the intercepting, processing,
        and routing of application traffic.
    type: list
  type:
    description:
      - Parameter used to specify the type of the transport-config object to manage.
      - Default setting is C(generic) with more options added in future.
    type: str
    choices:
      - generic
    default: generic
  partition:
    description:
      - Device partition to create transport-config object on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the transport-config object exists.
      - When C(absent), ensures the transport-config object is removed.
    type: str
    choices:
      - present
      - absent
    default: present
notes:
  - Requires BIG-IP >= 14.0.0
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create generic transport config
  bigip_message_routing_transport_config:
    name: foo
    profiles:
      transport: genericmsg
      tcp: tcp-lan-optimized
    description: new_transport
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify generic transport config
  bigip_message_routing_transport_config:
    name: foo
    rules:
      - rule_1
      - rule_2
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove generic transport config
  bigip_message_routing_transport_config:
    name: foo
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The user defined description of the router profile.
  returned: changed
  type: str
  sample: My description
rules:
  description: The iRules running on transport config.
  returned: changed
  type: list
  sample: ['/Common/rule1', '/Common/rule2']
profiles:
  description: The profiles for the outgoing connection .
  returned: changed
  type: list
  sample: ['/Common/profile1', '/Common/profile2']
src_addr_translation:
  description: The type of source address translation enabled for the transport config.
  type: complex
  returned: changed
  contains:
    type:
      description: the type of source address translation associated with the specified transport config.
      type: str
      returned: changed
      sample: automap
    pool:
      description: The name of a LSN or SNAT pool used by the specified transport config.
      type: str
      returned: changed
      sample: /Common/pool1
  sample: hash/dictionary of values
source_port:
  description: The source port to be used for the connection being created.
  returned: changed
  type: int
  sample: 10041
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
    from library.module_utils.network.f5.compare import cmp_simple_list
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none
    from ansible.module_utils.network.f5.compare import cmp_simple_list
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'sourceAddressTranslation': 'src_addr_translation',
        'sourcePort': 'src_port',
    }

    api_attributes = [
        'description',
        'sourceAddressTranslation',
        'sourcePort',
        'profiles',
        'rules',
    ]

    returnables = [
        'description',
        'snat_pool',
        'snat_type',
        'profiles',
        'rules',
        'src_port',
    ]

    updatables = [
        'description',
        'snat_pool',
        'snat_type',
        'profiles',
        'rules',
        'src_port',
    ]


class ApiParameters(Parameters):
    @property
    def profiles(self):
        if 'profilesReference' not in self._values:
            return None
        if 'items' not in self._values['profilesReference']:
            return None
        result = [item['fullPath'] for item in self._values['profilesReference']['items']]
        return result

    @property
    def snat_pool(self):
        if self._values['src_addr_translation'] is None:
            return None
        if 'pool' in self._values['src_addr_translation']:
            return self._values['src_addr_translation']['pool']

    @property
    def snat_type(self):
        if self._values['src_addr_translation'] is None:
            return None
        return self._values['src_addr_translation']['type']


class ModuleParameters(Parameters):
    @property
    def profiles(self):
        if self._values['profiles'] is None:
            return None
        result = [fq_name(self.partition, p) for p in self._values['profiles']]
        return result

    @property
    def rules(self):
        if self._values['rules'] is None:
            return None
        result = [fq_name(self.partition, rule) for rule in self._values['rules']]
        return result

    @property
    def snat_pool(self):
        if self._values['src_addr_translation'] is None:
            return None
        if self._values['src_addr_translation']['pool']:
            result = fq_name(self.partition, self._values['src_addr_translation']['pool'])
            return result

    @property
    def snat_type(self):
        if self._values['src_addr_translation'] is None:
            return None
        return self._values['src_addr_translation']['type']

    @property
    def src_port(self):
        if self._values['src_port'] is None:
            return None
        if 0 <= self._values['src_port'] <= 65535:
            return self._values['src_port']
        raise F5ModuleError(
            "Valid 'src_port' must be in range 0 - 65535 inclusive."
        )


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
    @property
    def src_addr_translation(self):
        if self._values['snat_type'] is None:
            return None
        if self._values['snat_type'] in ['none', 'automap']:
            result = dict(
                pool='none',
                type=self._values['snat_type']
            )
            return result

        result = dict(
            pool=self._values['snat_pool'],
            type=self._values['snat_type']
        )
        return result


class ReportableChanges(Changes):
    returnables = [
        'description',
        'src_addr_translation',
        'rules',
        'src_port',
        'profiles',
    ]

    @property
    def src_addr_translation(self):
        if self._values['snat_type'] is None:
            return None
        to_filter = dict(
            pool=self._values['snat_pool'],
            type=self._values['snat_type']
        )
        result = self._filter_params(to_filter)
        if result:
            return result


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
    def profiles(self):
        result = cmp_simple_list(self.want.profiles, self.have.profiles)
        return result

    @property
    def rules(self):
        result = cmp_simple_list(self.want.rules, self.have.rules)
        return result

    @property
    def description(self):
        result = cmp_str_with_none(self.want.description, self.have.description)
        return result


class BaseManager(object):
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
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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
        self._announce_deprecations(result)
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        if self.want.profiles is None:
            raise F5ModuleError(
                'Profiles parameter needs to be specified when creating transport config.'
            )
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True


class GenericModuleManager(BaseManager):
    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/transport-config/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/transport-config/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/transport-config/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/transport-config/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/transport-config/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        query = '?expandSubcollections=true'
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return ApiParameters(params=response)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.kwargs = kwargs

    def version_less_than_14(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('14.0.0'):
            return True
        return False

    def exec_module(self):
        if self.version_less_than_14():
            raise F5ModuleError('Message routing is not supported on TMOS version below 14.x')
        if self.module.params['type'] == 'generic':
            manager = self.get_manager('generic')
        else:
            raise F5ModuleError(
                "Unknown type specified."
            )
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'generic':
            return GenericModuleManager(**self.kwargs)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            description=dict(),
            profiles=dict(type='list'),
            src_port=dict(type='int'),
            src_addr_translation=dict(
                type='dict',
                options=dict(
                    type=dict(
                        choices=['none', 'automap', 'snat']
                    ),
                    pool=dict(),
                ),
                required_if=[
                    ['type', 'snat', ['pool']]
                ]
            ),
            rules=dict(type='list'),
            type=dict(
                choices=['generic'],
                default='generic'
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            )

        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
