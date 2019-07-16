# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import pytest

from ansible.module_utils.six import with_metaclass
from ansible.utils.singleton import Singleton


class FooSingleton(with_metaclass(Singleton, object)):
    pass


class BarSingleton(with_metaclass(Singleton, object)):
    pass


def test_multiple_creation_and_isolation():
    # ensure that we have the same instance of the same type, but that each type gets its own singleton instance
    a = FooSingleton()
    b = FooSingleton()
    c = BarSingleton()
    d = BarSingleton()

    assert isinstance(a, FooSingleton)
    assert isinstance(b, FooSingleton)
    assert isinstance(c, BarSingleton)
    assert isinstance(d, BarSingleton)
    assert a is b
    assert c is d
    assert a is not c


def test_set_clear_get():
    a = FooSingleton()
    Singleton.clear(FooSingleton)
    b = FooSingleton()

    assert isinstance(a, FooSingleton)
    assert isinstance(b, FooSingleton)
    assert a is not b

    Singleton.set(FooSingleton, a)

    c = FooSingleton()

    # ensure that set() gives us back the instance we passed in
    assert isinstance(c, FooSingleton)
    assert c is a

    direct_value = Singleton.get(FooSingleton)
    assert direct_value is c

    Singleton.clear(FooSingleton)

    # ensure that get doesn't create an instance
    direct_value = Singleton.get(FooSingleton)
    assert direct_value is None

    # and again to be sure
    direct_value = Singleton.get(FooSingleton)
    assert direct_value is None

    # finally, ensure the default behavior works properly after a get
    a = FooSingleton()
    b = FooSingleton()
    assert a is b


def test_assert_is_singleton():
    Singleton.assert_is_singleton(FooSingleton)
    with pytest.raises(TypeError):
        Singleton.assert_is_singleton(int)
