#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, William L Thomson Jr
# (c) 2013, Yap Sok Ann
# Written by Yap Sok Ann <sokann@gmail.com>
# Modified by William L. Thomson Jr. <wlt@o-sinc.com>
# Based on apt module written by Matthew Williams <matthew@flowroute.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: portage
short_description: Package manager for Gentoo
description:
  - Manages Gentoo packages
version_added: "1.6"

options:
  package:
    description:
      - Package atom or set, e.g. C(sys-apps/foo) or C(>foo-2.13) or C(@world)

  state:
    description:
      - State of the package atom
    default: "present"
    choices: [ "present", "installed", "emerged", "absent", "removed", "unmerged", "latest" ]

  update:
    description:
      - Update packages to the best version available (--update)
    type: bool
    default: 'no'

  deep:
    description:
      - Consider the entire dependency tree of packages (--deep)
    type: bool
    default: 'no'

  newuse:
    description:
      - Include installed packages where USE flags have changed (--newuse)
    type: bool
    default: 'no'

  changed_use:
    description:
      - Include installed packages where USE flags have changed, except when
      - flags that the user has not enabled are added or removed
      - (--changed-use)
    type: bool
    default: 'no'
    version_added: 1.8

  oneshot:
    description:
      - Do not add the packages to the world file (--oneshot)
    type: bool
    default: 'no'

  noreplace:
    description:
      - Do not re-emerge installed packages (--noreplace)
    type: bool
    default: 'no'

  nodeps:
    description:
      - Only merge packages but not their dependencies (--nodeps)
    type: bool
    default: 'no'

  onlydeps:
    description:
      - Only merge packages' dependencies but not the packages (--onlydeps)
    type: bool
    default: 'no'

  depclean:
    description:
      - Remove packages not needed by explicitly merged packages (--depclean)
      - If no package is specified, clean up the world's dependencies
      - Otherwise, --depclean serves as a dependency aware version of --unmerge
    type: bool
    default: 'no'

  quiet:
    description:
      - Run emerge in quiet mode (--quiet)
    type: bool
    default: 'no'

  verbose:
    description:
      - Run emerge in verbose mode (--verbose)
    type: bool
    default: 'no'

  sync:
    description:
      - Sync package repositories first
      - If yes, perform "emerge --sync"
      - If web, perform "emerge-webrsync"
    choices: [ "web", "yes", "no" ]

  getbinpkg:
    description:
      - Prefer packages specified at PORTAGE_BINHOST in make.conf
    type: bool
    default: 'no'

  usepkgonly:
    description:
      - Merge only binaries (no compiling). This sets getbinpkg=yes.
    type: bool
    default: 'no'

  keepgoing:
    description:
      - Continue as much as possible after an error.
    type: bool
    default: 'no'
    version_added: 2.3

  jobs:
    description:
      - Specifies the number of packages to build simultaneously.
      - "Since version 2.6: Value of 0 or False resets any previously added"
      - --jobs setting values
    version_added: 2.3

  loadavg:
    description:
      - Specifies that no new builds should be started if there are
      - other builds running and the load average is at least LOAD
      - "Since version 2.6: Value of 0 or False resets any previously added"
      - --load-average setting values
    version_added: 2.3

  quietbuild:
    description:
      - Redirect all build output to logs alone, and do not display it
      - on stdout (--quiet-build)
    type: bool
    default: 'no'
    version_added: 2.6

  quietfail:
    description:
      - Suppresses display of the build log on stdout (--quiet-fail)
      - Only the die message and the path of the build log will be
      - displayed on stdout.
    type: bool
    default: 'no'
    version_added: 2.6

requirements: [ gentoolkit ]
author:
    - "William L Thomson Jr (@wltjr)"
    - "Yap Sok Ann (@sayap)"
    - "Andrew Udvare (@Tatsh)"
'''

EXAMPLES = '''
# Make sure package foo is installed
- portage:
    package: foo
    state: present

# Make sure package foo is not installed
- portage:
    package: foo
    state: absent

# Update package foo to the "latest" version ( os specific alternative to latest )
- portage:
    package: foo
    update: yes

# Install package foo using PORTAGE_BINHOST setup
- portage:
    package: foo
    getbinpkg: yes

# Re-install world from binary packages only and do not allow any compiling
- portage:
    package: '@world'
    usepkgonly: yes

# Sync repositories and update world
- portage:
    package: '@world'
    update: yes
    deep: yes
    sync: yes

# Remove unneeded packages
- portage:
    depclean: yes

