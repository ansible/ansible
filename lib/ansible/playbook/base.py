# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import itertools
import operator

from copy import copy as shallowcopy
from functools import partial

from jinja2.exceptions import UndefinedError

from ansible import constants as C
from ansible import context
from ansible.module_utils.six import iteritems, string_types, with_metaclass
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.errors import AnsibleParserError, AnsibleUndefinedVariable, AnsibleAssertionError
from ansible.module_utils._text import to_text, to_native
from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.parsing.dataloader import DataLoader
from ansible.utils.display import Display
from ansible.utils.sentinel import Sentinel
from ansible.utils.vars import combine_vars, isidentifier, get_unique_id

display = Display()


def _generic_g(prop_name, self):
    try:
        value = self._attributes[prop_name]
    except KeyError:
        raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, prop_name))

    if value is Sentinel:
        value = self._attr_defaults[prop_name]

    return value


def _generic_g_method(prop_name, self):
    try:
        if self._squashed:
            return self._attributes[prop_name]
        method = "_get_attr_%s" % prop_name
        return getattr(self, method)()
    except KeyError:
        raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, prop_name))


def _generic_g_parent(prop_name, self):
    try:
        if self._squashed or self._finalized:
            value = self._attributes[prop_name]
        else:
            try:
                value = self._get_parent_attribute(prop_name)
            except AttributeError:
                value = self._attributes[prop_name]
    except KeyError:
        raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, prop_name))

    if value is Sentinel:
        value = self._attr_defaults[prop_name]

    return value


def _generic_s(prop_name, self, value):
    self._attributes[prop_name] = value


def _generic_d(prop_name, self):
    del self._attributes[prop_name]


class BaseMeta(type):

    """
    Metaclass for the Base object, which is used to construct the class
    attributes based on the FieldAttributes available.
    """

    def __new__(cls, name, parents, dct):
        def _create_attrs(src_dict, dst_dict):
            '''
            Helper method which creates the attributes based on those in the
            source dictionary of attributes. This also populates the other
            attributes used to keep track of these attributes and via the
            getter/setter/deleter methods.
            '''
            keys = list(src_dict.keys())
            for attr_name in keys:
                value = src_dict[attr_name]
                if isinstance(value, Attribute):
                    if attr_name.startswith('_'):
                        attr_name = attr_name[1:]

                    # here we selectively assign the getter based on a few
                    # things, such as whether we have a _get_attr_<name>
                    # method, or if the attribute is marked as not inheriting
                    # its value from a parent object
                    method = "_get_attr_%s" % attr_name
                    if method in src_dict or method in dst_dict:
                        getter = partial(_generic_g_method, attr_name)
                    elif ('_get_parent_attribute' in dst_dict or '_get_parent_attribute' in src_dict) and value.inherit:
                        getter = partial(_generic_g_parent, attr_name)
                    else:
                        getter = partial(_generic_g, attr_name)

                    setter = partial(_generic_s, attr_name)
                    deleter = partial(_generic_d, attr_name)

                    dst_dict[attr_name] = property(getter, setter, deleter)
                    dst_dict['_valid_attrs'][attr_name] = value
                    dst_dict['_attributes'][attr_name] = Sentinel
                    dst_dict['_attr_defaults'][attr_name] = value.default

                    if value.alias is not None:
                        dst_dict[value.alias] = property(getter, setter, deleter)
                        dst_dict['_valid_attrs'][value.alias] = value
                        dst_dict['_alias_attrs'][value.alias] = attr_name

        def _process_parents(parents, dst_dict):
            '''
            Helper method which creates attributes from all parent objects
            recursively on through grandparent objects
            '''
            for parent in parents:
                if hasattr(parent, '__dict__'):
                    _create_attrs(parent.__dict__, dst_dict)
                    new_dst_dict = parent.__dict__.copy()
                    new_dst_dict.update(dst_dict)
                    _process_parents(parent.__bases__, new_dst_dict)

        # create some additional class attributes
        dct['_attributes'] = {}
        dct['_attr_defaults'] = {}
        dct['_valid_attrs'] = {}
        dct['_alias_attrs'] = {}

        # now create the attributes based on the FieldAttributes
        # available, including from parent (and grandparent) objects
        _create_attrs(dct, dct)
        _process_parents(parents, dct)

        return super(BaseMeta, cls).__new__(cls, name, parents, dct)


