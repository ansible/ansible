# Copyright 2012, Dag Wieers <dag@wieers.com>
# Copyright 2016, Toshio Kuratomi <tkuratomi@ansible.com>
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
from __future__ import annotations

from ansible.errors import AnsibleValueOmittedError, AnsibleError
from ansible.module_utils.common.validation import _check_type_str_no_conversion
from ansible.plugins.action import ActionBase
from ansible._internal._templating._jinja_common import UndefinedMarker, TruncationMarker
from ansible._internal._templating._utils import Omit
from ansible._internal._templating._marker_behaviors import ReplacingMarkerBehavior, RoutingMarkerBehavior
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):
    """
    Emits informational messages, with special diagnostic handling of some templating failures.
    """

    TRANSFERS_FILES = False
    _requires_connection = False

    def run(self, tmp=None, task_vars=None):
        validation_result, new_module_args = self.validate_argument_spec(
            argument_spec=dict(
                msg=dict(type='raw', default='Hello world!'),
                var=dict(type=_check_type_str_no_conversion),
                verbosity=dict(type='int', default=0),
            ),
            mutually_exclusive=(
                ('msg', 'var'),
            ),
        )

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # get task verbosity
        verbosity = new_module_args['verbosity']

        replacing_behavior = ReplacingMarkerBehavior()

        var_behavior = RoutingMarkerBehavior({
            UndefinedMarker: replacing_behavior,
            TruncationMarker: replacing_behavior,
        })

        if verbosity <= self._display.verbosity:
            if raw_var_arg := new_module_args['var']:
                # If var name is same as result, try to template it
                try:
                    results = self._templar._engine.extend(marker_behavior=var_behavior).evaluate_expression(raw_var_arg)
                except AnsibleValueOmittedError as ex:
                    results = repr(Omit)
                    display.warning("The result of the `var` expression could not be omitted; a placeholder was used instead.", obj=ex.obj)
                except Exception as ex:
                    raise AnsibleError('Error while resolving `var` expression.', obj=raw_var_arg) from ex

                result[raw_var_arg] = results
            else:
                result['msg'] = new_module_args['msg']

            # force flag to make debug output module always verbose
            result['_ansible_verbose_always'] = True

            # propagate any warnings in the task result unless we're skipping the task
            replacing_behavior.emit_warnings()

        else:
            result['skipped_reason'] = "Verbosity threshold not met."
            result['skipped'] = True

        result['failed'] = False

        return result
