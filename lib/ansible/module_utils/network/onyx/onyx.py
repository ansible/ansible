# -*- coding: utf-8 -*-
#
# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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
import json

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.utils import to_list, EntityCollection

_DEVICE_CONFIGS = {}
_CONNECTION = None

_COMMAND_SPEC = {
    'command': dict(key=True),
    'prompt': dict(),
    'answer': dict()
}


def get_connection(module):
    global _CONNECTION
    if _CONNECTION:
        return _CONNECTION
    _CONNECTION = Connection(module._socket_path)
    return _CONNECTION


def to_commands(module, commands):
    if not isinstance(commands, list):
        raise AssertionError('argument must be of type <list>')

    transform = EntityCollection(module, _COMMAND_SPEC)
    commands = transform(commands)
    return commands


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)

    commands = to_commands(module, to_list(commands))

    responses = list()

    for cmd in commands:
        out = connection.get(**cmd)
        responses.append(to_text(out, errors='surrogate_then_replace'))

    return responses


def get_config(module, source='running'):
    conn = get_connection(module)
    out = conn.get_config(source)
    cfg = to_text(out, errors='surrogate_then_replace').strip()
    return cfg


def load_config(module, config):
    try:
        conn = get_connection(module)
        conn.edit_config(config)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def _parse_json_output(out):
    out_list = out.split('\n')
    first_index = 0
    opening_char = None
    lines_count = len(out_list)
    while first_index < lines_count:
        first_line = out_list[first_index].strip()
        if not first_line or first_line[0] not in ("[", "{"):
            first_index += 1
            continue
        opening_char = first_line[0]
        break
    if not opening_char:
        return "null"
    closing_char = ']' if opening_char == '[' else '}'
    last_index = lines_count - 1
    found = False
    while last_index > first_index:
        last_line = out_list[last_index].strip()
        if not last_line or last_line[0] != closing_char:
            last_index -= 1
            continue
        found = True
        break
    if not found:
        return opening_char + closing_char
    return "".join(out_list[first_index:last_index + 1])


def show_cmd(module, cmd, json_fmt=True, fail_on_error=True):
    if json_fmt:
        cmd += " | json-print"
    conn = get_connection(module)
    command_obj = to_commands(module, to_list(cmd))[0]
    try:
        out = conn.get(**command_obj)
    except ConnectionError:
        if fail_on_error:
            raise
        return None
    if json_fmt:
        out = _parse_json_output(out)
        try:
            cfg = json.loads(out)
        except ValueError:
            module.fail_json(
                msg="got invalid json",
                stderr=to_text(out, errors='surrogate_then_replace'))
    else:
        cfg = to_text(out, errors='surrogate_then_replace').strip()
    return cfg


def get_interfaces_config(module, interface_type, flags=None, json_fmt=True):
    cmd = "show interfaces %s" % interface_type
    if flags:
        cmd += " %s" % flags
    return show_cmd(module, cmd, json_fmt)


def show_version(module):
    return show_cmd(module, "show version")


def get_bgp_summary(module):
    cmd = "show running-config protocol bgp"
    return show_cmd(module, cmd, json_fmt=False, fail_on_error=False)


class BaseOnyxModule(object):
    ONYX_API_VERSION = "3.6.6000"

    def __init__(self):
        self._module = None
        self._commands = list()
        self._current_config = None
        self._required_config = None
        self._os_version = None

    def init_module(self):
        pass

    def load_current_config(self):
        pass

    def get_required_config(self):
        pass

    def _get_os_version(self):
        version_data = show_version(self._module)
        return self.get_config_attr(
            version_data, "Product release")

    # pylint: disable=unused-argument
    def check_declarative_intent_params(self, result):
        return None

    def _validate_key(self, param, key):
        validator = getattr(self, 'validate_%s' % key)
        if callable(validator):
            validator(param.get(key))

    def validate_param_values(self, obj, param=None):
        if param is None:
            param = self._module.params
        for key in obj:
            # validate the param value (if validator func exists)
            try:
                self._validate_key(param, key)
            except AttributeError:
                pass

    @classmethod
    def get_config_attr(cls, item, arg):
        return item.get(arg)

    @classmethod
    def get_mtu(cls, item):
        mtu = cls.get_config_attr(item, "MTU")
        mtu_parts = mtu.split()
        try:
            return int(mtu_parts[0])
        except ValueError:
            return None

    def _validate_range(self, attr_name, min_val, max_val, value):
        if value is None:
            return True
        if not min_val <= int(value) <= max_val:
            msg = '%s must be between %s and %s' % (
                attr_name, min_val, max_val)
            self._module.fail_json(msg=msg)

    def validate_mtu(self, value):
        self._validate_range('mtu', 1500, 9612, value)

    def generate_commands(self):
        pass

    def run(self):
        self.init_module()

        result = {'changed': False}

        self.get_required_config()
        self.load_current_config()

        self.generate_commands()
        result['commands'] = self._commands

        if self._commands:
            if not self._module.check_mode:
                load_config(self._module, self._commands)
            result['changed'] = True

        failed_conditions = self.check_declarative_intent_params(result)

        if failed_conditions:
            msg = 'One or more conditional statements have not been satisfied'
            self._module.fail_json(msg=msg,
                                   failed_conditions=failed_conditions)

        self._module.exit_json(**result)

    @classmethod
    def main(cls):
        app = cls()
        app.run()
