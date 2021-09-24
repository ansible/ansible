#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Matt Wright <matt@nobien.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: pip
short_description: Manages Python library dependencies
description:
     - "Manage Python library dependencies. To use this module, one of the following keys is required: C(name)
       or C(requirements)."
version_added: "0.7"
options:
  name:
    description:
      - The name of a Python library to install or the url(bzr+,hg+,git+,svn+) of the remote package.
      - This can be a list (since 2.2) and contain version specifiers (since 2.7).
    type: list
    elements: str
  version:
    description:
      - The version number to install of the Python library specified in the I(name) parameter.
    type: str
  requirements:
    description:
      - The path to a pip requirements file, which should be local to the remote system.
        File can be specified as a relative path if using the chdir option.
    type: str
  virtualenv:
    description:
      - An optional path to a I(virtualenv) directory to install into.
        It cannot be specified together with the 'executable' parameter
        (added in 2.1).
        If the virtualenv does not exist, it will be created before installing
        packages. The optional virtualenv_site_packages, virtualenv_command,
        and virtualenv_python options affect the creation of the virtualenv.
    type: path
  virtualenv_site_packages:
    description:
      - Whether the virtual environment will inherit packages from the
        global site-packages directory.  Note that if this setting is
        changed on an already existing virtual environment it will not
        have any effect, the environment must be deleted and newly
        created.
    type: bool
    default: "no"
    version_added: "1.0"
  virtualenv_command:
    description:
      - The command or a pathname to the command to create the virtual
        environment with. For example C(pyvenv), C(virtualenv),
        C(virtualenv2), C(~/bin/virtualenv), C(/usr/local/bin/virtualenv).
    type: path
    default: virtualenv
    version_added: "1.1"
  virtualenv_python:
    description:
      - The Python executable used for creating the virtual environment.
        For example C(python3.5), C(python2.7). When not specified, the
        Python version used to run the ansible module is used. This parameter
        should not be used when C(virtualenv_command) is using C(pyvenv) or
        the C(-m venv) module.
    type: str
    version_added: "2.0"
  state:
    description:
      - The state of module
      - The 'forcereinstall' option is only available in Ansible 2.1 and above.
    type: str
    choices: [ absent, forcereinstall, latest, present ]
    default: present
  extra_args:
    description:
      - Extra arguments passed to pip.
    type: str
    version_added: "1.0"
  editable:
    description:
      - Pass the editable flag.
    type: bool
    default: 'no'
    version_added: "2.0"
  chdir:
    description:
      - cd into this directory before running the command
    type: path
    version_added: "1.3"
  executable:
    description:
      - The explicit executable or pathname for the pip executable,
        if different from the Ansible Python interpreter. For
        example C(pip3.3), if there are both Python 2.7 and 3.3 installations
        in the system and you want to run pip for the Python 3.3 installation.
      - Mutually exclusive with I(virtualenv) (added in 2.1).
      - Does not affect the Ansible Python interpreter.
      - The setuptools package must be installed for both the Ansible Python interpreter
        and for the version of Python specified by this option.
    type: path
    version_added: "1.3"
  umask:
    description:
      - The system umask to apply before installing the pip package. This is
        useful, for example, when installing on systems that have a very
        restrictive umask by default (e.g., "0077") and you want to pip install
        packages which are to be used by all users. Note that this requires you
        to specify desired umask mode as an octal string, (e.g., "0022").
    type: str
    version_added: "2.1"
extends_documentation_fragment:
  -  action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    platform:
        platforms: posix
