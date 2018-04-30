#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_log_destination
short_description: Manages log destinations on a BIG-IP.
description:
  - Manages log destinations on a BIG-IP.
version_added: 2.6
options:
  name:
    description:
      - Specifies the name of the log destination.
    required: True
  description:
    description:
      - The description of the log destination.
  type:
    description:
      - Specifies the type of log destination.
      - Once created, this parameter cannot be changed.
    choices:
      - remote-high-speed-log
      - remote-syslog
    required: True
  pool_settings:
    description:
      - This parameter is only available when C(type) is C(remote-high-speed-log).
    suboptions:
      pool:
        description:
          - Specifies the existing pool of remote high-speed log servers where logs will be sent.
          - When creating a new destination (and C(type) is C(remote-high-speed-log)), this parameter
            is required.
      protocol:
        description:
          - Specifies the protocol for the system to use to send logs to the pool of remote high-speed
            log servers, where the logs are stored.
          - When creating a new log destination (and C(type) is C(remote-high-speed-log)), if this
            parameter is not specified, the default is C(tcp).
        choices:
          - tcp
          - udp
      distribution:
        description:
          - Specifies the distribution method used by the Remote High Speed Log destination to send
            messages to pool members.
          - When C(adaptive), connections to pool members will be added as required to provide enough
            logging bandwidth. This can have the undesirable effect of logs accumulating on only one
            pool member when it provides sufficient logging bandwidth on its own.
          - When C(balanced), sends each successive log to a new pool member, balancing the logs among
            them according to the pool's load balancing method.
          - When C(replicated), replicates each log to all pool members, for redundancy.
          - When creating a new log destination (and C(type) is C(remote-high-speed-log)), if this
            parameter is not specified, the default is C(adaptive).
        choices:
          - adaptive
          - balanced
          - replicated
  syslog_settings:
    description:
      - This parameter is only available when C(type) is C(remote-syslog).
    suboptions:
      syslog_format:
        description:
          - Specifies the method to use to format the logs associated with the remote Syslog log destination.
          - When creating a new log destination (and C(type) is C(remote-syslog)), if this parameter is
            not specified, the default is C(bsd-syslog).
          - The C(syslog) and C(rfc5424) choices are two ways of saying the same thing.
          - The C(bsd-syslog) and C(rfc3164) choices are two ways of saying the same thing.
        choices:
          - bsd-syslog
          - syslog
          - legacy-bigip
          - rfc5424
          - rfc3164
      forward_to:
        description:
          - Specifies the management port log destination, which will be used to forward the logs to a
            single log server, or a remote high-speed log destination, which will be used to forward the
            logs to a pool of remote log servers.
          - When creating a new log destination (and C(type) is C(remote-syslog)), this parameter is required.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a high-speed logging destination
  bigip_log_destination:
    name: foo
    type: remote-high-speed-log
    pool_settings:
      pool: my-ltm-pool
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Create a remote-syslog logging destination
  bigip_log_destination:
    name: foo
    type: remote-syslog
    syslog_settings:
      syslog_format: rfc5424
      forward_to: my-destination
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
param1:
  description: The new param1 value of the resource.
  returned: changed
  type: bool
  sample: true
param2:
  description: The new param2 value of the resource.
  returned: changed
  type: string
  sample: Foo is bar
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

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


class V1Parameters(AnsibleF5Parameters):
    """Base Parameters for remote-syslog

    """
    api_map = {
        'remoteHighSpeedLog': 'forward_to',
        'format': 'syslog_format'
    }

    api_attributes = [
        'remoteHighSpeedLog',
        'format'
    ]

    returnables = [
        'forward_to',
        'syslog_format'
    ]

    updatables = [
        'forward_to',
        'syslog_format',
        'type'
    ]


class V1ModuleParameters(V1Parameters):
    @property
    def forward_to(self):
        if self._values['syslog_settings'] is None:
            return None
        result = self._values['syslog_settings'].get('forward_to', None)
        if result:
            result = fq_name(self.partition, result)
        return result

    @property
    def syslog_format(self):
        if self._values['syslog_settings'] is None:
            return None
        result = self._values['syslog_settings'].get('syslog_format', None)
        if result == 'syslog':
            result = 'rfc5424'
        if result == 'bsd-syslog':
            result = 'rfc3164'
        return result


class V1ApiParameters(V1Parameters):
    @property
    def type(self):
        return 'remote-syslog'


