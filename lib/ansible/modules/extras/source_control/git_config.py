#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Marius Gedminas <marius@pov.lt>
# (c) 2016, Matthew Gamble <git@matthewgamble.net>
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

DOCUMENTATION = '''
---
module: git_config
author:
  - "Matthew Gamble"
  - "Marius Gedminas"
version_added: 2.1
requirements: ['git']
short_description: Read and write git configuration
description:
  - The M(git_config) module changes git configuration by invoking 'git config'.
    This is needed if you don't want to use M(template) for the entire git
    config file (e.g. because you need to change just C(user.email) in
    /etc/.git/config).  Solutions involving M(command) are cumbersone or
    don't work correctly in check mode.
options:
  list_all:
    description:
      - List all settings (optionally limited to a given I(scope))
    required: false
    choices: [ "yes", "no" ]
    default: no
  name:
    description:
      - The name of the setting. If no value is supplied, the value will
        be read from the config if it has been set.
    required: false
    default: null
  repo:
    description:
      - Path to a git repository for reading and writing values from a
        specific repo.
    required: false
    default: null
  scope:
    description:
      - Specify which scope to read/set values from. This is required
        when setting config values. If this is set to local, you must
        also specify the repo parameter. It defaults to system only when
        not using I(list_all)=yes.
    required: false
    choices: [ "local", "global", "system" ]
    default: null
  value:
    description:
      - When specifying the name of a single setting, supply a value to
        set that setting to the given value.
    required: false
    default: null
'''

EXAMPLES = '''
# Set some settings in ~/.gitconfig
- git_config: name=alias.ci scope=global value=commit
- git_config: name=alias.st scope=global value=status

# Or system-wide:
- git_config: name=alias.remotev scope=system value="remote -v"
- git_config: name=core.editor scope=global value=vim
# scope=system is the default
- git_config: name=alias.diffc value="diff --cached"
- git_config: name=color.ui value=auto

# Make etckeeper not complain when invoked by cron
- git_config: name=user.email repo=/etc scope=local value="root@{{ ansible_fqdn }}"

# Read individual values from git config
- git_config: name=alias.ci scope=global
# scope=system is also assumed when reading values, unless list_all=yes
- git_config: name=alias.diffc

# Read all values from git config
- git_config: list_all=yes scope=global
# When list_all=yes and no scope is specified, you get configuration from all scopes
- git_config: list_all=yes
# Specify a repository to include local settings
- git_config: list_all=yes repo=/path/to/repo.git
'''

RETURN = '''
---
config_value:
  description: When list_all=no and value is not set, a string containing the value of the setting in name
  returned: success
  type: string
  sample: "vim"

config_values:
  description: When list_all=yes, a dict containing key/value pairs of multiple configuration settings
  returned: success
  type: dictionary
  sample:
    core.editor: "vim"
    color.ui: "auto"
    alias.diffc: "diff --cached"
    alias.remotev: "remote -v"
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            list_all=dict(required=False, type='bool', default=False),
            name=dict(type='str'),
            repo=dict(type='path'),
            scope=dict(required=False, type='str', choices=['local', 'global', 'system']),
            value=dict(required=False)
        ),
        mutually_exclusive=[['list_all', 'name'], ['list_all', 'value']],
        required_if=[('scope', 'local', ['repo'])],
        required_one_of=[['list_all', 'name']],
        supports_check_mode=True,
    )
    git_path = module.get_bin_path('git')
    if not git_path:
        module.fail_json(msg="Could not find git. Please ensure it is installed.")

    params = module.params
    # We check error message for a pattern, so we need to make sure the messages appear in the form we're expecting.
    # Set the locale to C to ensure consistent messages.
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    if params['name']:
        name = params['name']
    else:
        name = None

    if params['scope']:
        scope = params['scope']
    elif params['list_all']:
        scope = None
    else:
        scope = 'system'

    if params['value']:
        new_value = params['value']
    else:
        new_value = None

    args = [git_path, "config", "--includes"]
    if params['list_all']:
        args.append('-l')
    if scope:
        args.append("--" + scope)
    if name:
        args.append(name)

    if scope == 'local':
        dir = params['repo']
    elif params['list_all'] and params['repo']:
        # Include local settings from a specific repo when listing all available settings
        dir = params['repo']
    else:
        # Run from root directory to avoid accidentally picking up any local config settings
        dir = "/"

    (rc, out, err) = module.run_command(' '.join(args), cwd=dir)
    if params['list_all'] and scope and rc == 128 and 'unable to read config file' in err:
        # This just means nothing has been set at the given scope
        module.exit_json(changed=False, msg='', config_values={})
    elif rc >= 2:
        # If the return code is 1, it just means the option hasn't been set yet, which is fine.
        module.fail_json(rc=rc, msg=err, cmd=' '.join(args))

    if params['list_all']:
        values = out.rstrip().splitlines()
        config_values = {}
        for value in values:
            k, v = value.split('=', 1)
            config_values[k] = v
        module.exit_json(changed=False, msg='', config_values=config_values)
    elif not new_value:
        module.exit_json(changed=False, msg='', config_value=out.rstrip())
    else:
        old_value = out.rstrip()
        if old_value == new_value:
            module.exit_json(changed=False, msg="")

    if not module.check_mode:
        new_value_quoted = "'" + new_value + "'"
        (rc, out, err) = module.run_command(' '.join(args + [new_value_quoted]), cwd=dir)
        if err:
            module.fail_json(rc=rc, msg=err, cmd=' '.join(args + [new_value_quoted]))
    module.exit_json(
        msg='setting changed',
        diff=dict(
            before_header=' '.join(args),
            before=old_value + "\n",
            after_header=' '.join(args),
            after=new_value + "\n"
        ),
        changed=True
    )

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