notes:
   - The virtualenv (U(http://www.virtualenv.org/)) must be
     installed on the remote host if the virtualenv parameter is specified and
     the virtualenv needs to be created.
   - Although it executes using the Ansible Python interpreter, the pip module shells out to
     run the actual pip command, so it can use any pip version you specify with I(executable).
     By default, it uses the pip version for the Ansible Python interpreter. For example, pip3 on python 3, and pip2 or pip on python 2.
   - The interpreter used by Ansible
     (see :ref:`ansible_python_interpreter<ansible_python_interpreter>`)
     requires the setuptools package, regardless of the version of pip set with
     the I(executable) option.
requirements:
- pip
- virtualenv
- setuptools
author:
- Matt Wright (@mattupstate)
'''

EXAMPLES = '''
- name: Install bottle python package
  pip:
    name: bottle

- name: Install bottle python package on version 0.11
  pip:
    name: bottle==0.11

- name: Install bottle python package with version specifiers
  pip:
    name: bottle>0.10,<0.20,!=0.11

- name: Install multi python packages with version specifiers
  pip:
    name:
      - django>1.11.0,<1.12.0
      - bottle>0.10,<0.20,!=0.11

- name: Install python package using a proxy
  # Pip doesn't use the standard environment variables, please use the CAPITALIZED ones below
  pip:
    name: six
  environment:
    HTTP_PROXY: '127.0.0.1:8080'
    HTTPS_PROXY: '127.0.0.1:8080'

# You do not have to supply '-e' option in extra_args
- name: Install MyApp using one of the remote protocols (bzr+,hg+,git+,svn+)
  pip:
    name: svn+http://myrepo/svn/MyApp#egg=MyApp

- name: Install MyApp using one of the remote protocols (bzr+,hg+,git+)
  pip:
    name: git+http://myrepo/app/MyApp

- name: Install MyApp from local tarball
  pip:
    name: file:///path/to/MyApp.tar.gz

- name: Install bottle into the specified (virtualenv), inheriting none of the globally installed modules
  pip:
    name: bottle
    virtualenv: /my_app/venv

- name: Install bottle into the specified (virtualenv), inheriting globally installed modules
  pip:
    name: bottle
    virtualenv: /my_app/venv
    virtualenv_site_packages: yes

- name: Install bottle into the specified (virtualenv), using Python 2.7
  pip:
    name: bottle
    virtualenv: /my_app/venv
    virtualenv_command: virtualenv-2.7

- name: Install bottle within a user home directory
  pip:
    name: bottle
    extra_args: --user

- name: Install specified python requirements
  pip:
    requirements: /my_app/requirements.txt

- name: Install specified python requirements in indicated (virtualenv)
  pip:
    requirements: /my_app/requirements.txt
    virtualenv: /my_app/venv

- name: Install specified python requirements and custom Index URL
  pip:
    requirements: /my_app/requirements.txt
    extra_args: -i https://example.com/pypi/simple

- name: Install specified python requirements offline from a local directory with downloaded packages
  pip:
    requirements: /my_app/requirements.txt
    extra_args: "--no-index --find-links=file:///my_downloaded_packages_dir"

- name: Install bottle for Python 3.3 specifically, using the 'pip3.3' executable
  pip:
    name: bottle
    executable: pip3.3

- name: Install bottle, forcing reinstallation if it's already installed
  pip:
    name: bottle
    state: forcereinstall

- name: Install bottle while ensuring the umask is 0022 (to ensure other users can use it)
  pip:
    name: bottle
    umask: "0022"
  become: True
'''

RETURN = '''
cmd:
  description: pip command used by the module
  returned: success
  type: str
  sample: pip2 install ansible six
name:
  description: list of python modules targetted by pip
  returned: success
  type: list
  sample: ['ansible', 'six']
requirements:
  description: Path to the requirements file
  returned: success, if a requirements file was provided
  type: str
  sample: "/srv/git/project/requirements.txt"
version:
  description: Version of the package specified in 'name'
  returned: success, if a name and version were provided
  type: str
  sample: "2.5.1"
virtualenv:
  description: Path to the virtualenv
  returned: success, if a virtualenv path was provided
  type: str
  sample: "/tmp/virtualenv"
'''

import os
import re
import sys
import tempfile
import operator
import shlex
import traceback
from ansible.module_utils.compat.version import LooseVersion

SETUPTOOLS_IMP_ERR = None
try:
    from pkg_resources import Requirement

    HAS_SETUPTOOLS = True
except ImportError:
    HAS_SETUPTOOLS = False
    SETUPTOOLS_IMP_ERR = traceback.format_exc()

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule, is_executable, missing_required_lib
from ansible.module_utils.common.locale import get_best_parsable_locale
from ansible.module_utils.six import PY3


#: Python one-liners to be run at the command line that will determine the
# installed version for these special libraries.  These are libraries that
# don't end up in the output of pip freeze.
_SPECIAL_PACKAGE_CHECKERS = {'setuptools': 'import setuptools; print(setuptools.__version__)',
                             'pip': 'import pkg_resources; print(pkg_resources.get_distribution("pip").version)'}

_VCS_RE = re.compile(r'(svn|git|hg|bzr)\+')

op_dict = {">=": operator.ge, "<=": operator.le, ">": operator.gt,
           "<": operator.lt, "==": operator.eq, "!=": operator.ne, "~=": operator.ge}


def _is_vcs_url(name):
    """Test whether a name is a vcs url or not."""
    return re.match(_VCS_RE, name)


def _is_package_name(name):
    """Test whether the name is a package name or a version specifier."""
    return not name.lstrip().startswith(tuple(op_dict.keys()))


def _recover_package_name(names):
    """Recover package names as list from user's raw input.

    :input: a mixed and invalid list of names or version specifiers
    :return: a list of valid package name

    eg.
    input: ['django>1.11.1', '<1.11.3', 'ipaddress', 'simpleproject>1.1.0', '<2.0.0']
    return: ['django>1.11.1,<1.11.3', 'ipaddress', 'simpleproject>1.1.0,<2.0.0']

    input: ['django>1.11.1,<1.11.3,ipaddress', 'simpleproject>1.1.0,<2.0.0']
    return: ['django>1.11.1,<1.11.3', 'ipaddress', 'simpleproject>1.1.0,<2.0.0']
    """
    # rebuild input name to a flat list so we can tolerate any combination of input
    tmp = []
    for one_line in names:
        tmp.extend(one_line.split(","))
    names = tmp

    # reconstruct the names
    name_parts = []
    package_names = []
    in_brackets = False
    for name in names:
        if _is_package_name(name) and not in_brackets:
            if name_parts:
                package_names.append(",".join(name_parts))
            name_parts = []
        if "[" in name:
            in_brackets = True
        if in_brackets and "]" in name:
            in_brackets = False
        name_parts.append(name)
    package_names.append(",".join(name_parts))
    return package_names


def _get_cmd_options(module, cmd):
    thiscmd = cmd + " --help"
    rc, stdout, stderr = module.run_command(thiscmd)
    if rc != 0:
        module.fail_json(msg="Could not get output from %s: %s" % (thiscmd, stdout + stderr))

    words = stdout.strip().split()
    cmd_options = [x for x in words if x.startswith('--')]
    return cmd_options


def _get_packages(module, pip, chdir):
    '''Return results of pip command to get packages.'''
    # Try 'pip list' command first.
    command = pip + ['list', '--format=freeze']
    locale = get_best_parsable_locale(module)
    lang_env = {'LANG': locale, 'LC_ALL': locale, 'LC_MESSAGES': locale}
    rc, out, err = module.run_command(command, cwd=chdir, environ_update=lang_env)

    # If there was an error (pip version too old) then use 'pip freeze'.
    if rc != 0:
        command = pip + ['freeze']
        rc, out, err = module.run_command(command, cwd=chdir)
        if rc != 0:
            _fail(module, command, out, err)

    return ' '.join(command), out, err


def _is_present(module, req, installed_pkgs, pkg_command):
    '''Return whether or not package is installed.'''
    for pkg in installed_pkgs:
        if '==' in pkg:
            pkg_name, pkg_version = pkg.split('==')
            pkg_name = Package.canonicalize_name(pkg_name)
        else:
            continue

        if pkg_name == req.package_name and req.is_satisfied_by(pkg_version):
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
    elif executable is None and env is None and _have_pip_module():
        # If no executable or virtualenv were specified, use the pip module for the current Python interpreter if available.
        # Use of `__main__` is required to support Python 2.6 since support for executing packages with `runpy` was added in Python 2.7.
        # Without it Python 2.6 gives the following error: pip is a package and cannot be directly executed
        pip = [sys.executable, '-m', 'pip.__main__']

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
                module.fail_json(msg='Unable to find pip in the virtualenv, %s, ' % env +
                                     'under any of these names: %s. ' % (', '.join(candidate_pip_basenames)) +
                                     'Make sure pip is present in the virtualenv.')

    if not isinstance(pip, list):
        pip = [pip]

    return pip


def _have_pip_module():  # type: () -> bool
    """Return True if the `pip` module can be found using the current Python interpreter, otherwise return False."""
    try:
        import importlib
    except ImportError:
        importlib = None

    if importlib:
        # noinspection PyBroadException
        try:
            # noinspection PyUnresolvedReferences
            found = bool(importlib.util.find_spec('pip'))
        except Exception:
            found = False
    else:
        # noinspection PyDeprecation
        import imp

        # noinspection PyBroadException
        try:
            # noinspection PyDeprecation
            imp.find_module('pip')
        except Exception:
            found = False
        else:
            found = True

    return found


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


def setup_virtualenv(module, env, chdir, out, err):
    if module.check_mode:
        module.exit_json(changed=True)

    cmd = shlex.split(module.params['virtualenv_command'])

    # Find the binary for the command in the PATH
    # and switch the command for the explicit path.
    if os.path.basename(cmd[0]) == cmd[0]:
        cmd[0] = module.get_bin_path(cmd[0], True)

    # Add the system-site-packages option if that
    # is enabled, otherwise explicitly set the option
    # to not use system-site-packages if that is an
    # option provided by the command's help function.
    if module.params['virtualenv_site_packages']:
        cmd.append('--system-site-packages')
    else:
        cmd_opts = _get_cmd_options(module, cmd[0])
        if '--no-site-packages' in cmd_opts:
            cmd.append('--no-site-packages')

    virtualenv_python = module.params['virtualenv_python']
    # -p is a virtualenv option, not compatible with pyenv or venv
    # this conditional validates if the command being used is not any of them
    if not any(ex in module.params['virtualenv_command'] for ex in ('pyvenv', '-m venv')):
        if virtualenv_python:
            cmd.append('-p%s' % virtualenv_python)
        elif PY3:
            # Ubuntu currently has a patch making virtualenv always
            # try to use python2.  Since Ubuntu16 works without
            # python2 installed, this is a problem.  This code mimics
            # the upstream behaviour of using the python which invoked
            # virtualenv to determine which python is used inside of
            # the virtualenv (when none are specified).
            cmd.append('-p%s' % sys.executable)

    # if venv or pyvenv are used and virtualenv_python is defined, then
    # virtualenv_python is ignored, this has to be acknowledged
    elif module.params['virtualenv_python']:
        module.fail_json(
            msg='virtualenv_python should not be used when'
                ' using the venv module or pyvenv as virtualenv_command'
        )

    cmd.append(env)
    rc, out_venv, err_venv = module.run_command(cmd, cwd=chdir)
    out += out_venv
    err += err_venv
    if rc != 0:
        _fail(module, cmd, out, err)
    return out, err


class Package:
    """Python distribution package metadata wrapper.

    A wrapper class for Requirement, which provides
    API to parse package name, version specifier,
    test whether a package is already satisfied.
    """

    _CANONICALIZE_RE = re.compile(r'[-_.]+')

    def __init__(self, name_string, version_string=None):
        self._plain_package = False
        self.package_name = name_string
        self._requirement = None

        if version_string:
            version_string = version_string.lstrip()
            separator = '==' if version_string[0].isdigit() else ' '
            name_string = separator.join((name_string, version_string))
        try:
            self._requirement = Requirement.parse(name_string)
            # old pkg_resource will replace 'setuptools' with 'distribute' when it's already installed
            if self._requirement.project_name == "distribute" and "setuptools" in name_string:
                self.package_name = "setuptools"
                self._requirement.project_name = "setuptools"
            else:
                self.package_name = Package.canonicalize_name(self._requirement.project_name)
            self._plain_package = True
        except ValueError as e:
            pass

    @property
    def has_version_specifier(self):
        if self._plain_package:
            return bool(self._requirement.specs)
        return False

    def is_satisfied_by(self, version_to_test):
        if not self._plain_package:
            return False
        try:
            return self._requirement.specifier.contains(version_to_test, prereleases=True)
        except AttributeError:
            # old setuptools has no specifier, do fallback
            version_to_test = LooseVersion(version_to_test)
            return all(
                op_dict[op](version_to_test, LooseVersion(ver))
                for op, ver in self._requirement.specs
            )

    @staticmethod
    def canonicalize_name(name):
        # This is taken from PEP 503.
        return Package._CANONICALIZE_RE.sub("-", name).lower()

    def __str__(self):
        if self._plain_package:
            return to_native(self._requirement)
        return self.package_name


def main():
    state_map = dict(
        present=['install'],
        absent=['uninstall', '-y'],
        latest=['install', '-U'],
        forcereinstall=['install', '-U', '--force-reinstall'],
    )

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=state_map.keys()),
            name=dict(type='list', elements='str'),
            version=dict(type='str'),
            requirements=dict(type='str'),
            virtualenv=dict(type='path'),
            virtualenv_site_packages=dict(type='bool', default=False),
            virtualenv_command=dict(type='path', default='virtualenv'),
            virtualenv_python=dict(type='str'),
            extra_args=dict(type='str'),
            editable=dict(type='bool', default=False),
            chdir=dict(type='path'),
            executable=dict(type='path'),
            umask=dict(type='str'),
        ),
        required_one_of=[['name', 'requirements']],
        mutually_exclusive=[['name', 'requirements'], ['executable', 'virtualenv']],
        supports_check_mode=True,
    )

    if not HAS_SETUPTOOLS:
        module.fail_json(msg=missing_required_lib("setuptools"),
                         exception=SETUPTOOLS_IMP_ERR)

    state = module.params['state']
    name = module.params['name']
    version = module.params['version']
    requirements = module.params['requirements']
    extra_args = module.params['extra_args']
    chdir = module.params['chdir']
    umask = module.params['umask']
    env = module.params['virtualenv']

    venv_created = False
    if env and chdir:
        env = os.path.join(chdir, env)

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

        if env:
            if not os.path.exists(os.path.join(env, 'bin', 'activate')):
                venv_created = True
                out, err = setup_virtualenv(module, env, chdir, out, err)

        pip = _get_pip(module, env, module.params['executable'])

        cmd = pip + state_map[state]

        # If there's a virtualenv we want things we install to be able to use other
        # installations that exist as binaries within this virtualenv. Example: we
        # install cython and then gevent -- gevent needs to use the cython binary,
        # not just a python package that will be found by calling the right python.
        # So if there's a virtualenv, we add that bin/ to the beginning of the PATH
        # in run_command by setting path_prefix here.
        path_prefix = None
        if env:
            path_prefix = os.path.join(env, 'bin')

        # Automatically apply -e option to extra_args when source is a VCS url. VCS
        # includes those beginning with svn+, git+, hg+ or bzr+
        has_vcs = False
        if name:
            for pkg in name:
                if pkg and _is_vcs_url(pkg):
                    has_vcs = True
                    break

            # convert raw input package names to Package instances
            packages = [Package(pkg) for pkg in _recover_package_name(name)]
            # check invalid combination of arguments
            if version is not None:
                if len(packages) > 1:
                    module.fail_json(
                        msg="'version' argument is ambiguous when installing multiple package distributions. "
                            "Please specify version restrictions next to each package in 'name' argument."
                    )
                if packages[0].has_version_specifier:
                    module.fail_json(
                        msg="The 'version' argument conflicts with any version specifier provided along with a package name. "
                            "Please keep the version specifier, but remove the 'version' argument."
                    )
                # if the version specifier is provided by version, append that into the package
                packages[0] = Package(to_native(packages[0]), version)

        if module.params['editable']:
            args_list = []  # used if extra_args is not used at all
            if extra_args:
                args_list = extra_args.split(' ')
            if '-e' not in args_list:
                args_list.append('-e')
                # Ok, we will reconstruct the option string
                extra_args = ' '.join(args_list)

        if extra_args:
            cmd.extend(shlex.split(extra_args))

        if name:
            cmd.extend(to_native(p) for p in packages)
        elif requirements:
            cmd.extend(['-r', requirements])
        else:
            module.exit_json(
                changed=False,
                warnings=["No valid name or requirements file found."],
            )

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

                for package in packages:
                    is_present = _is_present(module, package, pkg_list, pkg_cmd)
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

        changed = changed or venv_created

        module.exit_json(changed=changed, cmd=cmd, name=name, version=version,
                         state=state, requirements=requirements, virtualenv=env,
                         stdout=out, stderr=err)
    finally:
        if old_umask is not None:
            os.umask(old_umask)


if __name__ == '__main__':
    main()
