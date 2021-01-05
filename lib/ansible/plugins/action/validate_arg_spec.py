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
    '''AnsibleModule but with overridden _load_params so it doesnt read from stdin/ANSIBLE_ARGS'''
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
    ''' Validate a arg spec'''

    TRANSFERS_FILES = False

    # WARNING: modifies argument_spec
    def build_args(self, argument_spec, task_vars):
        args = {}
        for key, attrs in iteritems(argument_spec):
            if attrs is None:
                argument_spec[key] = {'type': 'str'}

            if key in task_vars:
                if isinstance(task_vars[key], string_types):
                    value = self._templar.do_template(task_vars[key])
                    if value:
                        args[key] = value
                else:
                    args[key] = task_vars[key]
            elif attrs:
                if 'aliases' in attrs:
                    for item in attrs['aliases']:
                        if item in task_vars:
                            args[key] = self._templar.do_template(task_vars[key])
                elif 'default' in attrs and key not in args:
                    args[key] = attrs['default']
        return args

    def run(self, tmp=None, task_vars=None):
        '''
        Validate an arg spec

        :arg tmp: Deprecated. Do not use.
        :arg dict task_vars: A dict of task variables.
            Valid args include 'argument_spec', 'provided_arguments'
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

        # get the task var called argument_spec
        argument_spec_data = self._task.args.get('argument_spec')

        # include arg spec data dict in return, use a copy since we 'pop' from it
        # and modify it in place later.
        orig_argument_spec_data = argument_spec_data.copy()

        # then get the 'argument_spec' item from the dict in the argument_spec task var
        # everything left in argument_spec_data is modifiers
        argument_spec = argument_spec_data.pop('argument_spec', [])

        # the values that were passed in and will be checked against argument_spec
        provided_arguments = self._task.args.get('provided_arguments', {})

        if not isinstance(argument_spec_data, dict):
            raise AnsibleError('Incorrect type for argument_spec, expected dict and got %s' % type(argument_spec_data))

        if not isinstance(provided_arguments, dict):
            raise AnsibleError('Incorrect type for provided_arguments, expected dict and got %s' % type(provided_arguments))

        module_params = provided_arguments

        # apply any defaults from the arg spec and setup aliases
        built_args = self.build_args(argument_spec, task_vars)
        module_params.update(built_args)

        module_args = {}
        module_args.update(argument_spec_data)
        module_args['argument_spec'] = argument_spec
        module_args['params'] = module_params

        try:
            validating_module = ArgSpecValidatingAnsibleModule(**module_args)
            validating_module.check_for_errors()
        except AnsibleArgSpecError as e:
            # result['_ansible_verbose_always'] = True
            result['failed'] = True
            result['msg'] = e.message
            result['argument_spec_data'] = orig_argument_spec_data
            result['argument_errors'] = e.argument_errors

            # TODO: we could return the passed in params which didn't meet arg spec,
            #       but they likely need to have no_log applied to them...
            # result['provided_arguments'] = provided_arguments

            return result

        result['changed'] = False
        result['msg'] = 'The arg spec validation passed'

        # result['valid_provided_arguments'] = provided_arguments

        return result
