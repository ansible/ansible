#!/usr/bin/python

# (c) 2018, Sean Myers <sean.myers@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: rhsm_release
short_description: Set or Unset RHSM Release version
version_added: '2.8'
description:
  - Sets or unsets the release version used by RHSM repositories.
notes:
  - This module will fail on an unregistered system.
    Use the C(redhat_subscription) module to register a system
    prior to setting the RHSM release.
requirements:
  - Red Hat Enterprise Linux 6+ with subscription-manager installed
options:
  release:
    description:
      - RHSM release version to use (use null to unset)
    required: true
author:
  - Sean Myers (@seandst)
'''

EXAMPLES = '''
# Set release version to 7.1
- name: Set RHSM release version
  rhsm_release:
      release: "7.1"

# Set release version to 6Server
- name: Set RHSM release version
  rhsm_release:
      release: "6Server"

# Unset release version
- name: Unset RHSM release release
  rhsm_release:
      release: null
'''

RETURN = '''
current_release:
  description: The current RHSM release version value
  returned: success
  type: str
'''

from ansible.module_utils.basic import AnsibleModule

import re

# Matches release-like values such as 7.2, 6.10, 10Server,
# but rejects unlikely values, like 100Server, 100.0, 1.100, etc.
release_matcher = re.compile(r'\b\d{1,2}(?:\.\d{1,2}|Server)\b')


def _sm_release(module, *args):
    # pass args to s-m release, e.g. _sm_release(module, '--set', '0.1') becomes
    # "subscription-manager release --set 0.1"
    sm_bin = module.get_bin_path('subscription-manager', required=True)
    cmd = '{0} release {1}'.format(sm_bin, " ".join(args))
    # delegate nonzero rc handling to run_command
    return module.run_command(cmd, check_rc=True)


def get_release(module):
    # Get the current release version, or None if release unset
    rc, out, err = _sm_release(module, '--show')
    try:
        match = release_matcher.findall(out)[0]
    except IndexError:
        # 0'th index did not exist; no matches
        match = None

    return match


def set_release(module, release):
    # Set current release version, or unset if release is None
    if release is None:
        args = ('--unset',)
    else:
        args = ('--set', release)

    return _sm_release(module, *args)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            release=dict(type='str', required=True),
        ),
        supports_check_mode=True
    )

    target_release = module.params['release']

    # sanity check: the target release at least looks like a valid release
    if target_release and not release_matcher.findall(target_release):
        module.fail_json(msg='"{0}" does not appear to be a valid release.'.format(target_release))

    # Will fail with useful error from s-m if system not subscribed
    current_release = get_release(module)

    changed = (target_release != current_release)
    if not module.check_mode and changed:
        set_release(module, target_release)
        # If setting the release fails, then a fail_json would have exited with
        # the s-m error, e.g. "No releases match '7.20'...".  If not, then the
        # current release is now set to the target release (job's done)
        current_release = target_release

    module.exit_json(current_release=current_release, changed=changed)


if __name__ == '__main__':
    main()
