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

from inspect import getmembers
from io import FileIO

from six import iteritems, string_types

from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.parsing.yaml import DataLoader

class Base:

    _tags = FieldAttribute(isa='list')
    _when = FieldAttribute(isa='list')

    def __init__(self, loader=DataLoader):

        # the data loader class is used to parse data from strings and files
        self._loader = loader

        # each class knows attributes set upon it, see Task.py for example
        self._attributes = dict()

        for (name, value) in iteritems(self._get_base_attributes()):
            self._attributes[name] = value.default

    def _get_base_attributes(self):
        '''
        Returns the list of attributes for this class (or any subclass thereof).
        If the attribute name starts with an underscore, it is removed
        '''
        base_attributes = dict()
        for (name, value) in getmembers(self.__class__):
            if isinstance(value, Attribute):
               if name.startswith('_'):
                   name = name[1:]
               base_attributes[name] = value
        return base_attributes

    def munge(self, ds):
        ''' infrequently used method to do some pre-processing of legacy terms '''

        return ds

    def load_data(self, ds):
        ''' walk the input datastructure and assign any values '''

        assert ds is not None

        if isinstance(ds, string_types) or isinstance(ds, FileIO):
            ds = self._loader.load(ds)

        # we currently don't do anything with private attributes but may
        # later decide to filter them out of 'ds' here.

        ds = self.munge(ds)

        # walk all attributes in the class
        for (name, attribute) in iteritems(self._get_base_attributes()):

            # copy the value over unless a _load_field method is defined
            if name in ds:
                method = getattr(self, '_load_%s' % name, None)
                if method:
                    self._attributes[name] = method(name, ds[name])
                else:
                    self._attributes[name] = ds[name]

        # return the constructed object
        self.validate()
        return self


    def validate(self):
        ''' validation that is done at parse time, not load time '''

        # walk all fields in the object
        for (name, attribute) in iteritems(self._get_base_attributes()):

            # run validator only if present
            method = getattr(self, '_validate_%s' % name, None)
            if method:
                method(self, attribute)

    def post_validate(self, runner_context):
        '''
        we can't tell that everything is of the right type until we have
        all the variables.  Run basic types (from isa) as well as
        any _post_validate_<foo> functions.
        '''

        raise exception.NotImplementedError

    def __getattr__(self, needle):

        # return any attribute names as if they were real
        # optionally allowing masking by accessors

        if not needle.startswith("_"):
            method = "get_%s" % needle
            if method in self.__dict__:
                return method(self)

        if needle in self._attributes:
            return self._attributes[needle]

        raise AttributeError("attribute not found: %s" % needle)
