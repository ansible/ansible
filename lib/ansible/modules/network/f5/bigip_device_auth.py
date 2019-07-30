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
module: bigip_device_auth
short_description: Manage system authentication on a BIG-IP
description:
  - Manage the system authentication configuration. This module can assist in configuring
    a number of different system authentication types. Note that this module can not be used
    to configure APM authentication types.
version_added: 2.7
options:
  type:
    description:
      - The authentication type to manage with this module.
      - Take special note that the parameters supported by this module will vary depending
        on the C(type) that you are configuring.
      - This module only supports a subset, at this time, of the total available auth types.
    type: str
    choices:
      - tacacs
      - local
  servers:
    description:
      - Specifies a list of the IPv4 addresses for servers using the Terminal
        Access Controller Access System (TACACS)+ protocol with which the system
        communicates to obtain authorization data.
      - For each address, an alternate TCP port number may be optionally specified
        by specifying the C(port) key.
      - If no port number is specified, the default port C(49163) is used.
      - This parameter is supported by the C(tacacs) type.
    type: raw
    suboptions:
      address:
        description:
          - The IP address of the server.
          - This field is required, unless you are specifying a simple list of servers.
            In that case, the simple list can specify server IPs. See examples for
            more clarification.
      port:
        description:
          - The port of the server.
        default: 49163
  secret:
    description:
      - Secret key used to encrypt and decrypt packets sent or received from the
        server.
      - B(Do not) use the pound/hash sign in the secret for TACACS+ servers.
      - When configuring TACACS+ auth for the first time, this value is required.
    type: str
  service_name:
    description:
      - Specifies the name of the service that the user is requesting to be
        authorized to use.
      - Identifying what the user is asking to be authorized for, enables the
        TACACS+ server to behave differently for different types of authorization
        requests.
      - When configuring this form of system authentication, this setting is required.
      - Note that the majority of TACACS+ implementations are of service type C(ppp),
        so try that first.
    type: str
    choices:
      - slip
      - ppp
      - arap
      - shell
      - tty-daemon
      - connection
      - system
      - firewall
  protocol_name:
    description:
      - Specifies the protocol associated with the value specified in C(service_name),
        which is a subset of the associated service being used for client authorization
        or system accounting.
      - Note that the majority of TACACS+ implementations are of protocol type C(ip),
        so try that first.
    type: str
    choices:
      - lcp
      - ip
      - ipx
      - atalk
      - vines
      - lat
      - xremote
      - tn3270
      - telnet
      - rlogin
      - pad
      - vpdn
      - ftp
      - http
      - deccp
      - osicp
      - unknown
  authentication:
    description:
      - Specifies the process the system employs when sending authentication requests.
      - When C(use-first-server), specifies that the system sends authentication
        attempts to only the first server in the list.
      - When C(use-all-servers), specifies that the system sends an authentication
        request to each server until authentication succeeds, or until the system has
        sent a request to all servers in the list.
      - This parameter is supported by the C(tacacs) type.
    type: str
    choices:
      - use-first-server
      - use-all-servers
  use_for_auth:
    description:
      - Specifies whether or not this auth source is put in use on the system.
    type: bool
  state:
    description:
      - The state of the authentication configuration on the system.
      - When C(present), guarantees that the system is configured for the specified C(type).
      - When C(absent), sets the system auth source back to C(local).
    type: str
    choices:
      - absent
      - present
    default: present
  update_secret:
    description:
      - C(always) will allow to update secrets if the user chooses to do so.
      - C(on_create) will only set the secret when a C(use_auth_source) is C(yes)
        and TACACS+ is not currently the auth source.
    type: str
    choices:
      - always
      - on_create
    default: always
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Set the system auth to TACACS+, default server port
  bigip_device_auth:
    type: tacacs
    authentication: use-all-servers
    protocol_name: ip
    secret: secret
    servers:
      - 10.10.10.10
      - 10.10.10.11
    service_name: ppp
    state: present
    use_for_auth: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Set the system auth to TACACS+, override server port
  bigip_device_auth:
    type: tacacs
    authentication: use-all-servers
    protocol_name: ip
    secret: secret
    servers:
      - address: 10.10.10.10
        port: 1234
      - 10.10.10.11
    service_name: ppp
    use_for_auth: yes
    state: present
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
servers:
  description: List of servers used in TACACS authentication.
  returned: changed
  type: list
  sample: ['1.2.2.1', '4.5.5.4']
