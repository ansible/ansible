from __future__ import annotations

import collections.abc as c
import types
import typing as t

from unittest import mock

import pytest

from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible.inventory.data import InventoryData
from ansible.inventory import helpers


def do_test(exec_str: str) -> None:
    hostname = TrustedAsTemplate().tag("hostname")
    groupname = TrustedAsTemplate().tag("groupname")

    # avoid unused locals
    assert hostname
    assert groupname

    inv = InventoryData()
    exec(exec_str)
    RecursiveChecker().visit(inv)


@pytest.mark.parametrize("exec_str, trust_removal_required", (
    # # cases where trust removal is required
    ("inv.add_host(hostname, group='all')", True),
    ("inv.add_group(groupname)", True),
    ("inv.get_host(TrustedAsTemplate().tag('localhost'))", True),
    ("inv.groups['all'].add_host(Host(hostname))", True),
    ("inv.get_host('localhost').set_variable(TrustedAsTemplate().tag('key'), 'value')", True),  # trusted key
    ("inv.get_host('localhost').add_group(Group(groupname))", True),
    ("inv.groups['all'].set_variable(TrustedAsTemplate().tag('key'), 'value')", True),  # trusted key
    # cases where trust removal is not required
    ("inv.add_host('hostname', group=TrustedAsTemplate().tag('all'))", False),  # trusted group
    ("inv.add_child('all', TrustedAsTemplate().tag(inv.add_host('hostname')))", False),  # host trusted
    ("inv.add_child(TrustedAsTemplate().tag('all'), inv.add_host('hostname'))", False),  # group trusted
))
def test_ensure_trust_stripping(exec_str: str, trust_removal_required: bool):
    do_test(exec_str)

    try:
        # re-run the test with the remove_trust helper no-opped to ensure that the test fails as expected
        with mock.patch.object(helpers, 'remove_trust', lambda o: o):
            do_test(exec_str)
    except TrustFoundError:
        if not trust_removal_required:
            pytest.fail("test expected no trust failure; the test is faulty")
    else:
        if trust_removal_required:
            pytest.fail("test expected trust failure; the test is faulty")


class TrustFoundError(Exception):
    """Raised when an object is trusted which should not be."""

    def __init__(self, obj: t.Any) -> None:
        super().__init__(f'TrustedAsTemplate is tagged on {obj}.')


class RecursiveChecker:
    """Recrursive visitor used to assert that an object is not tagged with, and does not contain, a TrustedAsTemplate tag."""

    def __init__(self) -> None:
        self.seen: set[int] = set()

    def visit(self, obj: t.Any) -> None:
        obj_id = id(obj)

        if obj_id in self.seen:
            return

        self.seen.add(obj_id)

        if TrustedAsTemplate.is_tagged_on(obj):
            raise TrustFoundError(obj)

        if isinstance(obj, (str, int, bool, types.NoneType)):
            pass  # expected scalar type
        elif isinstance(obj, (InventoryData, Host, Group)):
            self.visit(obj.__dict__)
        elif isinstance(obj, c.Mapping):
            for key, value in obj.items():
                self.visit(key)
                self.visit(value)
        elif isinstance(obj, c.Iterable):
            for item in obj:
                self.visit(item)
        else:
            raise TypeError(f'Checking of {type(obj)} is not supported.')  # pragma: nocover
