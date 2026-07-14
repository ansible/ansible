from __future__ import annotations

import ast

from ansible.errors import AnsibleTypeError


def python_literal_eval(value: object, ignore_errors=False) -> object:
    try:
        if isinstance(value, str):
            return ast.literal_eval(value)

        raise AnsibleTypeError("The `value` to eval must be a string.", obj=value)
    except Exception:
        if ignore_errors:
            return value

        raise


class FilterModule(object):
    @staticmethod
    def filters():
        return dict(python_literal_eval=python_literal_eval)
