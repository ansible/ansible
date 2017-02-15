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

from ncclient.xml_ import new_ele, sub_ele

from ansible.module_utils.netconf import send_request
from ansible.module_utils.netconf import discard_changes, validate
from ansible.module_utils.network_common import to_list

_DEVICE_CONFIGS = {}

def load_configuration(module, candidate=None, action='merge', rollback=None, format='xml'):
    if all((candidate is None, rollback is None)):
        module.fail_json(msg='one of candidate or rollback must be specified')
    elif all((candidate is not None, rollback is not None)):
        module.fail_json(msg='candidate and rollback are mutually exclusive')

    if rollback is not None:
        try:
            if not 0 <= int(rollback) <= 49:
                raise ValueError
            xattrs = {'rollback': str(rollback)}
        except ValueError:
            module.fail_json(msg='rollback must be between 0 and 49')
    else:
        xattrs = {'action': action, 'format': format}

    obj = new_ele('load-configuration', xattrs)

    if candidate is not None:
        if action not in ['merge', 'override', 'replace', 'update']:
            module.fail_json(msg='invalid value for kwarg action')

        if format not in ['xml', 'text', 'set', 'json']:
            module.fail_json(msg='invalid value for kwargs format')

        lookup = {'xml': 'configuration', 'text': 'configuration-text',
                  'set': 'configuration-set', 'json': 'configuration-json'}

        cfg = sub_ele(obj, lookup[format])
        cfg.append(candidate)

    return send_request(module, obj)

def get_configuration(module):
    attrs = {'compare': 'rollback', 'rollback': '0', 'format': 'text'}
    return send_request(module, new_ele('get-configuration', attrs))

def commit_configuration(module, check=False, comment=None, confirm_timeout=None):
    obj = new_ele('commit-configuration')
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


def load(module, candidate, commit=False, check=False, comment=None,
        action='merge', confirm_timeout=None):
    """Loads a configuration element into the target system

    This loads the candidate configuration onto the remote system
    and then generates a diff against the current active configuration.

    :params candidate: The candidate configuration as an XML data doc

    :returns: A config diff
    """
    with locked_config(module):
        load_configuration(module, candidate, action=action)

        validate(module)

        reply = get_configuration(module)

        diff = None
        output = reply.xpath('//configuration-output')
        if output:
            diff = output[0].text

        if diff:
            if commit:
                commit_configuration(module)
            else:
                discard_changes(module)

        return str(diff).strip()


def get_config(module, flags=[]):
    cmd = 'show configuration '
    cmd += ' '.join(flags)
    cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        rc, out, err = module.exec_command(cmd)
        if rc != 0:
            module.fail_json(msg='unable to retrieve current config', stderr=err)
        cfg = str(out).strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg

def run_commands(module, commands, check_rc=True):
    responses = list()
    for cmd in to_list(commands):
        cmd = module.jsonify(cmd)
        rc, out, err = module.exec_command(cmd)
        if check_rc and rc != 0:
            module.fail_json(msg=err, rc=rc)
        responses.append(out)
    return responses

def load_config(module, commands):
    """Loads the configuration into the remote device
    """
    self.exec_command('configure')

    for item in to_list(config):
        rc, out, err = self.exec_command(item)
        if rc != 0:
            module.fail_json(msg=str(err))

    self.exec_command('top')

    rc, diff, err = self.exec_command('show | compare')

    if commit:
        self.exec_command('commit and-quit')
    else:
        self.exec_command('rollback 0')

    return str(diff).strip()
