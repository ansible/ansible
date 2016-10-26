#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016 F5 Networks Inc.
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

DOCUMENTATION = '''
---
module: bigip_selfip
short_description: Manage Self-IPs on a BIG-IP system
description:
  - Manage Self-IPs on a BIG-IP system
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
    required: true
    default: Value of C(address)
  netmask:
    description:
      - The netmasks for the self IP.
    required: true
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that the Self-IP exists with the provided attributes. When C(absent),
        removes the Self-IP from the system.
    required: false
    default: present
    choices:
      - absent
      - present
  traffic_group:
    description:
      - The traffic group for the self IP addresses in an active-active,
        redundant load balancer configuration.
    required: false
  vlan:
    description:
      - The VLAN that the new self IPs will be on.
    required: true
  route_domain:
    description:
        - The route domain id of the system.
          If none, id of the route domain will be "0" (default route domain)
    required: false
    default: none
    version_added: 2.3
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

EXAMPLES = '''
- name: Create Self IP
  bigip_selfip:
      address: "10.10.10.10"
      name: "self1"
      netmask: "255.255.255.0"
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
      validate_certs: "no"
      vlan: "vlan1"
  delegate_to: localhost

- name: Create Self IP with a Route Domain
  bigip_selfip:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      validate_certs: "no"
      name: "self1"
      address: "10.10.10.10"
      netmask: "255.255.255.0"
      vlan: "vlan1"
      route_domain: "10"
      allow_service: "default"
  delegate_to: localhost

- name: Delete Self IP
  bigip_selfip:
      name: "self1"
      password: "secret"
      server: "lb.mydomain.com"
      state: "absent"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Allow management web UI to be accessed on this Self IP
  bigip_selfip:
      name: "self1"
      password: "secret"
      server: "lb.mydomain.com"
      state: "absent"
      user: "admin"
      validate_certs: "no"
      allow_service:
          - "tcp:443"
  delegate_to: localhost

- name: Allow HTTPS and SSH access to this Self IP
  bigip_selfip:
      name: "self1"
      password: "secret"
      server: "lb.mydomain.com"
      state: "absent"
      user: "admin"
      validate_certs: "no"
      allow_service:
          - "tcp:443"
          - "tpc:22"
  delegate_to: localhost

- name: Allow all services access to this Self IP
  bigip_selfip:
      name: "self1"
      password: "secret"
      server: "lb.mydomain.com"
      state: "absent"
      user: "admin"
      validate_certs: "no"
      allow_service:
          - all
  delegate_to: localhost

- name: Allow only GRE and IGMP protocols access to this Self IP
  bigip_selfip:
      name: "self1"
      password: "secret"
      server: "lb.mydomain.com"
      state: "absent"
      user: "admin"
      validate_certs: "no"
      allow_service:
          - gre:0
          - igmp:0
  delegate_to: localhost

- name: Allow all TCP, but no other protocols access to this Self IP
  bigip_selfip:
      name: "self1"
      password: "secret"
      server: "lb.mydomain.com"
      state: "absent"
      user: "admin"
      validate_certs: "no"
      allow_service:
          - tcp:0
  delegate_to: localhost
'''

RETURN = '''
allow_service:
    description: Services that allowed via this Self IP
    returned: changed
    type: list
    sample: ['igmp:0','tcp:22','udp:53']
address:
    description: The address for the Self IP
    returned: created
    type: string
    sample: "192.0.2.10"
name:
    description: The name of the Self IP
    returned:
        - created
        - changed
        - deleted
    type: string
    sample: "self1"
netmask:
    description: The netmask of the Self IP
    returned:
        - changed
        - created
    type: string
    sample: "255.255.255.0"
traffic_group:
    description: The traffic group that the Self IP is a member of
    return:
        - changed
        - created
    type: string
    sample: "traffic-group-local-only"
vlan:
    description: The VLAN set on the Self IP
    return:
        - changed
        - created
    type: string
    sample: "vlan1"