authentication:
  description: Process the system uses to serve authentication requests when using TACACS.
  returned: changed
  type: str
  sample: use-all-servers
service_name:
  description: Name of the service the user is requesting to be authorized to use.
  returned: changed
  type: str
  sample: ppp
protocol_name:
  description: Name of the protocol associated with C(service_name) used for client authentication.
  returned: changed
  type: str
  sample: ip
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec


class BaseParameters(AnsibleF5Parameters):
    @property
    def api_map(self):
        return {}

    @property
    def api_attributes(self):
        return []

    @property
    def returnables(self):
        return []

    @property
    def updatables(self):
        return []


class BaseApiParameters(BaseParameters):
    pass


class BaseModuleParameters(BaseParameters):
    pass


class BaseChanges(BaseParameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class BaseUsableChanges(BaseChanges):
    pass


class BaseReportableChanges(BaseChanges):
    pass


class TacacsParameters(BaseParameters):
    api_map = {
        'protocol': 'protocol_name',
        'service': 'service_name'
    }

    api_attributes = [
        'authentication',
        'protocol',
        'service',
        'secret',
        'servers'
    ]

    returnables = [
        'servers',
        'secret',
        'authentication',
        'service_name',
        'protocol_name'
    ]

    updatables = [
        'servers',
        'secret',
        'authentication',
        'service_name',
        'protocol_name',
        'auth_source',
    ]


class TacacsApiParameters(TacacsParameters):
    pass


class TacacsModuleParameters(TacacsParameters):
    @property
    def servers(self):
        if self._values['servers'] is None:
            return None
        result = []
        for server in self._values['servers']:
            if isinstance(server, dict):
                if 'address' not in server:
                    raise F5ModuleError(
                        "An 'address' field must be provided when specifying separate fields to the 'servers' parameter."
                    )
                address = server.get('address')
                port = server.get('port', 49163)
            elif isinstance(server, string_types):
                address = server
                port = 49163
            result.append('{0}:{1}'.format(address, port))
        return result

    @property
    def auth_source(self):
        return 'tacacs'


class TacacsChanges(BaseChanges, TacacsParameters):
    pass


class TacacsUsableChanges(TacacsChanges):
    pass


class TacacsReportableChanges(TacacsChanges):
    @property
    def secret(self):
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
        want = getattr(self.want, param)
        try:
            have = getattr(self.have, param)
            if want != have:
                return want
        except AttributeError:
            return want

    @property
    def secret(self):
        if self.want.secret != self.have.secret and self.want.update_secret == 'always':
            return self.want.secret


class BaseManager(object):
    def _set_changed_options(self):
        changed = {}
        for key in self.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = self.get_usable_changes(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = self.updatables
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

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

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

    def present(self):
        if self.exists():
            return self.update()
        return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def update_auth_source_on_device(self, source):
        """Set the system auth source.

        Configuring the authentication source is only one step in the process of setting
        up an auth source. The other step is to inform the system of the auth source
        you want to use.

        This method is used for situations where

        * The ``use_for_auth`` parameter is set to ``yes``
        * The ``use_for_auth`` parameter is set to ``no``
        * The ``state`` parameter is set to ``absent``

        When ``state`` equal to ``absent``, before you can delete the TACACS+ configuration,
        you must set the system auth to "something else". The system ships with a system
        auth called "local", so this is the logical "something else" to use.

        When ``use_for_auth`` is no, the same situation applies as when ``state`` equal
        to ``absent`` is done above.

        When ``use_for_auth`` is ``yes``, this method will set the current system auth
        state to TACACS+.

        Arguments:
            source (string): The source that you want to set on the device.
        """
        params = dict(
            type=source
        )
        uri = 'https://{0}:{1}/mgmt/tm/auth/source/'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
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

    def read_current_auth_source_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/source".format(
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
        return response['type']


class LocalManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = self.get_module_parameters(params=self.module.params)
        self.have = self.get_api_parameters()
        self.changes = self.get_usable_changes()

    @property
    def returnables(self):
        return []

    @property
    def updatables(self):
        return []

    def get_parameters(self, params=None):
        return BaseParameters(params=params)

    def get_usable_changes(self, params=None):
        return BaseUsableChanges(params=params)

    def get_reportable_changes(self, params=None):
        return BaseReportableChanges(params=params)

    def get_module_parameters(self, params=None):
        return BaseModuleParameters(params=params)

    def get_api_parameters(self, params=None):
        return BaseApiParameters(params=params)

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/source".format(
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
        if response['type'] == 'local':
            return True
        return False

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.update_auth_source_on_device('local')
        return True

    def present(self):
        if not self.exists():
            return self.create()

    def absent(self):
        raise F5ModuleError(
            "The 'local' type cannot be removed. "
            "Instead, specify a 'state' of 'present' on other types."
        )


class TacacsManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = self.get_module_parameters(params=self.module.params)
        self.have = self.get_api_parameters()
        self.changes = self.get_usable_changes()

    @property
    def returnables(self):
        return TacacsParameters.returnables

    @property
    def updatables(self):
        return TacacsParameters.updatables

    def get_usable_changes(self, params=None):
        return TacacsUsableChanges(params=params)

    def get_reportable_changes(self, params=None):
        return TacacsReportableChanges(params=params)

    def get_module_parameters(self, params=None):
        return TacacsModuleParameters(params=params)

    def get_api_parameters(self, params=None):
        return TacacsApiParameters(params=params)

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/tacacs/~Common~system-auth".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.want.use_for_auth:
            self.update_auth_source_on_device('tacacs')
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        result = False
        if self.update_on_device():
            result = True
        if self.want.use_for_auth and self.changes.auth_source == 'tacacs':
            self.update_auth_source_on_device('tacacs')
            result = True
        return result

    def remove(self):
        if self.module.check_mode:
            return True
        self.update_auth_source_on_device('local')
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = 'system-auth'
        uri = "https://{0}:{1}/mgmt/tm/auth/tacacs".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        if not params:
            return False

        uri = 'https://{0}:{1}/mgmt/tm/auth/tacacs/~Common~system-auth'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
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
        return True

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/tacacs/~Common~system-auth".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True
        raise F5ModuleError(resp.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/tacacs/~Common~system-auth".format(
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
        response['auth_source'] = self.read_current_auth_source_from_device()
        return self.get_api_parameters(params=response)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.kwargs = kwargs

    def exec_module(self):
        manager = self.get_manager(self.module.params['type'])
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'tacacs':
            return TacacsManager(**self.kwargs)
        elif type == 'local':
            return LocalManager(**self.kwargs)
        else:
            raise F5ModuleError(
                "The provided 'type' is unknown."
            )


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            type=dict(
                required=True,
                choices=['local', 'tacacs']
            ),
            servers=dict(type='raw'),
            secret=dict(no_log=True),
            service_name=dict(
                choices=[
                    'slip', 'ppp', 'arap', 'shell', 'tty-daemon',
                    'connection', 'system', 'firewall'
                ]
            ),
            protocol_name=dict(
                choices=[
                    'lcp', 'ip', 'ipx', 'atalk', 'vines', 'lat',
                    'xremote', 'tn3270', 'telnet', 'rlogin', 'pad',
                    'vpdn', 'ftp', 'http', 'deccp', 'osicp', 'unknown'
                ]
            ),
            authentication=dict(
                choices=[
                    'use-first-server',
                    'use-all-servers'
                ]
            ),
            use_for_auth=dict(type='bool'),
            update_secret=dict(
                choices=['always', 'on_create'],
                default='always'
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),

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
