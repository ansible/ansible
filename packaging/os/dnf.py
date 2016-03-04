#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Cristian van Ee <cristian at cvee.org>
# Copyright 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
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
#

DOCUMENTATION = '''
---
module: dnf
version_added: 1.9
short_description: Manages packages with the I(dnf) package manager
description:
     - Installs, upgrade, removes, and lists packages and groups with the I(dnf) package manager.
options:
  name:
    description:
      - "Package name, or package specifier with version, like C(name-1.0). When using state=latest, this can be '*' which means run: dnf -y update. You can also pass a url or a local path to a rpm file."
    required: true
    default: null
    aliases: []

  list:
    description:
      - Various (non-idempotent) commands for usage with C(/usr/bin/ansible) and I(not) playbooks. See examples.
    required: false
    default: null

  state:
    description:
      - Whether to install (C(present), C(latest)), or remove (C(absent)) a package.
    required: false
    choices: [ "present", "latest", "absent" ]
    default: "present"

  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    default: null
    aliases: []

  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    default: null
    aliases: []

  conf_file:
    description:
      - The remote dnf configuration file to use for the transaction.
    required: false
    default: null
    aliases: []

  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if state is I(present) or I(latest).
    required: false
    default: "no"
    choices: ["yes", "no"]
    aliases: []

notes: []
# informational: requirements for nodes
requirements:
  - "python >= 2.6"
  - python-dnf
author:
  - '"Igor Gnatenko (@ignatenkobrain)" <i.gnatenko.brain@gmail.com>'
  - '"Cristian van Ee (@DJMuggs)" <cristian at cvee.org>'
'''

EXAMPLES = '''
- name: install the latest version of Apache
  dnf: name=httpd state=latest

- name: remove the Apache package
  dnf: name=httpd state=absent

- name: install the latest version of Apache from the testing repo
  dnf: name=httpd enablerepo=testing state=present

- name: upgrade all packages
  dnf: name=* state=latest

- name: install the nginx rpm from a remote repo
  dnf: name=http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm state=present

- name: install nginx rpm from a local file
  dnf: name=/usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm state=present

- name: install the 'Development tools' package group
  dnf: name="@Development tools" state=present

'''
import os

try:
    import dnf
    from dnf import cli, const, exceptions, subject, util
    HAS_DNF = True
except ImportError:
    HAS_DNF = False


def _fail_if_no_dnf(module):
    """Fail if unable to import dnf."""
    if not HAS_DNF:
        module.fail_json(
            msg="`python2-dnf` is not installed, but it is required for the Ansible dnf module.")


def _configure_base(module, base, conf_file, disable_gpg_check):
    """Configure the dnf Base object."""
    conf = base.conf

    # Turn off debug messages in the output
    conf.debuglevel = 0

    # Set whether to check gpg signatures
    conf.gpgcheck = not disable_gpg_check

    # Don't prompt for user confirmations
    conf.assumeyes = True

    # Change the configuration file path if provided
    if conf_file:
        # Fail if we can't read the configuration file.
        if not os.access(conf_file, os.R_OK):
            module.fail_json(
                msg="cannot read configuration file", conf_file=conf_file)
        else:
            conf.config_file_path = conf_file

    # Read the configuration file
    conf.read()


def _specify_repositories(base, disablerepo, enablerepo):
    """Enable and disable repositories matching the provided patterns."""
    base.read_all_repos()
    repos = base.repos

    # Disable repositories
    for repo_pattern in disablerepo:
        for repo in repos.get_matching(repo_pattern):
            repo.disable()

    # Enable repositories
    for repo_pattern in enablerepo:
        for repo in repos.get_matching(repo_pattern):
            repo.enable()


def _base(module, conf_file, disable_gpg_check, disablerepo, enablerepo):
    """Return a fully configured dnf Base object."""
    base = dnf.Base()
    _configure_base(module, base, conf_file, disable_gpg_check)
    _specify_repositories(base, disablerepo, enablerepo)
    base.fill_sack()
    return base


def _package_dict(package):
    """Return a dictionary of information for the package."""
    # NOTE: This no longer contains the 'dnfstate' field because it is
    # already known based on the query type.
    result = {
        'name': package.name,
        'arch': package.arch,
        'epoch': str(package.epoch),
        'release': package.release,
        'version': package.version,
        'repo': package.repoid}
    result['nevra'] = '{epoch}:{name}-{version}-{release}.{arch}'.format(
        **result)

    return result