# Remove package foo if it is not explicitly needed
- portage:
    package: foo
    state: absent
    depclean: yes
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def query_package(module, package, action):
    if package.startswith('@'):
        return query_set(module, package, action)
    return query_atom(module, package, action)


def query_atom(module, atom, action):
    cmd = '%s list %s' % (module.equery_path, atom)

    rc, out, err = module.run_command(cmd)
    return rc == 0


def query_set(module, set, action):
    system_sets = [
        '@live-rebuild',
        '@module-rebuild',
        '@preserved-rebuild',
        '@security',
        '@selected',
        '@system',
        '@world',
        '@x11-module-rebuild',
    ]

    if set in system_sets:
        if action == 'unmerge':
            module.fail_json(msg='set %s cannot be removed' % set)
        return False

    world_sets_path = '/var/lib/portage/world_sets'
    if not os.path.exists(world_sets_path):
        return False

    cmd = 'grep %s %s' % (set, world_sets_path)

    rc, out, err = module.run_command(cmd)
    return rc == 0


def sync_repositories(module, webrsync=False):
    if module.check_mode:
        module.exit_json(msg='check mode not supported by sync')

    if webrsync:
        webrsync_path = module.get_bin_path('emerge-webrsync', required=True)
        cmd = '%s --quiet' % webrsync_path
    else:
        cmd = '%s --sync --quiet --ask=n' % module.emerge_path

    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg='could not sync package repositories')


# Note: In the 3 functions below, equery is done one-by-one, but emerge is done
# in one go. If that is not desirable, split the packages into multiple tasks
# instead of joining them together with comma.


def emerge_packages(module, packages):
    """Run emerge command against given list of atoms."""
    p = module.params

    if not (p['update'] or p['noreplace'] or p['state'] == 'latest'):
        for package in packages:
            if not query_package(module, package, 'emerge'):
                break
        else:
            module.exit_json(changed=False, msg='Packages already present.')
        if module.check_mode:
            module.exit_json(changed=True, msg='Packages would be installed.')

    args = []
    emerge_flags = {
        'update': '--update',
        'deep': '--deep',
        'newuse': '--newuse',
        'changed_use': '--changed-use',
        'oneshot': '--oneshot',
        'noreplace': '--noreplace',
        'nodeps': '--nodeps',
        'onlydeps': '--onlydeps',
        'quiet': '--quiet',
        'verbose': '--verbose',
        'getbinpkg': '--getbinpkg',
        'usepkgonly': '--usepkgonly',
        'usepkg': '--usepkg',
        'keepgoing': '--keep-going',
        'quietbuild': '--quiet-build',
        'quietfail': '--quiet-fail',
    }
    for flag, arg in emerge_flags.items():
        if p[flag]:
            args.append(arg)

    if p['state'] and p['state'] == 'latest':
        args.append("--update")

    if p['usepkg'] and p['usepkgonly']:
        module.fail_json(msg='Use only one of usepkg, usepkgonly')

    emerge_flags = {
        'jobs': '--jobs',
        'loadavg': '--load-average',
    }

    for flag, arg in emerge_flags.items():
        flag_val = p[flag]

        if flag_val is None:
            """Fallback to default: don't use this argument at all."""
            continue

        if not flag_val:
            """If the value is 0 or 0.0: add the flag, but not the value."""
            args.append(arg)
            continue

        """Add the --flag=value pair."""
        args.extend((arg, to_native(flag_val)))

    cmd, (rc, out, err) = run_emerge(module, packages, *args)
    if rc != 0:
        module.fail_json(
            cmd=cmd, rc=rc, stdout=out, stderr=err,
            msg='Packages not installed.',
        )

    # Check for SSH error with PORTAGE_BINHOST, since rc is still 0 despite
    #   this error
    if (p['usepkgonly'] or p['getbinpkg']) \
            and 'Permission denied (publickey).' in err:
        module.fail_json(
            cmd=cmd, rc=rc, stdout=out, stderr=err,
            msg='Please check your PORTAGE_BINHOST configuration in make.conf '
                'and your SSH authorized_keys file',
        )

    changed = True
    for line in out.splitlines():
        if re.match(r'(?:>+) Emerging (?:binary )?\(1 of', line):
            msg = 'Packages installed.'
            break
        elif module.check_mode and re.match(r'\[(binary|ebuild)', line):
            msg = 'Packages would be installed.'
            break
    else:
        changed = False
        msg = 'No packages installed.'

    module.exit_json(
        changed=changed, cmd=cmd, rc=rc, stdout=out, stderr=err,
        msg=msg,
    )


