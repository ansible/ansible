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

import collections
import itertools
import operator
import uuid

from functools import partial
from inspect import getmembers

from ansible.compat.six import iteritems, string_types

from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleParserError
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.utils.boolean import boolean
from ansible.utils.vars import combine_vars, isidentifier
from ansible.utils.unicode import to_unicode

BASE_ATTRIBUTES = {}


class Base:

    # connection/transport
    _connection          = FieldAttribute(isa='string')
    _port                = FieldAttribute(isa='int')
    _remote_user         = FieldAttribute(isa='string')

    # variables
    _vars                = FieldAttribute(isa='dict', priority=100)

    # flags and misc. settings
    _environment         = FieldAttribute(isa='list')
    _no_log              = FieldAttribute(isa='bool')
    _always_run           = FieldAttribute(isa='bool')
    _run_once             = FieldAttribute(isa='bool')
    _ignore_errors        = FieldAttribute(isa='bool')

    # param names which have been deprecated/removed
    DEPRECATED_ATTRIBUTES = [
        'sudo', 'sudo_user', 'sudo_pass', 'sudo_exe', 'sudo_flags',
        'su', 'su_user', 'su_pass', 'su_exe', 'su_flags',
    ]

    def __init__(self):

        # initialize the data loader and variable manager, which will be provided
        # later when the object is actually loaded
        self._loader = None
        self._variable_manager = None

        # every object gets a random uuid:
        self._uuid = uuid.uuid4()

        # and initialize the base attributes
        self._initialize_base_attributes()

        # and init vars, avoid using defaults in field declaration as it lives across plays
        self.vars = dict()


    # The following three functions are used to programatically define data
    # descriptors (aka properties) for the Attributes of all of the playbook
    # objects (tasks, blocks, plays, etc).
    #
    # The function signature is a little strange because of how we define
    # them.  We use partial to give each method the name of the Attribute that
    # it is for.  Since partial prefills the positional arguments at the
    # beginning of the function we end up with the first positional argument
    # being allocated to the name instead of to the class instance (self) as
    # normal.  To deal with that we make the property name field the first
    # positional argument and self the second arg.
    #
    # Because these methods are defined inside of the class, they get bound to
    # the instance when the object is created.  After we run partial on them
    # and put the result back into the class as a property, they get bound
    # a second time.  This leads to self being  placed in the arguments twice.
    # To work around that, we mark the functions as @staticmethod so that the
    # first binding to the instance doesn't happen.

    @staticmethod
    def _generic_g(prop_name, self):
        method = "_get_attr_%s" % prop_name
        if hasattr(self, method):
            return getattr(self, method)()

        value = self._attributes[prop_name]
        if value is None and hasattr(self, '_get_parent_attribute'):
            value = self._get_parent_attribute(prop_name)
        return value

    @staticmethod
    def _generic_s(prop_name, self, value):
        self._attributes[prop_name] = value

    @staticmethod
    def _generic_d(prop_name, self):
        del self._attributes[prop_name]

    def _get_base_attributes(self):
        '''
        Returns the list of attributes for this class (or any subclass thereof).
        If the attribute name starts with an underscore, it is removed
        '''

        # check cache before retrieving attributes
        if self.__class__ in BASE_ATTRIBUTES:
            return BASE_ATTRIBUTES[self.__class__]

        # Cache init
        base_attributes = dict()
        for (name, value) in getmembers(self.__class__):
            if isinstance(value, Attribute):
                if name.startswith('_'):
                    name = name[1:]
                base_attributes[name] = value
        BASE_ATTRIBUTES[self.__class__] = base_attributes
        return base_attributes

    def _initialize_base_attributes(self):
        # each class knows attributes set upon it, see Task.py for example
        self._attributes = dict()

        for (name, value) in self._get_base_attributes().items():
            getter = partial(self._generic_g, name)
            setter = partial(self._generic_s, name)
            deleter = partial(self._generic_d, name)

            # Place the property into the class so that cls.name is the
            # property functions.
            setattr(Base, name, property(getter, setter, deleter))

            # Place the value into the instance so that the property can
            # process and hold that value.
            setattr(self, name, value.default)

    def preprocess_data(self, ds):
        ''' infrequently used method to do some pre-processing of legacy terms '''

        for base_class in self.__class__.mro():
            method = getattr(self, "_preprocess_data_%s" % base_class.__name__.lower(), None)
            if method:
                return method(ds)
        return ds

    def load_data(self, ds, variable_manager=None, loader=None):
        ''' walk the input datastructure and assign any values '''

        assert ds is not None

        # cache the datastructure internally
        setattr(self, '_ds', ds)

        # the variable manager class is used to manage and merge variables
        # down to a single dictionary for reference in templating, etc.
        self._variable_manager = variable_manager

        # the data loader class is used to parse data from strings and files
        if loader is not None:
            self._loader = loader
        else:
            self._loader = DataLoader()

        # call the preprocess_data() function to massage the data into
        # something we can more easily parse, and then call the validation
        # function on it to ensure there are no incorrect key values
        ds = self.preprocess_data(ds)
        self._validate_attributes(ds)

        # Walk all attributes in the class. We sort them based on their priority
        # so that certain fields can be loaded before others, if they are dependent.
        base_attributes = self._get_base_attributes()
        for name, attr in sorted(base_attributes.items(), key=operator.itemgetter(1)):
            # copy the value over unless a _load_field method is defined
            if name in ds:
                method = getattr(self, '_load_%s' % name, None)
                if method:
                    self._attributes[name] = method(name, ds[name])
                else:
                    self._attributes[name] = ds[name]

        # run early, non-critical validation
        self.validate()

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

        valid_attrs = frozenset(name for name in self._get_base_attributes())
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
            else:
                # and make sure the attribute is of the type it should be
                value = getattr(self, name)
                if value is not None:
                    if attribute.isa == 'string' and isinstance(value, (list, dict)):
                        raise AnsibleParserError("The field '%s' is supposed to be a string type,"
                                " however the incoming data structure is a %s" % (name, type(value)), obj=self.get_ds())

    def copy(self):
        '''
        Create a copy of this object and return it.
        '''

        new_me = self.__class__()

        for name in self._get_base_attributes():
            attr_val = getattr(self, name)
            if isinstance(attr_val, collections.Sequence):
                setattr(new_me, name, attr_val[:])
            elif isinstance(attr_val, collections.Mapping):
                setattr(new_me, name, attr_val.copy())
            else:
                setattr(new_me, name, attr_val)

        new_me._loader           = self._loader
        new_me._variable_manager = self._variable_manager

        new_me._uuid = self._uuid

        # if the ds value was set on the object, copy it to the new copy too
        if hasattr(self, '_ds'):
            new_me._ds = self._ds

        return new_me

    def post_validate(self, templar):
        '''
        we can't tell that everything is of the right type until we have
        all the variables.  Run basic types (from isa) as well as
        any _post_validate_<foo> functions.
        '''

        # save the omit value for later checking
        omit_value = templar._available_variables.get('omit')

        for (name, attribute) in iteritems(self._get_base_attributes()):

            if getattr(self, name) is None:
                if not attribute.required:
                    continue
                else:
                    raise AnsibleParserError("the field '%s' is required but was not set" % name)
            elif not attribute.always_post_validate and self.__class__.__name__ not in ('Task', 'Handler', 'PlayContext'):
                # Intermediate objects like Play() won't have their fields validated by
                # default, as their values are often inherited by other objects and validated
                # later, so we don't want them to fail out early
                continue

            try:
                # Run the post-validator if present. These methods are responsible for
                # using the given templar to template the values, if required.
                method = getattr(self, '_post_validate_%s' % name, None)
                if method:
                    value = method(attribute, getattr(self, name), templar)
                else:
                    # if the attribute contains a variable, template it now
                    value = templar.template(getattr(self, name))

                # if this evaluated to the omit value, set the value back to
                # the default specified in the FieldAttribute and move on
                if omit_value is not None and value == omit_value:
                    setattr(self, name, attribute.default)
                    continue

                # and make sure the attribute is of the type it should be
                if value is not None:
                    if attribute.isa == 'string':
                        value = to_unicode(value)
                    elif attribute.isa == 'int':
                        value = int(value)
                    elif attribute.isa == 'float':
                        value = float(value)
                    elif attribute.isa == 'bool':
                        value = boolean(value)
                    elif attribute.isa == 'percent':
                        # special value, which may be an integer or float
                        # with an optional '%' at the end
                        if isinstance(value, string_types) and '%' in value:
                            value = value.replace('%', '')
                        value = float(value)
                    elif attribute.isa == 'list':
                        if value is None:
                            value = []
                        elif not isinstance(value, list):
                            value = [ value ]
                        if attribute.listof is not None:
                            for item in value:
                                if not isinstance(item, attribute.listof):
                                    raise AnsibleParserError("the field '%s' should be a list of %s,"
                                            " but the item '%s' is a %s" % (name, attribute.listof, item, type(item)), obj=self.get_ds())
                                elif attribute.required and attribute.listof == string_types:
                                    if item is None or item.strip() == "":
                                        raise AnsibleParserError("the field '%s' is required, and cannot have empty values" % (name,), obj=self.get_ds())
                    elif attribute.isa == 'set':
                        if value is None:
                            value = set()
                        else:
                            if not isinstance(value, (list, set)):
                                value = [ value ]
                            if not isinstance(value, set):
                                value = set(value)
                    elif attribute.isa == 'dict':
                        if value is None:
                            value = dict()
                        elif not isinstance(value, dict):
                            raise TypeError("%s is not a dictionary" % value)

                # and assign the massaged value back to the attribute field
                setattr(self, name, value)

            except (TypeError, ValueError) as e:
                raise AnsibleParserError("the field '%s' has an invalid value (%s), and could not be converted to an %s."
                        " Error was: %s" % (name, value, attribute.isa, e), obj=self.get_ds())
            except UndefinedError as e:
                if templar._fail_on_undefined_errors and name != 'name':
                    raise AnsibleParserError("the field '%s' has an invalid value, which appears to include a variable that is undefined."
                            " The error was: %s" % (name,e), obj=self.get_ds())

    def serialize(self):
        '''
        Serializes the object derived from the base object into
        a dictionary of values. This only serializes the field
        attributes for the object, so this may need to be overridden
        for any classes which wish to add additional items not stored
        as field attributes.
        '''

        repr = dict()

        for name in self._get_base_attributes():
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

    def _load_vars(self, attr, ds):
        '''
        Vars in a play can be specified either as a dictionary directly, or
        as a list of dictionaries. If the later, this method will turn the
        list into a single dictionary.
        '''

        def _validate_variable_keys(ds):
            for key in ds:
                if not isidentifier(key):
                    raise TypeError("'%s' is not a valid variable name" % key)

        try:
            if isinstance(ds, dict):
                _validate_variable_keys(ds)
                return ds
            elif isinstance(ds, list):
                all_vars = dict()
                for item in ds:
                    if not isinstance(item, dict):
                        raise ValueError
                    _validate_variable_keys(item)
                    all_vars = combine_vars(all_vars, item)
                return all_vars
            elif ds is None:
                return {}
            else:
                raise ValueError
        except ValueError:
            raise AnsibleParserError("Vars in a %s must be specified as a dictionary, or a list of dictionaries" % self.__class__.__name__, obj=ds)
        except TypeError as e:
            raise AnsibleParserError("Invalid variable name in vars specified for %s: %s" % (self.__class__.__name__, e), obj=ds)

    def _extend_value(self, value, new_value):
        '''
        Will extend the value given with new_value (and will turn both
        into lists if they are not so already). The values are run through
        a set to remove duplicate values.
        '''

        if not isinstance(value, list):
            value = [ value ]
        if not isinstance(new_value, list):
            new_value = [ new_value ]

        #return list(set(value + new_value))
        return [i for i,_ in itertools.groupby(value + new_value) if i is not None]

    def __getstate__(self):
        return self.serialize()

    def __setstate__(self, data):
        self.__init__()
        self.deserialize(data)