def list_items(module, base, command):
    """List package info based on the command."""
    # Rename updates to upgrades
    if command == 'updates':
        command = 'upgrades'

    # Return the corresponding packages
    if command in ['installed', 'upgrades', 'available']:
        results = [
            _package_dict(package)
            for package in getattr(base.sack.query(), command)()]
    # Return the enabled repository ids
    elif command in ['repos', 'repositories']:
        results = [
            {'repoid': repo.id, 'state': 'enabled'}
            for repo in base.repos.iter_enabled()]
    # Return any matching packages
    else:
        packages = subject.Subject(command).get_best_query(base.sack)
        results = [_package_dict(package) for package in packages]

    module.exit_json(results=results)


def _mark_package_install(module, base, pkg_spec):
    """Mark the package for install."""
    try:
        base.install(pkg_spec)
    except exceptions.MarkingError:
        module.fail_json(msg="No package {} available.".format(pkg_spec))


def ensure(module, base, state, names):
    allow_erasing = False
    if names == ['*'] and state == 'latest':
        base.upgrade_all()
    else:
        pkg_specs, group_specs, filenames = cli.commands.parse_spec_group_file(
            names)
        if group_specs:
            base.read_comps()

        groups = []
        for group_spec in group_specs:
            group = base.comps.group_by_pattern(group_spec)
            if group:
                groups.append(group)
            else:
                module.fail_json(
                    msg="No group {} available.".format(group_spec))

        if state in ['installed', 'present']:
            # Install files.
            for filename in filenames:
                base.package_install(base.add_remote_rpm(filename))
            # Install groups.
            for group in groups:
                base.group_install(group, const.GROUP_PACKAGE_TYPES)
            # Install packages.
            for pkg_spec in pkg_specs:
                _mark_package_install(module, base, pkg_spec)

        elif state == 'latest':
            # "latest" is same as "installed" for filenames.
            for filename in filenames:
                base.package_install(base.add_remote_rpm(filename))
            for group in groups:
                try:
                    base.group_upgrade(group)
                except exceptions.CompsError:
                    # If not already installed, try to install.
                    base.group_install(group, const.GROUP_PACKAGE_TYPES)
            for pkg_spec in pkg_specs:
                # best effort causes to install the latest package
                # even if not previously installed
                base.conf.best = True
                base.install(pkg_spec)

        else:
            # state == absent
            if filenames:
                module.fail_json(
                    msg="Cannot remove paths -- please specify package name.")

            installed = base.sack.query().installed()
            for group in groups:
                if installed.filter(name=group.name):
                    base.group_remove(group)
            for pkg_spec in pkg_specs:
                if installed.filter(name=pkg_spec):
                    base.remove(pkg_spec)
            # Like the dnf CLI we want to allow recursive removal of dependent
            # packages
            allow_erasing = True

    if not base.resolve(allow_erasing=allow_erasing):
        module.exit_json(msg="Nothing to do")
    else:
        if module.check_mode:
            module.exit_json(changed=True)
        base.download_packages(base.transaction.install_set)
        base.do_transaction()
        response = {'changed': True, 'results': []}
        for package in base.transaction.install_set:
            response['results'].append("Installed: {}".format(package))
        for package in base.transaction.remove_set:
            response['results'].append("Removed: {}".format(package))

        module.exit_json(**response)


def main():
    """The main function."""
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=['pkg'], type='list'),
            state=dict(
                default='installed',
                choices=[
                    'absent', 'present', 'installed', 'removed', 'latest']),
            enablerepo=dict(type='list', default=[]),
            disablerepo=dict(type='list', default=[]),
            list=dict(),
            conf_file=dict(default=None),
            disable_gpg_check=dict(default=False, type='bool'),
        ),
        required_one_of=[['name', 'list']],
        mutually_exclusive=[['name', 'list']],
        supports_check_mode=True)
    params = module.params

    _fail_if_no_dnf(module)
    if params['list']:
        base = _base(
            module, params['conf_file'], params['disable_gpg_check'],
            params['disablerepo'], params['enablerepo'])
        list_items(module, base, params['list'])
    else:
        # Note: base takes a long time to run so we want to check for failure
        # before running it.
        if not util.am_i_root():
            module.fail_json(msg="This command has to be run under the root user.")
        base = _base(
            module, params['conf_file'], params['disable_gpg_check'],
            params['disablerepo'], params['enablerepo'])

        ensure(module, base, params['state'], params['name'])


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
