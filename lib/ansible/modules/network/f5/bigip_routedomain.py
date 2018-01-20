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
module: bigip_routedomain
short_description: Manage route domains on a BIG-IP
description:
  - Manage route domains on a BIG-IP.
version_added: "2.2"
options:
  name:
    description:
      - The name of the route domain.
      - When creating a new route domain, if this value is not specified, then the
        value of C(id) will be used for it.
    version_added: 2.5
  bwc_policy:
    description:
      - The bandwidth controller for the route domain.
  connection_limit:
    description:
      - The maximum number of concurrent connections allowed for the
        route domain. Setting this to C(0) turns off connection limits.
  description:
    description:
      - Specifies descriptive text that identifies the route domain.
  flow_eviction_policy:
    description:
      - The eviction policy to use with this route domain. Apply an eviction
        policy to provide customized responses to flow overflows and slow
        flows on the route domain.
  id:
    description:
      - The unique identifying integer representing the route domain.
      - This field is required when creating a new route domain.
      - In version 2.5, this value is no longer used to reference a route domain when
        making modifications to it (for instance during update and delete operations).
        Instead, the C(name) parameter is used. In version 2.6, the C(name) value will
        become a required parameter.
  parent:
    description:
      Specifies the route domain the system searches when it cannot
      find a route in the configured domain.
  partition:
    description:
      - Partition to create the route domain on. Partitions cannot be updated
        once they are created.
    default: Common
    version_added: 2.5
  routing_protocol:
    description:
      - Dynamic routing protocols for the system to use in the route domain.
    choices:
      - BFD
      - BGP
      - IS-IS
      - OSPFv2
      - OSPFv3
      - PIM
      - RIP
      - RIPng
  service_policy:
    description:
      - Service policy to associate with the route domain.
  state:
    description:
      - Whether the route domain should exist or not.
    default: present
    choices:
      - present
      - absent
  strict:
    description:
      - Specifies whether the system enforces cross-routing restrictions
        or not.
    choices:
      - enabled
      - disabled
  vlans:
    description:
      - VLANs for the system to use in the route domain
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a route domain
  bigip_routedomain:
    name: foo
    id: 1234
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Set VLANs on the route domain
  bigip_routedomain:
    name: bar
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
    vlans:
      - net1
      - foo
  delegate_to: localhost
'''

RETURN = r'''
id:
  description: The ID of the route domain that was changed
  returned: changed
  type: int
  sample: 2
description:
  description: The description of the route domain
  returned: changed
  type: string
  sample: route domain foo
strict:
  description: The new strict isolation setting
  returned: changed
  type: string
  sample: enabled
parent:
  description: The new parent route domain
  returned: changed
  type: int
  sample: 0
vlans:
  description: List of new VLANs the route domain is applied to
  returned: changed
  type: list
  sample: ['/Common/http-tunnel', '/Common/socks-tunnel']
routing_protocol:
  description: List of routing protocols applied to the route domain
  returned: changed
  type: list
  sample: ['bfd', 'bgp']
bwc_policy:
  description: The new bandwidth controller
  returned: changed
  type: string
  sample: /Common/foo
connection_limit:
  description: The new connection limit for the route domain
  returned: changed
  type: int
  sample: 100
flow_eviction_policy:
  description: The new eviction policy to use with this route domain
  returned: changed
  type: string
  sample: /Common/default-eviction-policy
service_policy:
  description: The new service policy to use with this route domain
  returned: changed
  type: string
  sample: /Common-my-service-policy
