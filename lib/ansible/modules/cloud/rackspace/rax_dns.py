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
module: rax_dns
short_description: Manage domains on Rackspace Cloud DNS
description:
     - Manage domains on Rackspace Cloud DNS
version_added: 1.5
options:
  comment:
    description:
      - Brief description of the domain. Maximum length of 160 characters
  email:
    description:
      - Email address of the domain administrator
  name:
    description:
      - Domain name to create
  state:
    description:
      - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
  ttl:
    description:
      - Time to live of domain in seconds
    default: 3600
notes:
  - "It is recommended that plays utilizing this module be run with
    C(serial: 1) to avoid exceeding the API request limit imposed by
    the Rackspace CloudDNS API"
author: "Matt Martz (@sivel)"
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
- name: Create domain
  hosts: all
  gather_facts: False
  tasks:
    - name: Domain create request
      local_action:
        module: rax_dns
        credentials: ~/.raxpub
        name: example.org
        email: admin@example.org
      register: rax_dns
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import (rax_argument_spec,
                                      rax_required_together,
                                      rax_to_dict,
                                      setup_rax_module,
                                      )


def rax_dns(module, comment, email, name, state, ttl):
    changed = False

    dns = pyrax.cloud_dns
    if not dns:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    if state == 'present':
        if not email:
            module.fail_json(msg='An "email" attribute is required for '
                                 'creating a domain')

        try:
            domain = dns.find(name=name)
        except pyrax.exceptions.NoUniqueMatch as e:
            module.fail_json(msg='%s' % e.message)
        except pyrax.exceptions.NotFound:
            try:
                domain = dns.create(name=name, emailAddress=email, ttl=ttl,
                                    comment=comment)
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

        update = {}
        if comment != getattr(domain, 'comment', None):
            update['comment'] = comment
        if ttl != getattr(domain, 'ttl', None):
            update['ttl'] = ttl
        if email != getattr(domain, 'emailAddress', None):
            update['emailAddress'] = email

        if update:
            try:
                domain.update(**update)
                changed = True
                domain.get()
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

    elif state == 'absent':
        try:
            domain = dns.find(name=name)
        except pyrax.exceptions.NotFound:
            domain = {}
        except Exception as e:
            module.fail_json(msg='%s' % e.message)

        if domain:
            try:
                domain.delete()
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

    module.exit_json(changed=changed, domain=rax_to_dict(domain))


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            comment=dict(),
            email=dict(),
            name=dict(),
            state=dict(default='present', choices=['present', 'absent']),
            ttl=dict(type='int', default=3600),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    comment = module.params.get('comment')
    email = module.params.get('email')
    name = module.params.get('name')
    state = module.params.get('state')
    ttl = module.params.get('ttl')

    setup_rax_module(module, pyrax, False)

    rax_dns(module, comment, email, name, state, ttl)


if __name__ == '__main__':
    main()
