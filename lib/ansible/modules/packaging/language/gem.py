#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Johan Wiren <johan.wiren.se@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gem
short_description: Manage Ruby gems
description:
  - Manage installation and uninstallation of Ruby gems.
version_added: "1.1"
options:
  name:
    description:
      - The name of the gem to be managed.
    required: true
  state:
    description:
      - The desired state of the gem. C(latest) ensures that the latest version is installed.
    required: false
    choices: [present, absent, latest]
    default: present
  gem_source:
    description:
      - The path to a local gem used as installation source.
    required: false
  include_dependencies:
    description:
      - Whether to include dependencies or not.
    required: false
    type: bool
    default: "yes"
  repository:
    description:
      - The repository from which the gem will be installed
    required: false
    aliases: [source]
  user_install:
    description:
      - Install gem in user's local gems cache or for all users
    required: false
    type: bool
    default: "yes"
    version_added: "1.3"
  executable:
    description:
    - Override the path to the gem executable
    required: false
    version_added: "1.4"
  install_dir:
    description:
    - Install the gems into a specific directory.
      These gems will be independant from the global installed ones.
      Specifying this requires user_install to be false.
    required: false
    version_added: "2.6"
  env_shebang:
    description:
      - Rewrite the shebang line on installed scripts to use /usr/bin/env.
    required: false
    default: "no"
    type: bool
    version_added: "2.2"
  version:
    description:
      - Version of the gem to be installed/removed.
    required: false
  pre_release:
    description:
      - Allow installation of pre-release versions of the gem.
    required: false
    default: "no"
    type: bool
    version_added: "1.6"
  include_doc:
    description:
      - Install with or without docs.
    required: false
    default: "no"
    type: bool
    version_added: "2.0"
  build_flags:
    description:
      - Allow adding build flags for gem compilation
    required: false
    version_added: "2.0"
  force:
    description:
      - Force gem to install, bypassing dependency checks.
    required: false
    default: "no"
    type: bool
    version_added: "2.8"
author:
    - "Ansible Core Team"
    - "Johan Wiren (@johanwiren)"
'''

EXAMPLES = '''
# Installs version 1.0 of vagrant.
- gem:
    name: vagrant
    version: 1.0
    state: present

# Installs latest available version of rake.
- gem:
    name: rake
    state: latest

# Installs rake version 1.0 from a local gem on disk.
- gem:
    name: rake
    gem_source: /path/to/gems/rake-1.0.gem
    state: present
'''

import re

from ansible.module_utils.basic import AnsibleModule


def get_rubygems_path(module):
    if module.params['executable']:
        result = module.params['executable'].split(' ')
    else:
        result = [module.get_bin_path('gem', True)]
    return result


def get_rubygems_version(module):
    cmd = get_rubygems_path(module) + ['--version']
    (rc, out, err) = module.run_command(cmd, check_rc=True)

    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', out)
    if not match:
        return None

    return tuple(int(x) for x in match.groups())


def get_rubygems_environ(module):
    if module.params['install_dir']:
        return {'GEM_HOME': module.params['install_dir']}
    return None


def get_installed_versions(module, remote=False):

    cmd = get_rubygems_path(module)
    cmd.append('query')
    if remote:
        cmd.append('--remote')
        if module.params['repository']:
            cmd.extend(['--source', module.params['repository']])
    cmd.append('-n')
    cmd.append('^%s$' % module.params['name'])

    environ = get_rubygems_environ(module)
    (rc, out, err) = module.run_command(cmd, environ_update=environ, check_rc=True)
    installed_versions = []
    for line in out.splitlines():
        match = re.match(r"\S+\s+\((.+)\)", line)
        if match:
            versions = match.group(1)
            for version in versions.split(', '):
                installed_versions.append(version.split()[0])
    return installed_versions


def exists(module):
    if module.params['state'] == 'latest':
        remoteversions = get_installed_versions(module, remote=True)
        if remoteversions:
            module.params['version'] = remoteversions[0]
    installed_versions = get_installed_versions(module)
    if module.params['version']:
        if module.params['version'] in installed_versions:
            return True
    else:
        if installed_versions:
            return True
    return False


def uninstall(module):

    if module.check_mode:
        return
    cmd = get_rubygems_path(module)
    environ = get_rubygems_environ(module)
    cmd.append('uninstall')
    if module.params['install_dir']:
        cmd.extend(['--install-dir', module.params['install_dir']])

    if module.params['version']:
        cmd.extend(['--version', module.params['version']])
    else:
        cmd.append('--all')
        cmd.append('--executable')
    cmd.append(module.params['name'])
    module.run_command(cmd, environ_update=environ, check_rc=True)


def install(module):

    if module.check_mode:
        return

    ver = get_rubygems_version(module)
    if ver:
        major = ver[0]
    else:
        major = None

    cmd = get_rubygems_path(module)
    cmd.append('install')
    if module.params['version']:
        cmd.extend(['--version', module.params['version']])
    if module.params['repository']:
        cmd.extend(['--source', module.params['repository']])
    if not module.params['include_dependencies']:
        cmd.append('--ignore-dependencies')
    else:
        if major and major < 2:
            cmd.append('--include-dependencies')
    if module.params['user_install']:
        cmd.append('--user-install')
    else:
        cmd.append('--no-user-install')
    if module.params['install_dir']:
        cmd.extend(['--install-dir', module.params['install_dir']])
    if module.params['pre_release']:
        cmd.append('--pre')
    if not module.params['include_doc']:
        if major and major < 2:
            cmd.append('--no-rdoc')
            cmd.append('--no-ri')
        else:
            cmd.append('--no-document')
    if module.params['env_shebang']:
        cmd.append('--env-shebang')
    cmd.append(module.params['gem_source'])
    if module.params['build_flags']:
        cmd.extend(['--', module.params['build_flags']])
    if module.params['force']:
        cmd.append('--force')
    module.run_command(cmd, check_rc=True)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(required=False, type='path'),
            gem_source=dict(required=False, type='path'),
            include_dependencies=dict(required=False, default=True, type='bool'),
            name=dict(required=True, type='str'),
            repository=dict(required=False, aliases=['source'], type='str'),
            state=dict(required=False, default='present', choices=['present', 'absent', 'latest'], type='str'),
            user_install=dict(required=False, default=True, type='bool'),
            install_dir=dict(required=False, type='path'),
            pre_release=dict(required=False, default=False, type='bool'),
            include_doc=dict(required=False, default=False, type='bool'),
            env_shebang=dict(required=False, default=False, type='bool'),
            version=dict(required=False, type='str'),
            build_flags=dict(required=False, type='str'),
            force=dict(required=False, default=False, type='bool'),
        ),
        supports_check_mode=True,
        mutually_exclusive=[['gem_source', 'repository'], ['gem_source', 'version']],
    )

    if module.params['version'] and module.params['state'] == 'latest':
        module.fail_json(msg="Cannot specify version when state=latest")
    if module.params['gem_source'] and module.params['state'] == 'latest':
        module.fail_json(msg="Cannot maintain state=latest when installing from local source")
    if module.params['user_install'] and module.params['install_dir']:
        module.fail_json(msg="install_dir requires user_install=false")

    if not module.params['gem_source']:
        module.params['gem_source'] = module.params['name']

    changed = False

    if module.params['state'] in ['present', 'latest']:
        if not exists(module):
            install(module)
            changed = True
    elif module.params['state'] == 'absent':
        if exists(module):
            uninstall(module)
            changed = True

    result = {}
    result['name'] = module.params['name']
    result['state'] = module.params['state']
    if module.params['version']:
        result['version'] = module.params['version']
    result['changed'] = changed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
