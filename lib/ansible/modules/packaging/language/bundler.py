#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Tim Hoiberg <tim.hoiberg@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: bundler
short_description: Manage Ruby Gem dependencies with Bundler
description:
  - Manage installation and Gem version dependencies for Ruby using the Bundler gem
version_added: "2.0.0"
options:
  executable:
    description:
      - The path to the bundler executable
    required: false
    default: null
  state:
    description:
      - The desired state of the Gem bundle. C(latest) updates gems to the most recent, acceptable version
    required: false
    choices: [present, latest]
    default: present
  chdir:
    description:
      - The directory to execute the bundler commands from. This directoy
        needs to contain a valid Gemfile or .bundle/ directory
    required: false
    default: temporary working directory
  exclude_groups:
    description:
      - A list of Gemfile groups to exclude during operations. This only
        applies when state is C(present). Bundler considers this
        a 'remembered' property for the Gemfile and will automatically exclude
        groups in future operations even if C(exclude_groups) is not set
    required: false
    default: null
  clean:
    description:
      - Only applies if state is C(present). If set removes any gems on the
        target host that are not in the gemfile
    required: false
    choices: [yes, no]
    default: "no"
  gemfile:
    description:
      - Only applies if state is C(present). The path to the gemfile to use to install gems.
    required: false
    default: Gemfile in current directory
  local:
    description:
      - If set only installs gems from the cache on the target host
    required: false
    choices: [yes, no]
    default: "no"
  deployment_mode:
    description:
      - Only applies if state is C(present). If set it will only install gems
        that are in the default or production groups. Requires a Gemfile.lock
        file to have been created prior
    required: false
    choices: [yes, no]
    default: "no"
  user_install:
    description:
      - Only applies if state is C(present). Installs gems in the local user's cache or for all users
    required: false
    choices: [yes, no]
    default: "yes"
  gem_path:
    description:
      - Only applies if state is C(present). Specifies the directory to
        install the gems into. If C(chdir) is set then this path is relative to
        C(chdir)
    required: false
    default: RubyGems gem paths
  binstub_directory:
    description:
      - Only applies if state is C(present). Specifies the directory to
        install any gem bins files to. When executed the bin files will run
        within the context of the Gemfile and fail if any required gem
        dependencies are not installed. If C(chdir) is set then this path is
        relative to C(chdir)
    required: false
    default: null
  extra_args:
    description:
      - A space separated string of additional commands that can be applied to
        the Bundler command. Refer to the Bundler documentation for more
        information
    required: false
    default: null
author: "Tim Hoiberg (@thoiberg)"
'''

EXAMPLES = '''
# Installs gems from a Gemfile in the current directory
- bundler:
    state: present
    executable: ~/.rvm/gems/2.1.5/bin/bundle

# Excludes the production group from installing
- bundler:
    state: present
    exclude_groups: production

# Only install gems from the default and production groups
- bundler:
    state: present
    deployment_mode: yes

# Installs gems using a Gemfile in another directory
- bundler:
    state: present
    gemfile: ../rails_project/Gemfile

# Updates Gemfile in another directory
- bundler:
    state: latest
    chdir: ~/rails_project
'''

from ansible.module_utils.basic import AnsibleModule


def get_bundler_executable(module):
    if module.params.get('executable'):
        result = module.params.get('executable').split(' ')
    else:
        result = [module.get_bin_path('bundle', True)]
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(default=None, required=False),
            state=dict(default='present', required=False, choices=['present', 'latest']),
            chdir=dict(default=None, required=False, type='path'),
            exclude_groups=dict(default=None, required=False, type='list'),
            clean=dict(default=False, required=False, type='bool'),
            gemfile=dict(default=None, required=False, type='path'),
            local=dict(default=False, required=False, type='bool'),
            deployment_mode=dict(default=False, required=False, type='bool'),
            user_install=dict(default=True, required=False, type='bool'),
            gem_path=dict(default=None, required=False, type='path'),
            binstub_directory=dict(default=None, required=False, type='path'),
            extra_args=dict(default=None, required=False),
        ),
        supports_check_mode=True
    )

    state = module.params.get('state')
    chdir = module.params.get('chdir')
    exclude_groups = module.params.get('exclude_groups')
    clean = module.params.get('clean')
    gemfile = module.params.get('gemfile')
    local = module.params.get('local')
    deployment_mode = module.params.get('deployment_mode')
    user_install = module.params.get('user_install')
    gem_path = module.params.get('gem_path')
    binstub_directory = module.params.get('binstub_directory')
    extra_args = module.params.get('extra_args')

    cmd = get_bundler_executable(module)

    if module.check_mode:
        cmd.append('check')
        rc, out, err = module.run_command(cmd, cwd=chdir, check_rc=False)

        module.exit_json(changed=rc != 0, state=state, stdout=out, stderr=err)

    if state == 'present':
        cmd.append('install')
        if exclude_groups:
            cmd.extend(['--without', ':'.join(exclude_groups)])
        if clean:
            cmd.append('--clean')
        if gemfile:
            cmd.extend(['--gemfile', gemfile])
        if local:
            cmd.append('--local')
        if deployment_mode:
            cmd.append('--deployment')
        if not user_install:
            cmd.append('--system')
        if gem_path:
            cmd.extend(['--path', gem_path])
        if binstub_directory:
            cmd.extend(['--binstubs', binstub_directory])
    else:
        cmd.append('update')
        if local:
            cmd.append('--local')

    if extra_args:
        cmd.extend(extra_args.split(' '))

    rc, out, err = module.run_command(cmd, cwd=chdir, check_rc=True)

    module.exit_json(changed='Installing' in out, state=state, stdout=out, stderr=err)


if __name__ == '__main__':
    main()
