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
module: rax_dns_record
short_description: Manage DNS records on Rackspace Cloud DNS
description:
     - Manage DNS records on Rackspace Cloud DNS
version_added: 1.5
options:
  comment:
    description:
      - Brief description of the domain. Maximum length of 160 characters
  data:
    description:
      - IP address for A/AAAA record, FQDN for CNAME/MX/NS, or text data for
        SRV/TXT
    required: True
  domain:
    description:
      - Domain name to create the record in. This is an invalid option when
        type=PTR
  loadbalancer:
    description:
      - Load Balancer ID to create a PTR record for. Only used with type=PTR
    version_added: 1.7
  name:
    description:
      - FQDN record name to create
    required: True
  overwrite:
    description:
      - Add new records if data doesn't match, instead of updating existing
        record with matching name. If there are already multiple records with
        matching name and overwrite=true, this module will fail.
    default: true
    version_added: 2.1
  priority:
    description:
      - Required for MX and SRV records, but forbidden for other record types.
        If specified, must be an integer from 0 to 65535.
  server:
    description:
      - Server ID to create a PTR record for. Only used with type=PTR
    version_added: 1.7
  state:
    description:
      - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
  ttl:
    description:
      - Time to live of record in seconds
    default: 3600
  type:
    description:
      - DNS record type
    choices:
      - A
      - AAAA
      - CNAME
      - MX
      - NS
      - SRV
      - TXT
      - PTR
    required: true
notes:
  - "It is recommended that plays utilizing this module be run with
    C(serial: 1) to avoid exceeding the API request limit imposed by
    the Rackspace CloudDNS API"
  - To manipulate a C(PTR) record either C(loadbalancer) or C(server) must be
    supplied
  - As of version 1.7, the C(type) field is required and no longer defaults to an C(A) record.
  - C(PTR) record support was added in version 1.7
author: "Matt Martz (@sivel)"
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
- name: Create DNS Records
  hosts: all
  gather_facts: False
  tasks:
    - name: Create A record
      local_action:
        module: rax_dns_record
        credentials: ~/.raxpub
        domain: example.org
        name: www.example.org
        data: "{{ rax_accessipv4 }}"
        type: A
      register: a_record

    - name: Create PTR record
      local_action:
        module: rax_dns_record
        credentials: ~/.raxpub
        server: "{{ rax_id }}"
        name: "{{ inventory_hostname }}"
        region: DFW
      register: ptr_record
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import (rax_argument_spec,
                                      rax_find_loadbalancer,
                                      rax_find_server,
                                      rax_required_together,
                                      rax_to_dict,
                                      setup_rax_module,
                                      )


def rax_dns_record_ptr(module, data=None, comment=None, loadbalancer=None,
                       name=None, server=None, state='present', ttl=7200):
    changed = False
    results = []

    dns = pyrax.cloud_dns

    if not dns:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    if loadbalancer:
        item = rax_find_loadbalancer(module, pyrax, loadbalancer)
    elif server:
        item = rax_find_server(module, pyrax, server)

    if state == 'present':
        current = dns.list_ptr_records(item)
        for record in current:
            if record.data == data:
                if record.ttl != ttl or record.name != name:
                    try:
                        dns.update_ptr_record(item, record, name, data, ttl)
                        changed = True
                    except Exception as e:
                        module.fail_json(msg='%s' % e.message)
                    record.ttl = ttl
                    record.name = name
                    results.append(rax_to_dict(record))
                    break
                else:
                    results.append(rax_to_dict(record))
                    break

        if not results:
            record = dict(name=name, type='PTR', data=data, ttl=ttl,
                          comment=comment)
            try:
                results = dns.add_ptr_records(item, [record])
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

        module.exit_json(changed=changed, records=results)

    elif state == 'absent':
        current = dns.list_ptr_records(item)
        for record in current:
            if record.data == data:
                results.append(rax_to_dict(record))
                break

        if results:
            try:
                dns.delete_ptr_records(item, data)
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

        module.exit_json(changed=changed, records=results)


