# Copyright 2021 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.module_utils.common.arg_spec import ArgumentSpecValidator
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

from contextlib import suppress
from copy import deepcopy
from dataclasses import asdict, field, dataclass, make_dataclass

import typing as t

OPTION_TYPES = [None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str']

ROLE_OPTION_SPEC = dict(
    description=dict(type='list', elements='str'),
    type=dict(choices=OPTION_TYPES),
    default=dict(type='raw'),
    choices=dict(type='list'),
    elements=dict(choices=OPTION_TYPES),
    options=dict(type='dict'),
    required=dict(type='bool'),
    version_added=dict(type='raw'),
    # some module argument spec features are intentionally omitted since role argument specs are read-only
    # no_log, aliases, apply_defaults, and fallback are not supported
)

OPTION_SPEC = dict(ROLE_OPTION_SPEC)
OPTION_SPEC.update(dict(
    no_log=dict(type='bool'),
    aliases=dict(type='list', elements='str'),
    apply_defaults=dict(type='bool'),
    # fallback is excluded because tuple[callable, list[str]] can't be set via a task
))

display = Display()


@dataclass
class RoleSpec:
    """Argument spec supported by the ArgumentSpecValidator and roles."""

    @classmethod
    def from_spec(cls: t.Type[t.Self], fields: dict, role_name: str, spec_name: str, role_path: str) -> t.Self:
        """Load a valid role argument spec from a foreign argument spec."""
        fields = deepcopy(fields)

        errors: list[str] = []
        validator = ArgumentSpecValidator(ROLE_OPTION_SPEC, required_if=[('type', 'list', ('elements',))])
        validate_argspec(validator, [], fields, errors, prune=True)

        if errors:
            display.warning(f"Role '{role_name}' entrypoint '{spec_name}' contains errors in the argument spec. Use -vvv to see details.")
            display.vvv(f"Role '{role_name}' ({role_path}) argument spec '{spec_name}' contains errors:")
        for error in errors:
            display.vvv(f"- {error}")

        class_fields = []
        for key, value in fields.items():
            default = field(default_factory=lambda: value) if is_mutable(value) else field(default=value)  # pylint: disable=invalid-field-call
            class_fields.append((key, type(value), default))

        return make_dataclass(cls.__name__, class_fields)(**fields)


def validate_argspec(validator: ArgumentSpecValidator, context: list[str], argument_spec: dict, errors: list[str], prune: bool = False) -> None:
    """Validate the options in an argument spec and optionally prune those with errors."""
    invalid_options = []
    for option, fields in argument_spec.items():
        if not isinstance(option, str):
            invalid_options.append(option)
            continue
        validate_option_spec(validator, context + [option], fields, errors, prune)

    for option in invalid_options:
        str_option = f"{option}"
        errors.append(f"{'.'.join(context + [str_option])}: type {type(option)}. Option names must be strings.")
        if prune:
            argument_spec.pop(option)


def validate_option_spec(validator: ArgumentSpecValidator, context: list[str], fields: dict, errors: list[str], prune: bool = False) -> None:
    """Validate the fields for an option and optionally prune those with errors."""
    result = validator.validate(fields)

    if result.error_messages:
        errors.append(f"{'.'.join(context)}: {', '.join(result.error_messages)}")
    if prune and result.error_messages:
        for error in result.error_messages:
            field = error.split('.', 1)[0]
            fields.pop(field, None)

    if fields.get('type') in ('list', 'dict') and fields.get('options'):
        validate_argspec(validator, context, fields['options'], errors, prune)

    elif fields.get('options'):
        errors.append(f"{'.'.join(context)}: options. Suboptions are supported for types dict and list.")
        if prune:
            fields.pop('options')


def is_mutable(value: t.Any) -> bool:
    """Return true is a value is not hashable."""
    with suppress(TypeError):
        hash(value)
        return False
    return True


class ActionModule(ActionBase):
    """ Validate an arg spec"""

    TRANSFERS_FILES = False
    _requires_connection = False

    def get_args_from_task_vars(self, argument_spec, task_vars):
        """
        Get any arguments that may come from `task_vars`.

        Expand templated variables so we can validate the actual values.

        :param argument_spec: A dict of the argument spec.
        :param task_vars: A dict of task variables.

        :returns: A dict of values that can be validated against the arg spec.
        """
        args = {}

        for argument_name, argument_attrs in argument_spec.items():
            if argument_name in task_vars:
                args[argument_name] = task_vars[argument_name]
        args = self._templar.template(args)
        return args

    def run(self, tmp=None, task_vars=None):
        """
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
        """
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

        if self._task.implicit:
            argument_spec = RoleSpec.from_spec(
                argument_spec_data,
                result['validate_args_context']['name'],
                result['validate_args_context']['argument_spec_name'],
                result['validate_args_context']['path']
            )
            valid_argument_spec = asdict(argument_spec)
        else:
            errors = []
            argspec_option_validator = ArgumentSpecValidator(OPTION_SPEC, required_if=[('type', 'list', ('elements',))])
            validate_argspec(argspec_option_validator, [], argument_spec_data, errors)

            if errors:
                result['failed'] = True
                result['msg'] = "Invalid argument_spec cannot be used to validate variables."
                result['argument_spec_errors'] = errors
                result['argument_spec_data'] = argument_spec_data
                return result

            valid_argument_spec = argument_spec_data

        args_from_vars = self.get_args_from_task_vars(argument_spec_data, task_vars)
        validator = ArgumentSpecValidator(valid_argument_spec)
        validation_result = validator.validate(combine_vars(args_from_vars, provided_arguments), validate_role_argument_spec=True)

        if validation_result.error_messages:
            result['failed'] = True
            result['msg'] = 'Validation of arguments failed:\n%s' % '\n'.join(validation_result.error_messages)
            result['argument_spec_data'] = argument_spec_data
            result['argument_errors'] = validation_result.error_messages
            return result

        result['changed'] = False
        result['msg'] = 'The arg spec validation passed'

        return result
