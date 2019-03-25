#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Derek Carter<goozbach@friocorte.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['stableinterface'],
    'supported_by': 'core'
}

DOCUMENTATION = r'''
---
module: selinux
short_description: Change policy and state of SELinux
description:
  - Configures the SELinux mode and policy.
  - A reboot may be required after usage.
  - Ansible will not issue this reboot but will let you know when it is required.
version_added: "0.7"
options:
  policy:
    description:
      - The name of the SELinux policy to use (e.g. C(targeted)) will be required if state is not C(disabled).
  state:
    description:
      - The SELinux mode.
    required: true
    choices: [ disabled, enforcing, permissive ]
  configfile:
    description:
      - The path to the SELinux configuration file, if non-standard.
    default: /etc/selinux/config
    aliases: [ conf, file ]
requirements: [ libselinux-python ]
author:
- Derek Carter (@goozbach) <goozbach@friocorte.com>
'''

EXAMPLES = r'''
- name: Enable SELinux
  selinux:
    policy: targeted
    state: enforcing

- name: Put SELinux in permissive mode, logging actions that would be blocked.
  selinux:
    policy: targeted
    state: permissive

- name: Disable SELinux
  selinux:
    state: disabled
'''

RETURN = r'''
msg:
    description: Messages that describe changes that were made.
    returned: always
    type: str
    sample: Config SELinux state changed from 'disabled' to 'permissive'
configfile:
    description: Path to SELinux configuration file.
    returned: always
    type: str
    sample: /etc/selinux/config
policy:
    description: Name of the SELinux policy.
    returned: always
    type: str
    sample: targeted
state:
    description: SELinux mode.
    returned: always
    type: str
    sample: enforcing
reboot_required:
    description: Whether or not an reboot is required for the changes to take effect.
    returned: always
    type: bool
    sample: true
'''

import os
import re
import tempfile
import traceback

SELINUX_IMP_ERR = None
try:
    import selinux
    HAS_SELINUX = True
except ImportError:
    SELINUX_IMP_ERR = traceback.format_exc()
    HAS_SELINUX = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.facts.utils import get_file_lines


# getter subroutines
def get_config_state(configfile):
    lines = get_file_lines(configfile, strip=False)

    for line in lines:
        stateline = re.match(r'^SELINUX=.*$', line)
        if stateline:
            return line.split('=')[1].strip()


def get_config_policy(configfile):
    lines = get_file_lines(configfile, strip=False)

    for line in lines:
        stateline = re.match(r'^SELINUXTYPE=.*$', line)
        if stateline:
            return line.split('=')[1].strip()


# setter subroutines
def set_config_state(module, state, configfile):
    # SELINUX=permissive
    # edit config file with state value
    stateline = 'SELINUX=%s' % state
    lines = get_file_lines(configfile, strip=False)

    tmpfd, tmpfile = tempfile.mkstemp()

    with open(tmpfile, "w") as write_file:
        for line in lines:
            write_file.write(re.sub(r'^SELINUX=.*', stateline, line) + '\n')

    module.atomic_move(tmpfile, configfile)


def set_state(module, state):
    if state == 'enforcing':
        selinux.security_setenforce(1)
    elif state == 'permissive':
        selinux.security_setenforce(0)
    elif state == 'disabled':
        pass
    else:
        msg = 'trying to set invalid runtime state %s' % state
        module.fail_json(msg=msg)


def set_config_policy(module, policy, configfile):
    if not os.path.exists('/etc/selinux/%s/policy' % policy):
        module.fail_json(msg='Policy %s does not exist in /etc/selinux/' % policy)

    # edit config file with state value
    # SELINUXTYPE=targeted
    policyline = 'SELINUXTYPE=%s' % policy
    lines = get_file_lines(configfile, strip=False)

    tmpfd, tmpfile = tempfile.mkstemp()

    with open(tmpfile, "w") as write_file:
        for line in lines:
            write_file.write(re.sub(r'^SELINUXTYPE=.*', policyline, line) + '\n')

    module.atomic_move(tmpfile, configfile)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            policy=dict(type='str'),
            state=dict(type='str', required='True', choices=['enforcing', 'permissive', 'disabled']),
            configfile=dict(type='str', default='/etc/selinux/config', aliases=['conf', 'file']),
        ),
        supports_check_mode=True,
    )

    if not HAS_SELINUX:
        module.fail_json(msg=missing_required_lib('libselinux-python'), exception=SELINUX_IMP_ERR)

    # global vars
    changed = False
    msgs = []
    configfile = module.params['configfile']
    policy = module.params['policy']
    state = module.params['state']
    runtime_enabled = selinux.is_selinux_enabled()
    runtime_policy = selinux.selinux_getpolicytype()[1]
    runtime_state = 'disabled'
    reboot_required = False

    if runtime_enabled:
        # enabled means 'enforcing' or 'permissive'
        if selinux.security_getenforce():
            runtime_state = 'enforcing'
        else:
            runtime_state = 'permissive'

    if not os.path.isfile(configfile):
        module.fail_json(msg="Unable to find file {0}".format(configfile),
                         details="Please install SELinux-policy package, "
                                 "if this package is not installed previously.")

    config_policy = get_config_policy(configfile)
    config_state = get_config_state(configfile)

    # check to see if policy is set if state is not 'disabled'
    if state != 'disabled':
        if not policy:
            module.fail_json(msg="Policy is required if state is not 'disabled'")
    else:
        if not policy:
            policy = config_policy

    # check changed values and run changes
    if policy != runtime_policy:
        if module.check_mode:
            module.exit_json(changed=True)
        # cannot change runtime policy
        msgs.append("Running SELinux policy changed from '%s' to '%s'" % (runtime_policy, policy))
        changed = True

    if policy != config_policy:
        if module.check_mode:
            module.exit_json(changed=True)
        set_config_policy(module, policy, configfile)
        msgs.append("SELinux policy configuration in '%s' changed from '%s' to '%s'" % (configfile, config_policy, policy))
        changed = True

    if state != runtime_state:
        if runtime_enabled:
            if state == 'disabled':
                if runtime_state != 'permissive':
                    # Temporarily set state to permissive
                    if not module.check_mode:
                        set_state(module, 'permissive')
                    module.warn("SELinux state temporarily changed from '%s' to 'permissive'. State change will take effect next reboot." % (runtime_state))
                    changed = True
                else:
                    module.warn('SELinux state change will take effect next reboot')
                reboot_required = True
            else:
                if not module.check_mode:
                    set_state(module, state)
                msgs.append("SELinux state changed from '%s' to '%s'" % (runtime_state, state))

                # Only report changes if the file is changed.
                # This prevents the task from reporting changes every time the task is run.
                changed = True
        else:
            module.warn("Reboot is required to set SELinux state to '%s'" % state)
            reboot_required = True

    if state != config_state:
        if not module.check_mode:
            set_config_state(module, state, configfile)
        msgs.append("Config SELinux state changed from '%s' to '%s'" % (config_state, state))
        changed = True

    module.exit_json(changed=changed, msg=', '.join(msgs), configfile=configfile, policy=policy, state=state, reboot_required=reboot_required)


if __name__ == '__main__':
    main()
