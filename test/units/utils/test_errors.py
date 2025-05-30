from __future__ import annotations

import pytest

from ansible import errors

from units.test_utils.controller.display import emits_warnings


@pytest.mark.parametrize("name", (
    "AnsibleFilterTypeError",
    "_AnsibleActionDone",
))
def test_deprecated(name: str) -> None:
    with emits_warnings(deprecation_pattern='is deprecated'):
        getattr(errors, name)


def test_deprecated_attribute_error() -> None:
    with pytest.raises(AttributeError):
        getattr(errors, 'bogus')
