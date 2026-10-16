# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import sys
import types
import typing as t

from ansible.module_utils._internal import _deprecator
from ansible.utils.display import Display
from ansible.utils.sentinel import Sentinel

if t.TYPE_CHECKING:
    from ansible.playbook.base import FieldAttributeBase

display = Display()

_CONTAINERS = frozenset(('list', 'dict', 'set'))


class Attribute:

    def __init__(
        self,
        isa=None,
        private=False,
        default=None,
        required=False,
        listof=None,
        priority=0,
        class_type=None,
        always_post_validate=False,
        alias=None,
        static=False,
    ):

        """
        :class:`Attribute` specifies constraints for attributes of objects which
        derive from playbook data.  The attributes of the object are basically
        a schema for the yaml playbook.

        :kwarg isa: The type of the attribute.  Allowable values are a string
            representation of any yaml basic datatype, python class, or percent.
            (Enforced at post-validation time).
        :kwarg private: Not used at runtime.  The docs playbook keyword dumper uses it to determine
            that a keyword should not be documented.  mpdehaan had plans to remove attributes marked
            private from the ds so they would not have been available at all.
        :kwarg default: Default value if unspecified in the YAML document.
        :kwarg required: Whether or not the YAML document must contain this field.
            If the attribute is None when post-validated, an error will be raised.
        :kwarg listof: If isa is set to "list", this can optionally be set to
            ensure that all elements in the list are of the given type. Valid
            values here are the same as those for isa.
        :kwarg priority: The order in which the fields should be parsed. Generally
            this does not need to be set, it is for rare situations where another
            field depends on the fact that another field was parsed first.
        :kwarg class_type: If isa is set to "class", this can be optionally set to
            a class (not a string name). The YAML data for this field will be
            passed to the __init__ method of that class during post validation and
            the field will be an instance of that class.
        :kwarg always_post_validate: Controls whether a field should be post
            validated or not (default: False).
        :kwarg alias: An alias to use for the attribute name, for situations where
            the attribute name may conflict with a Python reserved word.
        """

        self.isa = isa
        self.private = private
        self.default = default
        self.required = required
        self.listof = listof
        self.priority = priority
        self.class_type = class_type
        self.always_post_validate = always_post_validate
        self.alias = alias
        self.static = static

        if default is not None and self.isa in _CONTAINERS and not callable(default):
            raise TypeError('defaults for FieldAttribute may not be mutable, please provide a callable instead')

    def __set_name__(self, owner, name):
        self.name = name

    def __eq__(self, other):
        return other.priority == self.priority

    def __ne__(self, other):
        return other.priority != self.priority

    # NB: higher priority numbers sort first

    def __lt__(self, other):
        return other.priority < self.priority

    def __gt__(self, other):
        return other.priority > self.priority

    def __le__(self, other):
        return other.priority <= self.priority

    def __ge__(self, other):
        return other.priority >= self.priority

    def __get__(self, obj: FieldAttributeBase, obj_type=None):
        method = f'_get_attr_{self.name}'
        if hasattr(obj, method):
            # NOTE this appears to be not used in the codebase,
            # _get_attr_connection has been replaced by ConnectionFieldAttribute.
            # Leaving it here for test_attr_method from
            # test/units/playbook/test_base.py to pass and for backwards compat.
            if getattr(obj, '_squashed', False):
                value = getattr(obj, f'_{self.name}', Sentinel)
            else:
                value = getattr(obj, method)()
        else:
            value = getattr(obj, f'_{self.name}', Sentinel)

        if value is Sentinel:
            value = self.default
            if callable(value):
                value = value()
                setattr(obj, f'_{self.name}', value)

        return value

    def __set__(self, obj: FieldAttributeBase, value):
        setattr(obj, f'_{self.name}', value)
        if self.alias is not None:
            setattr(obj, f'_{self.alias}', value)

    # NOTE this appears to be not needed in the codebase,
    # leaving it here for test_attr_int_del from
    # test/units/playbook/test_base.py to pass.
    def __delete__(self, obj):
        delattr(obj, f'_{self.name}')