'''

try:
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

try:
    from netaddr import IPNetwork, AddrFormatError
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False

FLOAT = ['enabled', 'disabled']
DEFAULT_TG = 'traffic-group-local-only'
ALLOWED_PROTOCOLS = ['eigrp', 'egp', 'gre', 'icmp', 'igmp', 'igp', 'ipip',
                     'l2tp', 'ospf', 'pim', 'tcp', 'udp']


class BigIpSelfIp(object):
    def __init__(self, *args, **kwargs):
        if not HAS_F5SDK:
            raise F5ModuleError("The python f5-sdk module is required")

        # The params that change in the module
        self.cparams = dict()

        # Stores the params that are sent to the module
        self.params = kwargs
        self.api = ManagementRoot(kwargs['server'],
                                  kwargs['user'],
                                  kwargs['password'],
                                  port=kwargs['server_port'])

    def present(self):
        changed = False

        if self.exists():
            changed = self.update()
        else:
            changed = self.create()

        return changed

    def absent(self):
        changed = False

        if self.exists():
            changed = self.delete()

        return changed

    def read(self):
        """Read information and transform it

        The values that are returned by BIG-IP in the f5-sdk can have encoding
        attached to them as well as be completely missing in some cases.

        Therefore, this method will transform the data from the BIG-IP into a
        format that is more easily consumable by the rest of the class and the
        parameters that are supported by the module.

        :return: List of values currently stored in BIG-IP, formatted for use
        in this class.
        """
        p = dict()
        name = self.params['name']
        partition = self.params['partition']
        r = self.api.tm.net.selfips.selfip.load(
            name=name,
            partition=partition
        )

        if hasattr(r, 'address'):
            p['route_domain'] = str(None)
            if '%' in r.address:
                ipaddr = []
                ipaddr = r.address.split('%', 1)
                rdmask = ipaddr[1].split('/', 1)
                r.address = "%s/%s" % (ipaddr[0], rdmask[1])
                p['route_domain'] = str(rdmask[0])
            ipnet = IPNetwork(r.address)
            p['address'] = str(ipnet.ip)
            p['netmask'] = str(ipnet.netmask)
        if hasattr(r, 'trafficGroup'):
            p['traffic_group'] = str(r.trafficGroup)
        if hasattr(r, 'vlan'):
            p['vlan'] = str(r.vlan)
        if hasattr(r, 'allowService'):
            if r.allowService == 'all':
                p['allow_service'] = set(['all'])
            else:
                p['allow_service'] = set([str(x) for x in r.allowService])
        else:
            p['allow_service'] = set(['none'])
        p['name'] = name
        return p

    def verify_services(self):
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
        result = []
        for svc in self.params['allow_service']:
            if svc in ['all', 'none', 'default']:
                result = [svc]
                break

            tmp = svc.split(':')
            if tmp[0] not in ALLOWED_PROTOCOLS:
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
                    "The provided port '%s' must be between 0 and 65535"
                    % (port)
                )
            else:
                result.append(svc)
        return set(result)

    def fmt_services(self, services):
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
        result = list(services)
        if result[0] == 'all':
            return 'all'
        elif result[0] == 'none':
            return None
        else:
            return list(services)

    def traffic_groups(self):
        result = []

        groups = self.api.tm.cm.traffic_groups.get_collection()
        for group in groups:
            # Just checking for the addition of the partition here for
            # different versions of BIG-IP
            if '/' + self.params['partition'] + '/' in group.name:
                result.append(group.name)
            else:
                full_name = '/%s/%s' % (self.params['partition'], group.name)
                result.append(str(full_name))
        return result

    def update(self):
        changed = False
        svcs = []
        params = dict()
        current = self.read()

        check_mode = self.params['check_mode']
        address = self.params['address']
        allow_service = self.params['allow_service']
        name = self.params['name']
        netmask = self.params['netmask']
        partition = self.params['partition']
        traffic_group = self.params['traffic_group']
        vlan = self.params['vlan']
        route_domain = self.params['route_domain']

        if address is not None and address != current['address']:
            raise F5ModuleError(
                'Self IP addresses cannot be updated'
            )

        if netmask is not None:
            # I ignore the address value here even if they provide it because
            # you are not allowed to change it.
            try:
                address = IPNetwork(current['address'])

                new_addr = "%s/%s" % (address.ip, netmask)
                nipnet = IPNetwork(new_addr)
                if route_domain is not None:
                    nipnet = "%s%s%s" % (address.ip, route_domain, netmask)

                cur_addr = "%s/%s" % (current['address'], current['netmask'])
                cipnet = IPNetwork(cur_addr)
                if route_domain is not None:
                    cipnet = "%s%s%s" % (current['address'], current['route_domain'], current['netmask'])

                if nipnet != cipnet:
                    if route_domain is not None:
                        address = "%s%s%s/%s" % (address.ip, '%', route_domain, netmask)
                    else:
                        address = "%s/%s" % (nipnet.ip, nipnet.prefixlen)
                    params['address'] = address
            except AddrFormatError:
                raise F5ModuleError(
                    'The provided address/netmask value was invalid'
                )

        if traffic_group is not None:
            traffic_group = "/%s/%s" % (partition, traffic_group)
            if traffic_group not in self.traffic_groups():
                raise F5ModuleError(
                    'The specified traffic group was not found'
                )

            if 'traffic_group' in current:
                if traffic_group != current['traffic_group']:
                    params['trafficGroup'] = traffic_group
            else:
                params['trafficGroup'] = traffic_group

        if vlan is not None:
            vlans = self.get_vlans()
            vlan = "/%s/%s" % (partition, vlan)

            if 'vlan' in current:
                if vlan != current['vlan']:
                    params['vlan'] = vlan
            else:
                params['vlan'] = vlan

            if vlan not in vlans:
                raise F5ModuleError(
                    'The specified VLAN was not found'
                )

        if allow_service is not None:
            svcs = self.verify_services()
            if 'allow_service' in current:
                if svcs != current['allow_service']:
                    params['allowService'] = self.fmt_services(svcs)
            else:
                params['allowService'] = self.fmt_services(svcs)

        if params:
            changed = True
            params['name'] = name
            params['partition'] = partition
            if check_mode:
                return changed
            self.cparams = camel_dict_to_snake_dict(params)
            if svcs:
                self.cparams['allow_service'] = list(svcs)
        else:
            return changed

        r = self.api.tm.net.selfips.selfip.load(
            name=name,
            partition=partition
        )
        r.update(**params)
        r.refresh()

        return True

    def get_vlans(self):
        """Returns formatted list of VLANs

        The VLAN values stored in BIG-IP are done so using their fully
        qualified name which includes the partition. Therefore, "correct"
        values according to BIG-IP look like this

            /Common/vlan1

        This is in contrast to the formats that most users think of VLANs
        as being stored as

            vlan1

        To provide for the consistent user experience while not turfing
        BIG-IP, we need to massage the values that are provided by the
        user so that they include the partition.

        :return: List of vlans formatted with preceeding partition
        """
        partition = self.params['partition']
        vlans = self.api.tm.net.vlans.get_collection()
        return [str("/" + partition + "/" + x.name) for x in vlans]

    def create(self):
        params = dict()

        svcs = []
        check_mode = self.params['check_mode']
        address = self.params['address']
        allow_service = self.params['allow_service']
        name = self.params['name']
        netmask = self.params['netmask']
        partition = self.params['partition']
        traffic_group = self.params['traffic_group']
        vlan = self.params['vlan']
        route_domain = self.params['route_domain']

        if address is None or netmask is None:
            raise F5ModuleError(
                'An address and a netmask must be specififed'
            )

        if vlan is None:
            raise F5ModuleError(
                'A VLAN name must be specified'
            )
        else:
            vlan = "/%s/%s" % (partition, vlan)

        try:
            ipin = "%s/%s" % (address, netmask)
            ipnet = IPNetwork(ipin)
            if route_domain is not None:
                params['address'] = "%s%s%s/%s" % (ipnet.ip, '%', route_domain, ipnet.prefixlen)
            else:
                params['address'] = "%s/%s" % (ipnet.ip, ipnet.prefixlen)
        except AddrFormatError:
            raise F5ModuleError(
                'The provided address/netmask value was invalid'
            )

        if traffic_group is None:
            params['trafficGroup'] = "/%s/%s" % (partition, DEFAULT_TG)
        else:
            traffic_group = "/%s/%s" % (partition, traffic_group)
            if traffic_group in self.traffic_groups():
                params['trafficGroup'] = traffic_group
            else:
                raise F5ModuleError(
                    'The specified traffic group was not found'
                )

        vlans = self.get_vlans()
        if vlan in vlans:
            params['vlan'] = vlan
        else:
            raise F5ModuleError(
                'The specified VLAN was not found'
            )

        if allow_service is not None:
            svcs = self.verify_services()
            params['allowService'] = self.fmt_services(svcs)

        params['name'] = name
        params['partition'] = partition

        self.cparams = camel_dict_to_snake_dict(params)
        if svcs:
            self.cparams['allow_service'] = list(svcs)

        if check_mode:
            return True

        d = self.api.tm.net.selfips.selfip
        d.create(**params)

        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the self IP")

    def delete(self):
        params = dict()
        check_mode = self.params['check_mode']

        params['name'] = self.params['name']
        params['partition'] = self.params['partition']

        self.cparams = camel_dict_to_snake_dict(params)
        if check_mode:
            return True

        dc = self.api.tm.net.selfips.selfip.load(**params)
        dc.delete()

        if self.exists():
            raise F5ModuleError("Failed to delete the self IP")
        return True

    def exists(self):
        name = self.params['name']
        partition = self.params['partition']
        return self.api.tm.net.selfips.selfip.exists(
            name=name,
            partition=partition
        )

    def flush(self):
        result = dict()
        state = self.params['state']

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.cparams)
        result.update(dict(changed=changed))
        return result


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        address=dict(required=False, default=None),
        allow_service=dict(type='list', default=None),
        name=dict(required=True),
        netmask=dict(required=False, default=None),
        traffic_group=dict(required=False, default=None),
        vlan=dict(required=False, default=None),
        route_domain=dict(required=False, default=None)
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    try:
        if not HAS_NETADDR:
            raise F5ModuleError(
                "The netaddr python module is required."
            )

        obj = BigIpSelfIp(check_mode=module.check_mode, **module.params)
        result = obj.flush()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
