#!/usr/bin/python

# Copyright: (c) 2018, Evan Van Dam <evandam92@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: r_package

short_description: Manage R packages.

version_added: "2.8"

description:
    - "Install, update, and remove R packages."

options:
    name:
        description:
            - The name of the R package to install.
            - This can be a list to install multiple packages at once.
            - Versions can be included in the name after an equal sign.
        required: true
    version:
        description:
            - The version of the R package to install.
            - Versions specified in the name override this value.
    state:
        description:
            - The state of the package
        choices: [absent, latest, present]
        default: present
        required: false
    executable:
        description:
            - The absoulte path to the R executable.
            - By default, find R from PATH.
    lib:
        description:
            - Library directories to install packages to,
              as used in the install.packages function.
    type:
        description:
            - The type of package to download and install,
              as used in the install.packages function.
        choices:
            - source
            - mac.binary
            - mac.binary.el-capitan
            - win.binary
            - binary
            - both
    repos:
        description:
            - The base URL(s) of the repositories to use, such as CRAN mirrors.
    extra_args:
        description:
            - Extra arguments passed to R functions to
              install.packages, install_version, or remove.packages
        default: {}

requirements:
    - R
    - devtools (for specifying versions)

author:
    - Evan Van Dam (@evandam)
'''

EXAMPLES = '''
- name: Install dplyr
  r_package:
    name: dplyr

- name: Install dplyr 0.7.7
  r_package:
    name: dplyr=0.7.7
    new: true

- name: Install dplyr 0.7.7 with the version arg
  r_package:
    name: dplyr
    version: 0.7.7

- name: Install the latest version of multiple packages to a home directory
  r_package:
    name:
      - dplyr
      - stringr
      - tidyr
    state: latest
    lib: ~/R-pkgs

- name: Set Ncpus to install dependencies in parallel
  r_package:
    name: dplyr
    extra_args:
        Ncpus: 4
