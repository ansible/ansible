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
from ansible.module_utils.mlnxos import check_args, load_config


class BaseMlnxosApp(object):
    def __init__(self):
        self._module = None
        self._commands = list()
        self._current_config = None
        self._required_config = None

    def init_module(self):
        pass

    def load_current_config(self):
        pass

    def get_required_config(self):
        pass

    def check_declarative_intent_params(self, result):
        return None

    def validate_param_values(self, obj, param=None):
        if param is None:
            param = self._module.params
        for key in obj:
            # validate the param value (if validator func exists)
            try:
                validator = getattr(self, 'validate_%s' % key)
                if callable(validator):
                    validator(param.get(key))
            except AttributeError:
                pass

    @classmethod
    def get_config_attr(cls, item, arg):
        return item.get(arg)

    @classmethod
    def get_mtu(cls, item):
        mtu = cls.get_config_attr(item, "MTU")
        ll = mtu.split()
        return ll[0]

    def validate_mtu(self, value):
        if value and not 1500 <= int(value) <= 9612:
            self._module.fail_json(msg='mtu must be between 1500 and 9612')

    def generate_commands(self):
        pass

    def run(self):
        self.init_module()
        warnings = list()
        check_args(self._module, warnings)

        result = {'changed': False}
        if warnings:
            result['warnings'] = warnings

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
