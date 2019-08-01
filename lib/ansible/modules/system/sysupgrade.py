#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Johnathan C. Maudlin <jcmdln@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: sysupgrade
short_description: Upgrade OpenBSD to the next release or snapshot
version_added: "2.9"

description:
    - Use the sysupgrade(8) utility to upgrade a system to the next
      release or the latest snapshot for OpenBSD 6.6 or later.

options:
    upgrade:
        description:
            - Upgrade to the next release or latest snapshot.
        type: bool
        default: false
        required: true
    force:
        description:
            - Force an already applied upgrade.  This option has no
              effect on releases.
        type: bool
        default: false
        required: false
    keep:
        description:
            - Keep the files in /home/_sysupgrade
        type: bool
        default: false
        required: false

author:
    - Johnathan C Maudlin (@jcmdln)
'''

EXAMPLES = '''
- name: Upgrade to latest release or snapshot
  when:
    - ansible_distribution == 'OpenBSD'
    - ansible_distribution_version >= '6.5' and ansible_distribution_release == 'current' or
      ansible_distribution_version >= '6.6'
  register: result
  sysupgrade:
    upgrade: yes

- name: Reboot if upgrade performed
  when:
    - 'result is succeeded'
    - result.changed == true
  reboot:
'''

RETURN = '''
changed:
    description: A change on the host was reported
    returned: always
    type: bool
command:
    description: The command and arguments that were used
    returned: always
    type: str
msg:
    description: The message returned by the command
    returned: always
    type: str
rc:
    description: The command return code (0 means success)
    returned: always
    type: int
stderr:
    description: sysupgrade standard error
    returned: always
    type: str
stdout:
    description: sysupgrade standard output
    returned: always
    type: str
'''

from ansible.module_utils.basic import AnsibleModule


def upgrade(module, force, keep):
    cmd = "/usr/sbin/sysupgrade -n"

    if force:
        cmd = "%s -f" % (cmd)
    if keep:
        cmd = "%s -k" % (cmd)

    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc != 0:
        changed = False
        msg = "received a non-zero exit code"
        module.fail_json(
            changed=changed, command=cmd, msg=msg,
            rc=rc, stderr=stderr, stdout=stdout
        )

    if 'Already on latest' in stdout:
        changed = False
        msg = "no action required"
    else:
        if 'Will upgrade on next reboot' in stdout:
            changed = True
            msg = "Upgrade prepared successfully"
        else:
            changed = True
            msg = "something isn't right"
            module.fail_json(
                changed=changed, command=cmd, msg=msg,
                rc=rc, stderr=stderr, stdout=stdout
            )

    module.exit_json(
        changed=changed, command=cmd, msg=msg,
        rc=rc, stderr=stderr, stdout=stdout
    )


def main():
    module = AnsibleModule(
        argument_spec={
            'upgrade': {
                'type': 'bool',
                'required': True,
            },
            'force': {
                'type': 'bool',
                'default': False,
            },
            'keep': {
                'type': 'bool',
                'default': False,
            },
        },

        supports_check_mode=True
    )

    p = module.params

    if p['upgrade'] in ['yes', True]:
        p['upgrade'] = True

        if p['force'] in ['yes', True]:
            p['force'] = True
        if p['keep'] in ['yes', True]:
            p['keep'] = True

        upgrade(module, p['force'], p['keep'])

    msg = "no suitable actions given"
    module.fail_json(changed=False, msg=msg, param=p)


if __name__ == '__main__':
    main()
