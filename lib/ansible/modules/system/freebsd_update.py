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
version_added: "2.7"
options:
    action:
        description:
            - freebsd-update command to execute: fetch, upgrade, install, rollback, IDS, cron.
        required: True
    server:
        description:
            - Server to download updates from.
        default: ''
    basedir:
        description:
            - path to filesystem to update.
        default: '/'
    workdir:
        description:
            - directory to store working files in.
        default: ''
    conffile:
        description:
            - file to read configuration options from
        default: ''
    force:
        description:
            - force freebsd-update run
        type: bool
        default: False
    key:
        description:
            - trust an RSA key with SHA256 of KEY
        default: ''
author:
- Ruslan Gustomiasov (@loqutus)
'''

EXAMPLES = '''
# fetch all available binary updates
- freebsd_update:
    action: update

# fetch all files needed for upgrade to a new release
- freebsd_update:
    action: upgrade
    basedir: /

# get all hosts, split by tab
- freebsd_update:
    action: install
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
            server=dict(type='str', default=''),
            basedir=dict(type='str', default=''),
            workdir=dict(type='str', default=''),
            conffile=dict(type='str', default=''),
            force=dict(type='bool', default=False),
            key=dict(type='str', default=''),
        ),
        supports_check_mode=True,
    )

    actions = ['fetch', 'upgrade', 'install', 'rollback', 'IDS', 'cron']

    action = module.params['action']
    msg = "Unexpected failure!"
    if action not in actions:
        msg = "Unexpected action: {}".format(action)
    server = module.params.get('server')
    basedir = module.params.get('basedir')
    workdir = module.params.get('workdir')
    conffile = module.params.get('conffile')
    force = module.params.get('force')
    key = module.params.get('key')

    freebsd_update_bin = module.get_bin_path('freebsd_update', True)
    cmd = []
    cmd.append(freebsd_update_bin)
    cmd.append(action)
    if server is not '':
        cmd.extend(('-s', server))
    if basedir is not '':
        cmd.extend(('-b', basedir))
    if workdir is not '':
        cmd.extend(('-d', workdir))
    if conffile is not '':
        cmd.extend(('-f', conffile))
    if force is True:
        cmd.extend('-F')
    if key is not '':
        cmd.extend(('-k', key))

    try:
        rc, out, err = module.run_command(cmd)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    dbtree = '_%s' % database
    results = {dbtree: {}}

    if rc == 0:
        for line in out.splitlines():
            record = line.split(split)
            results[dbtree][record[0]] = record[1:]

        module.exit_json(ansible_facts=results)

    else:
        msg = "freebsd_update failed"

    module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
