#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Matt Wright <matt@nobien.net>
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

import tempfile
import os.path

DOCUMENTATION = '''
---
module: easy_install
short_description: Installs Python libraries
description:
     - Installs Python libraries, optionally in a I(virtualenv)
version_added: "0.7"
options:
  name:
    description:
      - A Python library name
    required: true
    default: null
    aliases: []
  virtualenv:
    description:
      - an optional I(virtualenv) directory path to install into. If the
        I(virtualenv) does not exist, it is created automatically
    required: false
    default: null
  virtualenv_site_packages:
    version_added: "1.1"
    description:
      - Whether the virtual environment will inherit packages from the
        global site-packages directory.  Note that if this setting is
        changed on an already existing virtual environment it will not
        have any effect, the environment must be deleted and newly
        created.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  virtualenv_command:
    version_added: "1.1"
    description:
      - The command to create the virtual environment with. For example
        C(pyvenv), C(virtualenv), C(virtualenv2).
    required: false
    default: virtualenv
  executable:
    description:
      - The explicit executable or a pathname to the executable to be used to
        run easy_install for a specific version of Python installed in the
        system. For example C(easy_install-3.3), if there are both Python 2.7
        and 3.3 installations in the system and you want to run easy_install
        for the Python 3.3 installation.
    version_added: "1.3"
    required: false
    default: null
notes:
    - Please note that the M(easy_install) module can only install Python
      libraries. Thus this module is not able to remove libraries. It is
      generally recommended to use the M(pip) module which you can first install
      using M(easy_install).
    - Also note that I(virtualenv) must be installed on the remote host if the
      C(virtualenv) parameter is specified.
requirements: [ "virtualenv" ]
author: Matt Wright
'''

EXAMPLES = '''
# Examples from Ansible Playbooks
- easy_install: name=pip

# Install Bottle into the specified virtualenv.
- easy_install: name=bottle virtualenv=/webapps/myapp/venv
'''

def _is_package_installed(module, name, easy_install):
    cmd = '%s --dry-run %s' % (easy_install, name)
    rc, status_stdout, status_stderr = module.run_command(cmd)
    return not ('Reading' in status_stdout or 'Downloading' in status_stdout)


def _get_easy_install(module, env=None, executable=None):
    candidate_easy_inst_basenames = ['easy_install']
    easy_install = None
    if executable is not None:
        if os.path.isabs(executable):
            easy_install = executable
        else:
            candidate_easy_inst_basenames.insert(0, executable)
    if easy_install is None:
        if env is None:
            opt_dirs = []
        else:
            # Try easy_install with the virtualenv directory first.
            opt_dirs = ['%s/bin' % env]
        for basename in candidate_easy_inst_basenames:
            easy_install = module.get_bin_path(basename, False, opt_dirs)
            if easy_install is not None:
                break
    # easy_install should have been found by now.  The final call to
    # get_bin_path will trigger fail_json.
    if easy_install is None:
        basename = candidate_easy_inst_basenames[0]
        easy_install = module.get_bin_path(basename, True, opt_dirs)
    return easy_install


def main():
    arg_spec = dict(
        name=dict(required=True),
        virtualenv=dict(default=None, required=False),
        virtualenv_site_packages=dict(default='no', type='bool'),
        virtualenv_command=dict(default='virtualenv', required=False),
        executable=dict(default='easy_install', required=False),
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=True)

    name = module.params['name']
    env = module.params['virtualenv']
    executable = module.params['executable']
    site_packages = module.params['virtualenv_site_packages']
    virtualenv_command = module.params['virtualenv_command']

    rc = 0
    err = ''
    out = ''

    if env:
        virtualenv = module.get_bin_path(virtualenv_command, True)

        if not os.path.exists(os.path.join(env, 'bin', 'activate')):
            if module.check_mode:
                module.exit_json(changed=True)
            command = '%s %s' % (virtualenv, env)
            if site_packages:
                command += ' --system-site-packages'
            cwd = tempfile.gettempdir()
            rc_venv, out_venv, err_venv = module.run_command(command, cwd=cwd)

            rc += rc_venv
            out += out_venv
            err += err_venv

    easy_install = _get_easy_install(module, env, executable)

    cmd = None
    changed = False
    installed = _is_package_installed(module, name, easy_install)

    if not installed:
        if module.check_mode:
            module.exit_json(changed=True)
        cmd = '%s %s' % (easy_install, name)
        rc_easy_inst, out_easy_inst, err_easy_inst = module.run_command(cmd)

        rc += rc_easy_inst
        out += out_easy_inst
        err += err_easy_inst

        changed = True

    if rc != 0:
        module.fail_json(msg=err, cmd=cmd)

    module.exit_json(changed=changed, binary=easy_install,
                     name=name, virtualenv=env)

# import module snippets
from ansible.module_utils.basic import *

main()