class FieldAttributeBase(with_metaclass(BaseMeta, object)):

    def __init__(self):

        # initialize the data loader and variable manager, which will be provided
        # later when the object is actually loaded
        self._loader = None
        self._variable_manager = None

        # other internal params
        self._validated = False
        self._squashed = False
        self._finalized = False

        # every object gets a random uuid:
        self._uuid = get_unique_id()

        # we create a copy of the attributes here due to the fact that
        # it was initialized as a class param in the meta class, so we
        # need a unique object here (all members contained within are
        # unique already).
        self._attributes = self.__class__._attributes.copy()
        self._attr_defaults = self.__class__._attr_defaults.copy()
        for key, value in self._attr_defaults.items():
            if callable(value):
                self._attr_defaults[key] = value()

        # and init vars, avoid using defaults in field declaration as it lives across plays
        self.vars = dict()

    def dump_me(self, depth=0):
        ''' this is never called from production code, it is here to be used when debugging as a 'complex print' '''
        if depth == 0:
            display.debug("DUMPING OBJECT ------------------------------------------------------")
        display.debug("%s- %s (%s, id=%s)" % (" " * depth, self.__class__.__name__, self, id(self)))
        if hasattr(self, '_parent') and self._parent:
            self._parent.dump_me(depth + 2)
            dep_chain = self._parent.get_dep_chain()
            if dep_chain:
                for dep in dep_chain:
                    dep.dump_me(depth + 2)
        if hasattr(self, '_play') and self._play:
            self._play.dump_me(depth + 2)

    def preprocess_data(self, ds):
        ''' infrequently used method to do some pre-processing of legacy terms '''

        for base_class in self.__class__.mro():
            method = getattr(self, "_preprocess_data_%s" % base_class.__name__.lower(), None)
            if method:
                return method(ds)
        return ds

    def load_data(self, ds, variable_manager=None, loader=None):
        ''' walk the input datastructure and assign any values '''

        if ds is None:
            raise AnsibleAssertionError('ds (%s) should not be None but it is.' % ds)

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
        for name, attr in sorted(iteritems(self._valid_attrs), key=operator.itemgetter(1)):
            # copy the value over unless a _load_field method is defined
            target_name = name
            if name in self._alias_attrs:
                target_name = self._alias_attrs[name]
            if name in ds:
                method = getattr(self, '_load_%s' % name, None)
                if method:
                    self._attributes[target_name] = method(name, ds[name])
                else:
                    self._attributes[target_name] = ds[name]

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

    def _validate_debugger(self, attr, name, value):
        valid_values = frozenset(('always', 'on_failed', 'on_unreachable', 'on_skipped', 'never'))
        if value and isinstance(value, string_types) and value not in valid_values:
            raise AnsibleParserError("'%s' is not a valid value for debugger. Must be one of %s" % (value, ', '.join(valid_values)), obj=self.get_ds())
        return value

    def _validate_attributes(self, ds):
        '''
        Ensures that there are no keys in the datastructure which do
        not map to attributes for this object.
        '''

        valid_attrs = frozenset(self._valid_attrs.keys())
        for key in ds:
            if key not in valid_attrs:
                raise AnsibleParserError("'%s' is not a valid attribute for a %s" % (key, self.__class__.__name__), obj=ds)

    def validate(self, all_vars=None):
        ''' validation that is done at parse time, not load time '''
        all_vars = {} if all_vars is None else all_vars

        if not self._validated:
            # walk all fields in the object
            for (name, attribute) in iteritems(self._valid_attrs):

                if name in self._alias_attrs:
                    name = self._alias_attrs[name]

                # run validator only if present
                method = getattr(self, '_validate_%s' % name, None)
                if method:
                    method(attribute, name, getattr(self, name))
                else:
                    # and make sure the attribute is of the type it should be
                    value = self._attributes[name]
                    if value is not None:
                        if attribute.isa == 'string' and isinstance(value, (list, dict)):
                            raise AnsibleParserError(
                                "The field '%s' is supposed to be a string type,"
                                " however the incoming data structure is a %s" % (name, type(value)), obj=self.get_ds()
                            )

        self._validated = True

    def squash(self):
        '''
        Evaluates all attributes and sets them to the evaluated version,
        so that all future accesses of attributes do not need to evaluate
        parent attributes.
        '''
        if not self._squashed:
            for name in self._valid_attrs.keys():
                self._attributes[name] = getattr(self, name)
            self._squashed = True

    def copy(self):
        '''
        Create a copy of this object and return it.
        '''

        new_me = self.__class__()

        for name in self._valid_attrs.keys():
            if name in self._alias_attrs:
                continue
            new_me._attributes[name] = shallowcopy(self._attributes[name])
            new_me._attr_defaults[name] = shallowcopy(self._attr_defaults[name])

        new_me._loader = self._loader
        new_me._variable_manager = self._variable_manager
        new_me._validated = self._validated
        new_me._finalized = self._finalized
        new_me._uuid = self._uuid

        # if the ds value was set on the object, copy it to the new copy too
        if hasattr(self, '_ds'):
            new_me._ds = self._ds

        return new_me

    def get_validated_value(self, name, attribute, value, templar):
        if attribute.isa == 'string':
            value = to_text(value)
        elif attribute.isa == 'int':
            value = int(value)
        elif attribute.isa == 'float':
            value = float(value)
        elif attribute.isa == 'bool':
            value = boolean(value, strict=False)
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
                value = [value]
            if attribute.listof is not None:
                for item in value:
                    if not isinstance(item, attribute.listof):
                        raise AnsibleParserError("the field '%s' should be a list of %s, "
                                                 "but the item '%s' is a %s" % (name, attribute.listof, item, type(item)), obj=self.get_ds())
                    elif attribute.required and attribute.listof == string_types:
                        if item is None or item.strip() == "":
                            raise AnsibleParserError("the field '%s' is required, and cannot have empty values" % (name,), obj=self.get_ds())
        elif attribute.isa == 'set':
            if value is None:
                value = set()
            elif not isinstance(value, (list, set)):
                if isinstance(value, string_types):
                    value = value.split(',')
                else:
                    # Making a list like this handles strings of
                    # text and bytes properly
                    value = [value]
            if not isinstance(value, set):
                value = set(value)
        elif attribute.isa == 'dict':
            if value is None:
                value = dict()
            elif not isinstance(value, dict):
                raise TypeError("%s is not a dictionary" % value)
        elif attribute.isa == 'class':
            if not isinstance(value, attribute.class_type):
                raise TypeError("%s is not a valid %s (got a %s instead)" % (name, attribute.class_type, type(value)))
            value.post_validate(templar=templar)
        return value

    def post_validate(self, templar):
        '''
        we can't tell that everything is of the right type until we have
        all the variables.  Run basic types (from isa) as well as
        any _post_validate_<foo> functions.
        '''

        # save the omit value for later checking
        omit_value = templar._available_variables.get('omit')

        for (name, attribute) in iteritems(self._valid_attrs):

            if attribute.static:
                value = getattr(self, name)

                # we don't template 'vars' but allow template as values for later use
                if name not in ('vars',) and templar.is_template(value):
                    display.warning('"%s" is not templatable, but we found: %s, '
                                    'it will not be templated and will be used "as is".' % (name, value))
                continue

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
                elif attribute.isa == 'class':
                    value = getattr(self, name)
                else:
                    # if the attribute contains a variable, template it now
                    value = templar.template(getattr(self, name))

                # if this evaluated to the omit value, set the value back to
                # the default specified in the FieldAttribute and move on
                if omit_value is not None and value == omit_value:
                    if callable(attribute.default):
                        setattr(self, name, attribute.default())
                    else:
                        setattr(self, name, attribute.default)
                    continue

                # and make sure the attribute is of the type it should be
                if value is not None:
                    value = self.get_validated_value(name, attribute, value, templar)

                # and assign the massaged value back to the attribute field
                setattr(self, name, value)
            except (TypeError, ValueError) as e:
                value = getattr(self, name)
                raise AnsibleParserError("the field '%s' has an invalid value (%s), and could not be converted to an %s."
                                         "The error was: %s" % (name, value, attribute.isa, e), obj=self.get_ds(), orig_exc=e)
            except (AnsibleUndefinedVariable, UndefinedError) as e:
                if templar._fail_on_undefined_errors and name != 'name':
                    if name == 'args':
                        msg = "The task includes an option with an undefined variable. The error was: %s" % (to_native(e))
                    else:
                        msg = "The field '%s' has an invalid value, which includes an undefined variable. The error was: %s" % (name, to_native(e))
                    raise AnsibleParserError(msg, obj=self.get_ds(), orig_exc=e)

        self._finalized = True

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
                return combine_vars(self.vars, ds)
            elif isinstance(ds, list):
                all_vars = self.vars
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
        except ValueError as e:
            raise AnsibleParserError("Vars in a %s must be specified as a dictionary, or a list of dictionaries" % self.__class__.__name__,
                                     obj=ds, orig_exc=e)
        except TypeError as e:
            raise AnsibleParserError("Invalid variable name in vars specified for %s: %s" % (self.__class__.__name__, e), obj=ds, orig_exc=e)

    def _extend_value(self, value, new_value, prepend=False):
        '''
        Will extend the value given with new_value (and will turn both
        into lists if they are not so already). The values are run through
        a set to remove duplicate values.
        '''

        if not isinstance(value, list):
            value = [value]
        if not isinstance(new_value, list):
            new_value = [new_value]

        # Due to where _extend_value may run for some attributes
        # it is possible to end up with Sentinel in the list of values
        # ensure we strip them
        value[:] = [v for v in value if v is not Sentinel]
        new_value[:] = [v for v in new_value if v is not Sentinel]

        if prepend:
            combined = new_value + value
        else:
            combined = value + new_value

        return [i for i, _ in itertools.groupby(combined) if i is not None]

    def dump_attrs(self):
        '''
        Dumps all attributes to a dictionary
        '''
        attrs = {}
        for (name, attribute) in iteritems(self._valid_attrs):
            attr = getattr(self, name)
            if attribute.isa == 'class' and hasattr(attr, 'serialize'):
                attrs[name] = attr.serialize()
            else:
                attrs[name] = attr
        return attrs

    def from_attrs(self, attrs):
        '''
        Loads attributes from a dictionary
        '''
        for (attr, value) in iteritems(attrs):
            if attr in self._valid_attrs:
                attribute = self._valid_attrs[attr]
                if attribute.isa == 'class' and isinstance(value, dict):
                    obj = attribute.class_type()
                    obj.deserialize(value)
                    setattr(self, attr, obj)
                else:
                    setattr(self, attr, value)

    def serialize(self):
        '''
        Serializes the object derived from the base object into
        a dictionary of values. This only serializes the field
        attributes for the object, so this may need to be overridden
        for any classes which wish to add additional items not stored
        as field attributes.
        '''

        repr = self.dump_attrs()

        # serialize the uuid field
        repr['uuid'] = self._uuid
        repr['finalized'] = self._finalized
        repr['squashed'] = self._squashed

        return repr

    def deserialize(self, data):
        '''
        Given a dictionary of values, load up the field attributes for
        this object. As with serialize(), if there are any non-field
        attribute data members, this method will need to be overridden
        and extended.
        '''

        if not isinstance(data, dict):
            raise AnsibleAssertionError('data (%s) should be a dict but is a %s' % (data, type(data)))

        for (name, attribute) in iteritems(self._valid_attrs):
            if name in data:
                setattr(self, name, data[name])
            else:
                if callable(attribute.default):
                    setattr(self, name, attribute.default())
                else:
                    setattr(self, name, attribute.default)

        # restore the UUID field
        setattr(self, '_uuid', data.get('uuid'))
        self._finalized = data.get('finalized', False)
        self._squashed = data.get('squashed', False)


