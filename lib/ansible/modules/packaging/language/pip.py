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
import os

DOCUMENTATION = '''
---
module: pip
short_description: Manages Python library dependencies.
description:
     - "Manage Python library dependencies. To use this module, one of the following keys is required: C(name)
       or C(requirements)."
version_added: "0.7"
options:
  name:
    description:
      - The name of a Python library to install or the url of the remote package.
    required: false
    default: null
  version:
    description:
      - The version number to install of the Python library specified in the I(name) parameter
    required: false
    default: null
  requirements:
    description:
      - The path to a pip requirements file
    required: false
    default: null
  virtualenv:
    description:
      - An optional path to a I(virtualenv) directory to install into
    required: false
    default: null
  virtualenv_site_packages:
    version_added: "1.0"
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
    version_aded: "1.1"
    description:
      - The command or a pathname to the command to create the virtual
        environment with. For example C(pyvenv), C(virtualenv),
        C(virtualenv2), C(~/bin/virtualenv), C(/usr/local/bin/virtualenv).
    required: false
    default: virtualenv
  state:
    description:
      - The state of module
    required: false
    default: present
    choices: [ "present", "absent", "latest" ]
  extra_args:
    description:
      - Extra arguments passed to pip.
    required: false
    default: null
    version_added: "1.0"
  chdir:
    description:
      - cd into this directory before running the command
    version_added: "1.3"
    required: false
    default: null
  executable:
    description:
      - The explicit executable or a pathname to the executable to be used to
        run pip for a specific version of Python installed in the system. For
        example C(pip-3.3), if there are both Python 2.7 and 3.3 installations
        in the system and you want to run pip for the Python 3.3 installation.
    version_added: "1.3"
    required: false
    default: null
notes:
   - Please note that virtualenv (U(http://www.virtualenv.org/)) must be installed on the remote host if the virtualenv parameter is specified and the virtualenv needs to be initialized.
requirements: [ "virtualenv", "pip" ]
author: Matt Wright
'''

EXAMPLES = '''
# Install (Bottle) python package.
- pip: name=bottle

# Install (Bottle) python package on version 0.11.
- pip: name=bottle version=0.11

# Install (MyApp) using one of the remote protocols (bzr+,hg+,git+,svn+). You do not have to supply '-e' option in extra_args.
- pip: name='svn+http://myrepo/svn/MyApp#egg=MyApp'

# Install (MyApp) from local tarball
- pip: name='file:///path/to/MyApp.tar.gz'

# Install (Bottle) into the specified (virtualenv), inheriting none of the globally installed modules
- pip: name=bottle virtualenv=/my_app/venv

# Install (Bottle) into the specified (virtualenv), inheriting globally installed modules
- pip: name=bottle virtualenv=/my_app/venv virtualenv_site_packages=yes

# Install (Bottle) into the specified (virtualenv), using Python 2.7
- pip: name=bottle virtualenv=/my_app/venv virtualenv_command=virtualenv-2.7

# Install specified python requirements.
- pip: requirements=/my_app/requirements.txt

# Install specified python requirements in indicated (virtualenv).
- pip: requirements=/my_app/requirements.txt virtualenv=/my_app/venv

# Install specified python requirements and custom Index URL.
- pip: requirements=/my_app/requirements.txt extra_args='-i https://example.com/pypi/simple'

# Install (Bottle) for Python 3.3 specifically,using the 'pip-3.3' executable.
- pip: name=bottle executable=pip-3.3
'''

def _get_cmd_options(module, cmd):
    thiscmd = cmd + " --help"
    rc, stdout, stderr = module.run_command(thiscmd)
    if rc != 0:
        module.fail_json(msg="Could not get output from %s: %s" % (thiscmd, stdout + stderr))

    words = stdout.strip().split()
    cmd_options = [ x for x in words if x.startswith('--') ]
    return cmd_options
    

def _get_full_name(name, version=None):
    if version is None:
        resp = name
    else:
        resp = name + '==' + version
    return resp

def _is_present(name, version, installed_pkgs):
    for pkg in installed_pkgs:
        if '==' not in pkg:
            continue

        [pkg_name, pkg_version] = pkg.split('==')

        if pkg_name == name and (version is None or version == pkg_version):
            return True

    return False



def _get_pip(module, env=None, executable=None):
    # On Debian and Ubuntu, pip is pip.
    # On Fedora18 and up, pip is python-pip.
    # On Fedora17 and below, CentOS and RedHat 6 and 5, pip is pip-python.
    # On Fedora, CentOS, and RedHat, the exception is in the virtualenv.
    # There, pip is just pip.
    candidate_pip_basenames = ['pip', 'python-pip', 'pip-python']
    pip = None
    if executable is not None:
        if os.path.isabs(executable):
            pip = executable
        else:
            # If you define your own executable that executable should be the only candidate.
            candidate_pip_basenames = [executable]
    if pip is None:
        if env is None:
            opt_dirs = []
        else:
            # Try pip with the virtualenv directory first.
            opt_dirs = ['%s/bin' % env]
        for basename in candidate_pip_basenames:
            pip = module.get_bin_path(basename, False, opt_dirs)
            if pip is not None:
                break
    # pip should have been found by now.  The final call to get_bin_path will
    # trigger fail_json.
    if pip is None:
        basename = candidate_pip_basenames[0]
        pip = module.get_bin_path(basename, True, opt_dirs)
    return pip


