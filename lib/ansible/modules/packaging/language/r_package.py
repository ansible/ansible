#!/usr/bin/python

# Copyright: (c) 2018, Evan Van Dam <evandam92@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import re
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: r_package
short_description: A module to install and manage R packages
description:
  >
    Install, remove, and update R packages.
    Flexibility is provided to specify the R executable,
    the remote repository, source to build, and library location.
version_added: "2.8"
author: "Evan Van Dam (@evandam)"
options:
  name:
    description: The name of the targeted R package.
    required: true
  state:
    description: The target state of the package.
    choices: ["present", "absent"]
    default: present
  force:
    description: Force the package to be installed, even if it already exists.
    type: bool
    default: false
  executable:
    description: Path to the R executable. If not specified, find it from the PATH.
  src:
    description: The source file or directory to build the R package.
  type:
    description: Type of package to install, like "source" or "binary".
  lib:
    description: The library location to use to install or remove the package.
  repo:
    description: The CRAN repo to use to install the package.
notes:
  - Requires R to already be installed.
  - check mode is supported.
'''

EXAMPLES = '''
- name: Install dplyr
  r_package:
    name: dplyr
    state: present
- name: Force dplyr to be reinstalled
  r_package:
    name: dplyr
    force: true
- name: Uninstall dplyr
  r_package:
    name: dplyr
    state: absent
- name: Install dplyr from the cloud CRAN mirror to your home lib
  r_package:
    name: dplyr
    repo: https://cloud.r-project.org/
    lib: "~/R"
- name: Install h2o from source
  r_package:
    name: h2o
    src: ~/Downloads/h2o.tar.gz
    type: source
'''

RETURN = '''
cmd:
  description: The R function executed by the module.
  returned: changed
  type: string
  sample: install.packages("dplyr")
'''

import os
from numbers import Number
from ansible.module_utils.basic import AnsibleModule


R_OUTPUT_FORMAT = re.compile(r'\[\d+\] \'?(.*)\'?')


class RInstaller(object):
    
    def __init__(self, module, debug_info):
        self.module = module
        self.debug_info = debug_info
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
        return R_OUTPUT_FORMAT.match(out).group(1).strip()

    def _run_R_function(self, funcname, *args, check_rc=False, **kwargs):
        """Run an R function that might have positional and/or named args."""
        # Clean up all args before passing to R
        def _escape_arg(arg):
            if isinstance(arg, Number):
                return arg
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
        cmd = [self.exe, '--slave', '--no-save', '--no-restore', '-e', statement]
        return self.module.run_command(cmd, check_rc=check_rc) 

    def is_present(self, name, version=None):
        """Return whether or not the package is installed.
        
        Optionally check for the correct version.
        """
        present = False
        rc, out, err = self._run_R_function('packageVersion', name)
        if rc == 0:
            if version is not None:
                installed_version = self._parse_R_output(out)
                present = version == installed_version
            present = True
        self.debug_info['present'] = present
        return present

    def install_package(self, name, version):
        """Install a new package."""
        if version is not None:
            self._run_R_function('devtools::install_version', name, version=version, check_rc=True)
            self.debug_info['install'] = 'installed %s version %s' % (name, version)
        else:
            self._run_R_function('install.packages', name, check_rc=True)
            self.debug_info['install'] = 'installed %s' % name

    def is_old(self, name):
        """Check if an update is available for the package."""
        statement = '"{name}" %in% as.data.frame(old.packages())$Package'.format(name=name)
        rc, out, err = self._run_R_statement(statement)
        old = self._parse_R_output(out) == 'TRUE'
        self.debug_info['old'] = old
        return old

    def update_package(self, name):
        """Update to the latest version."""
        self._run_R_function('update.packages', oldPkgs=name, ask='FALSE')
        self.debug_info['update'] = 'Updated %s to latest version' % name

    def remove_package(self, name):
        """Uninstall a package."""
        self._run_R_function('remove.packages', name)
        self.debug_info['remove'] = 'Removed %s' % name


def main():
    """Run the Ansible module"""
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            version=dict(required=False),
            state=dict(default='present', choices=['present', 'latest', 'absent']),
            executable=dict(required=False),
            lib=dict(required=False),
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    version = module.params['version']
    state = module.params['state']

    debug_info = {}
    r_installer = RInstaller(module, debug_info)
    is_present = r_installer.is_present(name, version)

    changed = False
    if state == 'present' and not is_present:
        r_installer.install_package(name, version)
        changed = True
    if state == 'latest':
        if not is_present:
            r_installer.install_package(name, version)
            changed = True
        elif r_installer.is_old(name):
            r_installer.update_package(name)
            changed = True
    elif state == 'absent' and is_present:
        r_installer.remove_package(name)
        changed = True
    module.exit_json(changed=changed, **debug_info)


if __name__ == '__main__':
    main()
