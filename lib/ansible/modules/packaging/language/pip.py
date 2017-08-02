#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Matt Wright <matt@nobien.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'curated'}


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
        For example C(python3.5), C(python2.7). When not specified, the
        Python version used to run the ansible module is used. This parameter
        should not be used when C(virtualenv_command) is using C(pyvenv) or
        the C(-m venv) module.
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
      - Pass the editable flag.
    required: false
    default: false
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
        By default, it will take the appropriate version for the python interpreter
        use by ansible, e.g. pip3 on python 3, and pip2 or pip on python 2.
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
   - By default, this module will use the appropriate version of pip for the
     interpreter used by ansible (e.g. pip3 when using python 3, pip2 otherwise)
requirements: [ "virtualenv", "pip" ]
author: "Matt Wright (@mattupstate)"
'''

EXAMPLES = '''
# Install (Bottle) python package.
- pip:
    name: bottle

# Install (Bottle) python package on version 0.11.
- pip:
    name: bottle
    version: 0.11

# Install (MyApp) using one of the remote protocols (bzr+,hg+,git+,svn+). You do not have to supply '-e' option in extra_args.
- pip:
    name: svn+http://myrepo/svn/MyApp#egg=MyApp

# Install MyApp using one of the remote protocols (bzr+,hg+,git+).
- pip:
    name: git+http://myrepo/app/MyApp

# Install (MyApp) from local tarball
- pip:
    name: file:///path/to/MyApp.tar.gz

# Install (Bottle) into the specified (virtualenv), inheriting none of the globally installed modules
- pip:
    name: bottle
    virtualenv: /my_app/venv

# Install (Bottle) into the specified (virtualenv), inheriting globally installed modules
- pip:
    name: bottle
    virtualenv: /my_app/venv
    virtualenv_site_packages: yes

# Install (Bottle) into the specified (virtualenv), using Python 2.7
- pip:
    name: bottle
    virtualenv: /my_app/venv
    virtualenv_command: virtualenv-2.7

# Install (Bottle) within a user home directory.
- pip:
    name: bottle
    extra_args: --user

# Install specified python requirements.
- pip:
    requirements: /my_app/requirements.txt

# Install specified python requirements in indicated (virtualenv).
- pip:
    requirements: /my_app/requirements.txt
    virtualenv: /my_app/venv

# Install specified python requirements and custom Index URL.
- pip:
    requirements: /my_app/requirements.txt
    extra_args: -i https://example.com/pypi/simple

# Install (Bottle) for Python 3.3 specifically,using the 'pip-3.3' executable.
- pip:
    name: bottle
    executable: pip-3.3

# Install (Bottle), forcing reinstallation if it's already installed
- pip:
    name: bottle
    state: forcereinstall

# Install (Bottle) while ensuring the umask is 0022 (to ensure other users can use it)
- pip:
    name: bottle
    umask: 0022
  become: True
