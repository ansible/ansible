#!/usr/bin/python

# Copyright: (c) 2019, Kaarle Ritvanen <kaarle.ritvanen@datakunkku.fi>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: lbu

short_description: Local Backup Utility for Alpine Linux

version_added: "2.10"

description:
- Manage Local Backup Utility of Alpine Linux in run-from-RAM mode

options:
  commit:
    description:
    - Control whether to commit changed files.
    type: bool
  exclude:
    description:
    - List of paths to exclude.
    type: list
  include:
    description:
    - List of paths to include.
    type: list

author:
- Kaarle Ritvanen (@kunkku)
'''

EXAMPLES = '''
# Commit changed files (if any)
- name: Commit
  lbu:
    commit: true

# Exclude path and commit
- name: Exclude directory
  lbu:
    commit: true
    exclude:
    - /etc/opt

# Include paths without committing
- name: Include file and directory
  lbu:
    include:
    - /root/.ssh/authorized_keys
    - /var/lib/misc
'''

RETURN = '''
msg:
  description: Error message
  type: str
  returned: on failure
'''

from ansible.module_utils.basic import AnsibleModule

import os.path


def run_module():
    module = AnsibleModule(
        argument_spec={
            'commit': {'type': 'bool'},
            'exclude': {'type': 'list', 'elements': 'str'},
            'include': {'type': 'list', 'elements': 'str'}
        },
        supports_check_mode=True
    )

    changed = False

    def run_lbu(*args):
        code, stdout, stderr = module.run_command(
            [module.get_bin_path('lbu', required=True)] + list(args)
        )
        if code:
            module.fail_json(changed=changed, msg=stderr)
        return stdout

    update = False
    commit = False

    for param in ('include', 'exclude'):
        if module.params[param]:
            paths = run_lbu(param, '-l').split('\n')
            for path in module.params[param]:
                if os.path.normpath('/' + path)[1:] not in paths:
                    update = True

    if module.params['commit']:
        commit = update or run_lbu('status') > ''

    if module.check_mode:
        module.exit_json(changed=update or commit)

    if update:
        for param in ('include', 'exclude'):
            if module.params[param]:
                run_lbu(param, *module.params[param])
                changed = True

    if commit:
        run_lbu('commit')
        changed = True

    module.exit_json(changed=changed)


def main():
    run_module()


if __name__ == '__main__':
    main()
