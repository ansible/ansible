from __future__ import annotations

from ..module_utils.my_util import question  # pylint: disable=unused-import


def action_code():
    raise Exception('hello from my_action.py, this code should never execute')  # pragma: nocover
