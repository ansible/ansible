#!/usr/bin/python
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
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: junos_config
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Manage configuration on devices running Juniper JUNOS
description:
  - This module provides an implementation for working with the active
    configuration running on Juniper JUNOS devices.  It provides a set
    of arguments for loading configuration, performing rollback operations
    and zeroing the active configuration on the device.
extends_documentation_fragment: junos
options:
  lines:
    description:
      - This argument takes a list of C(set) or C(delete) configuration
        lines to push into the remote device.  Each line must start with
        either C(set) or C(delete).  This argument is mutually exclusive
        with the I(src) argument.
    required: false
    default: null
  src:
    description:
      - The I(src) argument provides a path to the configuration file
        to load into the remote system.  The path can either be a full
        system path to the configuration file if the value starts with /
        or relative to the root of the implemented role or playbook.
        This argument is mutually exclusive with the I(lines) argument.
    required: false
    default: null
    version_added: "2.2"
  src_format:
    description:
      - The I(src_format) argument specifies the format of the configuration
        found int I(src).  If the I(src_format) argument is not provided,
        the module will attempt to determine the format of the configuration
        file specified in I(src).
    required: false
    default: null
    choices: ['xml', 'set', 'text', 'json']
    version_added: "2.2"
  rollback:
    description:
      - The C(rollback) argument instructs the module to rollback the
        current configuration to the identifier specified in the
        argument.  If the specified rollback identifier does not
        exist on the remote device, the module will fail.  To rollback
        to the most recent commit, set the C(rollback) argument to 0.
    required: false
    default: null
  zeroize:
    description:
      - The C(zeroize) argument is used to completely sanitize the
        remote device configuration back to initial defaults.  This
        argument will effectively remove all current configuration
        statements on the remote device.
    required: false
    default: null
  confirm:
    description:
      - The C(confirm) argument will configure a time out value for
        the commit to be confirmed before it is automatically
        rolled back.  If the C(confirm) argument is set to False, this
        argument is silently ignored.  If the value for this argument
        is set to 0, the commit is confirmed immediately.
    required: false
    default: 0
  comment:
    description:
      - The C(comment) argument specifies a text string to be used
        when committing the configuration.  If the C(confirm) argument
        is set to False, this argument is silently ignored.
    required: false
    default: configured by junos_config
  replace:
    description:
      - The C(replace) argument will instruct the remote device to
        replace the current configuration hierarchy with the one specified
        in the corresponding hierarchy of the source configuration loaded
        from this module.
      - Note this argument should be considered deprecated.  To achieve
        the equivalent, set the I(update) argument to C(replace). This argument
        will be removed in a future release. The C(replace) and C(update) argument
        is mutually exclusive.
    required: false
    choices: ['yes', 'no']
    default: false
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory.  If the directory does not
        exist, it is created.
    required: false
    default: no
    choices: ['yes', 'no']
    version_added: "2.2"
  update:
    description:
      - This argument will decide how to load the configuration
        data particulary when the candidate configuration and loaded
        configuration contain conflicting statements. Following are
        accepted values.
        C(merge) combines the data in the loaded configuration with the
        candidate configuration. If statements in the loaded configuration
        conflict with statements in the candidate configuration, the loaded
        statements replace the candidate ones.
        C(override) discards the entire candidate configuration and replaces
        it with the loaded configuration.
        C(replace) substitutes each hierarchy level in the loaded configuration
        for the corresponding level.
    required: false
    default: merge
    choices: ['merge', 'override', 'replace']
    version_added: "2.3"
requirements:
  - junos-eznc
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
"""

EXAMPLES = """
- name: load configure file into device
  junos_config:
    src: srx.cfg
    comment: update config
    provider: "{{ netconf }}"

- name: rollback the configuration to id 10
  junos_config:
    rollback: 10
    provider: "{{ netconf }}"

- name: zero out the current configuration
  junos_config:
    zeroize: yes
    provider: "{{ netconf }}"

- name: confirm a previous commit
  junos_config:
    provider: "{{ netconf }}"
"""

RETURN = """
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: path
  sample: /playbooks/ansible/backup/config.2016-07-16@22:28:34
