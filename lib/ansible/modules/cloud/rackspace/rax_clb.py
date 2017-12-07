#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rax_clb
short_description: create / delete a load balancer in Rackspace Public Cloud
description:
     - creates / deletes a Rackspace Public Cloud load balancer.
version_added: "1.4"
options:
  algorithm:
    description:
      - algorithm for the balancer being created
    choices:
      - RANDOM
      - LEAST_CONNECTIONS
      - ROUND_ROBIN
      - WEIGHTED_LEAST_CONNECTIONS
      - WEIGHTED_ROUND_ROBIN
    default: LEAST_CONNECTIONS
  meta:
    description:
      - A hash of metadata to associate with the instance
    default: null
  name:
    description:
      - Name to give the load balancer
    default: null
  port:
    description:
      - Port for the balancer being created
    default: 80
  protocol:
    description:
      - Protocol for the balancer being created
    choices:
      - DNS_TCP
      - DNS_UDP
      - FTP
      - HTTP
      - HTTPS
      - IMAPS
      - IMAPv4
      - LDAP
      - LDAPS
      - MYSQL
      - POP3
      - POP3S
      - SMTP
      - TCP
      - TCP_CLIENT_FIRST
      - UDP
      - UDP_STREAM
      - SFTP
    default: HTTP
  state:
    description:
      - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
  timeout:
    description:
      - timeout for communication between the balancer and the node
    default: 30
  type:
    description:
      - type of interface for the balancer being created
    choices:
      - PUBLIC
      - SERVICENET
    default: PUBLIC
  vip_id:
    description:
      - Virtual IP ID to use when creating the load balancer for purposes of
        sharing an IP with another load balancer of another protocol
    version_added: 1.5
  wait:
    description:
      - wait for the balancer to be in state 'running' before returning
    default: "no"
    choices:
      - "yes"
      - "no"
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
author:
    - "Christopher H. Laco (@claco)"
    - "Matt Martz (@sivel)"
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
- name: Build a Load Balancer
  gather_facts: False
  hosts: local
  connection: local
  tasks:
    - name: Load Balancer create request
      local_action:
        module: rax_clb
        credentials: ~/.raxpub
        name: my-lb
        port: 8080
        protocol: HTTP
        type: SERVICENET
        timeout: 30
        region: DFW
        wait: yes
        state: present
        meta:
          app: my-cool-app
      register: my_lb
'''


try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import (CLB_ALGORITHMS,
                                      CLB_PROTOCOLS,
                                      rax_argument_spec,
                                      rax_required_together,
                                      rax_to_dict,
                                      setup_rax_module,
                                      )


def cloud_load_balancer(module, state, name, meta, algorithm, port, protocol,
                        vip_type, timeout, wait, wait_timeout, vip_id):
    if int(timeout) < 30:
        module.fail_json(msg='"timeout" must be greater than or equal to 30')

    changed = False
    balancers = []

    clb = pyrax.cloud_loadbalancers
    if not clb:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    balancer_list = clb.list()
    while balancer_list:
        retrieved = clb.list(marker=balancer_list.pop().id)
        balancer_list.extend(retrieved)
        if len(retrieved) < 2:
            break

    for balancer in balancer_list:
        if name != balancer.name and name != balancer.id:
            continue

        balancers.append(balancer)

    if len(balancers) > 1:
        module.fail_json(msg='Multiple Load Balancers were matched by name, '
                             'try using the Load Balancer ID instead')

    if state == 'present':
        if isinstance(meta, dict):
            metadata = [dict(key=k, value=v) for k, v in meta.items()]

        if not balancers:
            try:
                virtual_ips = [clb.VirtualIP(type=vip_type, id=vip_id)]
                balancer = clb.create(name, metadata=metadata, port=port,
                                      algorithm=algorithm, protocol=protocol,
                                      timeout=timeout, virtual_ips=virtual_ips)
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)
        else:
            balancer = balancers[0]
            setattr(balancer, 'metadata',
                    [dict(key=k, value=v) for k, v in
                     balancer.get_metadata().items()])
            atts = {
                'name': name,
                'algorithm': algorithm,
                'port': port,
                'protocol': protocol,
                'timeout': timeout
            }
            for att, value in atts.items():
                current = getattr(balancer, att)
                if current != value:
                    changed = True

            if changed:
                balancer.update(**atts)

            if balancer.metadata != metadata:
                balancer.set_metadata(meta)
                changed = True

            virtual_ips = [clb.VirtualIP(type=vip_type)]
            current_vip_types = set([v.type for v in balancer.virtual_ips])
            vip_types = set([v.type for v in virtual_ips])
            if current_vip_types != vip_types:
                module.fail_json(msg='Load balancer Virtual IP type cannot '
                                     'be changed')

        if wait:
            attempts = wait_timeout // 5
            pyrax.utils.wait_for_build(balancer, interval=5, attempts=attempts)

        balancer.get()
        instance = rax_to_dict(balancer, 'clb')

        result = dict(changed=changed, balancer=instance)

        if balancer.status == 'ERROR':
            result['msg'] = '%s failed to build' % balancer.id
        elif wait and balancer.status not in ('ACTIVE', 'ERROR'):
            result['msg'] = 'Timeout waiting on %s' % balancer.id

        if 'msg' in result:
            module.fail_json(**result)
        else:
            module.exit_json(**result)

    elif state == 'absent':
        if balancers:
            balancer = balancers[0]
            try:
                balancer.delete()
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

            instance = rax_to_dict(balancer, 'clb')

            if wait:
                attempts = wait_timeout // 5
                pyrax.utils.wait_until(balancer, 'status', ('DELETED'),
                                       interval=5, attempts=attempts)
        else:
            instance = {}

    module.exit_json(changed=changed, balancer=instance)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            algorithm=dict(choices=CLB_ALGORITHMS,
                           default='LEAST_CONNECTIONS'),
            meta=dict(type='dict', default={}),
            name=dict(required=True),
            port=dict(type='int', default=80),
            protocol=dict(choices=CLB_PROTOCOLS, default='HTTP'),
            state=dict(default='present', choices=['present', 'absent']),
            timeout=dict(type='int', default=30),
            type=dict(choices=['PUBLIC', 'SERVICENET'], default='PUBLIC'),
            vip_id=dict(),
            wait=dict(type='bool'),
            wait_timeout=dict(default=300),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    algorithm = module.params.get('algorithm')
    meta = module.params.get('meta')
    name = module.params.get('name')
    port = module.params.get('port')
    protocol = module.params.get('protocol')
    state = module.params.get('state')
    timeout = int(module.params.get('timeout'))
    vip_id = module.params.get('vip_id')
    vip_type = module.params.get('type')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    setup_rax_module(module, pyrax)

    cloud_load_balancer(module, state, name, meta, algorithm, port, protocol,
                        vip_type, timeout, wait, wait_timeout, vip_id)


if __name__ == '__main__':
    main()