'''

try:
    from f5.bigip import ManagementRoot
except ImportError:
    pass  # Handled via f5_utils.HAS_F5SDK

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

HAS_DEVEL_IMPORTS = False

try:
    # Sideband repository used for dev
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
    HAS_DEVEL_IMPORTS = True
except ImportError:
    # Upstream Ansible
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


PROTOCOLS = [
    'BFD', 'BGP', 'IS-IS', 'OSPFv2', 'OSPFv3', 'PIM', 'RIP', 'RIPng'
]

STRICTS = ['enabled', 'disabled']


class BigIpRouteDomain(object):
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
                                  port=kwargs['server_port'],
                                  token=True)

    def absent(self):
        if not self.exists():
            return False

        if self.params['check_mode']:
            return True

        if self.params['name'] is None:
            self.params['name'] = str(self.params['id'])

        rd = self.api.tm.net.route_domains.route_domain.load(
            name=self.params['name'],
            partition=self.params['partition']
        )
        rd.delete()

        if self.exists():
            raise F5ModuleError("Failed to delete the route domain")
        else:
            return True

    def present(self):
        if self.exists():
            return self.update()
        else:
            if self.params['check_mode']:
                return True
            return self.create()

    def read(self):
        """Read information and transform it

        The values that are returned by BIG-IP in the f5-sdk can have encoding
        attached to them as well as be completely missing in some cases.

        Therefore, this method will transform the data from the BIG-IP into a
        format that is more easily consumable by the rest of the class and the
        parameters that are supported by the module.
        """
        p = dict()

        if self.params['name'] is None:
            self.params['name'] = str(self.params['id'])

        r = self.api.tm.net.route_domains.route_domain.load(
            name=self.params['name'],
            partition=self.params['partition']
        )

        p['id'] = int(r.id)
        p['name'] = str(r.name)

        if hasattr(r, 'connectionLimit'):
            p['connection_limit'] = int(r.connectionLimit)
        if hasattr(r, 'description'):
            p['description'] = str(r.description)
        if hasattr(r, 'strict'):
            p['strict'] = str(r.strict)
        if hasattr(r, 'parent'):
            p['parent'] = r.parent
        if hasattr(r, 'vlans'):
            p['vlans'] = list(set([str(x) for x in r.vlans]))
        if hasattr(r, 'routingProtocol'):
            p['routing_protocol'] = list(set([str(x) for x in r.routingProtocol]))
        if hasattr(r, 'flowEvictionPolicy'):
            p['flow_eviction_policy'] = str(r.flowEvictionPolicy)
        if hasattr(r, 'bwcPolicy'):
            p['bwc_policy'] = str(r.bwcPolicy)
        if hasattr(r, 'servicePolicy'):
            p['service_policy'] = str(r.servicePolicy)
        return p

    def domains(self):
        result = []

        domains = self.api.tm.net.route_domains.get_collection()
        for domain in domains:
            # Just checking for the addition of the partition here for
            # different versions of BIG-IP
            if '/' + self.params['partition'] + '/' in domain.name:
                result.append(domain.name)
            else:
                full_name = '/%s/%s' % (self.params['partition'], domain.name)
                result.append(full_name)
        return result

    def create(self):
        params = dict()
        params['id'] = self.params['id']
        params['name'] = self.params['name']
        params['partition'] = self.params['partition']

        if params['name'] is None:
            self.params['name'] = str(self.params['id'])
        elif params['id'] is None:
            raise F5ModuleError(
                "The 'id' parameter is required when creating new route domains."
            )

        partition = self.params['partition']
        description = self.params['description']
        strict = self.params['strict']
        parent = self.params['parent']
        bwc_policy = self.params['bwc_policy']
        vlans = self.params['vlans']
        routing_protocol = self.params['routing_protocol']
        connection_limit = self.params['connection_limit']
        flow_eviction_policy = self.params['flow_eviction_policy']
        service_policy = self.params['service_policy']

        if description is not None:
            params['description'] = description

        if strict is not None:
            params['strict'] = strict

        if parent is not None:
            parent = '/%s/%s' % (partition, parent)
            if parent in self.domains():
                params['parent'] = parent
            else:
                raise F5ModuleError(
                    "The parent route domain was not found"
                )

        if bwc_policy is not None:
            policy = '/%s/%s' % (partition, bwc_policy)
            params['bwcPolicy'] = policy

        if vlans is not None:
            params['vlans'] = []
            for vlan in vlans:
                vname = '/%s/%s' % (partition, vlan)
                params['vlans'].append(vname)

        if routing_protocol is not None:
            params['routingProtocol'] = []
            for protocol in routing_protocol:
                if protocol in PROTOCOLS:
                    params['routingProtocol'].append(protocol)
                else:
                    raise F5ModuleError(
                        "routing_protocol must be one of: %s" % (PROTOCOLS)
                    )

        if connection_limit is not None:
            params['connectionLimit'] = connection_limit

        if flow_eviction_policy is not None:
            policy = '/%s/%s' % (partition, flow_eviction_policy)
            params['flowEvictionPolicy'] = policy

        if service_policy is not None:
            policy = '/%s/%s' % (partition, service_policy)
            params['servicePolicy'] = policy

        self.api.tm.net.route_domains.route_domain.create(**params)
        exists = self.api.tm.net.route_domains.route_domain.exists(
            name=self.params['name'],
            partition=self.params['partition']
        )

        if exists:
            return True
        else:
            raise F5ModuleError(
                "An error occurred while creating the route domain"
            )

    def update(self):
        changed = False
        params = dict()
        current = self.read()

        if self.params['name'] is None:
            self.params['name'] = str(self.params['id'])

        check_mode = self.params['check_mode']
        partition = self.params['partition']
        description = self.params['description']
        strict = self.params['strict']
        parent = self.params['parent']
        bwc_policy = self.params['bwc_policy']
        vlans = self.params['vlans']
        routing_protocol = self.params['routing_protocol']
        connection_limit = self.params['connection_limit']
        flow_eviction_policy = self.params['flow_eviction_policy']
        service_policy = self.params['service_policy']

        if description is not None:
            if 'description' in current:
                if description != current['description']:
                    params['description'] = description
            else:
                params['description'] = description

        if strict is not None:
            if strict != current['strict']:
                params['strict'] = strict

        if parent is not None:
            parent = '/%s/%s' % (partition, parent)
            if 'parent' in current:
                if parent != current['parent']:
                    params['parent'] = parent
            else:
                params['parent'] = parent

        if bwc_policy is not None:
            policy = '/%s/%s' % (partition, bwc_policy)
            if 'bwc_policy' in current:
                if policy != current['bwc_policy']:
                    params['bwcPolicy'] = policy
            else:
                params['bwcPolicy'] = policy

        if vlans is not None:
            tmp = set()
            for vlan in vlans:
                vname = '/%s/%s' % (partition, vlan)
                tmp.add(vname)
            tmp = list(tmp)
            if 'vlans' in current:
                if tmp != current['vlans']:
                    params['vlans'] = tmp
            else:
                params['vlans'] = tmp

        if routing_protocol is not None:
            tmp = set()
            for protocol in routing_protocol:
                if protocol in PROTOCOLS:
                    tmp.add(protocol)
                else:
                    raise F5ModuleError(
                        "routing_protocol must be one of: %s" % (PROTOCOLS)
                    )
            tmp = list(tmp)
            if 'routing_protocol' in current:
                if tmp != current['routing_protocol']:
                    params['routingProtocol'] = tmp
            else:
                params['routingProtocol'] = tmp

        if connection_limit is not None:
            if connection_limit != current['connection_limit']:
                params['connectionLimit'] = connection_limit

        if flow_eviction_policy is not None:
            policy = '/%s/%s' % (partition, flow_eviction_policy)
            if 'flow_eviction_policy' in current:
                if policy != current['flow_eviction_policy']:
                    params['flowEvictionPolicy'] = policy
            else:
                params['flowEvictionPolicy'] = policy

        if service_policy is not None:
            policy = '/%s/%s' % (partition, service_policy)
            if 'service_policy' in current:
                if policy != current['service_policy']:
                    params['servicePolicy'] = policy
            else:
                params['servicePolicy'] = policy

        if params:
            changed = True
            self.cparams = camel_dict_to_snake_dict(params)
            if check_mode:
                return changed
        else:
            return changed

        try:
            rd = self.api.tm.net.route_domains.route_domain.load(
                name=self.params['name'],
                partition=self.params['partition']
            )
            rd.update(**params)
            rd.refresh()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(e)

        return True

    def exists(self):
        if self.params['name'] is None:
            self.params['name'] = str(self.params['id'])
        return self.api.tm.net.route_domains.route_domain.exists(
            name=self.params['name'],
            partition=self.params['partition']
        )

    def exec_module(self):
        result = dict()
        state = self.params['state']

        if state == "present":
            changed = self.present()
            current = self.read()
            result.update(current)
        elif state == "absent":
            changed = self.absent()

        result.update(dict(changed=changed))
        return result


def main():
    argument_spec = f5_argument_spec

    meta_args = dict(
        name=dict(),
        id=dict(type='int'),
        description=dict(),
        strict=dict(choices=STRICTS),
        parent=dict(type='int'),
        vlans=dict(type='list'),
        routing_protocol=dict(type='list'),
        bwc_policy=dict(),
        connection_limit=dict(type='int',),
        flow_eviction_policy=dict(),
        service_policy=dict(),
        partition=dict(
            default='Common',
            fallback=(env_fallback, ['F5_PARTITION'])
        ),
        state=dict(
            default='present',
            choices=['present', 'absent']
        )
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['name', 'id']]
    )

    try:
        obj = BigIpRouteDomain(check_mode=module.check_mode, **module.params)
        result = obj.exec_module()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
