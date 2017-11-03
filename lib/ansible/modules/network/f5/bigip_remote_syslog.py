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
    required: True
  remote_port:
    description:
      - Specifies the port that the system uses to send messages to the
        remote logging server. When creating a remote syslog, if this parameter
        is not specified, the default value C(514) is used.
  local_ip:
    description:
      - Specifies the local IP address of the system that is logging. To
        provide no local IP, specify the value C(none). When creating a
        remote syslog, if this parameter is not specified, the default value
        C(none) is used.
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires the netaddr Python package on the host. This is as easy as pip
    install netaddr.
extends_documentation_fragment: f5
requirements:
  - f5-sdk >= 2.2.0
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Add a remote syslog server to log to
  bigip_remote_syslog:
    remote_host: 10.10.10.10
    password: secret
    server: lb.mydomain.com
    user: admin
    validate_certs: no
  delegate_to: localhost

- name: Add a remote syslog server on a non-standard port to log to
  bigip_remote_syslog:
    remote_host: 10.10.10.10
    remote_port: 1234
    password: secret
    server: lb.mydomain.com
    user: admin
    validate_certs: no
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
  type: string
  sample: 10.10.10.10
'''

try:
    import netaddr
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from ansible.module_utils.f5_utils import HAS_F5SDK
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    updatables = [
        'remote_port', 'local_ip', 'remoteServers'
    ]

    returnables = [
        'remote_port', 'local_ip'
    ]

    api_attributes = [
        'remoteServers'
    ]

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        self._values['__warnings'] = []
        if params:
            self.update(params=params)

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

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
    def remote_host(self):
        try:
            ip = netaddr.IPAddress(self._values['remote_host'])
            return str(ip)
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The provided 'remote_host' is not a valid IP address"
            )

    @property
    def remote_port(self):
        if self._values['remote_port'] is None:
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
        try:
            ip = netaddr.IPAddress(self._values['local_ip'])
            return str(ip)
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The provided 'local_ip' is not a valid IP address"
            )


class Changes(Parameters):
    @property
    def remote_port(self):
        return self._values['remote_port']

    @property
    def local_ip(self):
        return self._values['local_ip']


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

    @property
    def remoteServers(self):
        """Return changed list of remote servers

        The order of this list does not matter as BIG-IP will send to all the
        items in it.

        :return:
        """

        changed = False
        if self.want.remote_host is None:
            return None
        if self.have.remoteServers is None:
            remote = dict()
        else:
            remote = self.have.remoteServers
        current_hosts = dict((d['host'], d) for (i, d) in enumerate(remote))

        if self.want.state == 'absent':
            del current_hosts[self.want.remote_host]
            result = [v for (k, v) in iteritems(current_hosts)]
            return result

        if self.want.remote_host in current_hosts:
            item = current_hosts[self.want.remote_host]
            if self.want.remote_port is not None:
                if int(item['remotePort']) != self.want.remote_port:
                    item['remotePort'] = self.want.remote_port
                    self._remote_port = self.want.remote_port
                    changed = True
            if self.want.local_ip is not None:
                if item['localIp'] != self.want.local_ip:
                    item['localIp'] = self.want.local_ip
                    self._local_ip = self.want.local_ip
                    changed = True
        else:
            changed = True
            count = len(current_hosts.keys()) + 1
            host = self.want.remote_host
            current_hosts[self.want.remote_host] = dict(
                name="/Common/remotesyslog{0}".format(count),
                host=host
            )
            if self.want.remote_port is not None:
                current_hosts[host]['remotePort'] = self.want.remote_port
                self._remote_port = self.want.remote_port
            if self.want.local_ip is not None:
                current_hosts[host]['localIp'] = self.want.local_ip
                self._local_ip = self.want.local_ip
        if changed:
            result = [v for (k, v) in iteritems(current_hosts)]
            return result
        return None

    @property
    def remote_port(self):
        _ = self.remoteServers
        if self._remote_port:
            return self._remote_port

    @property
    def local_ip(self):
        _ = self.remoteServers
        if self._local_ip:
            return self._local_ip


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Changes()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(changed)
            self.changes.update({'remote_host': self.want.remote_host})

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
            self.changes = Changes(changed)
            self.changes.update({'remote_host': self.want.remote_host})
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

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        self._set_valid_defaults()
        self._update_changed_options()
        if self.client.check_mode:
            return True

        # This is an unnamed resource, so we only need to update
        self.update_on_device()
        return True

    def _set_valid_defaults(self):
        if self.changes.local_ip is None:
            self.changes.update({'local_ip': None})
        if self.changes.remote_port is None:
            self.changes.update({'remote_port': 514})
        remote_servers = [
            dict(
                name='/{0}/remotesyslog1'.format(self.want.partition),
                host=self.want.remote_host,
                localIp=self.changes.local_ip,
                remotePort=self.changes.remote_port
            )
        ]
        self.changes.update({'remoteServers': remote_servers})

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def exists(self):
        self.have = self.read_current_from_device()
        if self.have.remoteServers is None:
            return False

        for server in self.have.remoteServers:
            if server['host'] == self.want.remote_host:
                return True

    def update_on_device(self):
        params = self.changes.api_params()
        result = self.client.api.tm.sys.syslog.load()
        result.modify(**params)

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.syslog.load()
        attrs = resource.attrs
        result = Parameters(attrs)
        return result

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the remote syslog.")
        return True

    def remove_from_device(self):
        self._update_changed_options()
        params = self.changes.api_params()
        result = self.client.api.tm.sys.syslog.load()
        result.modify(**params)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            remote_host=dict(
                required=True
            ),
            remote_port=dict(),
            local_ip=dict(),
            state=dict(
                default='present',
                choices=['absent', 'present']
            )
        )
        self.f5_product_name = 'bigip'


def cleanup_tokens(client):
    try:
        resource = client.api.shared.authz.tokens_s.token.load(
            name=client.api.icrs.token
        )
        resource.delete()
    except Exception:
        pass


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    if not HAS_NETADDR:
        raise F5ModuleError("The python netaddr module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        cleanup_tokens(client)
        client.module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
