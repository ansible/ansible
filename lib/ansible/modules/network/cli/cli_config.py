#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: cli_config
version_added: "2.7"
author: "Trishna Guha (@trishnaguha)"
short_description: Push text based configuration to network devices over network_cli
description:
  - This module provides platform agnostic way of pushing text based
    configuration to network devices over network_cli connection plugin.
options:
  config:
    description:
      - The config to be pushed to the network device. This is a
        required argument.
    required: true
    type: 'str'
  commit:
    description:
      - The C(commit) argument instructs the module to push the
        configuration to the device. This is mapped to module check mode.
    type: 'bool'
  replace:
    description:
      - If the C(replace) argument is set to C(yes), it will replace
        the entire running-config of the device with the C(config)
        argument value.
    default: 'no'
    type: 'bool'
  rollback:
    description:
      - The C(rollback) argument instructs the module to rollback the
        current configuration to the identifier specified in the
        argument.  If the specified rollback identifier does not
        exist on the remote device, the module will fail.  To rollback
        to the most recent commit, set the C(rollback) argument to 0.
  commit_comment:
    description:
      - The C(commit_comment) argument specifies a text string to be used
        when committing the configuration. If the C(commit) argument
        is set to False, this argument is silently ignored. This argument
        is only valid for the platforms that support commit operation
        with comment.
    type: 'str'
  defaults:
    description:
      - The I(defaults) argument will influence how the running-config
        is collected from the device.  When the value is set to true,
        the command used to collect the running-config is append with
        the all keyword.  When the value is set to false, the command
        is issued without the all keyword.
    default: 'no'
    type: 'bool'
  multiline_delimiter:
    description:
      - This argument is used when pushing a multiline configuration
        element to the device. It specifies the character to use as
        the delimiting character. This only applies to the configuration
        action.
    type: 'str'
  diff_replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device. If the C(diff_replace) argument is set to I(line)
        then the modified lines are pushed to the device in configuration
        mode. If the argument is set to I(block) then the entire command
        block is pushed to the device in configuration mode if any
        line is not correct.
    choices: ['line', 'block', 'config']
  diff_match:
    description:
      - Instructs the module on the way to perform the matching of
        the set of commands against the current device config. If C(diff_match)
        is set to I(line), commands are matched line by line. If C(diff_match)
        is set to I(strict), command lines are matched with respect to position.
        If C(diff_match) is set to I(exact), command lines must be an equal match.
        Finally, if C(diff_match) is set to I(none), the module will not attempt
        to compare the source configuration with the running configuration on the
        remote device.
    choices: ['line', 'strict', 'exact', 'none']
  diff_ignore_lines:
    description:
      - Use this argument to specify one or more lines that should be
        ignored during the diff. This is used for lines in the configuration
        that are automatically updated by the system. This argument takes
        a list of regular expressions or exact line matches.
  severity:
    description:
      - The C(severity) argument decides what action to take if an input fails.
        If C(severity) is set to I(error) the module will fail, If C(severity)
        is set to I(warning), the module gives a warning and ignores the unsupported
        input silently.
    default: 'error'
    choices: ['error', 'warning']
"""

EXAMPLES = """
"""

RETURN = """
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['interface Loopback999', 'no shutdown']
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text


def _handle_severity(module, msg):
    """Severity of error
    """
    if module.params['severity'] == 'error':
        module.fail_json(msg=msg)
    else:
        module.warn('Skipping as ' + msg)


