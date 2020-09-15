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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import copy, deepcopy


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
        inherit=True,
        alias=None,
        extend=False,
        prepend=False,
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
        :kwarg inherit: A boolean value, which controls whether the object
            containing this field should attempt to inherit the value from its
            parent object if the local value is None.
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
        self.inherit = inherit
        self.alias = alias
        self.extend = extend
        self.prepend = prepend
        self.static = static

        if default is not None and self.isa in _CONTAINERS and not callable(default):
            raise TypeError('defaults for FieldAttribute may not be mutable, please provide a callable instead')

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


class FieldAttribute(Attribute):
    pass
