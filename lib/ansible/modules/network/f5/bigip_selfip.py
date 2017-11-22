#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_selfip
short_description: Manage Self-IPs on a BIG-IP system
description:
  - Manage Self-IPs on a BIG-IP system.
version_added: "2.2"
options:
  address:
    description:
      - The IP addresses for the new self IP. This value is ignored upon update
        as addresses themselves cannot be changed after they are created.
  allow_service:
    description:
      - Configure port lockdown for the Self IP. By default, the Self IP has a
        "default deny" policy. This can be changed to allow TCP and UDP ports
        as well as specific protocols. This list should contain C(protocol):C(port)
        values.
  name:
    description:
      - The self IP to create.
    required: True
    default: Value of C(address)
  netmask:
    description:
      - The netmask for the self IP. When creating a new Self IP, this value
        is required.
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that the Self-IP exists with the provided attributes. When C(absent),
        removes the Self-IP from the system.
    default: present
    choices:
      - absent
      - present
  traffic_group:
    description:
      - The traffic group for the Self IP addresses in an active-active,
        redundant load balancer configuration. When creating a new Self IP, if
        this value is not specified, the default of C(/Common/traffic-group-local-only)
        will be used.
  vlan:
    description:
      - The VLAN that the new self IPs will be on. When creating a new Self
        IP, this value is required.
  route_domain:
    description:
        - The route domain id of the system. When creating a new Self IP, if
          this value is not specified, a default value of C(0) will be used.
    version_added: 2.3
  partition:
    description:
      - Device partition to manage resources on. You can set different partitions
        for Self IPs, but the address used may not match any other address used
        by a Self IP. In that sense, Self IPs are not isolated by partitions as
        other resources on a BIG-IP are.
    default: Common
    version_added: 2.5
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires the netaddr Python package on the host.
extends_documentation_fragment: f5
requirements:
  - netaddr
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create Self IP
  bigip_selfip:
    address: 10.10.10.10
    name: self1
    netmask: 255.255.255.0
    password: secret
    server: lb.mydomain.com
    user: admin
    validate_certs: no
    vlan: vlan1
  delegate_to: localhost

- name: Create Self IP with a Route Domain
  bigip_selfip:
    server: lb.mydomain.com
    user: admin
    password: secret
    validate_certs: no
    name: self1
    address: 10.10.10.10
    netmask: 255.255.255.0
    vlan: vlan1
    route_domain: 10
    allow_service: default
  delegate_to: localhost

- name: Delete Self IP
  bigip_selfip:
    name: self1
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
    validate_certs: no
  delegate_to: localhost

- name: Allow management web UI to be accessed on this Self IP
  bigip_selfip:
    name: self1
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
    validate_certs: no
    allow_service:
      - tcp:443
  delegate_to: localhost

- name: Allow HTTPS and SSH access to this Self IP
  bigip_selfip:
    name: self1
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
    validate_certs: no
    allow_service:
      - tcp:443
      - tcp:22
  delegate_to: localhost

- name: Allow all services access to this Self IP
  bigip_selfip:
    name: self1
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
    validate_certs: no
    allow_service:
      - all
  delegate_to: localhost

- name: Allow only GRE and IGMP protocols access to this Self IP
  bigip_selfip:
    name: self1
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
    validate_certs: no
    allow_service:
      - gre:0
      - igmp:0
  delegate_to: localhost

- name: Allow all TCP, but no other protocols access to this Self IP
  bigip_selfip:
    name: self1
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
    validate_certs: no
    allow_service:
      - tcp:0
  delegate_to: localhost
'''

RETURN = r'''
allow_service:
  description: Services that allowed via this Self IP
  returned: changed
  type: list
  sample: ['igmp:0','tcp:22','udp:53']
address:
  description: The address for the Self IP
  returned: created
  type: string
  sample: 192.0.2.10
name:
  description: The name of the Self IP
  returned: created, changed and deleted
  type: string
  sample: self1
netmask:
  description: The netmask of the Self IP
  returned: changed and created
  type: string
  sample: 255.255.255.0
traffic_group:
  description: The traffic group that the Self IP is a member of
  returned: changed and created
  type: string
  sample: traffic-group-local-only
vlan:
  description: The VLAN set on the Self IP
  returned: changed and created
  type: string
  sample: vlan1
