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
import re
import os
import sys

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
      - As of 2.2 you can supply a list of names.
    required: false
    default: null
  version:
    description:
      - The version number to install of the Python library specified in the I(name) parameter
    required: false
    default: null
  requirements:
    description:
      - The path to a pip requirements file, which should be local to the remote system. 
        File can be specified as a relative path if using the chdir option.  
    required: false
    default: null
  virtualenv:
    description:
      - An optional path to a I(virtualenv) directory to install into.
        It cannot be specified together with the 'executable' parameter
        (added in 2.1).
        If the virtualenv does not exist, it will be created before installing
        packages. The optional virtualenv_site_packages, virtualenv_command,
        and virtualenv_python options affect the creation of the virtualenv.
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
    version_added: "1.1"
    description:
      - The command or a pathname to the command to create the virtual
        environment with. For example C(pyvenv), C(virtualenv),
        C(virtualenv2), C(~/bin/virtualenv), C(/usr/local/bin/virtualenv).
    required: false
    default: virtualenv
  virtualenv_python:
    version_added: "2.0"
    description:
      - The Python executable used for creating the virtual environment.
        For example C(python3.4), C(python2.7). When not specified, the
        system Python version is used.
    required: false
    default: null
  state:
    description:
      - The state of module
      - The 'forcereinstall' option is only available in Ansible 2.1 and above.
    required: false
    default: present
    choices: [ "present", "absent", "latest", "forcereinstall" ]
  extra_args:
    description:
      - Extra arguments passed to pip.
    required: false
    default: null
    version_added: "1.0"
  editable:
    description:
      - Pass the editable flag for versioning URLs.
    required: false
    default: yes
    version_added: "2.0"
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
        It cannot be specified together with the 'virtualenv' parameter (added in 2.1).
    version_added: "1.3"
    required: false
    default: null
  umask:
    description:
      - The system umask to apply before installing the pip package. This is
        useful, for example, when installing on systems that have a very
        restrictive umask by default (e.g., 0077) and you want to pip install
        packages which are to be used by all users. Note that this requires you
        to specify desired umask mode in octal, with a leading 0 (e.g., 0077).
    version_added: "2.1"
    required: false
    default: null

