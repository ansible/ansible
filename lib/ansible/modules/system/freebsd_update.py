#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Brian Coca <rusik@4ege.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

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
            - freebsd-update command to execute — fetch, install, fetch_install, rollback, IDS, cron.
        required: True
        choices:
        - fetch
        - install
        - fetch_install
        - rollback
        - IDS
        - cron
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

RETURN = ''' # '''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True, choices=['fetch', 'install', 'fetch_install', 'rollback', 'IDS', 'cron']),
            server=dict(type='str'),
            basedir=dict(type='str'),
            workdir=dict(type='str'),
            conffile=dict(type='str'),
            force=dict(type='bool', default=False),
            key=dict(type='str'),
        ),
    )

    action = module.params['action']
    msg = "Unexpected failure!"
    server = module.params.get('server')
    basedir = module.params.get('basedir')
    workdir = module.params.get('workdir')
    conffile = module.params.get('conffile')
    force = module.params.get('force')
    key = module.params.get('key')

    freebsd_update_bin = module.get_bin_path('freebsd-update', True)
    cmd = [freebsd_update_bin]
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
    cmd.append('--not-running-from-cron')
    if action == 'fetch_install':
        cmd.extend(('fetch', 'install'))
    else:
        cmd.append(action)

    try:
        rc, out, err = module.run_command(cmd)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    dbtree = 'freebsd-update'
    results = {dbtree: {}}

    if rc == 0:
        results[dbtree]['stdout'] = out
        results[dbtree]['stdout_lines'] = out.split('\n')
        results[dbtree]['command'] = cmd
        results['changed'] = True
        if 'No updates' in out:
            results['changed'] = False

        module.exit_json(**results)

    else:
        msg = ' '.join(cmd) + ' failed'

    module.fail_json(msg=msg, stderr=err, stdout=out)


if __name__ == '__main__':
    main()
