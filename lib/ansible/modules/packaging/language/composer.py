#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Dimitrios Tydeas Mengidis <tydeas.dr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: composer
author:
    - "Dimitrios Tydeas Mengidis (@dmtrs)"
    - "René Moser (@resmo)"
short_description: Dependency Manager for PHP
version_added: "1.6"
description:
    - >
      Composer is a tool for dependency management in PHP. It allows you to
      declare the dependent libraries your project needs and it will install
      them in your project for you.
options:
    command:
        version_added: "1.8"
        description:
            - Composer command like "install", "update" and so on.
        default: install
    arguments:
        version_added: "2.0"
        description:
            - Composer arguments like required package, version and so on.
    executable:
        version_added: "2.4"
        description:
            - Path to PHP Executable on the remote host, if PHP is not in PATH.
        aliases: [ php_path ]
    working_dir:
        description:
            - Directory of your project (see --working-dir). This is required when
              the command is not run globally.
            - Will be ignored if C(global_command=true).
        aliases: [ working-dir ]
    global_command:
        version_added: "2.4"
        description:
            - Runs the specified command globally.
        type: bool
        default: false
        aliases: [ global-command ]
    prefer_source:
        description:
            - Forces installation from package sources when possible (see --prefer-source).
        default: false
        type: bool
        aliases: [ prefer-source ]
    prefer_dist:
        description:
            - Forces installation from package dist even for dev versions (see --prefer-dist).
        default: false
        type: bool
        aliases: [ prefer-dist ]
    no_dev:
        description:
            - Disables installation of require-dev packages (see --no-dev).
        default: true
        type: bool
        aliases: [ no-dev ]
    no_scripts:
        description:
            - Skips the execution of all scripts defined in composer.json (see --no-scripts).
        default: false
        type: bool
        aliases: [ no-scripts ]
    no_plugins:
        description:
            - Disables all plugins ( see --no-plugins ).
        default: false
        type: bool
        aliases: [ no-plugins ]
    optimize_autoloader:
        description:
            - Optimize autoloader during autoloader dump (see --optimize-autoloader).
            - Convert PSR-0/4 autoloading to classmap to get a faster autoloader.
            - Recommended especially for production, but can take a bit of time to run.
        default: true
        type: bool
        aliases: [ optimize-autoloader ]
    ignore_platform_reqs:
        version_added: "2.0"
        description:
            - Ignore php, hhvm, lib-* and ext-* requirements and force the installation even if the local machine does not fulfill these.
        default: false
        type: bool
        aliases: [ ignore-platform-reqs ]
requirements:
    - php
    - composer installed in bin path (recommended /usr/local/bin)
notes:
    - Default options that are always appended in each execution are --no-ansi, --no-interaction and --no-progress if available.
    - We received reports about issues on macOS if composer was installed by Homebrew. Please use the official install method to avoid issues.
'''

EXAMPLES = '''
# Downloads and installs all the libs and dependencies outlined in the /path/to/project/composer.lock
- composer:
    command: install
    working_dir: /path/to/project

- composer:
    command: require
    arguments: my/package
    working_dir: /path/to/project

# Clone project and install with all dependencies
- composer:
    command: create-project
    arguments: package/package /path/to/project ~1.0
    working_dir: /path/to/project
    prefer_dist: yes

# Installs package globally
- composer:
    command: require
    global_command: yes
    arguments: my/package
'''

import re
from ansible.module_utils.basic import AnsibleModule


def parse_out(string):
    return re.sub(r"\s+", " ", string).strip()


def has_changed(string):
    return "Nothing to install or update" not in string


def get_available_options(module, command='install'):
    # get all available options from a composer command using composer help to json
    rc, out, err = composer_command(module, "help %s --format=json" % command)
    if rc != 0:
        output = parse_out(err)
        module.fail_json(msg=output)

    command_help_json = module.from_json(out)
    return command_help_json['definition']['options']


def composer_command(module, command, arguments="", options=None, global_command=False):
    if options is None:
        options = []

    if module.params['executable'] is None:
        php_path = module.get_bin_path("php", True, ["/usr/local/bin"])
    else:
        php_path = module.params['executable']

    composer_path = module.get_bin_path("composer", True, ["/usr/local/bin"])
    cmd = "%s %s %s %s %s %s" % (php_path, composer_path, "global" if global_command else "", command, " ".join(options), arguments)
    return module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            command=dict(default="install", type="str"),
            arguments=dict(default="", type="str"),
            executable=dict(type="path", aliases=["php_path"]),
            working_dir=dict(type="path", aliases=["working-dir"]),
            global_command=dict(default=False, type="bool", aliases=["global-command"]),
            prefer_source=dict(default=False, type="bool", aliases=["prefer-source"]),
            prefer_dist=dict(default=False, type="bool", aliases=["prefer-dist"]),
            no_dev=dict(default=True, type="bool", aliases=["no-dev"]),
            no_scripts=dict(default=False, type="bool", aliases=["no-scripts"]),
            no_plugins=dict(default=False, type="bool", aliases=["no-plugins"]),
            optimize_autoloader=dict(default=True, type="bool", aliases=["optimize-autoloader"]),
            ignore_platform_reqs=dict(default=False, type="bool", aliases=["ignore-platform-reqs"]),
        ),
        required_if=[('global_command', False, ['working_dir'])],
        supports_check_mode=True
    )

    # Get composer command with fallback to default
    command = module.params['command']
    if re.search(r"\s", command):
        module.fail_json(msg="Use the 'arguments' param for passing arguments with the 'command'")

    arguments = module.params['arguments']
    global_command = module.params['global_command']
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

    if not global_command:
        options.extend(['--working-dir', "'%s'" % module.params['working_dir']])

    option_params = {
        'prefer_source': 'prefer-source',
        'prefer_dist': 'prefer-dist',
        'no_dev': 'no-dev',
        'no_scripts': 'no-scripts',
        'no_plugins': 'no_plugins',
        'optimize_autoloader': 'optimize-autoloader',
        'ignore_platform_reqs': 'ignore-platform-reqs',
    }

    for param, option in option_params.items():
        if module.params.get(param) and option in available_options:
            option = "--%s" % option
            options.append(option)

    if module.check_mode:
        if 'dry-run' in available_options:
            options.append('--dry-run')
        else:
            module.exit_json(skipped=True, msg="command '%s' does not support check mode, skipping" % command)

    rc, out, err = composer_command(module, command, arguments, options, global_command)

    if rc != 0:
        output = parse_out(err)
        module.fail_json(msg=output, stdout=err)
    else:
        # Composer version > 1.0.0-alpha9 now use stderr for standard notification messages
        output = parse_out(out + err)
        module.exit_json(changed=has_changed(output), msg=output, stdout=out + err)


if __name__ == '__main__':
    main()