class NonInheritableFieldAttribute(Attribute):
    ...


class FieldAttribute(Attribute):
    def __init__(self, extend=False, prepend=False, **kwargs):
        super().__init__(**kwargs)

        self.extend = extend
        self.prepend = prepend

    def __get__(self, obj, obj_type=None):
        if getattr(obj, '_squashed', False) or getattr(obj, '_finalized', False):
            value = getattr(obj, f'_{self.name}', Sentinel)
        else:
            try:
                value = obj._get_parent_attribute(self.name)
            except AttributeError:
                method = f'_get_attr_{self.name}'
                if hasattr(obj, method):
                    # NOTE this appears to be not needed in the codebase,
                    # _get_attr_connection has been replaced by ConnectionFieldAttribute.
                    # Leaving it here for test_attr_method from
                    # test/units/playbook/test_base.py to pass and for backwards compat.
                    if getattr(obj, '_squashed', False):
                        value = getattr(obj, f'_{self.name}', Sentinel)
                    else:
                        value = getattr(obj, method)()
                else:
                    value = getattr(obj, f'_{self.name}', Sentinel)

        if value is Sentinel:
            value = self.default
            if callable(value):
                value = value()

        return value


class _DeprecatedFieldAttribute(FieldAttribute):
    """
    A `FieldAttribute` which warns when read or written by anything other than the `FieldAttributeBase` machinery.
    Owning classes should keep populating the attribute until its removal, via its private storage (e.g. `obj._name`).
    """

    def __init__(self, *, version: str, help_text: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)

        self._version = version
        self._help_text = help_text
        self._msg = ''

    def __set_name__(self, owner: type, name: str) -> None:
        super().__set_name__(owner, name)

        self._msg = f'The {owner.__name__}.{name} attribute is deprecated.'

    def __get__(self, obj, obj_type=None):
        if obj is not None:
            self._deprecate(sys._getframe(1))

        return super().__get__(obj, obj_type)

    def __set__(self, obj, value) -> None:
        self._deprecate(sys._getframe(1))

        super().__set__(obj, value)

    def _deprecate(self, frame: types.FrameType) -> None:
        """
        Emit a deprecation warning for the access made by `frame`.
        The plugin responsible is named when it can be determined from the accessing frame.
        """
        if frame.f_globals.get('__name__') == 'ansible.playbook.base':
            # Any internal machinery for field attributes should not trigger deprecation warnings.
            return

        help_text = self._help_text

        # None when the accessor is neither core nor a collection plugin (e.g. a script, test or role-local plugin)
        accessor = _deprecator._path_as_plugininfo(frame.f_code.co_filename)
        if accessor and accessor != _deprecator.ANSIBLE_CORE_DEPRECATOR:
            accessed_by = f"Accessed by {accessor.type} plugin {accessor.resolved_name!r}." if accessor.type else f"Accessed by {accessor.resolved_name!r}."
            help_text = f'{help_text} {accessed_by}' if help_text else accessed_by

        display.deprecated(
            msg=self._msg,
            version=self._version,
            help_text=help_text,
        )


# This is not used today but is kept for when the deprecated inherited fields of PlayContext need to be marked as removed.
class _RemovedFieldAttribute:
    """
    Marks an inherited field attribute as removed from the owning class. Any access raises `AttributeError` as if it never existed.
    """

    def __set_name__(self, owner: type, name: str) -> None:
        self._msg = f'{owner.__name__!r} object has no attribute {name!r}'

    def __get__(self, obj, obj_type=None):
        if obj is None:
            return self

        raise AttributeError(self._msg)

    def __set__(self, obj, value) -> None:
        raise AttributeError(self._msg)

    def __delete__(self, obj) -> None:
        raise AttributeError(self._msg)
