#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Alexander Winkler <mail () winkler-alexander.de>
# based on svr4pkg by
#  Boyd Adamson <boyd () boydadamson.com> (2012)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: pkgutil
short_description: Manage CSW-Packages on Solaris
description:
    - Manages CSW packages (SVR4 format) on Solaris 10 and 11.
    - These were the native packages on Solaris <= 10 and are available
      as a legacy feature in Solaris 11.
    - Pkgutil is an advanced packaging system, which resolves dependency on installation.
      It is designed for CSW packages.
version_added: "1.3"
author: "Alexander Winkler (@dermute)"
options:
  name:
    description:
      - Package name, e.g. (C(CSWnrpe))
    required: true
  site:
    description:
      - Specifies the repository path to install the package from.
      - Its global definition is done in C(/etc/opt/csw/pkgutil.conf).
    required: false
  state:
    description:
      - Whether to install (C(present)), or remove (C(absent)) a package.
      - The upgrade (C(latest)) operation will update/install the package to the latest version available.
      - "Note: The module has a limitation that (C(latest)) only works for one package, not lists of them."
    required: true
    choices: ["present", "absent", "latest"]
  update_catalog:
    description:
      - If you want to refresh your catalog from the mirror, set this to (C(yes)).
    required: false
    default: False
    version_added: "2.1"
'''

EXAMPLES = '''
# Install a package
- pkgutil:
    name: CSWcommon
    state: present

# Install a package from a specific repository
- pkgutil:
    name: CSWnrpe
    site: 'ftp://myinternal.repo/opencsw/kiel'
    state: latest
'''

import os
import pipes

def package_installed(module, name):
    cmd = ['pkginfo']
    cmd.append('-q')
    cmd.append(name)
    rc, out, err = run_command(module, cmd)
    if rc == 0:
        return True
    else:
        return False

def package_latest(module, name, site):
    # Only supports one package
    cmd = [ 'pkgutil', '-U', '--single', '-c' ]
    if site is not None:
        cmd += [ '-t', site]
    cmd.append(name)
    rc, out, err = run_command(module, cmd)
    # replace | tail -1 |grep -v SAME
    # use -2, because splitting on \n create a empty line
    # at the end of the list
    return 'SAME' in out.split('\n')[-2]

def run_command(module, cmd, **kwargs):
    progname = cmd[0]
    cmd[0] = module.get_bin_path(progname, True, ['/opt/csw/bin'])
    return module.run_command(cmd, **kwargs)

def package_install(module, state, name, site, update_catalog):
    cmd = [ 'pkgutil', '-iy' ]
    if update_catalog:
        cmd += [ '-U' ]
    if site is not None:
        cmd += [ '-t', site ]
    if state == 'latest':
        cmd += [ '-f' ]
    cmd.append(name)
    (rc, out, err) = run_command(module, cmd)
    return (rc, out, err)

def package_upgrade(module, name, site, update_catalog):
    cmd = [ 'pkgutil', '-ufy' ]
    if update_catalog:
        cmd += [ '-U' ]
    if site is not None:
        cmd += [ '-t', site ]
    cmd.append(name)
    (rc, out, err) = run_command(module, cmd)
    return (rc, out, err)

def package_uninstall(module, name):
    cmd = [ 'pkgutil', '-ry', name]
    (rc, out, err) = run_command(module, cmd)
    return (rc, out, err)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required = True),
            state = dict(required = True, choices=['present', 'absent','latest']),
            site = dict(default = None),
            update_catalog = dict(required = False, default = False, type='bool'),
        ),
        supports_check_mode=True
    )
    name = module.params['name']
    state = module.params['state']
    site = module.params['site']
    update_catalog = module.params['update_catalog']
    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = name
    result['state'] = state

    if state == 'present':
        if not package_installed(module, name):
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = package_install(module, state, name, site, update_catalog)
            # Stdout is normally empty but for some packages can be
            # very long and is not often useful
            if len(out) > 75:
                out = out[:75] + '...'
            if rc != 0:
                if err:
                    msg = err
                else:
                    msg = out
                module.fail_json(msg=msg)

    elif state == 'latest':
        if not package_installed(module, name):
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = package_install(module, state, name, site, update_catalog)
            if len(out) > 75:
                out = out[:75] + '...'
            if rc != 0:
                if err:
                    msg = err
                else:
                    msg = out
                module.fail_json(msg=msg)

        else:
            if not package_latest(module, name, site):
                if module.check_mode:
                    module.exit_json(changed=True)
                (rc, out, err) = package_upgrade(module, name, site, update_catalog)
                if len(out) > 75:
                    out = out[:75] + '...'
                if rc != 0:
                    if err:
                        msg = err
                    else:
                        msg = out
                    module.fail_json(msg=msg)

    elif state == 'absent':
        if package_installed(module, name):
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = package_uninstall(module, name)
            if len(out) > 75:
                out = out[:75] + '...'
            if rc != 0:
                if err:
                    msg = err
                else:
                    msg = out
                module.fail_json(msg=msg)

    if rc is None:
        # pkgutil was not executed because the package was already present/absent
        result['changed'] = False
    elif rc == 0:
        result['changed'] = True
    else:
        result['changed'] = False
        result['failed'] = True

    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
