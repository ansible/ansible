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

import itertools
import typing as t

from ansible.utils.sentinel import Sentinel

if t.TYPE_CHECKING:
    from ansible.playbook.base import FieldAttributeBase

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
        if (value := getattr(obj, f'_{self.name}', Sentinel)) is Sentinel:
            value = self.default
            if callable(value):
                value = value()
                setattr(obj, f'_{self.name}', value)

        return value

    def __set__(self, obj: FieldAttributeBase, value):
        setattr(obj, f'_{self.name}', value)
        if self.alias is not None:
            setattr(obj, f'_{self.alias}', value)


class NonInheritableFieldAttribute(Attribute):
    ...


def get_static_parents(obj):
    o = obj
    while getattr(o, '_parent', None):
        if getattr(o._parent, 'statically_loaded', True):
            yield o._parent
        o = getattr(o, '_parent', None)

    if role := getattr(obj, '_role', None):
        yield role
        if dep_chain := obj.get_dep_chain():
            yield from reversed(dep_chain)

    yield obj.play


# when, tags, module_defaults, environment
def _extend_value(value, new_value, prepend=False):
    if not isinstance(value, list):
        value = [value]
    if not isinstance(new_value, list):
        new_value = [new_value]

    value = [v for v in value if v is not Sentinel]
    new_value = [v for v in new_value if v is not Sentinel]

    if prepend:
        combined = new_value + value
    else:
        combined = value + new_value

    return [i for i, dummy in itertools.groupby(combined) if i is not None]


class FieldAttribute(Attribute):
    def __init__(self, extend=False, prepend=False, **kwargs):
        super().__init__(**kwargs)

        self.extend = extend
        self.prepend = prepend

    def __get__(self, obj, obj_type=None):
        value = getattr(obj, f'_{self.name}', Sentinel)
        if not obj.finalized:
            value = getattr(obj, f'_{self.name}', Sentinel)
            if self.extend:
                for parent in get_static_parents(obj):
                    parent_value = getattr(parent, f'_{self.name}', Sentinel)
                    value = _extend_value(value, parent_value, self.prepend)
            elif value is Sentinel:
                for parent in get_static_parents(obj):
                    if (value := getattr(parent, f'_{self.name}', Sentinel)) is not Sentinel:
                        break

        if value is Sentinel:
            value = self.default
            if callable(value):
                value = value()

        return value
