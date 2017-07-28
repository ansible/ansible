#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Michael Scherer <misc@zarb.org>
# inspired by code of github.com/dandiker/
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: selinux_permissive
short_description: Change permissive domain in SELinux policy
description:
  - Add and remove domain from the list of permissive domain.
version_added: "2.0"
options:
  domain:
    description:
        - "the domain that will be added or removed from the list of permissive domains"
    required: true
  permissive:
    description:
        - "indicate if the domain should or should not be set as permissive"
    required: true
    choices: [ 'True', 'False' ]
  no_reload:
    description:
        - "automatically reload the policy after a change"
        - "default is set to 'false' as that's what most people would want after changing one domain"
        - "Note that this doesn't work on older version of the library (example EL 6), the module will silently ignore it in this case"
    required: false
    default: False
    choices: [ 'True', 'False' ]
  store:
    description:
      - "name of the SELinux policy store to use"
    required: false
    default: null
notes:
    - Requires a version of SELinux recent enough ( ie EL 6 or newer )
requirements: [ policycoreutils-python ]
author: Michael Scherer <misc@zarb.org>
'''

EXAMPLES = '''
- selinux_permissive:
    name: httpd_t
    permissive: true
'''

import traceback

HAVE_SEOBJECT = False
try:
    import seobject
    HAVE_SEOBJECT = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(aliases=['name'], required=True),
            store=dict(required=False, default=''),
            permissive=dict(type='bool', required=True),
            no_reload=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=True
    )

    # global vars
    changed = False
    store = module.params['store']
    permissive = module.params['permissive']
    domain = module.params['domain']
    no_reload = module.params['no_reload']

    if not HAVE_SEOBJECT:
        module.fail_json(changed=False, msg="policycoreutils-python required for this module")

    try:
        permissive_domains = seobject.permissiveRecords(store)
    except ValueError as e:
        module.fail_json(domain=domain, msg=to_native(e), exception=traceback.format_exc())

    # not supported on EL 6
    if 'set_reload' in dir(permissive_domains):
        permissive_domains.set_reload(not no_reload)

    try:
        all_domains = permissive_domains.get_all()
    except ValueError as e:
        module.fail_json(domain=domain, msg=to_native(e), exception=traceback.format_exc())

    if permissive:
        if domain not in all_domains:
            if not module.check_mode:
                try:
                    permissive_domains.add(domain)
                except ValueError as e:
                    module.fail_json(domain=domain, msg=to_native(e), exception=traceback.format_exc())
            changed = True
    else:
        if domain in all_domains:
            if not module.check_mode:
                try:
                    permissive_domains.delete(domain)
                except ValueError as e:
                    module.fail_json(domain=domain, msg=to_native(e), exception=traceback.format_exc())
            changed = True

    module.exit_json(changed=changed, store=store,
                     permissive=permissive, domain=domain)


if __name__ == '__main__':
    main()
