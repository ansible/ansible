#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Michael Scherer <misc@zarb.org>
# inspired by code of github.com/dandiker/
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: selinux_permissive
short_description: Change permissive domain in SELinux policy
description:
  - Add and remove a domain from the list of permissive domains.
version_added: "2.0"
options:
  domain:
    description:
        - The domain that will be added or removed from the list of permissive domains.
    type: str
    required: true
    default: ''
    aliases: [ name ]
  permissive:
    description:
        - Indicate if the domain should or should not be set as permissive.
    type: bool
    required: true
  no_reload:
    description:
        - Disable reloading of the SELinux policy after making change to a domain's permissive setting.
        - The default is C(no), which causes policy to be reloaded when a domain changes state.
        - Reloading the policy does not work on older versions of the C(policycoreutils-python) library, for example in EL 6."
    type: bool
    default: no
  store:
    description:
      - Name of the SELinux policy store to use.
    type: str
notes:
    - Requires a recent version of SELinux and C(policycoreutils-python) (EL 6 or newer).
requirements: [ policycoreutils-python ]
author:
- Michael Scherer (@mscherer) <misc@zarb.org>
'''

EXAMPLES = r'''
- name: Change the httpd_t domain to permissive
  selinux_permissive:
    name: httpd_t
    permissive: true
'''

import traceback

HAVE_SEOBJECT = False
SEOBJECT_IMP_ERR = None
try:
    import seobject
    HAVE_SEOBJECT = True
except ImportError:
    SEOBJECT_IMP_ERR = traceback.format_exc()

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(type='str', required=True, aliases=['name']),
            store=dict(type='str', default=''),
            permissive=dict(type='bool', required=True),
            no_reload=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
    )

    # global vars
    changed = False
    store = module.params['store']
    permissive = module.params['permissive']
    domain = module.params['domain']
    no_reload = module.params['no_reload']

    if not HAVE_SEOBJECT:
        module.fail_json(changed=False, msg=missing_required_lib("policycoreutils-python"),
                         exception=SEOBJECT_IMP_ERR)

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
