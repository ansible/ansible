# Copyright 2018 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleModuleError
from ansible.plugins.action import ActionBase
from ansible.module_utils import basic
from ansible.module_utils.six import iteritems, string_types


class AnsibleArgSpecError(AnsibleModuleError):
    def __init__(self, *args, **kwargs):
        self.argument_errors = kwargs.pop('argument_errors', [])
        super(AnsibleArgSpecError, self).__init__(*args, **kwargs)


class ArgSpecValidatingAnsibleModule(basic.AnsibleModule):
    '''AnsibleModule but with overridden _load_params so it doesn't read from stdin/ANSIBLE_ARGS'''

    def __init__(self, *args, **kwargs):
        self._params = kwargs.pop('params', {})
        # remove meta fields that aren't valid AnsibleModule args
        self.arg_spec_name = kwargs.pop('name', None)
        self.arg_spec_description = kwargs.pop('description', None)

        self.arg_validation_errors = []
        super(ArgSpecValidatingAnsibleModule, self).__init__(*args, **kwargs)

    # AnsibleModule._load_params sets self.params from a global, so neuter it here
    # so our passed in 'params' kwarg is used instead
    def _load_params(self):
        self.params = self._params

    def fail_json(self, *args, **kwargs):
        msg = kwargs.pop('msg', 'Unknown arg spec validation error')

        clean_msg = basic.remove_values(msg, self.no_log_values)

        self.arg_validation_errors.append(clean_msg)

    def check_for_errors(self):
        if not self.arg_validation_errors:
            return

        msg = 'Validation of arguments failed:\n%s' % '\n'.join(self.arg_validation_errors)
        raise AnsibleArgSpecError(msg, argument_errors=self.arg_validation_errors)


class ActionModule(ActionBase):
    ''' Validate an arg spec'''

    TRANSFERS_FILES = False

    def get_args_from_task_vars(self, argument_spec, task_vars):
        '''
        Get any arguments that may come from `task_vars`.

        Expand templated variables so we can validate the actual values.

        :param argument_spec: A dict of the argument spec.
        :param task_vars: A dict of task variables.

        :returns: A dict of values that can be validated against the arg spec.
        '''
        args = {}

        for argument_name, argument_attrs in iteritems(argument_spec):
            if argument_name in task_vars:
                if isinstance(task_vars[argument_name], string_types):
                    value = self._templar.do_template(task_vars[argument_name])
                    if value:
                        args[argument_name] = value
                else:
                    args[argument_name] = task_vars[argument_name]
        return args

    def run(self, tmp=None, task_vars=None):
        '''
        Validate an argument specification against a provided set of data.

        The `validate_argument_spec` module expects to receive the arguments:
            - argument_spec: A dict whose keys are the valid argument names, and
                  whose values are dicts of the argument attributes (type, etc).
            - provided_arguments: A dict whose keys are the argument names, and
                  whose values are the argument value.

        :param tmp: Deprecated. Do not use.
        :param task_vars: A dict of task variables.
        :return: An action result dict, including a 'argument_errors' key with a
            list of validation errors found.
        '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # This action can be called from anywhere, so pass in some info about what it is
        # validating args for so the error results make some sense
        result['validate_args_context'] = self._task.args.get('validate_args_context', {})

        if 'argument_spec' not in self._task.args:
            raise AnsibleError('"argument_spec" arg is required in args: %s' % self._task.args)

        # Get the task var called argument_spec. This will contain the arg spec
        # data dict (for the proper entry point for a role).
        argument_spec_data = self._task.args.get('argument_spec')

        # the values that were passed in and will be checked against argument_spec
        provided_arguments = self._task.args.get('provided_arguments', {})

        if not isinstance(argument_spec_data, dict):
            raise AnsibleError('Incorrect type for argument_spec, expected dict and got %s' % type(argument_spec_data))

        if not isinstance(provided_arguments, dict):
            raise AnsibleError('Incorrect type for provided_arguments, expected dict and got %s' % type(provided_arguments))

        module_params = provided_arguments

        args_from_vars = self.get_args_from_task_vars(argument_spec_data, task_vars)
        module_params.update(args_from_vars)

        module_args = {}
        module_args['argument_spec'] = argument_spec_data
        module_args['params'] = module_params

        try:
            validating_module = ArgSpecValidatingAnsibleModule(**module_args)
            validating_module.check_for_errors()
        except AnsibleArgSpecError as e:
            result['failed'] = True
            result['msg'] = e.message
            result['argument_spec_data'] = argument_spec_data
            result['argument_errors'] = e.argument_errors
            return result

        result['changed'] = False
        result['msg'] = 'The arg spec validation passed'

        return result
