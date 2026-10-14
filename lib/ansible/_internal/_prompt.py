# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing as t
from collections import ChainMap

from ansible.errors import AnsibleError
from ansible._internal._templating._engine import TemplateEngine, TemplateOptions
from ansible._internal._templating._lazy_containers import _AnsibleLazyTemplateMixin
from ansible._internal._templating._utils import LazyOptions, TemplateContext


def build_prompt_validator(expression: object, varname: str, templar: TemplateEngine) -> t.Callable[[str], bool] | None:
    """Evaluate a prompt condition with each candidate overriding the variable of the same name."""
    if expression is None:
        return None
    if not isinstance(expression, str) or not expression.strip():
        raise AnsibleError("The vars_prompt validate option must be a non-empty Jinja2 expression string.", obj=expression)

    # Parse without evaluating variables or running plugins, including during syntax checks.
    try:
        templar.environment.parse('{% if ' + expression + ' %}{% endif %}')
    except Exception as ex:
        raise AnsibleError("Invalid Jinja2 expression in vars_prompt validate.", obj=expression) from ex

    def validate(value: str) -> bool:
        # Input is data, not a trusted template, even when the final prompt value allows templating.
        with TemplateContext(template_value=expression, templar=templar, options=TemplateOptions.DEFAULT):
            candidate_vars = _AnsibleLazyTemplateMixin._try_create({varname: value}, LazyOptions.SKIP_TEMPLATES)
        candidate_templar = templar.extend(variables=ChainMap(candidate_vars, templar.available_variables))
        try:
            return candidate_templar.evaluate_conditional(expression)
        except Exception as ex:
            raise AnsibleError(f"Error evaluating vars_prompt validation for {varname!r}.", obj=expression) from ex

    return validate