notes:
   - Please note that virtualenv (U(http://www.virtualenv.org/)) must be
     installed on the remote host if the virtualenv parameter is specified and
     the virtualenv needs to be created.
requirements: [ "virtualenv", "pip" ]
author: "Matt Wright (@mattupstate)"
'''

EXAMPLES = '''
# Install (Bottle) python package.
- pip: name=bottle

# Install (Bottle) python package on version 0.11.
- pip: name=bottle version=0.11

# Install (MyApp) using one of the remote protocols (bzr+,hg+,git+,svn+). You do not have to supply '-e' option in extra_args.
- pip: name='svn+http://myrepo/svn/MyApp#egg=MyApp'

# Install MyApp using one of the remote protocols (bzr+,hg+,git+) in a non editable way.
- pip: name='git+http://myrepo/app/MyApp' editable=false

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

# Install (Bottle), forcing reinstallation if it's already installed
- pip: name=bottle state=forcereinstall

# Install (Bottle) while ensuring the umask is 0022 (to ensure other users can use it)
- pip: name=bottle umask=0022
  become: True
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
        executable = os.path.expanduser(executable)
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
        forcereinstall='install -U --force-reinstall',
    )

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=state_map.keys()),
            name=dict(type='list'),
            version=dict(type='str'),
            requirements=dict(),
            virtualenv=dict(),
            virtualenv_site_packages=dict(default=False, type='bool'),
            virtualenv_command=dict(default='virtualenv'),
            virtualenv_python=dict(type='str'),
            use_mirrors=dict(default=True, type='bool'),
            extra_args=dict(),
            editable=dict(default=True, type='bool'),
            chdir=dict(type='path'),
            executable=dict(),
            umask=dict(),
        ),
        required_one_of=[['name', 'requirements']],
        mutually_exclusive=[['name', 'requirements'], ['executable', 'virtualenv']],
        supports_check_mode=True
    )

    state = module.params['state']
    name = module.params['name']
    version = module.params['version']
    requirements = module.params['requirements']
    extra_args = module.params['extra_args']
    virtualenv_python = module.params['virtualenv_python']
    chdir = module.params['chdir']
    umask = module.params['umask']

    if umask and not isinstance(umask, int):
        try:
            umask = int(umask, 8)
        except Exception:
            module.fail_json(msg="umask must be an octal integer",
                    details=str(sys.exc_info()[1]))


    old_umask = None
    if umask != None:
        old_umask = os.umask(umask)
    try:
        if state == 'latest' and version is not None:
            module.fail_json(msg='version is incompatible with state=latest')

        if chdir is None:
            # this is done to avoid permissions issues with privilege escalation and virtualenvs
            chdir =  tempfile.gettempdir()

        err = ''
        out = ''

        env = module.params['virtualenv']
        virtualenv_command = module.params['virtualenv_command']

        if env:
            env = os.path.expanduser(env)
            if not os.path.exists(os.path.join(env, 'bin', 'activate')):
                if module.check_mode:
                    module.exit_json(changed=True)

                cmd = os.path.expanduser(virtualenv_command)
                if os.path.basename(cmd) == cmd:
                    cmd = module.get_bin_path(virtualenv_command, True)

                if module.params['virtualenv_site_packages']:
                    cmd += ' --system-site-packages'
                else:
                    cmd_opts = _get_cmd_options(module, cmd)
                    if '--no-site-packages' in cmd_opts:
                        cmd += ' --no-site-packages'

                if virtualenv_python:
                    cmd += ' -p%s' % virtualenv_python

                cmd = "%s %s" % (cmd, env)
                rc, out_venv, err_venv = module.run_command(cmd, cwd=chdir)
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
            path_prefix = "/".join(pip.split('/')[:-1])

        # Automatically apply -e option to extra_args when source is a VCS url. VCS
        # includes those beginning with svn+, git+, hg+ or bzr+
        has_vcs = False
        if name:
            for pkg in name:
                if bool(pkg and re.match(r'(svn|git|hg|bzr)\+', pkg)):
                    has_vcs = True
                    break

        if has_vcs and module.params['editable']:
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
            for pkg in name:
                cmd += ' %s' % _get_full_name(pkg, version)
        else:
            if requirements:
                cmd += ' -r %s' % requirements


        if module.check_mode:
            if extra_args or requirements or state == 'latest' or not name:
                module.exit_json(changed=True)
            elif has_vcs:
                module.exit_json(changed=True)

            freeze_cmd = '%s freeze' % pip

            rc, out_pip, err_pip = module.run_command(freeze_cmd, cwd=chdir)

            if rc != 0:
                module.exit_json(changed=True)

            out += out_pip
            err += err_pip

            if name:
                for pkg in name:
                    is_present = _is_present(pkg, version, out.split())
                    if (state == 'present' and not is_present) or (state == 'absent' and is_present):
                        changed = True
                        break
            module.exit_json(changed=changed, cmd=freeze_cmd, stdout=out, stderr=err)

        if requirements or has_vcs:
            freeze_cmd = '%s freeze' % pip
            out_freeze_before = module.run_command(freeze_cmd, cwd=chdir)[1]
        else:
            out_freeze_before = None

        rc, out_pip, err_pip = module.run_command(cmd, path_prefix=path_prefix, cwd=chdir)
        out += out_pip
        err += err_pip
        if rc == 1 and state == 'absent' and \
           ('not installed' in out_pip or 'not installed' in err_pip):
            pass  # rc is 1 when attempting to uninstall non-installed package
        elif rc != 0:
            _fail(module, cmd, out, err)

        if state == 'absent':
            changed = 'Successfully uninstalled' in out_pip
        else:
            if out_freeze_before is None:
                changed = 'Successfully installed' in out_pip
            else:
                if out_freeze_before is None:
                    changed = 'Successfully installed' in out_pip
                else:
                    out_freeze_after = module.run_command(freeze_cmd, cwd=chdir)[1]
                    changed = out_freeze_before != out_freeze_after

        module.exit_json(changed=changed, cmd=cmd, name=name, version=version,
                         state=state, requirements=requirements, virtualenv=env,
                         stdout=out, stderr=err)
    finally:
        if old_umask != None:
            os.umask(old_umask)

# import module snippets
from ansible.module_utils.basic import *

main()
