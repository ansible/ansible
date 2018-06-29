#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


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
  src:
    description:
      - The I(src) argument provides a path to the configuration file
        to load into the remote system. The path can either be a full
        system path to the configuration file if the value starts with /
        or relative to the root of the implemented role or playbook.
        This argument is mutually exclusive with the I(lines) argument.
    version_added: "2.2"
  src_format:
    description:
      - The I(src_format) argument specifies the format of the configuration
        found int I(src).  If the I(src_format) argument is not provided,
        the module will attempt to determine the format of the configuration
        file specified in I(src).
    choices: ['xml', 'set', 'text', 'json']
    version_added: "2.2"
  rollback:
    description:
      - The C(rollback) argument instructs the module to rollback the
        current configuration to the identifier specified in the
        argument.  If the specified rollback identifier does not
        exist on the remote device, the module will fail.  To rollback
        to the most recent commit, set the C(rollback) argument to 0.
  zeroize:
    description:
      - The C(zeroize) argument is used to completely sanitize the
        remote device configuration back to initial defaults.  This
        argument will effectively remove all current configuration
        statements on the remote device.
  confirm:
    description:
      - The C(confirm) argument will configure a time out value in minutes
        for the commit to be confirmed before it is automatically
        rolled back.  If the C(confirm) argument is set to False, this
        argument is silently ignored.  If the value for this argument
        is set to 0, the commit is confirmed immediately.
    default: 0
  comment:
    description:
      - The C(comment) argument specifies a text string to be used
        when committing the configuration.  If the C(confirm) argument
        is set to False, this argument is silently ignored.
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
    type: bool
    default: 'no'
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory or role root directory, if
        playbook is part of an ansible role. If the directory does not exist,
        it is created.
    type: bool
    default: 'no'
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
    default: merge
    choices: ['merge', 'override', 'replace']
    version_added: "2.3"
  confirm_commit:
    description:
      - This argument will execute commit operation on remote device.
        It can be used to confirm a previous commit.
    type: bool
    default: 'no'
    version_added: "2.4"
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Abbreviated commands are NOT idempotent, see
    L(Network FAQ,../network/user_guide/faq.html#why-do-the-config-modules-always-return-changed-true-with-abbreviated-commands).
  - Loading JSON-formatted configuration I(json) is supported
    starting in Junos OS Release 16.1 onwards.
  - Tested against vSRX JUNOS version 15.1X49-D15.4, vqfx-10000 JUNOS Version 15.1X53-D60.4.
  - Recommended connection is C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).
  - This module also works with C(local) connections for legacy playbooks.
"""

EXAMPLES = """
- name: load configure file into device
  junos_config:
    src: srx.cfg
    comment: update config

- name: load configure lines into device
  junos_config:
    lines:
      - set interfaces ge-0/0/1 unit 0 description "Test interface"
      - set vlans vlan01 description "Test vlan"
    comment: update config

- name: rollback the configuration to id 10
  junos_config:
    rollback: 10

- name: zero out the current configuration
  junos_config:
    zeroize: yes

- name: confirm a previous commit
  junos_config:
    confirm_commit: yes

- name: for idempotency, use full-form commands
  junos_config:
    lines:
      # - set int ge-0/0/1 unit 0 desc "Test interface"
      - set interfaces ge-0/0/1 unit 0 description "Test interface"
"""

RETURN = """
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: string
  sample: /playbooks/ansible/backup/config.2016-07-16@22:28:34
"""
import re
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.netconf import exec_rpc
from ansible.module_utils.network.junos.junos import get_diff, load_config, get_configuration
from ansible.module_utils.network.junos.junos import commit_configuration, discard_changes, locked_config
from ansible.module_utils.network.junos.junos import junos_argument_spec, load_configuration, get_connection, tostring
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native, to_text

try:
    from lxml.etree import Element, fromstring
except ImportError:
    from xml.etree.ElementTree import Element, fromstring

try:
    from lxml.etree import ParseError
except ImportError:
    try:
        from xml.etree.ElementTree import ParseError
    except ImportError:
        # for Python < 2.7
        from xml.parsers.expat import ExpatError
        ParseError = ExpatError

USE_PERSISTENT_CONNECTION = True
DEFAULT_COMMENT = 'configured by junos_config'


def check_args(module, warnings):
    if module.params['replace'] is not None:
        module.fail_json(msg='argument replace is deprecated, use update')


def zeroize(module):
    return exec_rpc(module, tostring(Element('request-system-zeroize')), ignore_warning=False)


def rollback(ele, id='0'):
    return get_diff(ele, id)


def guess_format(config):
    try:
        json.loads(config)
        return 'json'
    except ValueError:
        pass

    try:
        fromstring(config)
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
    config = to_native(match.text, encoding='latin-1')

    modified_candidate = candidate[:]
    for index, line in reversed(list(enumerate(candidate))):
        if line.startswith('delete'):
            newline = re.sub('^delete', 'set', line)
            if newline not in config:
                del modified_candidate[index]

    return modified_candidate


def configure_device(module, warnings, candidate):

    kwargs = {}
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
        confirm_commit=dict(type='bool', default=False),

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

    candidate = module.params['lines'] or module.params['src']
    commit = not module.check_mode

    result = {'changed': False, 'warnings': warnings}

    if module.params['backup']:
        for conf_format in ['set', 'text']:
            reply = get_configuration(module, format=conf_format)
            match = reply.find('.//configuration-%s' % conf_format)
            if match is not None:
                break
        else:
            module.fail_json(msg='unable to retrieve device configuration')

        result['__backup__'] = match.text.strip()

    rollback_id = module.params['rollback']
    if rollback_id:
        diff = rollback(module, rollback_id)
        if commit:
            kwargs = {
                'comment': module.params['comment']
            }
            with locked_config(module):
                load_configuration(module, rollback=rollback_id)
                commit_configuration(module, **kwargs)
            if module._diff:
                result['diff'] = {'prepared': diff}
        result['changed'] = True

    elif module.params['zeroize']:
        if commit:
            zeroize(module)
        result['changed'] = True

    else:
        if candidate:
            with locked_config(module):
                diff = configure_device(module, warnings, candidate)
                if diff:
                    if commit:
                        kwargs = {
                            'comment': module.params['comment']
                        }

                        confirm = module.params['confirm']
                        if confirm > 0:
                            kwargs.update({
                                'confirm': True,
                                'confirm_timeout': to_text(confirm, errors='surrogate_then_replace')
                            })
                        commit_configuration(module, **kwargs)
                    else:
                        discard_changes(module)
                    result['changed'] = True

                    if module._diff:
                        result['diff'] = {'prepared': diff}

        elif module.params['confirm_commit']:
            with locked_config(module):
                # confirm a previous commit
                commit_configuration(module)

            result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