"""
import re
import json
import sys

from xml.etree import ElementTree

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import get_diff, load_config, get_configuration
from ansible.module_utils.junos import junos_argument_spec
from ansible.module_utils.junos import check_args as junos_check_args
from ansible.module_utils.netconf import send_request
from ansible.module_utils.six import string_types

if sys.version_info < (2, 7):
    from xml.parsers.expat import ExpatError
    ParseError = ExpatError
else:
    ParseError = ElementTree.ParseError

USE_PERSISTENT_CONNECTION = True
DEFAULT_COMMENT = 'configured by junos_config'

def check_args(module, warnings):
    junos_check_args(module, warnings)

    if module.params['replace'] is not None:
        module.fail_json(msg='argument replace is deprecated, use update')

zeroize = lambda x: send_request(x, ElementTree.Element('request-system-zeroize'))
rollback = lambda x: get_diff(x)

def guess_format(config):
    try:
        json.loads(config)
        return 'json'
    except ValueError:
        pass

    try:
        ElementTree.fromstring(config)
        return 'xml'
    except ParseError:
        pass

    if config.startswith('set') or config.startswith('delete'):
        return 'set'

    return 'text'

def filter_delete_statements(module, candidate):
    reply = get_configuration(module, format='set')
    match = reply.find('.//configuration-set')
    if match is None:
        # Could not find configuration-set in reply, perhaps device does not support it?
        return candidate
    config = str(match.text)

    modified_candidate = candidate[:]
    for index, line in reversed(list(enumerate(candidate))):
        if line.startswith('delete'):
            newline = re.sub('^delete', 'set', line)
            if newline not in config:
                del modified_candidate[index]

    return modified_candidate

def configure_device(module, warnings):
    candidate = module.params['lines'] or module.params['src']

    kwargs = {
        'comment': module.params['comment'],
        'commit': not module.check_mode
    }

    if module.params['confirm'] > 0:
        kwargs.update({
            'confirm': True,
            'confirm_timeout': module.params['confirm']
        })

    config_format = None

    if module.params['src']:
        config_format = module.params['src_format'] or guess_format(str(candidate))
        if config_format == 'set':
            kwargs.update({'format': 'text', 'action': 'set'})
        else:
            kwargs.update({'format': config_format, 'action': module.params['update']})

    if isinstance(candidate, string_types):
        candidate = candidate.split('\n')

    # this is done to filter out `delete ...` statements which map to
    # nothing in the config as that will cause an exception to be raised
    if any((module.params['lines'], config_format == 'set')):
        candidate = filter_delete_statements(module, candidate)
        kwargs['format'] = 'text'
        kwargs['action'] = 'set'

    return load_config(module, candidate, warnings, **kwargs)

def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        lines=dict(type='list'),

        src=dict(type='path'),
        src_format=dict(choices=['xml', 'text', 'set', 'json']),

        # update operations
        update=dict(default='merge', choices=['merge', 'override', 'replace', 'update']),

        # deprecated replace in Ansible 2.3
        replace=dict(type='bool'),

        confirm=dict(default=0, type='int'),
        comment=dict(default=DEFAULT_COMMENT),

        # config operations
        backup=dict(type='bool', default=False),
        rollback=dict(type='int'),

        zeroize=dict(default=False, type='bool'),
    )

    argument_spec.update(junos_argument_spec)

    mutually_exclusive = [('lines', 'src', 'rollback', 'zeroize')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

    if module.params['backup']:
        for conf_format in ['set', 'text']:
            reply = get_configuration(module, format=conf_format)
            match = reply.find('.//configuration-%s' % conf_format)
            if match is not None:
                break
        else:
            module.fail_json(msg='unable to retrieve device configuration')

        result['__backup__'] = str(match.text).strip()

    if module.params['rollback']:
        if not module.check_mode:
            diff = rollback(module)
            if module._diff:
                result['diff'] = {'prepared': diff}
        result['changed'] = True

    elif module.params['zeroize']:
        if not module.check_mode:
            zeroize(module)
        result['changed'] = True

    else:
        diff = configure_device(module, warnings)
        if diff:
            if module._diff:
                result['diff'] = {'prepared': diff}
            result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
