#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Alexander Winkler <mail () winkler-alexander.de>
# based on svr4pkg by
#  Boyd Adamson <boyd () boydadamson.com> (2012)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
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
      - When using state=latest, this can be '*', which updates all installed packages managed by pkgutil.
      - Multiple packages can be specified using a comma as a separator.
    required: true
    aliases: [ 'pkg' ]
  site:
    description:
      - Specifies the repository path to install the package from.
      - Its global definition is done in C(/etc/opt/csw/pkgutil.conf).
    required: false
  state:
    description:
      - Whether to install (C(present)), or remove (C(absent)) packages.
      - The upgrade (C(latest)) operation will update/install the packages to the latest version available.
    required: true
    choices: ["present", "absent", "latest"]
  update_catalog:
    description:
      - If you want to refresh your catalog from the mirror, set this to (C(yes)).
    type: bool
    default: no
    version_added: "2.1"
  force:
    description:
      - Allows the update process to downgrade packages to what is present in the repostory set this to (C(yes)).
      - It is useful as a rollback to stable from testing, and similar operations.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    version_added: "2.4"
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

# Remove a package
- pkgutil:
    name: CSWtop
    state: absent

# Install several packages
- pkgutil:
    name: CSWtop,CSWsudo
    state: present

# Update all packages
- pkgutil:
    name: '*'
    state: latest

# Update all packages and force versions to match latest in catalog
- pkgutil:
    name: '*'
    state: latest
    force: yes
'''

from ansible.module_utils.basic import AnsibleModule


def packages_not_installed(module, name):
    # check if each package is installed
    # and return list of the ones absent
    pkgs = []
    for pkg in name:
        cmd = ['pkginfo']
        cmd.append('-q')
        cmd.append(pkg)
        rc, out, err = run_command(module, cmd)
        if rc != 0:
            pkgs += [ pkg ]
    return pkgs
    
def packages_installed(module, name):
    # check if each package is installed
    # and return list of the ones present
    pkgs = []
    for pkg in name:
        cmd = ['pkginfo']
        cmd.append('-q')
        cmd.append(pkg)
        rc, out, err = run_command(module, cmd)
        if rc == 0 and 'CSW' in pkg:
            pkgs += [ pkg ]
    return pkgs
    
def packages_not_latest(module, name, site, update_catalog):
    # check status of each package
    # and return list of the ones with an upgrade available
    cmd = [ 'pkgutil' ]
    if update_catalog:
        cmd += [ '-U' ]
    cmd += [ '-c' ]
    if site is not None:
        cmd += [ '-t', site]
    if name != ['*']:
        for package in name:
            cmd.append(package)
    rc, out, err = run_command(module, cmd)
    packages = []
    # find packages in the catalog which are not up to date
    for line in out.split('\n')[1:-1]:
        if 'catalog' not in line:
            if 'SAME' not in line:
                packages += [ line.split(' ')[0] ]
    # remove duplicates
    pkgs = list(set(packages))
    return pkgs


def run_command(module, cmd, **kwargs):
    progname = cmd[0]
    cmd[0] = module.get_bin_path(progname, True, ['/opt/csw/bin'])
    return module.run_command(cmd, **kwargs)

def package_install(module, state, pkgs, site, update_catalog, force):
    cmd = [ 'pkgutil' ]
    if module.check_mode:
        cmd += [ '-n' ]
    cmd += [ '-iy' ]
    if update_catalog:
        cmd += ['-U']
    if site is not None:
        cmd += [ '-t', site ]
    if force:
        cmd += [ '-f' ]
    cmd += pkgs
    (rc, out, err) = run_command(module, cmd)
    return (rc, out, err)

def package_upgrade(module, pkgs, site, update_catalog, force):
    cmd = [ 'pkgutil' ]
    if module.check_mode:
        cmd += [ '-n' ]
    cmd += [ '-uy' ]
    if update_catalog:
        cmd += ['-U']
    if site is not None:
        cmd += [ '-t', site ]
    if force:
        cmd += [ '-f' ]
    cmd += pkgs
    (rc, out, err) = run_command(module, cmd)
    return (rc, out, err)

def package_uninstall(module, pkgs):
    cmd = [ 'pkgutil' ]
    if module.check_mode:
        cmd += [ '-n' ]
    cmd += [ '-ry' ]
    cmd += pkgs
    (rc, out, err) = run_command(module, cmd)
    return (rc, out, err)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required = True, aliases=['pkg'], type='list'),
            state = dict(required = True, choices=['present','installed','absent','removed','latest']),
            site = dict(default = None),
            update_catalog = dict(required = False, default = False, type='bool'),
            force = dict(required = False, default = False, type='bool'),
        ),
        supports_check_mode=True
    )
    name = module.params['name']
    state = module.params['state']
    site = module.params['site']
    update_catalog = module.params['update_catalog']
    force = module.params['force']
    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = name
    result['state'] = state

    if state in ['installed', 'present']:
        if name != ['*']:
            # Build list of packages that are actually not installed from the ones requested
            pkgs = packages_not_installed(module, name)
            if pkgs != []:
                (rc, out, err) = package_install(module, state, pkgs, site, update_catalog, force)
                if rc != 0:
                    if err:
                        msg = err
                    else:
                        msg = out
                    module.fail_json(msg=msg)
            # f the package list is empty then all packages are already present
            else:
                module.exit_json(changed=False)
        # Fail with an explicit error when trying to "install" '*'
        else:
            module.fail_json(msg="Can not use state: present with name: *")

    elif state in ['latest']:
        if name != ['*']:
            # Build list of packages that are either outdated or not installed
            pkgs = packages_not_installed(module, name)
            pkgs += packages_not_latest(module, name, site, update_catalog)
            if pkgs != []:
                (rc, out, err) = package_upgrade(module, pkgs, site, update_catalog, force)
                if rc != 0:
                    if err:
                        msg = err
                    else:
                        msg = out
                    module.fail_json(msg=msg)
            # If the package list is empty that means all packages are installed and up to date
            else:
                module.exit_json(changed=False)
        # When using latest for *
        else:
            # Check for packages that are actually outdated
            pkgs = packages_not_latest(module, name, site, update_catalog)
            if pkgs != []:
                # If there are packages to update, just empty the list and run the command without it
                # pkgutil logic is to update all when run without packages names
                pkgs == []
                (rc, out, err) = package_upgrade(module, pkgs, site, update_catalog, force)
                if rc != 0:
                    if err:
                        msg = err
                    else:
                        msg = out
                    module.fail_json(msg=msg)
            # If the package list comes up empty, everything is already up to date
            else:
                module.exit_json(changed=False)
        

    elif state in ['absent', 'removed']:
        # Build list of packages requested for removal that are actually present
        pkgs = packages_installed(module, name)
        if pkgs != []:
            (rc, out, err) = package_uninstall(module, pkgs)
            if rc != 0:
                if err:
                    msg = err
                else:
                    msg = out
                module.fail_json(msg=msg)
        # If the list is empty, no packages need to be removed
        else:
            module.exit_json(changed=False)

    if rc is None:
        # pkgutil was not executed because the package was already present/absent/up to date
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


if __name__ == '__main__':
    main()