'''

import os
import re

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False

try:
    from netaddr import IPNetwork, AddrFormatError, IPAddress
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'trafficGroup': 'traffic_group',
        'allowService': 'allow_service'
    }

    updatables = [
        'traffic_group', 'allow_service', 'vlan', 'route_domain', 'netmask'
    ]

    returnables = [
        'traffic_group', 'allow_service', 'vlan', 'route_domain', 'netmask'
    ]

    api_attributes = [
        'trafficGroup', 'allowService', 'vlan', 'address'
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
    def address(self):
        address = "{0}%{1}/{2}".format(
            self.ip, self.route_domain, self.netmask
        )
        return address

    @address.setter
    def address(self, value):
        self._values['ip'] = value

    @property
    def ip(self):
        if self._values['ip'] is None:
            return None
        try:
            ip = str(IPAddress(self._values['ip']))
            return ip
        except AddrFormatError:
            raise F5ModuleError(
                'The provided address is not a valid IP address'
            )

    @property
    def traffic_group(self):
        if self._values['traffic_group'] is None:
            return None
        return self._fqdn_name(self._values['traffic_group'])

    @property
    def route_domain(self):
        if self._values['route_domain'] is None:
            return None
        result = int(self._values['route_domain'])
        return result

    @property
    def netmask(self):
        if self._values['netmask'] is None:
            return None

        # Check if numeric
        if isinstance(self._values['netmask'], int):
            result = int(self._values['netmask'])
            if 0 < result < 256:
                return result
            raise F5ModuleError(
                'The provided netmask {0} is neither in IP or CIDR format'.format(result)
            )
        else:
            try:
                # IPv4 netmask
                address = '0.0.0.0/' + self._values['netmask']
                ip = IPNetwork(address)
            except AddrFormatError as ex:
                try:
                    # IPv6 netmask
                    address = '::/' + self._values['netmask']
                    ip = IPNetwork(address)
                except AddrFormatError as ex:
                    raise F5ModuleError(
                        'The provided netmask {0} is neither in IP or CIDR format'.format(self._values['netmask'])
                    )
            result = int(ip.prefixlen)
        return result

    @property
    def allow_service(self):
        """Verifies that a supplied service string has correct format

        The string format for port lockdown is PROTOCOL:PORT. This method
        will verify that the provided input matches the allowed protocols
        and the port ranges before submitting to BIG-IP.

        The only allowed exceptions to this rule are the following values

          * all
          * default
          * none

        These are special cases that are handled differently in the API.
        "all" is set as a string, "default" is set as a one item list, and
        "none" removes the key entirely from the REST API.

        :raises F5ModuleError:
        """
        if self._values['allow_service'] is None:
            return None
        result = []
        allowed_protocols = [
            'eigrp', 'egp', 'gre', 'icmp', 'igmp', 'igp', 'ipip',
            'l2tp', 'ospf', 'pim', 'tcp', 'udp'
        ]
        special_protocols = [
            'all', 'none', 'default'
        ]
        for svc in self._values['allow_service']:
            if svc in special_protocols:
                result = [svc]
                break
            elif svc in allowed_protocols:
                full_service = '{0}:0'.format(svc)
                result.append(full_service)
            else:
                tmp = svc.split(':')
                if tmp[0] not in allowed_protocols:
                    raise F5ModuleError(
                        "The provided protocol '%s' is invalid" % (tmp[0])
                    )
                try:
                    port = int(tmp[1])
                except Exception:
                    raise F5ModuleError(
                        "The provided port '%s' is not a number" % (tmp[1])
                    )

                if port < 0 or port > 65535:
                    raise F5ModuleError(
                        "The provided port '{0}' must be between 0 and 65535".format(port)
                    )
                else:
                    result.append(svc)
        return set(result)

    def _fqdn_name(self, value):
        if value is not None and not value.startswith('/'):
            return '/{0}/{1}'.format(self.partition, value)
        return value

    @property
    def vlan(self):
        if self._values['vlan'] is None:
            return None
        return self._fqdn_name(self._values['vlan'])


class ApiParameters(Parameters):
    api_map = {}

    @property
    def address(self):
        if self.ip and self.route_domain and self.netmask:
            return '{0}%{1}/{2}'.format(self.ip, self.route_domain, self.netmask)
        elif self.ip and self.netmask:
            return '{0}/{1}'.format(self.ip, self.netmask)

    @address.setter
    def address(self, value):
        pattern = r'^(?P<ip>[0-9A-Fa-f:.]+)%?(?P<rd>\d+)?\/(?P<nm>\d+)$'
        matches = re.match(pattern, value)
        if not matches:
            raise F5ModuleError(
                "The specified address is malformed. Please see documentation."
            )
        try:
            ip = matches.group('ip')
            self._values['ip'] = str(IPAddress(ip))
        except AddrFormatError:
            raise F5ModuleError(
                'The provided address is not a valid IP address'
            )
        self._values['route_domain'] = matches.group('rd')
        self._values['netmask'] = matches.group('nm')

    @property
    def allow_service(self):
        return self._values['allow_service']

    @property
    def trafficGroup(self):
        return self.traffic_group

    @trafficGroup.setter
    def trafficGroup(self, value):
        self._values['traffic_group'] = value

    @property
    def allowService(self):
        return self._values['allow_service']

    @allowService.setter
    def allowService(self, value):
        if value == 'all':
            self._values['allow_service'] = set(['all'])
        else:
            self._values['allow_service'] = set([str(x) for x in value])


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = ApiParameters()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = ApiParameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if k in ['netmask', 'route_domain']:
                    changed['address'] = change
                else:
                    changed[k] = change
        if changed:
            self.changes = ApiParameters(changed)
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
            changed = self.update()
        else:
            changed = self.create()
        return changed

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def read_current_from_device(self):
        resource = self.client.api.tm.net.selfips.selfip.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        params = ApiParameters(result)
        return params

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.net.selfips.selfip.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def create(self):
        if self.want.address is None or self.want.netmask is None:
            raise F5ModuleError(
                'An address and a netmask must be specified'
            )
        if self.want.vlan is None:
            raise F5ModuleError(
                'A VLAN name must be specified'
            )
        if self.want.traffic_group is None:
            self.want.update({'traffic_group': '/Common/traffic-group-local-only'})
        if self.want.route_domain is None:
            self.want.update({'route_domain': 0})

        if self.want.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the Self IP")

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.net.selfips.selfip.create(
            name=self.want.name,
            partition=self.want.partition,
            address=self.want.address,
            vlan=self.want.vlan,
            **params
        )

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the Self IP")
        return True

    def remove_from_device(self):
        resource = self.client.api.tm.net.selfips.selfip.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()

    def exists(self):
        result = self.client.api.tm.net.selfips.selfip.exists(
            name=self.want.name,
            partition=self.want.partition
        )
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
    def allow_service(self):
        """Returns services formatted for consumption by f5-sdk update

        The BIG-IP endpoint for services takes different values depending on
        what you want the "allowed services" to be. It can be any of the
        following

            - a list containing "protocol:port" values
            - the string "all"
            - a null value, or None

        This is a convenience function to massage the values the user has
        supplied so that they are formatted in such a way that BIG-IP will
        accept them and apply the specified policy.

        :param services: The services to format. This is always a Python set
        :return:
        """
        if self.want.allow_service is None:
            return None
        result = list(self.want.allow_service)
        if self.want.allow_service == self.have.allow_service:
            return None
        elif result[0] == 'none' and self.have.allow_service is None:
            return None
        elif result[0] == 'all':
            return 'all'
        elif result[0] == 'none':
            return []
        else:
            return list(result)

    @property
    def netmask(self):
        if self.want.netmask is None:
            return None
        try:
            address = IPNetwork(self.have.ip)
            if self.want.route_domain is not None:
                nipnet = "{0}%{1}/{2}".format(address.ip, self.want.route_domain, self.want.netmask)
                cipnet = "{0}%{1}/{2}".format(address.ip, self.want.route_domain, self.have.netmask)
            elif self.have.route_domain is not None:
                nipnet = "{0}%{1}/{2}".format(address.ip, self.have.route_domain, self.want.netmask)
                cipnet = "{0}%{1}/{2}".format(address.ip, self.have.route_domain, self.have.netmask)
            else:
                nipnet = "{0}/{1}".format(address.ip, self.want.netmask)
                cipnet = "{0}/{1}".format(address.ip, self.have.netmask)
            if nipnet != cipnet:
                return nipnet
        except AddrFormatError:
            raise F5ModuleError(
                'The provided address/netmask value "{0}" was invalid'.format(self.have.ip)
            )

    @property
    def route_domain(self):
        if self.want.route_domain is None:
            return None
        try:
            address = IPNetwork(self.have.ip)

            if self.want.netmask is not None:
                nipnet = "{0}%{1}/{2}".format(address.ip, self.want.route_domain, self.want.netmask)
                cipnet = "{0}%{1}/{2}".format(address.ip, self.have.route_domain, self.want.netmask)
            elif self.have.netmask is not None:
                nipnet = "{0}%{1}/{2}".format(address.ip, self.want.route_domain, self.have.netmask)
                cipnet = "{0}%{1}/{2}".format(address.ip, self.have.route_domain, self.have.netmask)

            if nipnet != cipnet:
                return nipnet
        except AddrFormatError:
            raise F5ModuleError(
                'The provided address/netmask value was invalid'
            )

    @property
    def traffic_group(self):
        if self.want.traffic_group == self.have.traffic_group:
            return None
        return self.want.traffic_group


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            address=dict(),
            allow_service=dict(type='list'),
            name=dict(required=True),
            netmask=dict(),
            traffic_group=dict(),
            vlan=dict(),
            route_domain=dict()
        )
        self.f5_product_name = 'bigip'


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
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