class V1Changes(V1Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class V1UsableChanges(V1Changes):
    pass


class V1ReportableChanges(V1Changes):
    pass


class V2Parameters(AnsibleF5Parameters):
    """Base Parameters for remote-high-speed-log

    """
    api_map = {
        'poolName': 'pool'
    }

    api_attributes = [
        'distribution',
        'poolName',
        'protocol'
    ]

    returnables = [
        'pool',
        'distribution',
        'protocol'
    ]

    updatables = [
        'pool',
        'distribution',
        'protocol',
        'type'
    ]


class V2ModuleParameters(V2Parameters):
    @property
    def pool(self):
        if self._values['pool_settings'] is None:
            return None
        result = self._values['pool_settings'].get('pool', None)
        if result:
            result = fq_name(self.partition, result)
        return result

    @property
    def protocol(self):
        if self._values['pool_settings'] is None:
            return None
        return self._values['pool_settings'].get('protocol', None)

    @property
    def distribution(self):
        if self._values['pool_settings'] is None:
            return None
        return self._values['pool_settings'].get('distribution', None)


class V2ApiParameters(V2Parameters):
    @property
    def type(self):
        return 'remote-high-speed-log'


class V2Changes(V2Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class V2UsableChanges(V2Changes):
    pass


class V2ReportableChanges(V2Changes):
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
    def type(self):
        if self.want.type != self.have.type:
            raise F5ModuleError(
                "'type' cannot be changed once it is set."
            )


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = self.get_module_params(params=self.module.params)
        self.have = self.get_api_params()
        self.changes = self.get_usable_changes()

    def get_usable_changes(self, params=None):
        pass

    def get_api_params(self, params=None):
        pass

    def get_module_params(self, params=None):
        pass

    def get_reportable_changes(self, params=None):
        pass

    def _set_changed_options(self):
        changed = {}
        for key in self.get_returnables():
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = self.get_usable_changes(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = self.get_updatables()
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
            self.changes = self.get_usable_changes(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
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

        reportable = self.get_reportable_changes(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _validate_creation_parameters(self):
        pass

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

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
        self._validate_creation_parameters()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False


class V1Manager(BaseManager):
    """Manages remote-syslog settings

    """
    def _validate_creation_parameters(self):
        if self.want.syslog_format is None:
            self.want.update({'syslog_format': 'bsd-syslog'})
        if self.want.forward_to is None:
            raise F5ModuleError(
                "'forward_to' is required when creating a new remote-syslog destination."
            )

    def get_reportable_changes(self, params=None):
        if params:
            return V1ReportableChanges(params=params)
        return V1ReportableChanges()

    def get_usable_changes(self, params=None):
        if params:
            return V1UsableChanges(params=params)
        return V1UsableChanges()

    def get_returnables(self):
        return V1ApiParameters.returnables

    def get_updatables(self):
        return V1ApiParameters.updatables

    def get_module_params(self, params=None):
        if params:
            return V1ModuleParameters(params=params)
        return V1ModuleParameters()

    def get_api_params(self, params=None):
        if params:
            return V1ApiParameters(params=params)
        return V1ApiParameters()

    def exists(self):
        result = self.client.api.tm.sys.log_config.destination.remote_syslogs.remote_syslog.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.sys.log_config.destination.remote_syslogs.remote_syslog.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.sys.log_config.destination.remote_syslogs.remote_syslog.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def remove_from_device(self):
        resource = self.client.api.tm.sys.log_config.destination.remote_syslogs.remote_syslog.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.log_config.destination.remote_syslogs.remote_syslog.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return V1ApiParameters(params=result)


class V2Manager(BaseManager):
    """Manages remote-high-speed-log settings

    """
    def get_reportable_changes(self, params=None):
        if params:
            return V2ReportableChanges(params=params)
        return V2ReportableChanges()

    def get_usable_changes(self, params=None):
        if params:
            return V2UsableChanges(params=params)
        return V2UsableChanges()

    def _validate_creation_parameters(self):
        if self.want.protocol is None:
            self.want.update({'protocol': 'tcp'})
        if self.want.distribution is None:
            self.want.update({'distribution': 'adaptive'})
        if self.want.pool is None:
            raise F5ModuleError(
                "'pool' is required when creating a new remote-high-speed-log destination."
            )

    def get_returnables(self):
        return V2ApiParameters.returnables

    def get_updatables(self):
        return V2ApiParameters.updatables

    def get_module_params(self, params=None):
        if params:
            return V2ModuleParameters(params=params)
        return V2ModuleParameters()

    def get_api_params(self, params=None):
        if params:
            return V2ApiParameters(params=params)
        return V2ApiParameters()

    def exists(self):
        result = self.client.api.tm.sys.log_config.destination.remote_high_speed_logs.remote_high_speed_log.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.sys.log_config.destination.remote_high_speed_logs.remote_high_speed_log.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.sys.log_config.destination.remote_high_speed_logs.remote_high_speed_log.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def remove_from_device(self):
        resource = self.client.api.tm.sys.log_config.destination.remote_high_speed_logs.remote_high_speed_log.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.log_config.destination.remote_high_speed_logs.remote_high_speed_log.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return V2ApiParameters(params=result)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.module = kwargs.get('module', None)

    def exec_module(self):
        if self.module.params['type'] == 'remote-syslog':
            manager = self.get_manager('v1')
        elif self.module.params['type'] == 'remote-high-speed-log':
            manager = self.get_manager('v2')
        result = manager.exec_module()
        return result

    def get_manager(self, type):
        if type == 'v1':
            return V1Manager(**self.kwargs)
        elif type == 'v2':
            return V2Manager(**self.kwargs)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            type=dict(
                required=True,
                choices=[
                    'remote-high-speed-log',
                    'remote-syslog'
                ]
            ),
            description=dict(),
            pool_settings=dict(
                type='dict',
                suboptions=dict(
                    pool=dict(),
                    protocol=dict(
                        choices=['tcp', 'udp']
                    ),
                    distribution=dict(
                        choices=[
                            'adaptive',
                            'balanced',
                            'replicated',
                        ]
                    )
                )
            ),
            syslog_settings=dict(
                type='dict',
                suboptions=dict(
                    syslog_format=dict(
                        choices=[
                            'bsd-syslog',
                            'syslog',
                            'legacy-bigip',
                            'rfc5424',
                            'rfc3164'
                        ]
                    ),
                    foward_to=dict()
                )
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
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
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
