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

import uuid

from inspect import getmembers
from io import FileIO

from six import iteritems, string_types

from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleParserError
from ansible.parsing import DataLoader
from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.template import Templar
from ansible.utils.boolean import boolean

from ansible.utils.debug import debug

from ansible.template import template

class Base:

    def __init__(self):

        # initialize the data loader and variable manager, which will be provided
        # later when the object is actually loaded
        self._loader = None
        self._variable_manager = None

        # every object gets a random uuid:
        self._uuid = uuid.uuid4()

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

    def load_data(self, ds, variable_manager=None, loader=None):
        ''' walk the input datastructure and assign any values '''

        assert ds is not None

        # the variable manager class is used to manage and merge variables
        # down to a single dictionary for reference in templating, etc.
        self._variable_manager = variable_manager

        # the data loader class is used to parse data from strings and files
        if loader is not None:
            self._loader = loader
        else:
            self._loader = DataLoader()

        if isinstance(ds, string_types) or isinstance(ds, FileIO):
            ds = self._loader.load(ds)

        # call the munge() function to massage the data into something
        # we can more easily parse, and then call the validation function
        # on it to ensure there are no incorrect key values
        ds = self.munge(ds)
        self._validate_attributes(ds)

        # Walk all attributes in the class.
        #
        # FIXME: we currently don't do anything with private attributes but
        #        may later decide to filter them out of 'ds' here.

        for (name, attribute) in iteritems(self._get_base_attributes()):
            # copy the value over unless a _load_field method is defined
            if name in ds:
                method = getattr(self, '_load_%s' % name, None)
                if method:
                    self._attributes[name] = method(name, ds[name])
                else:
                    self._attributes[name] = ds[name]

        # run early, non-critical validation
        self.validate()

        # cache the datastructure internally
        setattr(self, '_ds', ds)

        # return the constructed object
        return self

    def get_ds(self):
       	try:
            return getattr(self, '_ds')
        except AttributeError:
            return None

    def get_loader(self):
        return self._loader

    def get_variable_manager(self):
        return self._variable_manager

    def _validate_attributes(self, ds):
        '''
        Ensures that there are no keys in the datastructure which do
        not map to attributes for this object.
        '''

        valid_attrs = [name for (name, attribute) in iteritems(self._get_base_attributes())]
        for key in ds:
            if key not in valid_attrs:
                raise AnsibleParserError("'%s' is not a valid attribute for a %s" % (key, self.__class__.__name__), obj=ds)

    def validate(self, all_vars=dict()):
        ''' validation that is done at parse time, not load time '''

        # walk all fields in the object
        for (name, attribute) in iteritems(self._get_base_attributes()):

            # run validator only if present
            method = getattr(self, '_validate_%s' % name, None)
            if method:
                method(attribute, name, getattr(self, name))

    def copy(self):
        '''
        Create a copy of this object and return it.
        '''

        new_me = self.__class__()

        for (name, attribute) in iteritems(self._get_base_attributes()):
            setattr(new_me, name, getattr(self, name))

        new_me._loader           = self._loader
        new_me._variable_manager = self._variable_manager

        return new_me

    def post_validate(self, all_vars=dict(), fail_on_undefined=True):
        '''
        we can't tell that everything is of the right type until we have
        all the variables.  Run basic types (from isa) as well as
        any _post_validate_<foo> functions.
        '''

        basedir = None
        if self._loader is not None:
            basedir = self._loader.get_basedir()

        templar = Templar(loader=self._loader, variables=all_vars, fail_on_undefined=fail_on_undefined)

        for (name, attribute) in iteritems(self._get_base_attributes()):

            if getattr(self, name) is None:
                if not attribute.required:
                    continue
                else:
                    raise AnsibleParserError("the field '%s' is required but was not set" % name)

            try:
                # if the attribute contains a variable, template it now
                value = templar.template(getattr(self, name))
                
                # run the post-validator if present
                method = getattr(self, '_post_validate_%s' % name, None)
                if method:
                    value = method(attribute, value, all_vars, fail_on_undefined)
                else:
                    # otherwise, just make sure the attribute is of the type it should be
                    if attribute.isa == 'string':
                        value = unicode(value)
                    elif attribute.isa == 'int':
                        value = int(value)
                    elif attribute.isa == 'bool':
                        value = boolean(value)
                    elif attribute.isa == 'list':
                        if not isinstance(value, list):
                            value = [ value ]
                    elif attribute.isa == 'dict' and not isinstance(value, dict):
                        raise TypeError()

                # and assign the massaged value back to the attribute field
                setattr(self, name, value)

            except (TypeError, ValueError), e:
                raise AnsibleParserError("the field '%s' has an invalid value (%s), and could not be converted to an %s. Error was: %s" % (name, value, attribute.isa, e), obj=self.get_ds())
            except UndefinedError, e:
                if fail_on_undefined:
                    raise AnsibleParserError("the field '%s' has an invalid value, which appears to include a variable that is undefined. The error was: %s" % (name,e), obj=self.get_ds())

    def serialize(self):
        '''
        Serializes the object derived from the base object into
        a dictionary of values. This only serializes the field
        attributes for the object, so this may need to be overridden
        for any classes which wish to add additional items not stored
        as field attributes.
        '''

        repr = dict()

        for (name, attribute) in iteritems(self._get_base_attributes()):
            repr[name] = getattr(self, name)

        # serialize the uuid field
        repr['uuid'] = getattr(self, '_uuid')

        return repr

    def deserialize(self, data):
        '''
        Given a dictionary of values, load up the field attributes for
        this object. As with serialize(), if there are any non-field
        attribute data members, this method will need to be overridden
        and extended.
        '''

        assert isinstance(data, dict)

        for (name, attribute) in iteritems(self._get_base_attributes()):
            if name in data:
                setattr(self, name, data[name])
            else:
                setattr(self, name, attribute.default)

        # restore the UUID field
        setattr(self, '_uuid', data.get('uuid'))

    def __getattr__(self, needle):

        # return any attribute names as if they were real
        # optionally allowing masking by accessors

        if not needle.startswith("_"):
            method = "get_%s" % needle
            if method in self.__dict__:
                return method(self)

        if needle in self._attributes:
            return self._attributes[needle]

        raise AttributeError("attribute not found in %s: %s" % (self.__class__.__name__, needle))

    def __getstate__(self):
        return self.serialize()

    def __setstate__(self, data):
        self.__init__()
        self.deserialize(data)

