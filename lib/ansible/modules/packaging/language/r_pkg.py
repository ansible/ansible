#!/usr/bin/python

# Copyright: (c) 2018, Evan Van Dam <evandam92@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: r_pkg
short_description: A module to install and manage R packages
description:
  >
    Install, remove, and update R packages.
    Flexibility is provided to specify the R executable,
    the remote repository, source to build, and library location.
version_added: "2.7"
author: "Evan Van Dam (@evandam)"
options:
  name:
    description: The name of the targeted R package.
    required: true
  state:
    description: The target state of the package.
    choices: ["present", "absent"]
    required: true
  force:
    description: Force the package to be installed, even if it already exists.
    type: bool
    default: false
  executable:
    description: Path to the R executable. If not specified, find it from the PATH.
  src:
    description: The source file or directory to build the R package.
  lib:
    description: The library location to use to install or remove the package.
  repo:
    description: The CRAN repo to use to install the package.
notes: Requires R to already be installed. check_mode is supported.
'''

EXAMPLES = '''
- name: Install dplyr
  r_pkg:
    name: dplyr
    state: present
- name: Force dplyr to be reinstalled
  r_pkg:
    name: dplyr
    force: true
- name: Uninstall dplyr
  r_pkg:
    name: dplyr
    state: absent
- name: Install dplyr from the cloud CRAN mirror to your home lib
  r_pkg:
    name: dplyr
    repo: https://cloud.r-project.org/
    lib: "~/R"
- name: Install h2o from source
  r_pkg:
    name: h2o
    src: ~/Downloads/h2o.tar.gz
'''

RETURN = '''
msg:
  description: The output from the R command to install/remove the package.
'''

import os
from numbers import Number
from ansible.module_utils.basic import AnsibleModule


def is_package_installed(module, exe, name, lib=None):
    """Check if the package is installed.
    
    :param module: The current ansible module
    :param exe: The R executable to run
    :param name: The R package to check
    :param lib: The library directory to check. Optional.
    :returns: `True` if the package was found, `False` otherwise.
    """
    # lib.loc isn't a valid Python variable,
    # so pass kwargs as a dict and unpack it.
    retcode, _, _ = run_command(module, exe, 'find.package', name,
                                check_rc=False, **{'lib.loc': lib})
    # an error is thrown if the package isn't found,
    # so check if it exited successfully.
    return retcode == 0


def install_package(module, exe, name, src=None, lib=None, repo=None):
    """Attempt to install the R package.
    
    :param module: The current ansible module
    :param exe: The R executable to run
    :param name: The name of the R package to install
    :param src: The source file/directory of the R package to install. Optional.
    :param lib: The library to use to install the package. Optional.
    :param repo: The CRAN mirror/repo to use. Optional.
    :return: The output of the `install.packages` R command.
    """
    # Install the package from the repo to the lib.
    install_name = src or name
    _, out, _ = run_command(module, exe, 'install.packages', install_name,
                            lib=lib, repos=repo, check_rc=True)
    return out


def remove_package(module, exe, name, lib=None):
    """Attempt to remove the R package.
    
    :param module: The current ansible module
    :param exe: The R executable to run
    :param name: The name of the R package to install
    :param lib: The library to remove the package from. Optional.
    :return: The output of the `remove.packages` R command.
    """
    # Remove the package from the specified lib or the default location.
    _, out, _ = run_command(module, exe, 'remove.packages', name,
                            lib=lib, check_rc=True)
    return out


def _find_r(module):
    """Locate R in the PATH, or verify the input exists"""
    executable = module.params['executable']
    if executable:
        if os.path.isfile(executable):
            return executable
        module.fail_json(msg='{} cannot be found or is not a file'.format(executable))
    return module.get_bin_path('R', required=True)


def _escape_arg(arg):
    """Strings must be quoted. Numbers are fine as is."""
    if isinstance(arg, Number):
        return arg
    return '"{}"'.format(arg)


def build_r_function(funcname, *args, **kwargs):
    """Build an R function string to execute.

    :param funcname: The name of the R function to call
    :param args: Positional arguments to pass the R function
    :param kwargs: Keyword arguments to pass to the R function
    :return: A string of the R function with all parameters
    """
    r_args = [_escape_arg(a) for a in args]
    r_args += [k + ' = ' + _escape_arg(v) for k, v in kwargs.items() if v is not None]
    return funcname + '(' + ', '.join(r_args) + ')'


def run_command(module, exe, funcname, *args, **kwargs):
    """Build the R function and run the command.

    :param module: The current ansible module
    :param exe: The R executable to run
    :param funcname: The name of the R function to run.
    :param args: Positional arguments to pass to the R function.
    :param kwargs: Keyword arguments to pass to the R function.
    :return: A tuple of the returncode, stdout, and stderr of the command.
    """
    # Intercept the check_rc arg and use it to control module.run_command.
    try:
        check_rc = kwargs.pop('check_rc')
    except KeyError:
        check_rc = False

    # Build the function string to call in R
    func = build_r_function(funcname, *args, **kwargs)
    cmd = [exe, '--slave', '--no-save', '--no-restore', '-e', func]
    return module.run_command(cmd, check_rc=check_rc)


def main():
    """Run the Ansible module"""
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            force=dict(default=False, type='bool'),
            executable=dict(required=False),
            src=dict(required=False),
            lib=dict(required=False),
            repo=dict(required=False),
        ),
        supports_check_mode=True
    )

    exe = _find_r(module)
    name = module.params['name']
    src = module.params['src']
    state = module.params['state']
    force = module.params['force']
    lib = module.params['lib']
    repo = module.params['repo']

    installed = is_package_installed(module, exe, name, lib)
    changed = False
    msg = ''
    if state == 'absent' and installed:
        if not module.check_mode:
            msg = remove_package(module, exe, name, lib=lib)
        changed = True
    elif state == 'present' and (not installed or force):
        if not module.check_mode:
            msg = install_package(module, exe, name, src, lib=lib, repo=repo)
        changed = True
    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
