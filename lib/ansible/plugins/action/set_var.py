
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible.errors import AnsibleActionFail
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase
from ansible.utils.vars import isidentifier, combine_vars


class ActionModule(ActionBase):

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('scope',))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if self._task.args:
            scope = self._task.args.pop('scope', 'host')

            if not isinstance(scope, string_types):
                raise AnsibleActionFail("The 'scope' option should be a string, but got a %s" % type(scope))
            elif scope not in C.VALID_VAR_SCOPES:
                raise AnsibleActionFail("Invalid 'scope' option, got '%s' but shoudl be one of: %s" % (scope, ', '.join(C.VALID_VAR_SCOPES)))

            for variable in self._task.args.keys():

                if not isidentifier(variable):
                    raise AnsibleActionFail("The variable name '%s' is not valid. Variables must start with a letter or underscore character, and contain only "
                                            "letters, numbers and underscores." % variable)

                # allow for setting in loop
                if task_vars.get('_ansible_vars', {}).get(scope, {}).get(variable, False):
                    result['_ansible_vars'][scope][variable] = combine_vars(task_vars['_ansible_facts'][scope][variable], self._task.args[variable])
                else:
                    result['_ansible_vars'][scope][variable] = self._task.args[variable]

        result['changed'] = False

        return result