'''

import os
import re
import sys
import tempfile

from ansible.module_utils.basic import AnsibleModule, is_executable
from ansible.module_utils._text import to_native
from ansible.module_utils.six import PY3


#: Python one-liners to be run at the command line that will determine the
# installed version for these special libraries.  These are libraries that
# don't end up in the output of pip freeze.
_SPECIAL_PACKAGE_CHECKERS = {'setuptools': 'import setuptools; print(setuptools.__version__)',
                             'pip': 'import pkg_resources; print(pkg_resources.get_distribution("pip").version)'}


def _get_cmd_options(module, cmd):
    thiscmd = cmd + " --help"
    rc, stdout, stderr = module.run_command(thiscmd)
    if rc != 0:
        module.fail_json(msg="Could not get output from %s: %s" % (thiscmd, stdout + stderr))

    words = stdout.strip().split()
    cmd_options = [x for x in words if x.startswith('--')]
    return cmd_options


def _get_full_name(name, version=None):
    if version is None:
        resp = name
    else:
        resp = name + '==' + version
    return resp


def _get_packages(module, pip, chdir):
    '''Return results of pip command to get packages.'''
    # Try 'pip list' command first.
    command = '%s list' % pip
    lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
    rc, out, err = module.run_command(command, cwd=chdir, environ_update=lang_env)

    # If there was an error (pip version too old) then use 'pip freeze'.
    if rc != 0:
        command = '%s freeze' % pip
        rc, out, err = module.run_command(command, cwd=chdir)
        if rc != 0:
            _fail(module, command, out, err)

    return (command, out, err)


def _is_present(name, version, installed_pkgs, pkg_command):
    '''Return whether or not package is installed.'''
    for pkg in installed_pkgs:
        # Package listing will be different depending on which pip
        # command was used ('pip list' vs. 'pip freeze').
        if 'list' in pkg_command:
            pkg = pkg.replace('(', '').replace(')', '')
            if ',' in pkg:
                pkg_name, pkg_version, _ = pkg.replace(',', '').split(' ')
            else:
                pkg_name, pkg_version = pkg.split(' ')
        elif 'freeze' in pkg_command:
            if '==' in pkg:
                pkg_name, pkg_version = pkg.split('==')
            else:
                continue
        else:
            continue

        if pkg_name == name and (version is None or version == pkg_version):
            return True

    return False


def _get_pip(module, env=None, executable=None):
    # Older pip only installed under the "/usr/bin/pip" name.  Many Linux
    # distros install it there.
    # By default, we try to use pip required for the current python
    # interpreter, so people can use pip to install modules dependencies
    candidate_pip_basenames = ('pip2', 'pip')
    if PY3:
        # pip under python3 installs the "/usr/bin/pip3" name
        candidate_pip_basenames = ('pip3',)

    pip = None
    if executable is not None:
        if os.path.isabs(executable):
            pip = executable
        else:
            # If you define your own executable that executable should be the only candidate.
            # As noted in the docs, executable doesn't work with virtualenvs.
            candidate_pip_basenames = (executable,)

    if pip is None:
        if env is None:
            opt_dirs = []
            for basename in candidate_pip_basenames:
                pip = module.get_bin_path(basename, False, opt_dirs)
                if pip is not None:
                    break
            else:
                # For-else: Means that we did not break out of the loop
                # (therefore, that pip was not found)
                module.fail_json(msg='Unable to find any of %s to use.  pip'
                        ' needs to be installed.' % ', '.join(candidate_pip_basenames))
        else:
            # If we're using a virtualenv we must use the pip from the
            # virtualenv
            venv_dir = os.path.join(env, 'bin')
            candidate_pip_basenames = (candidate_pip_basenames[0], 'pip')
            for basename in candidate_pip_basenames:
                candidate = os.path.join(venv_dir, basename)
                if os.path.exists(candidate) and is_executable(candidate):
                    pip = candidate
                    break
            else:
                # For-else: Means that we did not break out of the loop
                # (therefore, that pip was not found)
                module.fail_json(msg='Unable to find pip in the virtualenv,'
                        ' %s, under any of these names: %s. Make sure pip is'
                        ' present in the virtualenv.' % (env,
                            ', '.join(candidate_pip_basenames)))

    return pip


def _fail(module, cmd, out, err):
    msg = ''
    if out:
        msg += "stdout: %s" % (out, )
    if err:
        msg += "\n:stderr: %s" % (err, )
    module.fail_json(cmd=cmd, msg=msg)


def _get_package_info(module, package, env=None):
    """This is only needed for special packages which do not show up in pip freeze

    pip and setuptools fall into this category.

    :returns: a string containing the version number if the package is
        installed.  None if the package is not installed.
    """
    if env:
        opt_dirs = ['%s/bin' % env]
    else:
        opt_dirs = []
    python_bin = module.get_bin_path('python', False, opt_dirs)

    if python_bin is None:
        formatted_dep = None
    else:
        rc, out, err = module.run_command([python_bin, '-c', _SPECIAL_PACKAGE_CHECKERS[package]])
        if rc:
            formatted_dep = None
        else:
            formatted_dep = '%s==%s' % (package, out.strip())
    return formatted_dep


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
            requirements=dict(type='str'),
            virtualenv=dict(type='path'),
            virtualenv_site_packages=dict(default=False, type='bool'),
            virtualenv_command=dict(default='virtualenv', type='path'),
            virtualenv_python=dict(type='str'),
            use_mirrors=dict(default=True, type='bool'),
            extra_args=dict(type='str'),
            editable=dict(default=False, type='bool'),
            chdir=dict(type='path'),
            executable=dict(type='path'),
            umask=dict(type='str'),
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
                             details=to_native(sys.exc_info()[1]))

    old_umask = None
    if umask is not None:
        old_umask = os.umask(umask)
    try:
        if state == 'latest' and version is not None:
            module.fail_json(msg='version is incompatible with state=latest')

        if chdir is None:
            # this is done to avoid permissions issues with privilege escalation and virtualenvs
            chdir = tempfile.gettempdir()

        err = ''
        out = ''

        env = module.params['virtualenv']

        if env:
            if not os.path.exists(os.path.join(env, 'bin', 'activate')):
                if module.check_mode:
                    module.exit_json(changed=True)

                cmd = module.params['virtualenv_command']
                if os.path.basename(cmd) == cmd:
                    cmd = module.get_bin_path(cmd, True)

                if module.params['virtualenv_site_packages']:
                    cmd += ' --system-site-packages'
                else:
                    cmd_opts = _get_cmd_options(module, cmd)
                    if '--no-site-packages' in cmd_opts:
                        cmd += ' --no-site-packages'

                # -p is a virtualenv option, not compatible with pyenv or venv
                # this if validates if the command being used is not any of them
                if not any(ex in module.params['virtualenv_command'] for ex in ('pyvenv', '-m venv')):
                    if virtualenv_python:
                        cmd += ' -p%s' % virtualenv_python
                    elif PY3:
                        # Ubuntu currently has a patch making virtualenv always
                        # try to use python2.  Since Ubuntu16 works without
                        # python2 installed, this is a problem.  This code mimics
                        # the upstream behaviour of using the python which invoked
                        # virtualenv to determine which python is used inside of
                        # the virtualenv (when none are specified).
                        cmd += ' -p%s' % sys.executable

                # if venv or pyvenv are used and virtualenv_python is defined, then
                # virtualenv_python is ignored, this has to be acknowledged
                elif module.params['virtualenv_python']:
                    module.fail_json(
                        msg='virtualenv_python should not be used when'
                            ' using the venv module or pyvenv as virtualenv_command'
                    )

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

        if module.params['editable']:
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

            pkg_cmd, out_pip, err_pip = _get_packages(module, pip, chdir)

            out += out_pip
            err += err_pip

            changed = False
            if name:
                pkg_list = [p for p in out.split('\n') if not p.startswith('You are using') and not p.startswith('You should consider') and p]

                if pkg_cmd.endswith(' freeze') and ('pip' in name or 'setuptools' in name):
                    # Older versions of pip (pre-1.3) do not have pip list.
                    # pip freeze does not list setuptools or pip in its output
                    # So we need to get those via a specialcase
                    for pkg in ('setuptools', 'pip'):
                        if pkg in name:
                            formatted_dep = _get_package_info(module, pkg, env)
                            if formatted_dep is not None:
                                pkg_list.append(formatted_dep)
                                out += '%s\n' % formatted_dep

                for pkg in name:
                    is_present = _is_present(pkg, version, pkg_list, pkg_cmd)
                    if (state == 'present' and not is_present) or (state == 'absent' and is_present):
                        changed = True
                        break
            module.exit_json(changed=changed, cmd=pkg_cmd, stdout=out, stderr=err)

        out_freeze_before = None
        if requirements or has_vcs:
            _, out_freeze_before, _ = _get_packages(module, pip, chdir)

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
                _, out_freeze_after, _ = _get_packages(module, pip, chdir)
                changed = out_freeze_before != out_freeze_after

        module.exit_json(changed=changed, cmd=cmd, name=name, version=version,
                         state=state, requirements=requirements, virtualenv=env,
                         stdout=out, stderr=err)
    finally:
        if old_umask is not None:
            os.umask(old_umask)


if __name__ == '__main__':
    main()
