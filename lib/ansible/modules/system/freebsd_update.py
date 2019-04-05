#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Brian Coca <rusik@4ege.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: freebsd_update
short_description: A wrapper to the freebsd-update utility
description:
     - Runs freebsd-update utility and updates freebsd system.
version_added: "2.8"
options:
    action:
        description:
            - freebsd-update command to execute: fetch, install, fetch_install, rollback, IDS, cron.
        required: True
    server:
        description:
            - Server to download updates from.
    basedir:
        description:
            - path to filesystem to update.
    workdir:
        description:
            - directory to store working files in.
    conffile:
        description:
            - file to read configuration options from
    force:
        description:
            - force freebsd-update run
        type: bool
        default: False
    key:
        description:
            - trust an RSA key with SHA256 of KEY
author:
- "Ruslan Gustomiasov (@loqutus)"
- "Maxim Filimonov (@part1zano)"
'''

EXAMPLES = '''
# fetch all available binary updates
- freebsd_update:
    action: fetch

# Fetch and install all updates:
- freebsd_update:
    action: fetch_install
    force: yes
    workdir: /tmp/freebsd_update
'''
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True),
            server=dict(type='str'),
            basedir=dict(type='str'),
            workdir=dict(type='str'),
            conffile=dict(type='str'),
            force=dict(type='bool', default=False),
            key=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    actions = ['fertch', 'fetch_install', 'install', 'rollback', 'IDS', 'cron']

    action = module.params['action']
    msg = "Unexpected failure!"
    if action not in actions:
        msg = "Unexpected action"
    server = module.params.get('server')
    basedir = module.params.get('basedir')
    workdir = module.params.get('workdir')
    conffile = module.params.get('conffile')
    force = module.params.get('force')
    key = module.params.get('key')

    freebsd_update_bin = module.get_bin_path('freebsd-update', True)
    cmd = []
    cmd.append(freebsd_update_bin)
    if server is not None:
        cmd.extend(('-s', server))
    if basedir is not None:
        cmd.extend(('-b', basedir))
    if workdir is not None:
        cmd.extend(('-d', workdir))
    if conffile is not None:
        cmd.extend(('-f', conffile))
    if force:
        cmd.append('-F')
    if key is not None:
        cmd.extend(('-k', key))
    if action == 'fetch_install':
        cmd.extend(('fetch', 'install'))
    else:
        cmd.append(action)

    try:
        rc, out, err = module.run_command(cmd)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    database = 'freebsd-update'
    dbtree = '_%s' % database
    results = {dbtree: {}}

    if rc == 0:
        results[dbtree]['output'] = []
        for line in out.splitlines():
            results[dbtree]['output'].append(line)
        results[dbtree]['command'] = cmd
        changed = True
        if 'No updates' in out:
            changed = False

        module.exit_json(ansible_facts=results, changed=changed)

    else:
        msg = ' '.join(cmd) + ' failed'

    module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
