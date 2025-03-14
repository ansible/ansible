from __future__ import annotations

import typing as t

from ansible.module_utils.common.messages import SummaryBase, Detail

_TSummaryBase = t.TypeVar('_TSummaryBase', bound=SummaryBase)


def make_summary(summary_type: type[_TSummaryBase], *details: Detail, formatted_traceback: t.Optional[str] = None, **kwargs) -> _TSummaryBase:
    """Utility factory method to avoid inline tuples."""
    return summary_type(details=details, formatted_traceback=formatted_traceback, **kwargs)