def unmerge_packages(module, packages):
    p = module.params

    for package in packages:
        if query_package(module, package, 'unmerge'):
            break
    else:
        module.exit_json(changed=False, msg='Packages already absent.')

    args = ['--unmerge']

    for flag in ['quiet', 'verbose']:
        if p[flag]:
            args.append('--%s' % flag)

    cmd, (rc, out, err) = run_emerge(module, packages, *args)

    if rc != 0:
        module.fail_json(
            cmd=cmd, rc=rc, stdout=out, stderr=err,
            msg='Packages not removed.',
        )

    module.exit_json(
        changed=True, cmd=cmd, rc=rc, stdout=out, stderr=err,
        msg='Packages removed.',
    )


def cleanup_packages(module, packages):
    p = module.params

    if packages:
        for package in packages:
            if query_package(module, package, 'unmerge'):
                break
        else:
            module.exit_json(changed=False, msg='Packages already absent.')

    args = ['--depclean']

    for flag in ['quiet', 'verbose']:
        if p[flag]:
            args.append('--%s' % flag)

    cmd, (rc, out, err) = run_emerge(module, packages, *args)
    if rc != 0:
        module.fail_json(cmd=cmd, rc=rc, stdout=out, stderr=err)

    removed = 0
    for line in out.splitlines():
        if not line.startswith('Number removed:'):
            continue
        parts = line.split(':')
        removed = int(parts[1].strip())
    changed = removed > 0

    module.exit_json(
        changed=changed, cmd=cmd, rc=rc, stdout=out, stderr=err,
        msg='Depclean completed.',
    )


def run_emerge(module, packages, *args):
    args = list(args)

    args.append('--ask=n')
    if module.check_mode:
        args.append('--pretend')

    cmd = [module.emerge_path] + args + packages
    return cmd, module.run_command(cmd)


portage_present_states = ['present', 'emerged', 'installed', 'latest']
portage_absent_states = ['absent', 'unmerged', 'removed']


def main():
    module = AnsibleModule(
        argument_spec=dict(
            package=dict(default=None, aliases=['name'], type='list'),
            state=dict(
                default=portage_present_states[0],
                choices=portage_present_states + portage_absent_states,
            ),
            update=dict(default=False, type='bool'),
            deep=dict(default=False, type='bool'),
            newuse=dict(default=False, type='bool'),
            changed_use=dict(default=False, type='bool'),
            oneshot=dict(default=False, type='bool'),
            noreplace=dict(default=False, type='bool'),
            nodeps=dict(default=False, type='bool'),
            onlydeps=dict(default=False, type='bool'),
            depclean=dict(default=False, type='bool'),
            quiet=dict(default=False, type='bool'),
            verbose=dict(default=False, type='bool'),
            sync=dict(default=None, choices=['yes', 'web', 'no']),
            getbinpkg=dict(default=False, type='bool'),
            usepkgonly=dict(default=False, type='bool'),
            usepkg=dict(default=False, type='bool'),
            keepgoing=dict(default=False, type='bool'),
            jobs=dict(default=None, type='int'),
            loadavg=dict(default=None, type='float'),
            quietbuild=dict(default=False, type='bool'),
            quietfail=dict(default=False, type='bool'),
        ),
        required_one_of=[['package', 'sync', 'depclean']],
        mutually_exclusive=[
            ['nodeps', 'onlydeps'],
            ['quiet', 'verbose'],
            ['quietbuild', 'verbose'],
            ['quietfail', 'verbose'],
        ],
        supports_check_mode=True,
    )

    module.emerge_path = module.get_bin_path('emerge', required=True)
    module.equery_path = module.get_bin_path('equery', required=True)

    p = module.params

    if p['sync'] and p['sync'].strip() != 'no':
        sync_repositories(module, webrsync=(p['sync'] == 'web'))
        if not p['package']:
            module.exit_json(msg='Sync successfully finished.')

    packages = []
    if p['package']:
        packages.extend(p['package'])

    if p['depclean']:
        if packages and p['state'] not in portage_absent_states:
            module.fail_json(
                msg='Depclean can only be used with package when the state is '
                    'one of: %s' % portage_absent_states,
            )

        cleanup_packages(module, packages)

    elif p['state'] in portage_present_states:
        emerge_packages(module, packages)

    elif p['state'] in portage_absent_states:
        unmerge_packages(module, packages)


if __name__ == '__main__':
    main()
