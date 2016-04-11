#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Dimitrios Tydeas Mengidis <tydeas.dr@gmail.com>

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

DOCUMENTATION = '''
---
module: composer
author:
    - "Dimitrios Tydeas Mengidis (@dmtrs)"
    - "René Moser (@resmo)"
short_description: Dependency Manager for PHP
version_added: "1.6"
description:
    - Composer is a tool for dependency management in PHP. It allows you to declare the dependent libraries your project needs and it will install them in your project for you
options:
    command:
        version_added: "1.8"
        description:
            - Composer command like "install", "update" and so on
        required: false
        default: install
    arguments:
        version_added: "2.0"
        description:
            - Composer arguments like required package, version and so on
        required: false
        default: null
    working_dir:
        description:
            - Directory of your project ( see --working-dir )
        required: true
        default: null
        aliases: [ "working-dir" ]
    prefer_source:
        description:
            - Forces installation from package sources when possible ( see --prefer-source )
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        aliases: [ "prefer-source" ]
    prefer_dist:
        description:
            - Forces installation from package dist even for dev versions ( see --prefer-dist )
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        aliases: [ "prefer-dist" ]
    no_dev:
        description:
            - Disables installation of require-dev packages ( see --no-dev )
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
        aliases: [ "no-dev" ]
    no_scripts:
        description:
            - Skips the execution of all scripts defined in composer.json ( see --no-scripts )
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        aliases: [ "no-scripts" ]
    no_plugins:
        description:
            - Disables all plugins ( see --no-plugins )
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        aliases: [ "no-plugins" ]
    optimize_autoloader:
        description:
            - Optimize autoloader during autoloader dump ( see --optimize-autoloader ). Convert PSR-0/4 autoloading to classmap to get a faster autoloader. This is recommended especially for production, but can take a bit of time to run so it is currently not done by default.
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
        aliases: [ "optimize-autoloader" ]
    ignore_platform_reqs:
        version_added: "2.0"
        description:
            - Ignore php, hhvm, lib-* and ext-* requirements and force the installation even if the local machine does not fulfill these.
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        aliases: [ "ignore-platform-reqs" ]
requirements:
    - php
    - composer installed in bin path (recommended /usr/local/bin)
notes:
    - Default options that are always appended in each execution are --no-ansi, --no-interaction and --no-progress if available.
'''

EXAMPLES = '''
# Downloads and installs all the libs and dependencies outlined in the /path/to/project/composer.lock
- composer: command=install working_dir=/path/to/project

- composer:
    command: "require"
    arguments: "my/package"
    working_dir: "/path/to/project"

# Clone project and install with all dependencies
- composer:
    command: "create-project"
    arguments: "package/package /path/to/project ~1.0"
    working_dir: "/path/to/project"
    prefer_dist: "yes"
'''

import os
import re

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Let snippet from module_utils/basic.py return a proper error in this case
        pass


def parse_out(string):
    return re.sub("\s+", " ", string).strip()

def has_changed(string):
    return "Nothing to install or update" not in string

def get_available_options(module, command='install'):
    # get all availabe options from a composer command using composer help to json
    rc, out, err = composer_command(module, "help %s --format=json" % command)
    if rc != 0:
        output = parse_out(err)
        module.fail_json(msg=output)

    command_help_json = json.loads(out)
    return command_help_json['definition']['options']

def composer_command(module, command, arguments = "", options=[]):
    php_path      = module.get_bin_path("php", True, ["/usr/local/bin"])
    composer_path = module.get_bin_path("composer", True, ["/usr/local/bin"])
    cmd           = "%s %s %s %s %s" % (php_path, composer_path, command, " ".join(options), arguments)
    return module.run_command(cmd)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            command              = dict(default="install", type="str", required=False),
            arguments            = dict(default="", type="str", required=False),
            working_dir          = dict(aliases=["working-dir"], required=True),
            prefer_source        = dict(default="no", type="bool", aliases=["prefer-source"]),
            prefer_dist          = dict(default="no", type="bool", aliases=["prefer-dist"]),
            no_dev               = dict(default="yes", type="bool", aliases=["no-dev"]),
            no_scripts           = dict(default="no", type="bool", aliases=["no-scripts"]),
            no_plugins           = dict(default="no", type="bool", aliases=["no-plugins"]),
            optimize_autoloader  = dict(default="yes", type="bool", aliases=["optimize-autoloader"]),
            ignore_platform_reqs = dict(default="no", type="bool", aliases=["ignore-platform-reqs"]),
        ),
        supports_check_mode=True
    )

    # Get composer command with fallback to default
    command = module.params['command']
    if re.search(r"\s", command):
        module.fail_json(msg="Use the 'arguments' param for passing arguments with the 'command'")

    arguments = module.params['arguments']
    available_options = get_available_options(module=module, command=command)

    options = []

    # Default options
    default_options = [
        'no-ansi',
        'no-interaction',
        'no-progress',
    ]

    for option in default_options:
        if option in available_options:
            option = "--%s" % option
            options.append(option)

    options.extend(['--working-dir', os.path.abspath(module.params['working_dir'])])

    option_params = {
        'prefer_source':        'prefer-source',
        'prefer_dist':          'prefer-dist',
        'no_dev':               'no-dev',
        'no_scripts':           'no-scripts',
        'no_plugins':           'no_plugins',
        'optimize_autoloader':  'optimize-autoloader',
        'ignore_platform_reqs': 'ignore-platform-reqs',
        }

    for param, option in option_params.iteritems():
        if module.params.get(param) and option in available_options:
            option = "--%s" % option
            options.append(option)

    if module.check_mode:
        options.append('--dry-run')

    rc, out, err = composer_command(module, command, arguments, options)

    if rc != 0:
        output = parse_out(err)
        module.fail_json(msg=output, stdout=err)
    else:
        # Composer version > 1.0.0-alpha9 now use stderr for standard notification messages
        output = parse_out(out + err)
        module.exit_json(changed=has_changed(output), msg=output, stdout=out+err)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
