#!/usr/bin/python

# Copyright: (c) 2019, Luke Pafford <lukepafford@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: anaconda
short_description: Creates an Anaconda environment and installs required packages.
version_added: "2.9"
description:
  - Idempotently ensures that an Anaconda environment exists,
  - and the specified packages are installed.

notes:
  - Anaconda must be installed (U(https://www.anaconda.com/distribution/))
  - This module is a simple wrapper around the conda utility.
  - It will parse the output `conda env list` and `conda list`
  - to determine if any action needs to be taken. This module
  - was tested using conda V 4.6.11 with the --json output.
  - The goal of this module is to wrap the most common use cases
  - for idempotently configuring anaconda - Ensuring an environment
  - exists, using the correct python version, and installing the dependencies.
options:
  name:
      description:
          - Name of the anaconda environment.
      required: true
      type: str
  version:
      description:
          - Python version to use for the Anaconda environment.
      required: false
      type: str
      default: 3.7.3
  packages:
    description:
      - list of packages that should be installed into the environment.
    required: false
    type: list
  channels:
   description:
      - list of channels that will be enabled during the package install
   required: false
   type: list
  executable:
    description:
      - Absolute path to the conda command line program.
      - To ensure that this module always works, it is
      - recommended to set this variable.
    required: false
    type: str
    default: conda
  state:
    description:
      - Whether the environment should be present or absent.
    choices:
      - present
      - absent
    type: str
    default: 'present'
requirements:
- anaconda
author:
    - Luke Pafford (@lukepafford)
'''

EXAMPLES = '''
# Create an anaconda environment
- name: Create Anaconda environment
  anaconda:
    name: sandbox

# Create an environment, and specify the python version
- name: Create python 3.6.8 environment
  anaconda:
    name: sandbox
    version: 3.6.8

# Create environment with absolute conda path
- name: Create environment
  anaconda:
    name: sandbox
    executable: /home/anaconda/bin/conda

# Create environment and install dependencies
- name: Create flask project
  anconda:
    name: flask_project
    packages:
      - flask
      - sqlalchemy
      - gunicorn
      - celery
    channels:
      - conda-forge
'''

RETURN = '''
changed:
  description: Boolean indicating whether any action was taken on the host.
  type: bool
  returned: always

environment_created:
  description: Boolean indicating if the environment didn't exist and was created.
  type: bool
  returned: always

environment_removed:
  description: Boolean indicating if the environment was deleted
  type: bool
  returned: always

installed_packages:
  description: List of packages that were newly installed.
  type: list
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from functools import wraps
import json
import os


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        version=dict(type='str', required=False, default='3.7.3'),
        packages=dict(type='list', required=False, default=[]),
        channels=dict(type='list', required=False, default=[]),
        executable=dict(type='str', required=False, default='conda'),
        state=dict(type='str', default='present',
                   choices=['present', 'absent']),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        environment_created=False,
        environment_removed=False,
        installed_packages=[]
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
    version = module.params.get('version', '3.7.3')
    packages = module.params.get('packages', [])
    channels = module.params.get('channels', [])
    executable = module.params.get('executable', 'conda')
    state = module.params.get('state', 'present')

    def checkMode(fn):
        """ Exits the module if in check mode before performing
            state changing operation
        """
        def inner(*args, **kwargs):
            if module.check_mode:
                module.exit_json(**result)
            else:
                return fn(*args, **kwargs)
        return inner

    def subprocessError(result):
        """ Decorator to raise failure if a subprocess doesn't have
            an exit status of 0
        """
        def decorator(fn):
            @wraps(fn)
            def inner(*args, **kwargs):
                (ret, out, err) = fn(*args, **kwargs)
                if ret != 0:
                    module.fail_json(msg='args: {0} kwargs: {1}; Error: {2}'.format(
                        args, kwargs, json.loads(out)), **result)
                else:
                    return (ret, out, err)
            return inner
        return decorator

    # Build our conda executable that fails on errors, and has the default
    # executable set
    def makeConda(executable):
        """ functools.Partial doesnt work on class methods so we are setting the conda exe
            in a closure
        """
        @subprocessError(result)
        def inner(*args):
            args = list(args)
            args.insert(0, executable)
            return module.run_command(args)
        return inner

    conda = makeConda(executable)

    def _envList():
        envList = ['env', 'list', '--json']
        (ret, out, err) = conda(*envList)
        j = json.loads(out)
        envNames = map(os.path.basename, j['envs'])
        return envNames

    def envExists(name):
        """ Boolean function to check whether the environment exists """
        envNames = _envList()
        return True if name in envNames else False

    @checkMode
    def createEnv(name, version):
        create = ['create',
                  '-n',
                  name,
                  'python={0}'.format(version),
                  '--yes',
                  '--json'
                  ]
        conda(*create)

    @checkMode
    def removeEnv(name):
        remove = ['env',
                  'remove',
                  '-n',
                  name,
                  '--json'
                  ]
        conda(*remove)

    def _packageList(env):
        packageList = ['list', '-n', env, '--json']
        (ret, out, err) = conda(*packageList)
        j = json.loads(out)
        packages = map(lambda x: x['name'], j)
        return packages

    def packageState(env, packages):
        """ Given a list of packages returns a
            2 item tuple. The first item contains
            packages that are not installed in the environment.
            The second item contains packages that are installed
        """
        packages = set(packages)
        envPackages = set(_packageList(env))

        uninstalledPackages = packages.difference(envPackages)
        installedPackages = packages.intersection(envPackages)
        return (uninstalledPackages, installedPackages)

    @checkMode
    def installPackages(env, packages, channels):
        channelArgs = list()
        for channel in channels:
            channelArgs.append('-c')
            channelArgs.append(channel)

        install = ['install',
                   '-n',
                   env,
                   '--json'
                   ] + channelArgs + list(packages)
        conda(*install)

    # Begin module actions
    if envExists(name):
        # Path 1 - Environment exists and we want to remove it
        if state == 'absent':
            result['changed'] = True
            result['environment_removed'] = True
            removeEnv(name)

            # Remove the environment and exit
            module.exit_json(**result)

        # Path 2 - Environment exists, and we want to create it and install
        #          packages
        if state == 'present':
            if packages:
                (uninstalledPackages, installedPackages) = packageState(name, packages)
                result['installed_packages'] = uninstalledPackages

                # All we need to do is install the packages
                if uninstalledPackages:
                    result['changed'] = True
                    installPackages(name, uninstalledPackages, channels)
            module.exit_json(**result)

    else:
        # Path 3 - Environment doesn't exist and we want it removed
        if state == 'absent':
            # Exit with no changes
            module.exit_json(**result)

        # Path 4 - Environment doesn't exist and we want to create it
        # 				 and install packages
        if state == 'present':
            result['changed'] = True
            result['environment_created'] = True
            result['installed_packages'] = packages

            createEnv(name, version)
            if packages:
                installPackages(name, packages, channels)
                module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
