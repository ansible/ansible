#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_remote_syslog
short_description: Manipulate remote syslog settings on a BIG-IP
description:
  - Manipulate remote syslog settings on a BIG-IP.
version_added: 2.5
options:
  remote_host:
    description:
      - Specifies the IP address, or hostname, for the remote system to
        which the system sends log messages.
    type: str
    required: True
  name:
    description:
      - Specifies the name of the syslog object.
      - This option is required when multiple C(remote_host) with the same IP
        or hostname are present on the device.
      - If C(name) is not provided C(remote_host) is used by default.
    type: str
    version_added: 2.8
  remote_port:
    description:
      - Specifies the port that the system uses to send messages to the
        remote logging server.
      - When creating a remote syslog, if this parameter is not specified, the
        default value C(514) is used.
    type: str
  local_ip:
    description:
      - Specifies the local IP address of the system that is logging. To
        provide no local IP, specify the value C(none).
      - When creating a remote syslog, if this parameter is not specified, the
        default value C(none) is used.
    type: str
  state:
    description:
      - When C(present), guarantees that the remote syslog exists with the provided
        attributes.
      - When C(absent), removes the remote syslog from the system.
    type: str
    choices:
      - absent
      - present
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Add a remote syslog server to log to
  bigip_remote_syslog:
    remote_host: 10.10.10.10
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Add a remote syslog server on a non-standard port to log to
  bigip_remote_syslog:
    remote_host: 10.10.10.10
    remote_port: 1234
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
remote_port:
  description: New remote port of the remote syslog server.
  returned: changed
  type: int
  sample: 514
local_ip:
  description: The new local IP of the remote syslog server
  returned: changed
  type: str
  sample: 10.10.10.10
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import is_valid_hostname
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.ipaddress import is_valid_ip
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import is_valid_hostname
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip


class Parameters(AnsibleF5Parameters):
    api_map = {
        'remotePort': 'remote_port',
        'localIp': 'local_ip',
        'host': 'remote_host',
    }

    updatables = [
        'remote_port',
        'local_ip',
        'remote_host',
        'name',
    ]

    returnables = [
        'remote_port',
        'local_ip',
        'remote_host',
        'name',
        'remoteServers',
    ]

    api_attributes = [
        'remotePort',
        'localIp',
        'host',
        'name',
        'remoteServers',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def remote_host(self):
        if is_valid_ip(self._values['remote_host']):
            return self._values['remote_host']
        elif is_valid_hostname(self._values['remote_host']):
            return str(self._values['remote_host'])
        raise F5ModuleError(
            "The provided 'remote_host' is not a valid IP or hostname"
        )

    @property
    def remote_port(self):
        if self._values['remote_port'] in [None, 'none']:
            return None
        if self._values['remote_port'] == 0:
            raise F5ModuleError(
                "The 'remote_port' value must between 1 and 65535"
            )
        return int(self._values['remote_port'])

    @property
    def local_ip(self):
        if self._values['local_ip'] in [None, 'none']:
            return None
        if is_valid_ip(self._values['local_ip']):
            return self._values['local_ip']
        else:
            raise F5ModuleError(
                "The provided 'local_ip' is not a valid IP address"
            )

    @property
    def name(self):
        if self._values['remote_host'] is None:
            return None
        if self._values['name'] is None:
            return None
        name = fq_name(self.partition, self._values['name'])
        return name


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                change = getattr(self, returnable)
                if isinstance(change, dict):
                    result.update(change)
                else:
                    result[returnable] = change
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    @property
    def remote_port(self):
        if self._values['remote_port'] is None:
            return None
        return int(self._values['remote_port'])

    @property
    def remoteServers(self):
        pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have
        self._local_ip = None
        self._remote_port = None

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
        self.module = kwargs.pop('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

        # A list of all the syslogs queried from the API when reading current info
        # from the device. This is used when updating the API as the value that needs
        # to be updated is a list of syslogs and PATCHing a list would override any
        # default settings.
        self.syslogs = dict()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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

    def format_syslogs(self, syslogs):
        result = None
        for x in syslogs:
            syslog = ApiParameters(params=x)
            self.syslogs[syslog.name] = x

            if syslog.name == self.want.name:
                result = syslog
            elif syslog.remote_host == self.want.remote_host:
                result = syslog

        if not result:
            return ApiParameters()
        return result

    def exec_module(self):
        result = dict()

        changed = self.present()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def present(self):
        return self.update()

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.format_syslogs(self.read_current_from_device())
        if not self.should_update() and self.want.state != 'absent':
            return False
        if self.module.check_mode:
            return True

        if self.want.name is None:
            self.want.update({'name': self.want.remote_host})

            syslogs = [v for k, v in iteritems(self.syslogs)]
            dupes = [x for x in syslogs if x['host'] == self.want.remote_host]
            if len(dupes) > 1:
                raise F5ModuleError(
                    "Multiple occurrences of hostname: {0} detected, please specify 'name' parameter". format(self.want.remote_host)
                )

        # A absent syslog does not appear in the list of existing syslogs
        if self.want.state == 'absent':
            if self.want.name not in self.syslogs:
                return False

        # At this point we know the existing syslog is not absent, so we need
        # to change it in some way.
        #
        # First, if we see that the syslog is in the current list of syslogs,
        # we are going to update it
        changes = dict(self.changes.api_params())
        if self.want.name in self.syslogs:
            self.syslogs[self.want.name].update(changes)
        else:
            # else, we are going to add it to the list of syslogs
            self.syslogs[self.want.name] = changes

        # Since the name attribute is not a parameter tracked in the Parameter
        # classes, we will add the name to the list of attributes so that when
        # we update the API, it creates the correct vector
        self.syslogs[self.want.name].update({'name': self.want.name})

        # Finally, the absent state forces us to remove the syslog from the
        # list.
        if self.want.state == 'absent':
            del self.syslogs[self.want.name]

        # All of the syslogs must be re-assembled into a list of dictionaries
        # so that when we PATCH the API endpoint, the syslogs list is filled
        # correctly.
        #
        # There are **not** individual API endpoints for the individual syslogs.
        # Instead, the endpoint includes a list of syslogs that is part of the
        # system config
        result = [v for k, v in iteritems(self.syslogs)]

        self.changes = Changes(params=dict(remoteServers=result))
        self.changes.update(self.want._values)
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        params = dict(
            remoteServers=params.get('remoteServers')
        )
        uri = "https://{0}:{1}/mgmt/tm/sys/syslog/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/syslog/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = response.get('remoteServers', [])
        return result


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            remote_host=dict(
                required=True
            ),
            remote_port=dict(),
            local_ip=dict(),
            name=dict(),
            state=dict(
                default='present',
                choices=['absent', 'present']
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

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
