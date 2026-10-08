# (c) 2015, Marius Gedminas <marius@gedmin.as>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import unittest

import pytest

from ansible.module_utils._internal import _deprecator, _messages
from ansible.playbook.attribute import Attribute, _DeprecatedFieldAttribute, _RemovedFieldAttribute
from ansible.playbook.base import Base
from ansible.utils.display import Display


class TestAttribute(unittest.TestCase):

    def setUp(self):
        self.one = Attribute(priority=100)
        self.two = Attribute(priority=0)

    def test_eq(self):
        self.assertTrue(self.one == self.one)
        self.assertFalse(self.one == self.two)

    def test_ne(self):
        self.assertFalse(self.one != self.one)
        self.assertTrue(self.one != self.two)

    def test_lt(self):
        self.assertFalse(self.one < self.one)
        self.assertTrue(self.one < self.two)
        self.assertFalse(self.two < self.one)

    def test_gt(self):
        self.assertFalse(self.one > self.one)
        self.assertFalse(self.one > self.two)
        self.assertTrue(self.two > self.one)

    def test_le(self):
        self.assertTrue(self.one <= self.one)
        self.assertTrue(self.one <= self.two)
        self.assertFalse(self.two <= self.one)

    def test_ge(self):
        self.assertTrue(self.one >= self.one)
        self.assertFalse(self.one >= self.two)
        self.assertTrue(self.two >= self.one)


class DeprecatedThing(Base):
    """A playbook object with a deprecated attribute of its own and a deprecated override of an inherited one."""

    old = _DeprecatedFieldAttribute(isa='string', default='legacy', version='2.99', help_text='Use new instead.')
    connection = _DeprecatedFieldAttribute(isa='string', version='2.99')


@pytest.fixture
def deprecated(mocker):
    return mocker.patch.object(Display, 'deprecated')


def test_deprecated_field_attribute_warns_on_read_and_write(deprecated):
    thing = DeprecatedThing()

    assert thing.old == 'legacy'

    deprecated.assert_called_once_with(msg='The DeprecatedThing.old attribute is deprecated.', version='2.99', help_text='Use new instead.')

    thing.old = 'value'

    assert deprecated.call_count == 2
    assert thing._old == 'value'


def test_deprecated_field_attribute_private_storage_is_silent(deprecated):
    """Owners should keep populating deprecated attributes via their private storage until removal, without warning."""
    thing = DeprecatedThing()
    thing._old = 'populated'

    assert thing._old == 'populated'
    assert not deprecated.called

    assert thing.old == 'populated'  # only the consumer is warned

    assert deprecated.call_count == 1


def test_deprecated_field_attribute_machinery_is_silent(deprecated):
    thing = DeprecatedThing()
    thing._old = 'value'

    copied = thing.copy()
    attrs = thing.dump_attrs()
    restored = DeprecatedThing()
    restored.from_attrs(attrs)

    assert attrs['old'] == 'value'
    assert copied._old == restored._old == 'value'
    assert not deprecated.called


def test_deprecated_field_attribute_overrides_inherited(deprecated):
    assert not isinstance(Base.fattributes['connection'], _DeprecatedFieldAttribute)  # the base class is unaffected
    assert isinstance(DeprecatedThing.fattributes['connection'], _DeprecatedFieldAttribute)

    thing = DeprecatedThing()

    assert thing.connection is None

    deprecated.assert_called_once_with(msg='The DeprecatedThing.connection attribute is deprecated.', version='2.99', help_text=None)


@pytest.mark.parametrize('accessor, expected_help_text', (
    (_messages.PluginInfo(resolved_name='ns.col.thing', type=_messages.PluginType.ACTION), "Use new instead. Accessed by 'ns.col.thing'."),
    (_deprecator.ANSIBLE_CORE_DEPRECATOR, 'Use new instead.'),
    (None, 'Use new instead.'),
))
def test_deprecated_field_attribute_names_accessor(deprecated, mocker, accessor, expected_help_text):
    mocker.patch.object(_deprecator, '_path_as_plugininfo', return_value=accessor)

    assert DeprecatedThing().old == 'legacy'

    assert deprecated.call_args.kwargs['help_text'] == expected_help_text


class RemovedThing(Base):
    """A playbook object which has removed an inherited attribute."""

    connection = _RemovedFieldAttribute()


def test_removed_field_attribute_is_not_a_field():
    assert 'connection' in Base.fattributes  # the base class is unaffected
    assert 'connection' not in RemovedThing.fattributes


def test_removed_field_attribute_machinery_skips_it():
    thing = RemovedThing()
    thing.port = 22  # another base field still works

    copied = thing.copy()
    attrs = thing.dump_attrs()
    restored = RemovedThing()
    restored.from_attrs(attrs)

    assert 'connection' not in attrs
    assert '_connection' not in vars(thing) and '_connection' not in vars(copied)
    assert copied.port == restored.port == 22


def test_removed_field_attribute_access_raises():
    thing = RemovedThing()

    assert not hasattr(thing, 'connection')
    assert getattr(thing, 'connection', 'default') == 'default'

    with pytest.raises(AttributeError, match="'RemovedThing' object has no attribute 'connection'"):
        thing.connection  # pylint: disable=pointless-statement

    with pytest.raises(AttributeError, match="'RemovedThing' object has no attribute 'connection'"):
        thing.connection = 'ssh'

    with pytest.raises(AttributeError, match="'RemovedThing' object has no attribute 'connection'"):
        del thing.connection