def _fail(module, cmd, out, err):
    msg = ''
    if out:
        msg += "stdout: %s" % (out, )
    if err:
        msg += "\n:stderr: %s" % (err, )
    module.fail_json(cmd=cmd, msg=msg)


def main():
    state_map = dict(
        present='install',
        absent='uninstall -y',
        latest='install -U',
    )

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=state_map.keys()),
            name=dict(default=None, required=False),
            version=dict(default=None, required=False, type='str'),
            requirements=dict(default=None, required=False),
            virtualenv=dict(default=None, required=False),
            virtualenv_site_packages=dict(default='no', type='bool'),
            virtualenv_command=dict(default='virtualenv', required=False),
            use_mirrors=dict(default='yes', type='bool'),
            extra_args=dict(default=None, required=False),
            chdir=dict(default=None, required=False),
            executable=dict(default=None, required=False),
        ),
        required_one_of=[['name', 'requirements']],
        mutually_exclusive=[['name', 'requirements']],
        supports_check_mode=True
    )

    state = module.params['state']
    name = module.params['name']
    version = module.params['version']
    requirements = module.params['requirements']
    extra_args = module.params['extra_args']
    chdir = module.params['chdir']

    if state == 'latest' and version is not None:
        module.fail_json(msg='version is incompatible with state=latest')

    err = ''
    out = ''

    env = module.params['virtualenv']
    virtualenv_command = module.params['virtualenv_command']

    if env:
        env = os.path.expanduser(env)
        if not os.path.exists(os.path.join(env, 'bin', 'activate')):
            if module.check_mode:
                module.exit_json(changed=True)

            virtualenv = os.path.expanduser(virtualenv_command)
            if os.path.basename(virtualenv) == virtualenv:
                virtualenv = module.get_bin_path(virtualenv_command, True)

            if module.params['virtualenv_site_packages']:
                cmd = '%s --system-site-packages %s' % (virtualenv, env)
            else:
                cmd_opts = _get_cmd_options(module, virtualenv)
                if '--no-site-packages' in cmd_opts:
                    cmd = '%s --no-site-packages %s' % (virtualenv, env)
                else:
                    cmd = '%s %s' % (virtualenv, env)
            this_dir = tempfile.gettempdir()
            if chdir:
                this_dir = os.path.join(this_dir, chdir)
            rc, out_venv, err_venv = module.run_command(cmd, cwd=this_dir)
            out += out_venv
            err += err_venv
            if rc != 0:
                _fail(module, cmd, out, err)

    pip = _get_pip(module, env, module.params['executable'])

    cmd = '%s %s' % (pip, state_map[state])

    # If there's a virtualenv we want things we install to be able to use other
    # installations that exist as binaries within this virtualenv. Example: we 
    # install cython and then gevent -- gevent needs to use the cython binary, 
    # not just a python package that will be found by calling the right python. 
    # So if there's a virtualenv, we add that bin/ to the beginning of the PATH
    # in run_command by setting path_prefix here.
    path_prefix = None
    if env:
        path_prefix="/".join(pip.split('/')[:-1])

    # Automatically apply -e option to extra_args when source is a VCS url. VCS
    # includes those beginning with svn+, git+, hg+ or bzr+
    if name:
        if name.startswith('svn+') or name.startswith('git+') or \
                name.startswith('hg+') or name.startswith('bzr+'):
            args_list = []  # used if extra_args is not used at all
            if extra_args:
                args_list = extra_args.split(' ')
            if '-e' not in args_list:
                args_list.append('-e')
                # Ok, we will reconstruct the option string
                extra_args = ' '.join(args_list)

    if extra_args:
        cmd += ' %s' % extra_args
    if name:
        cmd += ' %s' % _get_full_name(name, version)
    elif requirements:
        cmd += ' -r %s' % requirements

    this_dir = tempfile.gettempdir()
    if chdir:
        this_dir = os.path.join(this_dir, chdir)

    if module.check_mode:
        if env or extra_args or requirements or state == 'latest' or not name:
            module.exit_json(changed=True)
        elif name.startswith('svn+') or name.startswith('git+') or \
                name.startswith('hg+') or name.startswith('bzr+'):
            module.exit_json(changed=True)

        freeze_cmd = '%s freeze' % pip
        rc, out_pip, err_pip = module.run_command(freeze_cmd, cwd=this_dir)

        if rc != 0:
            module.exit_json(changed=True)

        out += out_pip
        err += err_pip

        is_present = _is_present(name, version, out.split())

        changed = (state == 'present' and not is_present) or (state == 'absent' and is_present)
        module.exit_json(changed=changed, cmd=freeze_cmd, stdout=out, stderr=err)

    rc, out_pip, err_pip = module.run_command(cmd, path_prefix=path_prefix, cwd=this_dir)
    out += out_pip
    err += err_pip
    if rc == 1 and state == 'absent' and 'not installed' in out_pip:
        pass  # rc is 1 when attempting to uninstall non-installed package
    elif rc != 0:
        _fail(module, cmd, out, err)

    if state == 'absent':
        changed = 'Successfully uninstalled' in out_pip
    else:
        changed = 'Successfully installed' in out_pip

    module.exit_json(changed=changed, cmd=cmd, name=name, version=version,
                     state=state, requirements=requirements, virtualenv=env, stdout=out, stderr=err)

# import module snippets
from ansible.module_utils.basic import *

main()