class Base(FieldAttributeBase):

    _name = FieldAttribute(isa='string', default='', always_post_validate=True, inherit=False)

    # connection/transport
    _connection = FieldAttribute(isa='string', default=context.cliargs_deferred_get('connection'))
    _port = FieldAttribute(isa='int')
    _remote_user = FieldAttribute(isa='string', default=context.cliargs_deferred_get('remote_user'))

    # variables
    _vars = FieldAttribute(isa='dict', priority=100, inherit=False, static=True)

    # module default params
    _module_defaults = FieldAttribute(isa='list', extend=True, prepend=True)

    # flags and misc. settings
    _environment = FieldAttribute(isa='list', extend=True, prepend=True)
    _no_log = FieldAttribute(isa='bool')
    _run_once = FieldAttribute(isa='bool')
    _ignore_errors = FieldAttribute(isa='bool')
    _ignore_unreachable = FieldAttribute(isa='bool')
    _check_mode = FieldAttribute(isa='bool', default=context.cliargs_deferred_get('check'))
    _diff = FieldAttribute(isa='bool', default=context.cliargs_deferred_get('diff'))
    _any_errors_fatal = FieldAttribute(isa='bool', default=C.ANY_ERRORS_FATAL)

    # explicitly invoke a debugger on tasks
    _debugger = FieldAttribute(isa='string')

    # param names which have been deprecated/removed
    DEPRECATED_ATTRIBUTES = [
        'sudo', 'sudo_user', 'sudo_pass', 'sudo_exe', 'sudo_flags',
        'su', 'su_user', 'su_pass', 'su_exe', 'su_flags',
    ]
