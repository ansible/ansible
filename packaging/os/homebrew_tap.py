#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Daniel Jaouen <dcj24@cornell.edu>
# Based on homebrew (Andrew Dunham <andrew@du.nham.ca>)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import re

DOCUMENTATION = '''
---
module: homebrew_tap
author: Daniel Jaouen
short_description: Tap a Homebrew repository.
description:
    - Tap external Homebrew repositories.
version_added: "1.6"
options:
    tap:
        description:
            - The repository to tap.
        required: true
    state:
        description:
            - state of the repository.
        choices: [ 'present', 'absent' ]
        required: false
        default: 'present'
requirements: [ homebrew ]
'''

EXAMPLES = '''
homebrew_tap: tap=homebrew/dupes state=present
homebrew_tap: tap=homebrew/dupes state=absent
homebrew_tap: tap=homebrew/dupes,homebrew/science state=present
'''


def a_valid_tap(tap):
    '''Returns True if the tap is valid.'''
    regex = re.compile(r'^([\w-]+)/(homebrew-)?([\w-]+)$')
    return regex.match(tap)


def already_tapped(module, brew_path, tap):
    '''Returns True if already tapped.'''

    rc, out, err = module.run_command([
        brew_path,
        'tap',
    ])
    taps = [tap_.strip().lower() for tap_ in out.split('\n') if tap_]
    return tap.lower() in taps


def add_tap(module, brew_path, tap):
    '''Adds a single tap.'''
    failed, changed, msg = False, False, ''

    if not a_valid_tap(tap):
        failed = True
        msg = 'not a valid tap: %s' % tap

    elif not already_tapped(module, brew_path, tap):
        if module.check_mode:
            module.exit_json(changed=True)

        rc, out, err = module.run_command([
            brew_path,
            'tap',
            tap,
        ])
        if already_tapped(module, brew_path, tap):
            changed = True
            msg = 'successfully tapped: %s' % tap
        else:
            failed = True
            msg = 'failed to tap: %s' % tap

    else:
        msg = 'already tapped: %s' % tap

    return (failed, changed, msg)


def add_taps(module, brew_path, taps):
    '''Adds one or more taps.'''
    failed, unchanged, added, msg = False, 0, 0, ''

    for tap in taps:
        (failed, changed, msg) = add_tap(module, brew_path, tap)
        if failed:
            break
        if changed:
            added += 1
        else:
            unchanged += 1

    if failed:
        msg = 'added: %d, unchanged: %d, error: ' + msg
        msg = msg % (added, unchanged)
    elif added:
        changed = True
        msg = 'added: %d, unchanged: %d' % (added, unchanged)
    else:
        msg = 'added: %d, unchanged: %d' % (added, unchanged)

    return (failed, changed, msg)


def remove_tap(module, brew_path, tap):
    '''Removes a single tap.'''
    failed, changed, msg = False, False, ''

    if not a_valid_tap(tap):
        failed = True
        msg = 'not a valid tap: %s' % tap

    elif already_tapped(module, brew_path, tap):
        if module.check_mode:
            module.exit_json(changed=True)

        rc, out, err = module.run_command([
            brew_path,
            'untap',
            tap,
        ])
        if not already_tapped(module, brew_path, tap):
            changed = True
            msg = 'successfully untapped: %s' % tap
        else:
            failed = True
            msg = 'failed to untap: %s' % tap

    else:
        msg = 'already untapped: %s' % tap

    return (failed, changed, msg)


def remove_taps(module, brew_path, taps):
    '''Removes one or more taps.'''
    failed, unchanged, removed, msg = False, 0, 0, ''

    for tap in taps:
        (failed, changed, msg) = remove_tap(module, brew_path, tap)
        if failed:
            break
        if changed:
            removed += 1
        else:
            unchanged += 1

    if failed:
        msg = 'removed: %d, unchanged: %d, error: ' + msg
        msg = msg % (removed, unchanged)
    elif removed:
        changed = True
        msg = 'removed: %d, unchanged: %d' % (removed, unchanged)
    else:
        msg = 'removed: %d, unchanged: %d' % (removed, unchanged)

    return (failed, changed, msg)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=['tap'], required=True),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True,
    )

    brew_path = module.get_bin_path(
        'brew',
        required=True,
        opt_dirs=['/usr/local/bin']
    )

    taps = module.params['name'].split(',')

    if module.params['state'] == 'present':
        failed, changed, msg = add_taps(module, brew_path, taps)

        if failed:
            module.fail_json(msg=msg)
        else:
            module.exit_json(changed=changed, msg=msg)

    elif module.params['state'] == 'absent':
        failed, changed, msg = remove_taps(module, brew_path, taps)

        if failed:
            module.fail_json(msg=msg)
        else:
            module.exit_json(changed=changed, msg=msg)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
