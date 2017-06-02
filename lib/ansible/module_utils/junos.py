#
# (c) 2017 Red Hat, Inc.
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
from contextlib import contextmanager

from xml.etree.ElementTree import Element, SubElement, fromstring

from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.netconf import send_request, children
from ansible.module_utils.netconf import discard_changes, validate
from ansible.module_utils.six import string_types

ACTIONS = frozenset(['merge', 'override', 'replace', 'update', 'set'])
JSON_ACTIONS = frozenset(['merge', 'override', 'update'])
FORMATS = frozenset(['xml', 'text', 'json'])
CONFIG_FORMATS = frozenset(['xml', 'text', 'json', 'set'])

junos_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'timeout': dict(type='int'),
    'provider': dict(type='dict'),
    'transport': dict()
}

# Add argument's default value here
ARGS_DEFAULT_VALUE = {
    'timeout': 10
}

def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in junos_argument_spec:
        if key not in ('provider',) and module.params[key]:
            warnings.append('argument %s has been deprecated and will be '
                    'removed in a future version' % key)

    # set argument's default value if not provided in input
    # This is done to avoid unwanted argument deprecation warning
    # in case argument is not given as input (outside provider).
    for key in ARGS_DEFAULT_VALUE:
        if not module.params.get(key, None):
            module.params[key] = ARGS_DEFAULT_VALUE[key]

    if provider:
        for param in ('password',):
            if provider.get(param):
                module.no_log_values.update(return_values(provider[param]))

def _validate_rollback_id(module, value):
    try:
        if not 0 <= int(value) <= 49:
            raise ValueError
    except ValueError:
        module.fail_json(msg='rollback must be between 0 and 49')

def load_configuration(module, candidate=None, action='merge', rollback=None, format='xml'):

    if all((candidate is None, rollback is None)):
        module.fail_json(msg='one of candidate or rollback must be specified')

    elif all((candidate is not None, rollback is not None)):
        module.fail_json(msg='candidate and rollback are mutually exclusive')

    if format not in FORMATS:
        module.fail_json(msg='invalid format specified')

    if format == 'json' and action not in JSON_ACTIONS:
        module.fail_json(msg='invalid action for format json')
    elif format in ('text', 'xml') and action not in ACTIONS:
        module.fail_json(msg='invalid action format %s' % format)
    if action == 'set' and not format == 'text':
        module.fail_json(msg='format must be text when action is set')

    if rollback is not None:
        _validate_rollback_id(module, rollback)
        xattrs = {'rollback': str(rollback)}
    else:
        xattrs = {'action': action, 'format': format}

    obj = Element('load-configuration', xattrs)

    if candidate is not None:
        lookup = {'xml': 'configuration', 'text': 'configuration-text',
                  'set': 'configuration-set', 'json': 'configuration-json'}

        if action == 'set':
            cfg = SubElement(obj, 'configuration-set')
        else:
            cfg = SubElement(obj, lookup[format])

        if isinstance(candidate, string_types):
            if format == 'xml':
                cfg.append(fromstring(candidate))
            else:
                cfg.text = candidate
        else:
            cfg.append(candidate)
    return send_request(module, obj)

def get_configuration(module, compare=False, format='xml', rollback='0'):
    if format not in CONFIG_FORMATS:
        module.fail_json(msg='invalid config format specified')
    xattrs = {'format': format}
    if compare:
        _validate_rollback_id(module, rollback)
        xattrs['compare'] = 'rollback'
        xattrs['rollback'] = str(rollback)
    return send_request(module, Element('get-configuration', xattrs))

def commit_configuration(module, confirm=False, check=False, comment=None, confirm_timeout=None):
    obj = Element('commit-configuration')
    if confirm:
        SubElement(obj, 'confirmed')
    if check:
        SubElement(obj, 'check')
    if comment:
        subele = SubElement(obj, 'log')
        subele.text = str(comment)
    if confirm_timeout:
        subele = SubElement(obj, 'confirm-timeout')
        subele.text = str(confirm_timeout)
    return send_request(module, obj)

def command(module, command, format='text', rpc_only=False):
    xattrs = {'format': format}
    if rpc_only:
        command += ' | display xml rpc'
        xattrs['format'] = 'text'
    return send_request(module, Element('command', xattrs, text=command))

lock_configuration = lambda x: send_request(x, Element('lock-configuration'))
unlock_configuration = lambda x: send_request(x, Element('unlock-configuration'))

@contextmanager
def locked_config(module):
    try:
        lock_configuration(module)
        yield
    finally:
        unlock_configuration(module)

def get_diff(module):

    reply = get_configuration(module, compare=True, format='text')
    output = reply.find('.//configuration-output')
    if output is not None:
        return output.text

def load_config(module, candidate, warnings, action='merge', commit=False, format='xml',
                comment=None, confirm=False, confirm_timeout=None):

    if not candidate:
        return

    with locked_config(module):
        if isinstance(candidate, list):
            candidate = '\n'.join(candidate)

        reply = load_configuration(module, candidate, action=action, format=format)
        if isinstance(reply, list):
            warnings.extend(reply)

        validate(module)
        diff = get_diff(module)

        if diff:
            diff = str(diff).strip()
            if commit:
                commit_configuration(module, confirm=confirm, comment=comment,
                                     confirm_timeout=confirm_timeout)
            else:
                discard_changes(module)

        return diff

def get_param(module, key):
    return module.params[key] or module.params['provider'].get(key)