def rax_dns_record(module, comment=None, data=None, domain=None, name=None,
                   overwrite=True, priority=None, record_type='A',
                   state='present', ttl=7200):
    """Function for manipulating record types other than PTR"""

    changed = False

    dns = pyrax.cloud_dns
    if not dns:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    if state == 'present':
        if not priority and record_type in ['MX', 'SRV']:
            module.fail_json(msg='A "priority" attribute is required for '
                                 'creating a MX or SRV record')

        try:
            domain = dns.find(name=domain)
        except Exception as e:
            module.fail_json(msg='%s' % e.message)

        try:
            if overwrite:
                record = domain.find_record(record_type, name=name)
            else:
                record = domain.find_record(record_type, name=name, data=data)
        except pyrax.exceptions.DomainRecordNotUnique as e:
            module.fail_json(msg='overwrite=true and there are multiple matching records')
        except pyrax.exceptions.DomainRecordNotFound as e:
            try:
                record_data = {
                    'type': record_type,
                    'name': name,
                    'data': data,
                    'ttl': ttl
                }
                if comment:
                    record_data.update(dict(comment=comment))
                if priority and record_type.upper() in ['MX', 'SRV']:
                    record_data.update(dict(priority=priority))

                record = domain.add_records([record_data])[0]
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

        update = {}
        if comment != getattr(record, 'comment', None):
            update['comment'] = comment
        if ttl != getattr(record, 'ttl', None):
            update['ttl'] = ttl
        if priority != getattr(record, 'priority', None):
            update['priority'] = priority
        if data != getattr(record, 'data', None):
            update['data'] = data

        if update:
            try:
                record.update(**update)
                changed = True
                record.get()
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

    elif state == 'absent':
        try:
            domain = dns.find(name=domain)
        except Exception as e:
            module.fail_json(msg='%s' % e.message)

        try:
            record = domain.find_record(record_type, name=name, data=data)
        except pyrax.exceptions.DomainRecordNotFound as e:
            record = {}
        except pyrax.exceptions.DomainRecordNotUnique as e:
            module.fail_json(msg='%s' % e.message)

        if record:
            try:
                record.delete()
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

    module.exit_json(changed=changed, record=rax_to_dict(record))


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            comment=dict(),
            data=dict(required=True),
            domain=dict(),
            loadbalancer=dict(),
            name=dict(required=True),
            overwrite=dict(type='bool', default=True),
            priority=dict(type='int'),
            server=dict(),
            state=dict(default='present', choices=['present', 'absent']),
            ttl=dict(type='int', default=3600),
            type=dict(required=True, choices=['A', 'AAAA', 'CNAME', 'MX', 'NS',
                                              'SRV', 'TXT', 'PTR'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
        mutually_exclusive=[
            ['server', 'loadbalancer', 'domain'],
        ],
        required_one_of=[
            ['server', 'loadbalancer', 'domain'],
        ],
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    comment = module.params.get('comment')
    data = module.params.get('data')
    domain = module.params.get('domain')
    loadbalancer = module.params.get('loadbalancer')
    name = module.params.get('name')
    overwrite = module.params.get('overwrite')
    priority = module.params.get('priority')
    server = module.params.get('server')
    state = module.params.get('state')
    ttl = module.params.get('ttl')
    record_type = module.params.get('type')

    setup_rax_module(module, pyrax, False)

    if record_type.upper() == 'PTR':
        if not server and not loadbalancer:
            module.fail_json(msg='one of the following is required: '
                                 'server,loadbalancer')
        rax_dns_record_ptr(module, data=data, comment=comment,
                           loadbalancer=loadbalancer, name=name, server=server,
                           state=state, ttl=ttl)
    else:
        rax_dns_record(module, comment=comment, data=data, domain=domain,
                       name=name, overwrite=overwrite, priority=priority,
                       record_type=record_type, state=state, ttl=ttl)


if __name__ == '__main__':
    main()
