# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import contextlib
import typing as t

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleUndefinedVariable, AnsibleTemplateError
from ansible.module_utils.common.text.converters import to_native
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar
from ansible.utils.display import Display

display = Display()


class Conditional:
    '''
    This is a mix-in class, to be used with Base to allow the object
    to be run conditionally when a condition is met or skipped.
    '''

    when = FieldAttribute(isa='list', default=list, extend=True, prepend=True)

    def __init__(self, loader=None):
        # when used directly, this class needs a loader, but we want to
        # make sure we don't trample on the existing one if this class
        # is used as a mix-in with a playbook base class
        if not hasattr(self, '_loader'):
            if loader is None:
                raise AnsibleError("a loader must be specified when using Conditional() directly")
            else:
                self._loader = loader
        super().__init__()

    def _validate_when(self, attr, name, value):
        if not isinstance(value, list):
            setattr(self, name, [value])

    def evaluate_conditional(self, templar: Templar, all_vars: dict[str, t.Any]) -> bool:
        '''
        Loops through the conditionals set on this object, returning
        False if any of them evaluate as such.
        '''
        return self.evaluate_conditional_with_result(templar, all_vars)[0]

    def evaluate_conditional_with_result(self, templar: Templar, all_vars: dict[str, t.Any]) -> tuple[bool, t.Optional[str]]:
        """Loops through the conditionals set on this object, returning
        False if any of them evaluate as such as well as the condition
        that was false.
        """
        for conditional in self.when:
            if conditional is None or conditional == "":
                res = True
            elif isinstance(conditional, bool):
                res = conditional
            else:
                try:
                    res = self._check_conditional(conditional, templar, all_vars)
                except AnsibleError as e:
                    # propagate error `obj` if present, use conditional if position-tagged, fall back to task DS
                    obj = e.obj or conditional if hasattr(conditional, 'ansible_pos') else getattr(self, '_ds', None)

                    raise AnsibleError(
                        "The conditional check '%s' failed. The error was: %s" % (to_native(conditional), to_native(e)),
                        obj=obj,
                    )

            display.debug("Evaluated conditional (%s): %s" % (conditional, res))
            if not res:
                return res, conditional

        return True, None

    def _check_conditional(self, conditional: str, templar: Templar, all_vars: dict[str, t.Any]) -> bool:
        original = conditional
        templar.available_variables = all_vars

        try:
            if templar.is_template(conditional):
                display.warning(
                    "conditional statements should not include jinja2 "
                    "templating delimiters such as {{ }} or {%% %%}. "
                    "Found: %s" % conditional
                )
                conditional = templar.template(conditional)
                if isinstance(conditional, bool):
                    return conditional
                elif conditional == "":
                    return False

            # these should be module-global, but can't be for esoteric config chicken/egg scenarios
            _allow_broken_conditionals = C.config.get_config_value('ALLOW_BROKEN_CONDITIONALS')
            _disable_backported_inspections = C.config.get_config_value('_DISABLE_BACKPORTED_INSPECTIONS')

            # If the result of the first-pass template render (to resolve inline templates) is marked unsafe,
            # explicitly fail since the next templating operation would never evaluate
            if hasattr(conditional, '__UNSAFE__'):
                raise AnsibleTemplateError('Conditional is marked as unsafe, and cannot be evaluated.')

            if _disable_backported_inspections:
                # internal escape hatch to restore original conditional wrapper behavior
                # NOTE The spaces around True and False are intentional to short-circuit literal_eval for
                #      jinja2_native=False and avoid its expensive calls.
                return templar.template(
                    "{%% if %s %%} True {%% else %%} False {%% endif %%}" % conditional,
                ).strip() == "True"

            result, result_type_name = templar.template(f'{{% set __cres = {conditional} %}}{{{{ [true if __cres else false, __cres.__class__.__name__] }}}}')

            if result_type_name != 'bool':
                if _allow_broken_conditionals:
                    display.deprecated(
                        msg=f"Conditional result at {self._get_conditional_source_context(conditional)} was of type {result_type_name!r}. "
                            f"Conditional results should only be True or False. The result was interpreted as {result}.",
                        version="2.19",
                    )
                else:
                    raise AnsibleTemplateError(
                        message=f"Conditional result was of type {result_type_name!r}. "
                                "Conditional results must be True or False when `ALLOW_BROKEN_CONDITIONALS` is disabled, "
                                "which is the default in Ansible Core >= 2.19.",
                        obj=original,
                    )

            return result
        except AnsibleUndefinedVariable as e:
            raise AnsibleUndefinedVariable("error while evaluating conditional (%s): %s" % (original, e))

    def _get_conditional_source_context(self, conditional: str) -> str:
        """Utility method to approximate 2.19+ source context for warnings."""
        src: str | None = None
        location_label: str | None = None

        # most string expressions should have been tagged by the YAML parser
        with contextlib.suppress(AttributeError, ValueError):
            src, line, col = conditional.ansible_pos
            location_label = "location"

        if not location_label:
            # report approximate location from the conditional's task DS, if available
            with contextlib.suppress(AttributeError, ValueError):
                src, line, col = self._ds.ansible_pos
                location_label = "approximate location"

        # display the conditional expression inline only if we have no other source context
        return f'{location_label} {src} {line}:{col}' if location_label else f'unknown location (conditional: {conditional!r})'
