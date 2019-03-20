# Copyright 2012, Dag Wieers <dag@wieers.com>
# Copyright 2016, Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright 2019, Virgil Chereches <virgil.chereches@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleUndefinedVariable, AnsibleActionFail
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase
from ansible.module_utils._text import to_text, to_native
from os import path


class ActionModule(ActionBase):

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('var', 'schema', 'extensions'))
    VALID_FILE_EXTENSIONS = ['yaml', 'yml', 'json']

    def _is_valid_file_ext(self, source_file):
        """ Verify if source file has a valid extension
        Args:
            source_file (str): The full path of source file or source file.
        Returns:
            Bool
        """
        file_ext = path.splitext(source_file)
        return bool(len(file_ext) > 1 and file_ext[-1][1:] in self.valid_extensions)

    def _load_files(self, filename, validate_extensions=False):
        """ Loads a file and converts the output into a valid Python dict.
        Args:
            filename (str): The source file.

        Returns:
            Tuple (bool, str, dict)
        """

        data = dict()
        failed = False
        err_msg = ''
        if validate_extensions and not self._is_valid_file_ext(filename):
            failed = True
            err_msg = ('{0} does not have a valid extension: {1}'.format(to_native(filename), ', '.join(self.valid_extensions)))
        else:
            b_data, show_content = self._loader._get_file_contents(filename)
            data = to_text(b_data, errors='surrogate_or_strict')

            self.show_content = show_content
            data = self._loader.load(data, file_name=filename, show_content=show_content)

            if not isinstance(data, dict):
                failed = True
                err_msg = ('{0} must be stored as a dictionary/hash'.format(to_native(filename)))

        return failed, err_msg, data

    def _set_args(self):
        """ Set instance variables based on the arguments that were passed """
        if not ('schema' in self._task.args and 'var' in self._task.args):
            return {"failed": True, "msg": "'var' and 'schema' are required options"}
        self.var = self._task.args['var']
        self.schema = self._task.args['schema']
        self.valid_extensions = self._task.args.get('extensions', self.VALID_FILE_EXTENSIONS)

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        # set internal vars from args
        self._set_args()

        try:
            from jsonschema import validate, draft7_format_checker, exceptions
        except ImportError as e:
            raise AnsibleError("The validate module requires jsonschema python module.")

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Check type of schema - inline dictionary passed via Jinja2 or filename
        if isinstance(self.schema, dict):
            schema_data = self.schema
        elif isinstance(self.schema, string_types):
            try:
                failed, err_msg, schema_data = (
                    self._load_files(self.schema, validate_extensions=True)
                )
                if failed:
                    raise AnsibleActionFail(err_msg)

            except AnsibleError as e:
                raise AnsibleActionFail(to_native(e))

        else:
            raise AnsibleActionFail("'schema' parameter should be a filename or a dictionary")

        # Variable substitution code borrowed from debug plugin
        try:
            variable_value = self._templar.template(self.var, convert_bare=True, fail_on_undefined=True)
            if variable_value == self.var:
                # if variable_value is not str/unicode type, raise an exception
                if not isinstance(variable_value, string_types):
                    raise AnsibleUndefinedVariable
                # If var name is same as result, try to template it
                variable_value = self._templar.template("{{" + variable_value + "}}",
                                                        convert_bare=True, fail_on_undefined=True)
        except AnsibleUndefinedVariable as e:
            raise AnsibleActionFail("'var' {} is not defined".format(self.var))

        try:
            validate(instance=variable_value, schema=schema_data,
                     format_checker=draft7_format_checker,)
        except exceptions.ValidationError as e:
            raise AnsibleActionFail("Failed validating {} in {}: {}".format(e.validator, e.schema_path, e.message))

        return result
