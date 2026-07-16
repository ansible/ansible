from __future__ import annotations

import typing as t

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
        # accepts a list of literal expressions (no templating), evaluates with no failure on undefined, returns all results
        _vr, args = self.validate_argument_spec(
            argument_spec=dict(
                expression=dict(type='list', strict=True, elements='str', required=True),
            ),
        )

        with ReplacingMarkerBehavior.warning_context() as replacing_behavior:
            templar = self._templar._engine.extend(marker_behavior=replacing_behavior)

            return dict(
                _ansible_verbose_always=True,
                expression_result=[templar.evaluate_expression(expression) for expression in args['expression']],
            )
