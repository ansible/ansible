#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014 Peter Oliver <ansible@mavit.org.uk>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: pkg5_publisher
author: "Peter Oliver (@mavit)"
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
- pkg5_publisher:
    name: solaris
    sticky: true
    origin: https://pkg.oracle.com/solaris/support/

# Configure a publisher for locally-produced packages:
- pkg5_publisher:
    name: site
    origin: 'https://pkg.example.com/site/'
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, aliases=['publisher']),
            state=dict(default='present', choices=['present', 'absent']),
            sticky=dict(type='bool'),
            enabled=dict(type='bool'),
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
            if params[option] is not None:
                if params[option] != existing[name][option]:
                    return set_publisher(module, params)
    else:
        return set_publisher(module, params)

    module.exit_json()


def set_publisher(module, params):
    name = params['name']
    args = []

    if params['origin'] is not None:
        args.append('--remove-origin=*')
        args.extend(['--add-origin=' + u for u in params['origin']])
    if params['mirror'] is not None:
        args.append('--remove-mirror=*')
        args.extend(['--add-mirror=' + u for u in params['mirror']])

    if params['sticky'] is not None and params['sticky']:
        args.append('--sticky')
    elif params['sticky'] is not None:
        args.append('--non-sticky')

    if params['enabled'] is not None and params['enabled']:
        args.append('--enable')
    elif params['enabled'] is not None:
        args.append('--disable')

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
    if rc != 0:
        module.fail_json(**response)
    module.exit_json(**response)


def unset_publisher(module, publisher):
    if publisher not in get_publishers(module):
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
    if rc != 0:
        module.fail_json(**response)
    module.exit_json(**response)


def get_publishers(module):
    rc, out, err = module.run_command(["pkg", "publisher", "-Ftsv"], True)

    lines = out.splitlines()
    keys = lines.pop(0).lower().split("\t")

    publishers = {}
    for line in lines:
        values = dict(zip(keys, map(unstringify, line.split("\t"))))
        name = values['publisher']

        if name not in publishers:
            publishers[name] = dict(
                (k, values[k]) for k in ['sticky', 'enabled']
            )
            publishers[name]['origin'] = []
            publishers[name]['mirror'] = []

        if values['type'] is not None:
            publishers[name][values['type']].append(values['uri'])

    return publishers


def unstringify(val):
    if val == "-" or val == '':
        return None
    if val in ["true", "false"]:
        return val == 'true'
    return val


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