def validate_args(module, capabilities):
    """validate param if it is supported on the platform
    """
    if (module.params['replace'] and
            not capabilities['device_operations']['supports_replace']):
        _handle_severity(module, msg='replace is not supported on this platform')

    if (module.params['rollback'] and
            not capabilities['device_operations']['supports_rollback']):
        _handle_severity(module, msg='rollback is not supported on this platform')

    if (module.params['commit_comment'] and
            not capabilities['device_operations']['supports_commit_comment']):
        _handle_severity(module, msg='commit_comment is not supported on this platform')

    if (module.params['defaults'] and
            not capabilities['device_operations']['supports_defaults']):
        _handle_severity(module, msg='defaults is not supported on this platform')

    if (module.params['multiline_delimiter'] and
            not capabilities['device_operations']['supports_multiline_delimiter']):
        _handle_severity(module, msg='multiline_delimiter is not supported on this platform')

    if (module.params['diff_replace'] and
            not capabilities['device_operations']['supports_diff_replace']):
        _handle_severity(module, msg='diff_replace is not supported on this platform')

    if (module.params['diff_match'] and
            not capabilities['device_operations']['supports_diff_match']):
        _handle_severity(module, msg='diff_match is not supported on this platform')

    if (module.params['diff_ignore_lines'] and
            not capabilities['device_operations']['supports_diff_ignore_lines']):
        _handle_severity(module, msg='diff_ignore_lines is not supported on this platform')


def run(module, connection, candidate, running):
    result = {}

    replace = module.params['replace']
    rollback = module.params['rollback']
    commit_comment = module.params['commit_comment']
    multiline_delimiter = module.params['multiline_delimiter']
    diff_replace = module.params['diff_replace']
    diff_match = module.params['diff_match']
    diff_ignore_lines = module.params['diff_ignore_lines']

    commit = not module.check_mode

    kwargs = {'candidate': candidate, 'running': running}
    if diff_match:
        kwargs.update({'match': diff_match})
    if diff_replace:
        kwargs.update({'replace': diff_replace})
    if diff_ignore_lines:
        kwargs.update({'diff_ignore_lines': diff_ignore_lines})

    diff_response = connection.get_diff(**kwargs)

    config_diff = diff_response.get('config_diff')
    banner_diff = diff_response.get('banner_diff')

    if config_diff:
        if isinstance(config_diff, list):
            candidate = config_diff
        else:
            candidate = config_diff.splitlines()

        kwargs = {'candidate': candidate, 'commit': commit, 'replace': replace,
                  'comment': commit_comment}
        try:
            resp = connection.edit_config(**kwargs)
            if 'diff' in resp:
                if resp['diff']:
                    result['commands'] = resp['diff']
            else:
                result['commands'] = candidate
        except ConnectionError as exc:
            msg = to_text(exc)
            if 'check mode is not supported' in msg:
                _handle_severity(module, msg=msg)
            else:
                module.fail_json(msg=msg)

    if banner_diff:
        candidate = banner_diff
        result['banners'] = candidate

        kwargs = {'candidate': candidate, 'commit': commit}
        if multiline_delimiter:
            kwargs.update({'multiline_delimiter': multiline_delimiter})
        connection.edit_banner(**kwargs)

    if any(key in result for key in ('commands', 'banners')):
        result['changed'] = True

    return result


def main():
    """main entry point for execution
    """
    argument_spec = dict(
        config=dict(required=True, type='str'),
        commit=dict(type='bool'),
        replace=dict(default=False, type='bool'),
        rollback=dict(type='int'),
        commit_comment=dict(type='str'),
        defaults=dict(default=False, type='bool'),
        multiline_delimiter=dict(type='str'),
        diff_replace=dict(choices=['line', 'block', 'config']),
        diff_match=dict(choices=['line', 'strict', 'exact', 'none']),
        diff_ignore_lines=dict(type='list'),
        severity=dict(default='error', choices=['error', 'warning'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    connection = Connection(module._socket_path)
    capabilities = module.from_json(connection.get_capabilities())

    if capabilities:
        validate_args(module, capabilities)

    if module.params['defaults']:
        if 'get_default_flag' in capabilities.get('rpc'):
            filter = connection.get_default_flag()
        else:
            filter = 'all'
    else:
        filter = []

    candidate = to_text(module.params['config'])
    running = connection.get_config(filter=filter)

    try:
        result.update(run(module, connection, candidate, running))
    except Exception as exc:
        module.fail_json(msg=to_text(exc))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