'''

RETURN = '''
packages:
    description: List of packages that were modified.
    returned: changed
    type: list
    sample: [stringr", "tidyr"]
'''

import os
import re
from numbers import Number
from ansible.module_utils.basic import AnsibleModule


class RInstaller(object):
    R_OUTPUT_FORMAT = re.compile(r'\[\d+\] (\'?)(.*)\1')

    def __init__(self, module):
        self.module = module
        self.exe = self._get_R(module.params['executable'])

    def _get_R(self, executable):
        r_cmd = None
        if executable:
            if os.path.isfile(executable):
                r_cmd = executable
            else:
                self.module.fail_json(msg='%s is not a valid R executable' % executable)
        else:
            r_cmd = self.module.get_bin_path('R')
            if not r_cmd:
                self.module.fail_json(msg='R could not be found in the PATH and was not specified.')
        return r_cmd

    @staticmethod
    def _parse_R_output(out):
        return RInstaller.R_OUTPUT_FORMAT.match(out).group(2).strip().strip('\'')

    @staticmethod
    def _parse_package_version(name, version=None):
        if '=' in name:
            return name.split('=')
        else:
            return (name, version)

    def _run_R_function(self, funcname, args=[], kwargs={}, check_rc=False):
        """Run an R function that might have positional and/or named args."""
        # Clean up all args before passing to R
        def _escape_arg(arg):
            if isinstance(arg, list):
                safe_args = [_escape_arg(a) for a in arg]
                return 'c({items})'.format(items=', '.join(safe_args))
            elif isinstance(arg, Number):
                return str(arg)
            elif arg in ('TRUE', 'FALSE'):
                return arg
            elif arg is None:
                return 'NULL'
            return '"{0}"'.format(arg)

        r_args = [_escape_arg(a) for a in args]
        r_args += [k + ' = ' + _escape_arg(v) for k, v in kwargs.items() if v is not None]
        r_func = '{func}({args})'.format(func=funcname, args=', '.join(r_args))

        return self._run_R_statement(r_func, check_rc=check_rc)

    def _run_R_statement(self, statement, check_rc=False):
        """Run a raw line of R code"""
        # Fancy quotes make parsing a nightmare.
        disable_fancy_quotes = 'options(useFancyQuotes = FALSE)'
        cmd = [self.exe, '--slave', '--no-save', '--no-restore', '-e',
               '; '.join([disable_fancy_quotes, statement])]
        print('Running: %s' % cmd)
        return self.module.run_command(cmd, check_rc=check_rc)

    def is_present(self, name, version=None, lib=None):
        """Return whether or not the package is installed.

        Optionally check for the correct version.
        """
        present = False
        rc, out, err = self._run_R_function('packageVersion', [name], {'lib.loc': lib})
        if rc == 0:
            if version is not None:
                installed_version = self._parse_R_output(out)
                present = version == installed_version
            else:
                present = True
        return present

    def is_old(self, name, lib=None):
        """Check if an update is available for the package."""
        statement = ('"{name}" %in% as.data.frame(old.packages(lib.loc="{lib}"))$Package'
                     .format(name=name, lib=lib))
        rc, out, err = self._run_R_statement(statement)
        old = self._parse_R_output(out) == 'TRUE'
        return old

    def install_packages(self, names, versions=None, lib=None,
                         install_type=None, repos=None, **kwargs):
        """Install a new package."""
        # Check if we can lump all packages into one command when no versions are specified
        if versions is None:
            versions = [None for n in names]

        names_and_versions = list(zip(names, versions))
        specific_versions = [(n, v) for n, v in names_and_versions if v]
        no_versions = [n for n, v in names_and_versions if not v]

        # Install all unversioned packages in batch
        if no_versions:
            print('Installing packages in one batch: %s' % no_versions)
            r_kwargs = {'lib': lib, 'type': install_type, 'repos': repos}
            r_kwargs.update(kwargs)
            self._run_R_function('install.packages', [no_versions], r_kwargs, check_rc=True)

        # Install each package one at a time, specifying versions
        if specific_versions:
            for name, version in specific_versions:
                print('Installing %s=%s' % (name, version))
                r_kwargs = {'lib': lib, 'version': version, 'type': install_type, 'repos': repos}
                r_kwargs.update(kwargs)
                self._run_R_function('devtools::install_version', [name], r_kwargs, check_rc=True)

    def update_packages(self, name, lib=None):
        """Update to the latest version."""
        print('Updating packages %s' % name)
        r_kwargs = {'lib.loc': lib, 'oldPkgs': name, 'ask': False}
        self._run_R_function('update.packages', kwargs=r_kwargs)

    def remove_packages(self, name, lib=None, **kwargs):
        """Uninstall a package."""
        print('Removing packages %s' % name)
        r_kwargs = {'lib': lib}
        r_kwargs.update(kwargs)
        self._run_R_function('remove.packages', [name], r_kwargs)


def run_module():
    # define available arguments/parameters a user can pass to the module
    install_types = ['source', 'mac.binary', 'mac.binary.el-capitan',
                     'win.binary', 'binary', 'both']
    module_args = dict(
        name=dict(required=True, type='list'),
        version=dict(required=False),
        state=dict(default='present', choices=['present', 'latest', 'absent']),
        executable=dict(required=False, type='path'),
        lib=dict(required=False, type='list'),
        type=dict(required=False, choices=install_types),
        repos=dict(required=False, type='list'),
        extra_args=dict(required=False, type='dict', default={})
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    name = module.params['name']
    version = module.params['version']
    state = module.params['state']
    lib = module.params['lib']
    install_type = module.params['type']
    repos = module.params['repos']
    extra_args = module.params['extra_args']

    r_installer = RInstaller(module)
    packages = [r_installer._parse_package_version(n, version) for n in name]

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if state == 'present':
        absent_packages = [x for x in packages if not r_installer.is_present(*x, lib=lib)]
        if absent_packages:
            if not module.check_mode:
                packages, versions = zip(*absent_packages)
                r_installer.install_packages(packages, versions, lib=lib, repos=repos,
                                             install_type=install_type, **extra_args)
            result['packages'] = absent_packages
            result['changed'] = True
    elif state == 'latest':
        to_install = [n for n, v in packages
                      if not r_installer.is_present(n, v, lib=lib)
                      or r_installer.is_old(n, lib=lib)]
        if to_install:
            if not module.check_mode:
                r_installer.install_packages(to_install, None, lib=lib, repos=repos,
                                             install_type=install_type, **extra_args)
            result['packages'] = to_install
            result['changed'] = True
    elif state == 'absent':
        to_remove = [n for n, v in packages if r_installer.is_present(n, lib=lib)]
        if to_remove:
            if not module.check_mode:
                r_installer.remove_packages(to_remove, lib=lib, **extra_args)
            result['packages'] = to_remove
            result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
