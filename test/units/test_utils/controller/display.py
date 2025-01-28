from __future__ import annotations

import contextlib
import re
import typing as t

from ansible.utils.display import _DeferredWarningContext


@contextlib.contextmanager
def emits_deprecation_warning(match: str) -> t.Iterator[None]:
    """Assert that the code within the context manager body emits a deprecation warning whose formatted output matches the supplied regex."""
    with _DeferredWarningContext(variables=dict(ansible_deprecation_warnings=True)) as ctx:
        yield

    warnings = ctx.get_deprecation_warnings()

    assert re.search(match, str(warnings))
    assert len(warnings) == 1
