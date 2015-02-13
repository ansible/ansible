#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014 Peter Oliver <ansible@mavit.org.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: pkg5_publisher
author: Peter Oliver
short_description: Manages Solaris 11 Image Packaging System publishers
version_added: 1.9
description:
  - IPS packages are the native packages in Solaris 11 and higher.
  - This modules will configure which publishers a client will download IPS
    packages from.
options:
  name:
    description:
      - The publisher's name.
    required: true
    aliases: [ publisher ]
  state:
    description:
      - Whether to ensure that a publisher is present or absent.
    required: false
    default: present
    choices: [ present, absent ]
  sticky:
    description:
      - Packages installed from a sticky repository can only receive updates
        from that repository.
    required: false
    default: null
    choices: [ true, false ]
  enabled:
    description:
      - Is the repository enabled or disabled?
    required: false
    default: null
    choices: [ true, false ]
  origin:
    description:
      - A path or URL to the repository.
      - Multiple values may be provided.
    required: false
    default: null
  mirror:
    description:
      - A path or URL to the repository mirror.
      - Multiple values may be provided.
    required: false
    default: null
'''
EXAMPLES = '''
# Fetch packages for the solaris publisher direct from Oracle:
- pkg5_publisher: name=solaris sticky=true origin=https://pkg.oracle.com/solaris/support/

# Configure a publisher for locally-produced packages:
- pkg5_publisher: name=site origin=https://pkg.example.com/site/
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, aliases=['publisher']),
            state=dict(default='present', choices=['present', 'absent']),
            sticky=dict(choices=BOOLEANS),
            enabled=dict(choices=BOOLEANS),
            # search_after=dict(),
            # search_before=dict(),
            origin=dict(type='list'),
            mirror=dict(type='list'),
        )
    )

    for option in ['origin', 'mirror']:
        if module.params[option] == ['']:
            module.params[option] = []

    if module.params['state'] == 'present':
        modify_publisher(module, module.params)
    else:
        unset_publisher(module, module.params['name'])


def modify_publisher(module, params):
    name = params['name']
    existing = get_publishers(module)

    if name in existing:
        for option in ['origin', 'mirror', 'sticky', 'enabled']:
            if params[option] != None:
                if params[option] != existing[name][option]:
                    return set_publisher(module, params)
    else:
        return set_publisher(module, params)

    module.exit_json()


def set_publisher(module, params):
    name = params['name']
    args = []

    if params['origin'] != None:
        args.append('--remove-origin=*')
        args.extend(['--add-origin=' + u for u in params['origin']])
    if params['mirror'] != None:
        args.append('--remove-mirror=*')
        args.extend(['--add-mirror=' + u for u in params['mirror']])

    if params['sticky'] != None:
        args.append('--sticky' if params['sticky'] else '--non-sticky')
    if params['enabled'] != None:
        args.append('--enable' if params['enabled'] else '--disable')

    rc, out, err = module.run_command(
        ["pkg", "set-publisher"] + args + [name],
        check_rc=True
    )
    response = {
        'rc': rc,
        'results': [out],
        'msg': err,
        'changed': True,
    }
    module.exit_json(**response)


def unset_publisher(module, publisher):
    if not publisher in get_publishers(module):
        module.exit_json()

    rc, out, err = module.run_command(
        ["pkg", "unset-publisher", publisher],
        check_rc=True
    )
    response = {
        'rc': rc,
        'results': [out],
        'msg': err,
        'changed': True,
    }
    module.exit_json(**response)


def get_publishers(module):
    rc, out, err = module.run_command(["pkg", "publisher", "-Ftsv"], True)

    lines = out.splitlines()
    keys = lines.pop(0).lower().split("\t")

    publishers = {}
    for line in lines:
        values = dict(zip(keys, map(unstringify, line.split("\t"))))
        name = values['publisher']

        if not name in publishers:
            publishers[name] = dict(
                (k, values[k]) for k in ['sticky', 'enabled']
            )
            publishers[name]['origin'] = []
            publishers[name]['mirror'] = []

        publishers[name][values['type']].append(values['uri'])

    return publishers


def unstringify(val):
    if val == "-":
        return None
    elif val == "true":
        return True
    elif val == "false":
        return False
    else:
        return val


from ansible.module_utils.basic import *
main()
