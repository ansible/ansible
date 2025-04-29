from __future__ import annotations

import typing as t

import pytest

from ansible.module_utils.common.yaml import yaml_dump, yaml_dump_all
from ansible.module_utils._internal._datatag import Tripwire
from ansible.module_utils._internal._datatag._tags import Deprecated
from units.mock.custom_types import CustomMapping, CustomSequence

_test_tag = Deprecated(msg="test")


@pytest.mark.parametrize("value, expected", (
    (CustomMapping(dict(a=1)), "a: 1"),
    (CustomSequence([1]), "- 1"),
    (_test_tag.tag(dict(a=1)), "a: 1"),
    (_test_tag.tag([1]), "- 1"),
    (_test_tag.tag(1), "1"),
    (_test_tag.tag("Ansible"), "Ansible"),
))
def test_dump(value: t.Any, expected: str) -> None:
    """Verify supported types can be dumped."""
    result = yaml_dump(value).strip()

    assert result == expected

    result = yaml_dump_all([value]).strip()

    assert result == expected


def test_dump_tripwire() -> None:
    """Verify dumping a tripwire trips it."""
    class Tripped(Exception):
        pass

    class CustomTripwire(Tripwire):
        def trip(self) -> t.NoReturn:
            raise Tripped()

    with pytest.raises(Tripped):
        yaml_dump(CustomTripwire())

    with pytest.raises(Tripped):
        yaml_dump_all([CustomTripwire()])
