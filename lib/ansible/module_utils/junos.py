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

from ncclient.xml_ import new_ele, sub_ele, to_xml

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.netconf import send_request
from ansible.module_utils.netconf import discard_changes, validate
from ansible.module_utils.network_common import to_list
from ansible.module_utils.connection import exec_command

ACTIONS = frozenset(['merge', 'override', 'replace', 'update', 'set'])
JSON_ACTIONS = frozenset(['merge', 'override', 'update'])
FORMATS = frozenset(['xml', 'text', 'json'])
CONFIG_FORMATS = frozenset(['xml', 'text', 'json', 'set'])

_DEVICE_CONFIGS = {}

junos_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'timeout': dict(type='int', default=10),
    'provider': dict(type='dict'),
}

def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in junos_argument_spec:
        if key in ('provider', 'transport') and module.params[key]:
            warnings.append('argument %s has been deprecated and will be '
                    'removed in a future version' % key)

def validate_rollback_id(value):
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
        validate_rollback_id(rollback)
        xattrs = {'rollback': str(rollback)}
    else:
        xattrs = {'action': action, 'format': format}

    obj = new_ele('load-configuration', xattrs)

    if candidate is not None:
        lookup = {'xml': 'configuration', 'text': 'configuration-text',
                  'set': 'configuration-set', 'json': 'configuration-json'}

        if action == 'set':
            cfg = sub_ele(obj, 'configuration-set')
            cfg.text = '\n'.join(candidate)
        else:
            cfg = sub_ele(obj, lookup[format])
            cfg.append(candidate)

    return send_request(module, obj)

def get_configuration(module, compare=False, format='xml', rollback='0'):
    if format not in CONFIG_FORMATS:
        module.fail_json(msg='invalid config format specified')
    xattrs = {'format': format}
    if compare:
        validate_rollback_id(rollback)
        xattrs['compare'] = 'rollback'
        xattrs['rollback'] = str(rollback)
    return send_request(module, new_ele('get-configuration', xattrs))

def commit_configuration(module, confirm=False, check=False, comment=None, confirm_timeout=None):
    obj = new_ele('commit-configuration')
    if confirm:
        sub_ele(obj, 'confirmed')
    if check:
        sub_ele(obj, 'check')
    if comment:
        children(obj, ('log', str(comment)))
    if confirm_timeout:
        children(obj, ('confirm-timeout', int(confirm_timeout)))
    return send_request(module, obj)

lock_configuration = lambda x: send_request(x, new_ele('lock-configuration'))
unlock_configuration = lambda x: send_request(x, new_ele('unlock-configuration'))

@contextmanager
def locked_config(module):
    try:
        lock_configuration(module)
        yield
    finally:
        unlock_configuration(module)

def get_diff(module):
    reply = get_configuration(module, compare=True, format='text')
    output = reply.xpath('//configuration-output')
    if output:
        return output[0].text

def load(module, candidate, action='merge', commit=False, format='xml'):
    """Loads a configuration element into the target system
    """
    with locked_config(module):
        resp = load_configuration(module, candidate, action=action, format=format)

        validate(module)
        diff = get_diff(module)

        if diff:
            diff = str(diff).strip()
            if commit:
                commit_configuration(module)
            else:
                discard_changes(module)

        return diff



# START CLI FUNCTIONS

def get_config(module, flags=[]):
    cmd = 'show configuration '
    cmd += ' '.join(flags)
    cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        rc, out, err = exec_command(module, cmd)
        if rc != 0:
            module.fail_json(msg='unable to retrieve current config', stderr=err)
        cfg = str(out).strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg

def run_commands(module, commands, check_rc=True):
    responses = list()
    for cmd in to_list(commands):
        cmd = module.jsonify(cmd)
        rc, out, err = exec_command(module, cmd)
        if check_rc and rc != 0:
            module.fail_json(msg=err, rc=rc)

        try:
            out = module.from_json(out)
        except ValueError:
            out = str(out).strip()

        responses.append(out)
    return responses

def load_config(module, config, commit=False, comment=None,
        confirm=False, confirm_timeout=None):

    exec_command(module, 'configure')

    for item in to_list(config):
        rc, out, err = exec_command(module, item)
        if rc != 0:
            module.fail_json(msg=str(err))

    exec_command(module, 'top')
    rc, diff, err = exec_command(module, 'show | compare')

    if commit:
        cmd = 'commit'
        if commit:
            cmd = 'commit confirmed'
            if confirm_timeout:
                cmd +' %s' % confirm_timeout
        if comment:
            cmd += ' comment "%s"' % comment
        cmd += ' and-quit'
        exec_command(module, cmd)
    else:
        for cmd in ['rollback 0', 'exit']:
            exec_command(module, cmd)

    return str(diff).strip()
