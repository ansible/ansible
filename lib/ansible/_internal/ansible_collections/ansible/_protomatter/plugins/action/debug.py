from __future__ import annotations

import typing as t

from ansible.module_utils.common.validation import check_type_str_no_conversion, check_type_list_that_does_not_suck
from ansible.plugins.action import ActionBase
from ansible._internal._templating._engine import TemplateEngine
from ansible._internal._templating._marker_behaviors import ReplacingMarkerBehavior


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _requires_connection = False

    @classmethod
    def finalize_task_arg(cls, name: str, value: t.Any, templar: TemplateEngine, context: t.Any) -> t.Any:
        if name == 'expression':
            return value

        return super().finalize_task_arg(name, value, templar, context)

    def run(self, tmp=None, task_vars=None):
        _vr, args = self.validate_argument_spec(
            argument_spec=dict(
                expression=dict(type=check_type_list_that_does_not_suck, elements=check_type_str_no_conversion, required=True),
            ),
        )

        with ReplacingMarkerBehavior.warning_context() as replacing_behavior:
            templar = self._templar._engine.extend(marker_behavior=replacing_behavior)

            return dict(
                _ansible_verbose_always=True,
                expression_result=[templar.evaluate_expression(expression) for expression in args['expression']],
            )
