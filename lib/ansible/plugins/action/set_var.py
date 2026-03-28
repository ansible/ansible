
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible.errors import AnsibleActionFail
from ansible.module_utils.common._collections_compat import Mapping, Sequence
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase
from ansible.utils.vars import isidentifier, combine_vars


class ActionModule(ActionBase):

    TRANSFERS_FILES = False
    _VALID_VARS_DEF = frozenset(('scope', 'name', 'value'))
    _VALID_ARGS = frozenset(('scope', 'defs'))

    def _extract_validated_var_definition(self, var_def, global_scope):

        if not isinstance(var_def, Mapping):
            raise AnsibleActionFail("The variable definition should be a dictionary, but got a %s" % type(var_def))

        try:
            name = var_def.pop('name')
        except KeyError:
            raise AnsibleActionFail("The variable definition requires a 'name' entry")

        if not isidentifier(name):
            raise AnsibleActionFail("The variable name '%s' is not valid. Variables must start with a letter or underscore character, and contain only "
                                    "letters, numbers and underscores." % name)
        try:
            value = var_def.pop('value')
        except KeyError:
            raise AnsibleActionFail("The variable definition requires a 'value' entry")

        scope = var_def.pop('scope', global_scope)
        if not isinstance(scope, string_types):
            raise AnsibleActionFail("The 'scope' option for '%s' should be a string, but got a %s" % (name, type(scope)))
        elif scope not in C.VALID_VAR_SCOPES:
            raise AnsibleActionFail("Invalid 'scope' option for '%s', got '%s' but should be one of: %s" % (name, scope, ', '.join(C.VALID_VAR_SCOPES)))

        if len(var_def) > 0:
            raise AnsibleActionFail("Unknown arguments were passed into variable definition for '%s', only '%s' are valid." % (name, ', '.join(self._VALID_VARS_DEF)))

        return name, value, scope

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        result['_ansible_vars'] = {}
        if self._task.args:

            try:
                vars_list = self._task.args.pop('defs')
            except KeyError:
                raise AnsibleActionFail("set_var requires a 'defs' option, none was provided")

            scope = self._task.args.pop('scope', 'host')

            if len(self._task.args) > 0:
                raise AnsibleActionFail("Unknown arguments were passed into set_var, only valid ones are: %s" % ', '.join(self._VALID_ARGS))

            if isinstance(vars_list, string_types) or not isinstance(vars_list, Sequence):
                raise AnsibleActionFail("set_var takes a list of variable definitions, but got a '%s' instead" % type(vars_list))

            for var_def in vars_list:

                name, value, scope = self._extract_validated_var_definition(var_def, scope)

                if scope not in result['_ansible_vars']:
                    result['_ansible_vars'][scope] = {}

                # allow for setting in loop
                if '_ansible_vars' in task_vars and scope in task_vars['_ansilbe_vars'] and name in task_vars['_ansible_vars'][scope]:
                    result['_ansible_vars'][scope][name] = combine_vars(task_vars['_ansible_facts'][scope][name], value)
                else:
                    result['_ansible_vars'][scope][name] = value

        result['changed'] = False

        return result
