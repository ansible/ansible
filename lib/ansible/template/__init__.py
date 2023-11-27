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

import ast
import datetime
import os
import pwd
import re
import time

from collections.abc import Iterator, Sequence, Mapping, MappingView, MutableMapping
from contextlib import contextmanager
from numbers import Number
from traceback import format_exc

from jinja2.exceptions import TemplateSyntaxError, UndefinedError, SecurityError
from jinja2.loaders import FileSystemLoader
from jinja2.nativetypes import NativeEnvironment
from jinja2.runtime import Context, StrictUndefined

from ansible import constants as C
from ansible.errors import (
    AnsibleAssertionError,
    AnsibleError,
    AnsibleFilterError,
    AnsibleLookupError,
    AnsibleOptionsError,
    AnsibleUndefinedVariable,
)
from ansible.module_utils.six import string_types, text_type
from ansible.module_utils._text import to_native, to_text, to_bytes
from ansible.module_utils.common.collections import is_sequence
from ansible.plugins.loader import filter_loader, lookup_loader, test_loader
from ansible.template.native_helpers import ansible_native_concat, ansible_eval_concat, ansible_concat
from ansible.template.template import AnsibleJ2Template
from ansible.template.vars import AnsibleJ2Vars
from ansible.utils.display import Display
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.utils.native_jinja import NativeJinjaText
from ansible.utils.unsafe_proxy import wrap_var, AnsibleUnsafeText, AnsibleUnsafeBytes, NativeJinjaUnsafeText

display = Display()


__all__ = ['Templar', 'generate_ansible_template_vars']

# Primitive Types which we don't want Jinja to convert to strings.
NON_TEMPLATED_TYPES = (bool, Number)

JINJA2_OVERRIDE = '#jinja2:'

JINJA2_BEGIN_TOKENS = frozenset(('variable_begin', 'block_begin', 'comment_begin', 'raw_begin'))
JINJA2_END_TOKENS = frozenset(('variable_end', 'block_end', 'comment_end', 'raw_end'))

RANGE_TYPE = type(range(0))


def generate_ansible_template_vars(path, fullpath=None, dest_path=None):

    if fullpath is None:
        b_path = to_bytes(path)
    else:
        b_path = to_bytes(fullpath)

    try:
        template_uid = pwd.getpwuid(os.stat(b_path).st_uid).pw_name
    except (KeyError, TypeError):
        template_uid = os.stat(b_path).st_uid

    temp_vars = {
        'template_host': to_text(os.uname()[1]),
        'template_path': path,
        'template_mtime': datetime.datetime.fromtimestamp(os.path.getmtime(b_path)),
        'template_uid': to_text(template_uid),
        'template_run_date': datetime.datetime.now(),
        'template_destpath': to_native(dest_path) if dest_path else None,
    }

    if fullpath is None:
        temp_vars['template_fullpath'] = os.path.abspath(path)
    else:
        temp_vars['template_fullpath'] = fullpath

    managed_default = C.DEFAULT_MANAGED_STR
    managed_str = managed_default.format(
        host=temp_vars['template_host'],
        uid=temp_vars['template_uid'],
        file=temp_vars['template_path'],
    )
    temp_vars['ansible_managed'] = to_text(time.strftime(to_native(managed_str), time.localtime(os.path.getmtime(b_path))))

    return temp_vars


def _escape_backslashes(data, jinja_env):
    """Double backslashes within jinja2 expressions

    A user may enter something like this in a playbook::

      debug:
        msg: "Test Case 1\\3; {{ test1_name | regex_replace('^(.*)_name$', '\\1')}}"

    The string inside of the {{ gets interpreted multiple times First by yaml.
    Then by python.  And finally by jinja2 as part of it's variable.  Because
    it is processed by both python and jinja2, the backslash escaped
    characters get unescaped twice.  This means that we'd normally have to use
    four backslashes to escape that.  This is painful for playbook authors as
    they have to remember different rules for inside vs outside of a jinja2
    expression (The backslashes outside of the "{{ }}" only get processed by
    yaml and python.  So they only need to be escaped once).  The following
    code fixes this by automatically performing the extra quoting of
    backslashes inside of a jinja2 expression.

    """
    if '\\' in data and '{{' in data:
        new_data = []
        d2 = jinja_env.preprocess(data)
        in_var = False

        for token in jinja_env.lex(d2):
            if token[1] == 'variable_begin':
                in_var = True
                new_data.append(token[2])
            elif token[1] == 'variable_end':
                in_var = False
                new_data.append(token[2])
            elif in_var and token[1] == 'string':
                # Double backslashes only if we're inside of a jinja2 variable
                new_data.append(token[2].replace('\\', '\\\\'))
            else:
                new_data.append(token[2])

        data = ''.join(new_data)

    return data


def is_possibly_template(data, jinja_env):
    """Determines if a string looks like a template, by seeing if it
    contains a jinja2 start delimiter. Does not guarantee that the string
    is actually a template.

    This is different than ``is_template`` which is more strict.
    This method may return ``True`` on a string that is not templatable.

    Useful when guarding passing a string for templating, but when
    you want to allow the templating engine to make the final
    assessment which may result in ``TemplateSyntaxError``.
    """
    if isinstance(data, string_types):
        for marker in (jinja_env.block_start_string, jinja_env.variable_start_string, jinja_env.comment_start_string):
            if marker in data:
                return True
    return False


def is_template(data, jinja_env):
    """This function attempts to quickly detect whether a value is a jinja2
    template. To do so, we look for the first 2 matching jinja2 tokens for
    start and end delimiters.
    """
    found = None
    start = True
    comment = False
    d2 = jinja_env.preprocess(data)

    # Quick check to see if this is remotely like a template before doing
    # more expensive investigation.
    if not is_possibly_template(d2, jinja_env):
        return False

    # This wraps a lot of code, but this is due to lex returning a generator
    # so we may get an exception at any part of the loop
    try:
        for token in jinja_env.lex(d2):
            if token[1] in JINJA2_BEGIN_TOKENS:
                if start and token[1] == 'comment_begin':
                    # Comments can wrap other token types
                    comment = True
                start = False
                # Example: variable_end -> variable
                found = token[1].split('_')[0]
            elif token[1] in JINJA2_END_TOKENS:
                if token[1].split('_')[0] == found:
                    return True
                elif comment:
                    continue
                return False
    except TemplateSyntaxError:
        return False

    return False


def _count_newlines_from_end(in_str):
    '''
    Counts the number of newlines at the end of a string. This is used during
    the jinja2 templating to ensure the count matches the input, since some newlines
    may be thrown away during the templating.
    '''

    try:
        i = len(in_str)
        j = i - 1
        while in_str[j] == '\n':
            j -= 1
        return i - 1 - j
    except IndexError:
        # Uncommon cases: zero length string and string containing only newlines
        return i


def recursive_check_defined(item):
    from jinja2.runtime import Undefined

    if isinstance(item, MutableMapping):
        for key in item:
            recursive_check_defined(item[key])
    elif isinstance(item, list):
        for i in item:
            recursive_check_defined(i)
    else:
        if isinstance(item, Undefined):
            raise AnsibleFilterError("{0} is undefined".format(item))


def _is_rolled(value):
    """Helper method to determine if something is an unrolled generator,
    iterator, or similar object
    """
    return (
        isinstance(value, Iterator) or
        isinstance(value, MappingView) or
        isinstance(value, RANGE_TYPE)
    )


def _unroll_iterator(func):
    """Wrapper function, that intercepts the result of a templating
    and auto unrolls a generator, so that users are not required to
    explicitly use ``|list`` to unroll.
    """
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        if _is_rolled(ret):
            return list(ret)
        return ret

    return _update_wrapper(wrapper, func)


def _update_wrapper(wrapper, func):
    # This code is duplicated from ``functools.update_wrapper`` from Py3.7.
    # ``functools.update_wrapper`` was failing when the func was ``functools.partial``
    for attr in ('__module__', '__name__', '__qualname__', '__doc__', '__annotations__'):
        try:
            value = getattr(func, attr)
        except AttributeError:
            pass
        else:
            setattr(wrapper, attr, value)
    for attr in ('__dict__',):
        getattr(wrapper, attr).update(getattr(func, attr, {}))
    wrapper.__wrapped__ = func
    return wrapper


def _wrap_native_text(func):
    """Wrapper function, that intercepts the result of a filter
    and wraps it into NativeJinjaText which is then used
    in ``ansible_native_concat`` to indicate that it is a text
    which should not be passed into ``literal_eval``.
    """
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        return NativeJinjaText(ret)

    return _update_wrapper(wrapper, func)


class AnsibleUndefined(StrictUndefined):
    '''
    A custom Undefined class, which returns further Undefined objects on access,
    rather than throwing an exception.
    '''
    def __getattr__(self, name):
        if name == '__UNSAFE__':
            # AnsibleUndefined should never be assumed to be unsafe
            # This prevents ``hasattr(val, '__UNSAFE__')`` from evaluating to ``True``
            raise AttributeError(name)
        # Return original Undefined object to preserve the first failure context
        return self

    def __getitem__(self, key):
        # Return original Undefined object to preserve the first failure context
        return self

    def __repr__(self):
        return 'AnsibleUndefined(hint={0!r}, obj={1!r}, name={2!r})'.format(
            self._undefined_hint,
            self._undefined_obj,
            self._undefined_name
        )

    def __contains__(self, item):
        # Return original Undefined object to preserve the first failure context
        return self


class AnsibleContext(Context):
    '''
    A custom context, which intercepts resolve_or_missing() calls and sets a flag
    internally if any variable lookup returns an AnsibleUnsafe value. This
    flag is checked post-templating, and (when set) will result in the
    final templated result being wrapped in AnsibleUnsafe.
    '''
    _disallowed_callables = frozenset({
        AnsibleUnsafeText._strip_unsafe.__qualname__,
        AnsibleUnsafeBytes._strip_unsafe.__qualname__,
        NativeJinjaUnsafeText._strip_unsafe.__qualname__,
    })

    def __init__(self, *args, **kwargs):
        super(AnsibleContext, self).__init__(*args, **kwargs)
        self.unsafe = False

    def call(self, obj, *args, **kwargs):
        if getattr(obj, '__qualname__', None) in self._disallowed_callables or obj in self._disallowed_callables:
            raise SecurityError(f"{obj!r} is not safely callable")
        return super().call(obj, *args, **kwargs)

    def _is_unsafe(self, val):
        '''
        Our helper function, which will also recursively check dict and
        list entries due to the fact that they may be repr'd and contain
        a key or value which contains jinja2 syntax and would otherwise
        lose the AnsibleUnsafe value.
        '''
        if isinstance(val, dict):
            for key in val.keys():
                if self._is_unsafe(val[key]):
                    return True
        elif isinstance(val, list):
            for item in val:
                if self._is_unsafe(item):
                    return True
        elif getattr(val, '__UNSAFE__', False) is True:
            return True
        return False

    def _update_unsafe(self, val):
        if val is not None and not self.unsafe and self._is_unsafe(val):
            self.unsafe = True

    def resolve_or_missing(self, key):
        val = super(AnsibleContext, self).resolve_or_missing(key)
        self._update_unsafe(val)
        return val

    def get_all(self):
        """Return the complete context as a dict including the exported
        variables. For optimizations reasons this might not return an
        actual copy so be careful with using it.

        This is to prevent from running ``AnsibleJ2Vars`` through dict():

            ``dict(self.parent, **self.vars)``

        In Ansible this means that ALL variables would be templated in the
        process of re-creating the parent because ``AnsibleJ2Vars`` templates
        each variable in its ``__getitem__`` method. Instead we re-create the
        parent via ``AnsibleJ2Vars.add_locals`` that creates a new
        ``AnsibleJ2Vars`` copy without templating each variable.

        This will prevent unnecessarily templating unused variables in cases
        like setting a local variable and passing it to {% include %}
        in a template.

        Also see ``AnsibleJ2Template``and
        https://github.com/pallets/jinja/commit/d67f0fd4cc2a4af08f51f4466150d49da7798729
        """
        if not self.vars:
            return self.parent
        if not self.parent:
            return self.vars

        if isinstance(self.parent, AnsibleJ2Vars):
            return self.parent.add_locals(self.vars)
        else:
            # can this happen in Ansible?
            return dict(self.parent, **self.vars)


class JinjaPluginIntercept(MutableMapping):
    ''' Simulated dict class that loads Jinja2Plugins at request
        otherwise all plugins would need to be loaded a priori.

        NOTE: plugin_loader still loads all 'builtin/legacy' at
        start so only collection plugins are really at request.
    '''

    def __init__(self, delegatee, pluginloader, *args, **kwargs):

        super(JinjaPluginIntercept, self).__init__(*args, **kwargs)

        self._pluginloader = pluginloader

        # Jinja environment's mapping of known names (initially just J2 builtins)
        self._delegatee = delegatee

        # our names take precedence over Jinja's, but let things we've tried to resolve skip the pluginloader
        self._seen_it = set()

    def __getitem__(self, key):

        if not isinstance(key, string_types):
            raise ValueError('key must be a string, got %s instead' % type(key))

        original_exc = None
        if key not in self._seen_it:
            # this looks too early to set this- it isn't. Setting it here keeps requests for Jinja builtins from
            # going through the pluginloader more than once, which is extremely slow for something that won't ever succeed.
            self._seen_it.add(key)
            plugin = None
            try:
                plugin = self._pluginloader.get(key)
            except (AnsibleError, KeyError) as e:
                original_exc = e
            except Exception as e:
                display.vvvv('Unexpected plugin load (%s) exception: %s' % (key, to_native(e)))
                raise e

            # if a plugin was found/loaded
            if plugin:
                # set in filter cache and avoid expensive plugin load
                self._delegatee[key] = plugin.j2_function

        # raise template syntax error if we could not find ours or jinja2 one
        try:
            func = self._delegatee[key]
        except KeyError as e:
            self._seen_it.remove(key)
            raise TemplateSyntaxError('Could not load "%s": %s' % (key, to_native(original_exc or e)), 0)

        # if i do have func and it is a filter, it nees wrapping
        if self._pluginloader.type == 'filter':
            # filter need wrapping
            if key in C.STRING_TYPE_FILTERS:
                # avoid litera_eval when you WANT strings
                func = _wrap_native_text(func)
            else:
                # conditionally unroll iterators/generators to avoid having to use `|list` after every filter
                func = _unroll_iterator(func)

        return func

    def __setitem__(self, key, value):
        return self._delegatee.__setitem__(key, value)

    def __delitem__(self, key):
        raise NotImplementedError()

    def __iter__(self):
        # not strictly accurate since we're not counting dynamically-loaded values
        return iter(self._delegatee)

    def __len__(self):
        # not strictly accurate since we're not counting dynamically-loaded values
        return len(self._delegatee)


def _fail_on_undefined(data):
    """Recursively find an undefined value in a nested data structure
    and properly raise the undefined exception.
    """
    if isinstance(data, Mapping):
        for value in data.values():
            _fail_on_undefined(value)
    elif is_sequence(data):
        for item in data:
            _fail_on_undefined(item)
    else:
        if isinstance(data, StrictUndefined):
            # To actually raise the undefined exception we need to
            # access the undefined object otherwise the exception would
            # be raised on the next access which might not be properly
            # handled.
            # See https://github.com/ansible/ansible/issues/52158
            # and StrictUndefined implementation in upstream Jinja2.
            str(data)
    return data


@_unroll_iterator
def _ansible_finalize(thing):
    """A custom finalize function for jinja2, which prevents None from being
    returned. This avoids a string of ``"None"`` as ``None`` has no
    importance in YAML.

    The function is decorated with ``_unroll_iterator`` so that users are not
    required to explicitly use ``|list`` to unroll a generator. This only
    affects the scenario where the final result of templating
    is a generator, e.g. ``range``, ``dict.items()`` and so on. Filters
    which can produce a generator in the middle of a template are already
    wrapped with ``_unroll_generator`` in ``JinjaPluginIntercept``.
    """
    return thing if _fail_on_undefined(thing) is not None else ''


class AnsibleEnvironment(NativeEnvironment):
    '''
    Our custom environment, which simply allows us to override the class-level
    values for the Template and Context classes used by jinja2 internally.
    '''
    context_class = AnsibleContext
    template_class = AnsibleJ2Template
    concat = staticmethod(ansible_eval_concat)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters = JinjaPluginIntercept(self.filters, filter_loader)
        self.tests = JinjaPluginIntercept(self.tests, test_loader)

        self.trim_blocks = True

        self.undefined = AnsibleUndefined
        self.finalize = _ansible_finalize


class AnsibleNativeEnvironment(AnsibleEnvironment):
    concat = staticmethod(ansible_native_concat)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.finalize = _unroll_iterator(_fail_on_undefined)


class Templar:
    '''
    The main class for templating, with the main entry-point of template().
    '''

    def __init__(self, loader, shared_loader_obj=None, variables=None):
        if shared_loader_obj is not None:
            display.deprecated(
                "The `shared_loader_obj` option to `Templar` is no longer functional, "
                "ansible.plugins.loader is used directly instead.",
                version='2.16',
            )

        self._loader = loader
        self._available_variables = {} if variables is None else variables

        self._fail_on_undefined_errors = C.DEFAULT_UNDEFINED_VAR_BEHAVIOR

        environment_class = AnsibleNativeEnvironment if C.DEFAULT_JINJA2_NATIVE else AnsibleEnvironment

        self.environment = environment_class(
            extensions=self._get_extensions(),
            loader=FileSystemLoader(loader.get_basedir() if loader else '.'),
        )
        self.environment.template_class.environment_class = environment_class

        # jinja2 global is inconsistent across versions, this normalizes them
        self.environment.globals['dict'] = dict

        # Custom globals
        self.environment.globals['lookup'] = self._lookup
        self.environment.globals['query'] = self.environment.globals['q'] = self._query_lookup
        self.environment.globals['now'] = self._now_datetime
        self.environment.globals['undef'] = self._make_undefined

        # the current rendering context under which the templar class is working
        self.cur_context = None

        # FIXME this regex should be re-compiled each time variable_start_string and variable_end_string are changed
        self.SINGLE_VAR = re.compile(r"^%s\s*(\w*)\s*%s$" % (self.environment.variable_start_string, self.environment.variable_end_string))

        self.jinja2_native = C.DEFAULT_JINJA2_NATIVE

    def copy_with_new_env(self, environment_class=AnsibleEnvironment, **kwargs):
        r"""Creates a new copy of Templar with a new environment.

        :kwarg environment_class: Environment class used for creating a new environment.
        :kwarg \*\*kwargs: Optional arguments for the new environment that override existing
            environment attributes.

        :returns: Copy of Templar with updated environment.
        """
        # We need to use __new__ to skip __init__, mainly not to create a new
        # environment there only to override it below
        new_env = object.__new__(environment_class)
        new_env.__dict__.update(self.environment.__dict__)

        new_templar = object.__new__(Templar)
        new_templar.__dict__.update(self.__dict__)
        new_templar.environment = new_env

        new_templar.jinja2_native = environment_class is AnsibleNativeEnvironment

        mapping = {
            'available_variables': new_templar,
            'searchpath': new_env.loader,
        }

        for key, value in kwargs.items():
            obj = mapping.get(key, new_env)
            try:
                if value is not None:
                    setattr(obj, key, value)
            except AttributeError:
                # Ignore invalid attrs
                pass

        return new_templar

    def _get_extensions(self):
        '''
        Return jinja2 extensions to load.

        If some extensions are set via jinja_extensions in ansible.cfg, we try
        to load them with the jinja environment.
        '''

        jinja_exts = []
        if C.DEFAULT_JINJA2_EXTENSIONS:
            # make sure the configuration directive doesn't contain spaces
            # and split extensions in an array
            jinja_exts = C.DEFAULT_JINJA2_EXTENSIONS.replace(" ", "").split(',')

        return jinja_exts

    @property
    def available_variables(self):
        return self._available_variables

    @available_variables.setter
    def available_variables(self, variables):
        '''
        Sets the list of template variables this Templar instance will use
        to template things, so we don't have to pass them around between
        internal methods. We also clear the template cache here, as the variables
        are being changed.
        '''

        if not isinstance(variables, Mapping):
            raise AnsibleAssertionError("the type of 'variables' should be a Mapping but was a %s" % (type(variables)))
        self._available_variables = variables

    @contextmanager
    def set_temporary_context(self, **kwargs):
        """Context manager used to set temporary templating context, without having to worry about resetting
        original values afterward

        Use a keyword that maps to the attr you are setting. Applies to ``self.environment`` by default, to
        set context on another object, it must be in ``mapping``.
        """
        mapping = {
            'available_variables': self,
            'searchpath': self.environment.loader,
        }
        original = {}

        for key, value in kwargs.items():
            obj = mapping.get(key, self.environment)
            try:
                original[key] = getattr(obj, key)
                if value is not None:
                    setattr(obj, key, value)
            except AttributeError:
                # Ignore invalid attrs
                pass

        yield

        for key in original:
            obj = mapping.get(key, self.environment)
            setattr(obj, key, original[key])

    def template(self, variable, convert_bare=False, preserve_trailing_newlines=True, escape_backslashes=True, fail_on_undefined=None, overrides=None,
                 convert_data=True, static_vars=None, cache=None, disable_lookups=False):
        '''
        Templates (possibly recursively) any given data as input. If convert_bare is
        set to True, the given data will be wrapped as a jinja2 variable ('{{foo}}')
        before being sent through the template engine.
        '''
        static_vars = [] if static_vars is None else static_vars

        if cache is not None:
            display.deprecated("The `cache` option to `Templar.template` is no longer functional, and will be removed in a future release.", version='2.18')

        # Don't template unsafe variables, just return them.
        if hasattr(variable, '__UNSAFE__'):
            return variable

        if fail_on_undefined is None:
            fail_on_undefined = self._fail_on_undefined_errors

        if convert_bare:
            variable = self._convert_bare_variable(variable)

        if isinstance(variable, string_types):
            if not self.is_possibly_template(variable):
                return variable

            # Check to see if the string we are trying to render is just referencing a single
            # var.  In this case we don't want to accidentally change the type of the variable
            # to a string by using the jinja template renderer. We just want to pass it.
            only_one = self.SINGLE_VAR.match(variable)
            if only_one:
                var_name = only_one.group(1)
                if var_name in self._available_variables:
                    resolved_val = self._available_variables[var_name]
                    if isinstance(resolved_val, NON_TEMPLATED_TYPES):
                        return resolved_val
                    elif resolved_val is None:
                        return C.DEFAULT_NULL_REPRESENTATION

            result = self.do_template(
                variable,
                preserve_trailing_newlines=preserve_trailing_newlines,
                escape_backslashes=escape_backslashes,
                fail_on_undefined=fail_on_undefined,
                overrides=overrides,
                disable_lookups=disable_lookups,
                convert_data=convert_data,
            )

            return result

        elif is_sequence(variable):
            return [self.template(
                v,
                preserve_trailing_newlines=preserve_trailing_newlines,
                fail_on_undefined=fail_on_undefined,
                overrides=overrides,
                disable_lookups=disable_lookups,
            ) for v in variable]
        elif isinstance(variable, Mapping):
            d = {}
            # we don't use iteritems() here to avoid problems if the underlying dict
            # changes sizes due to the templating, which can happen with hostvars
            for k in variable.keys():
                if k not in static_vars:
                    d[k] = self.template(
                        variable[k],
                        preserve_trailing_newlines=preserve_trailing_newlines,
                        fail_on_undefined=fail_on_undefined,
                        overrides=overrides,
                        disable_lookups=disable_lookups,
                    )
                else:
                    d[k] = variable[k]
            return d
        else:
            return variable

    def is_template(self, data):
        '''lets us know if data has a template'''
        if isinstance(data, string_types):
            return is_template(data, self.environment)
        elif isinstance(data, (list, tuple)):
            for v in data:
                if self.is_template(v):
                    return True
        elif isinstance(data, dict):
            for k in data:
                if self.is_template(k) or self.is_template(data[k]):
                    return True
        return False

    templatable = is_template

    def is_possibly_template(self, data):
        return is_possibly_template(data, self.environment)

    def _convert_bare_variable(self, variable):
        '''
        Wraps a bare string, which may have an attribute portion (ie. foo.bar)
        in jinja2 variable braces so that it is evaluated properly.
        '''

        if isinstance(variable, string_types):
            contains_filters = "|" in variable
            first_part = variable.split("|")[0].split(".")[0].split("[")[0]
            if (contains_filters or first_part in self._available_variables) and self.environment.variable_start_string not in variable:
                return "%s%s%s" % (self.environment.variable_start_string, variable, self.environment.variable_end_string)

        # the variable didn't meet the conditions to be converted,
        # so just return it as-is
        return variable

    def _fail_lookup(self, name, *args, **kwargs):
        raise AnsibleError("The lookup `%s` was found, however lookups were disabled from templating" % name)

    def _now_datetime(self, utc=False, fmt=None):
        '''jinja2 global function to return current datetime, potentially formatted via strftime'''
        if utc:
            now = datetime.datetime.utcnow()
        else:
            now = datetime.datetime.now()

        if fmt:
            return now.strftime(fmt)

        return now

    def _query_lookup(self, name, *args, **kwargs):
        ''' wrapper for lookup, force wantlist true'''
        kwargs['wantlist'] = True
        return self._lookup(name, *args, **kwargs)

    def _lookup(self, name, *args, **kwargs):
        instance = lookup_loader.get(name, loader=self._loader, templar=self)

        if instance is None:
            raise AnsibleError("lookup plugin (%s) not found" % name)

        wantlist = kwargs.pop('wantlist', False)
        allow_unsafe = kwargs.pop('allow_unsafe', C.DEFAULT_ALLOW_UNSAFE_LOOKUPS)
        errors = kwargs.pop('errors', 'strict')

        loop_terms = listify_lookup_plugin_terms(terms=args, templar=self, fail_on_undefined=True, convert_bare=False)
        # safely catch run failures per #5059
        try:
            ran = instance.run(loop_terms, variables=self._available_variables, **kwargs)
        except (AnsibleUndefinedVariable, UndefinedError) as e:
            raise AnsibleUndefinedVariable(e)
        except AnsibleOptionsError as e:
            # invalid options given to lookup, just reraise
            raise e
        except AnsibleLookupError as e:
            # lookup handled error but still decided to bail
            msg = 'Lookup failed but the error is being ignored: %s' % to_native(e)
            if errors == 'warn':
                display.warning(msg)
            elif errors == 'ignore':
                display.display(msg, log_only=True)
            else:
                raise e
            return [] if wantlist else None
        except Exception as e:
            # errors not handled by lookup
            msg = u"An unhandled exception occurred while running the lookup plugin '%s'. Error was a %s, original message: %s" % \
                  (name, type(e), to_text(e))
            if errors == 'warn':
                display.warning(msg)
            elif errors == 'ignore':
                display.display(msg, log_only=True)
            else:
                display.vvv('exception during Jinja2 execution: {0}'.format(format_exc()))
                raise AnsibleError(to_native(msg), orig_exc=e)
            return [] if wantlist else None

        if not is_sequence(ran):
            display.deprecated(
                f'The lookup plugin \'{name}\' was expected to return a list, got \'{type(ran)}\' instead. '
                f'The lookup plugin \'{name}\' needs to be changed to return a list. '
                'This will be an error in Ansible 2.18',
                version='2.18'
            )

        if ran and allow_unsafe is False:
            if self.cur_context:
                self.cur_context.unsafe = True

            if wantlist:
                return wrap_var(ran)

            try:
                if isinstance(ran[0], NativeJinjaText):
                    ran = wrap_var(NativeJinjaText(",".join(ran)))
                else:
                    ran = wrap_var(",".join(ran))
            except TypeError:
                # Lookup Plugins should always return lists.  Throw an error if that's not
                # the case:
                if not isinstance(ran, Sequence):
                    raise AnsibleError("The lookup plugin '%s' did not return a list."
                                       % name)

                # The TypeError we can recover from is when the value *inside* of the list
                # is not a string
                if len(ran) == 1:
                    ran = wrap_var(ran[0])
                else:
                    ran = wrap_var(ran)
            except KeyError:
                # Lookup Plugin returned a dict.  Return comma-separated string of keys
                # for backwards compat.
                # FIXME this can be removed when support for non-list return types is removed.
                # See https://github.com/ansible/ansible/pull/77789
                ran = wrap_var(",".join(ran))

        return ran

    def _make_undefined(self, hint=None):
        from jinja2.runtime import Undefined

        if hint is None or isinstance(hint, Undefined) or hint == '':
            hint = "Mandatory variable has not been overridden"
        return AnsibleUndefined(hint)

    def do_template(self, data, preserve_trailing_newlines=True, escape_backslashes=True, fail_on_undefined=None, overrides=None, disable_lookups=False,
                    convert_data=False):
        if self.jinja2_native and not isinstance(data, string_types):
            return data

        # For preserving the number of input newlines in the output (used
        # later in this method)
        data_newlines = _count_newlines_from_end(data)

        if fail_on_undefined is None:
            fail_on_undefined = self._fail_on_undefined_errors

        has_template_overrides = data.startswith(JINJA2_OVERRIDE)

        try:
            # NOTE Creating an overlay that lives only inside do_template means that overrides are not applied
            # when templating nested variables in AnsibleJ2Vars where Templar.environment is used, not the overlay.
            # This is historic behavior that is kept for backwards compatibility.
            if overrides:
                myenv = self.environment.overlay(overrides)
            elif has_template_overrides:
                myenv = self.environment.overlay()
            else:
                myenv = self.environment

            # Get jinja env overrides from template
            if has_template_overrides:
                eol = data.find('\n')
                line = data[len(JINJA2_OVERRIDE):eol]
                data = data[eol + 1:]
                for pair in line.split(','):
                    if ':' not in pair:
                        raise AnsibleError("failed to parse jinja2 override '%s'."
                                           " Did you use something different from colon as key-value separator?" % pair.strip())
                    (key, val) = pair.split(':', 1)
                    key = key.strip()
                    setattr(myenv, key, ast.literal_eval(val.strip()))

            if escape_backslashes:
                # Allow users to specify backslashes in playbooks as "\\" instead of as "\\\\".
                data = _escape_backslashes(data, myenv)

            try:
                t = myenv.from_string(data)
            except TemplateSyntaxError as e:
                raise AnsibleError("template error while templating string: %s. String: %s" % (to_native(e), to_native(data)), orig_exc=e)
            except Exception as e:
                if 'recursion' in to_native(e):
                    raise AnsibleError("recursive loop detected in template string: %s" % to_native(data), orig_exc=e)
                else:
                    return data

            if disable_lookups:
                t.globals['query'] = t.globals['q'] = t.globals['lookup'] = self._fail_lookup

            jvars = AnsibleJ2Vars(self, t.globals)

            # In case this is a recursive call to do_template we need to
            # save/restore cur_context to prevent overriding __UNSAFE__.
            cached_context = self.cur_context

            # In case this is a recursive call and we set different concat
            # function up the stack, reset it in case the value of convert_data
            # changed in this call
            myenv.concat = myenv.__class__.concat
            # the concat function is set for each Ansible environment,
            # however for convert_data=False we need to use the concat
            # function that avoids any evaluation and set it temporarily
            # on the environment so it is used correctly even when
            # the concat function is called internally in Jinja,
            # most notably for macro execution
            if not self.jinja2_native and not convert_data:
                myenv.concat = ansible_concat

            self.cur_context = t.new_context(jvars, shared=True)
            rf = t.root_render_func(self.cur_context)

            try:
                res = myenv.concat(rf)
                unsafe = getattr(self.cur_context, 'unsafe', False)
                if unsafe:
                    res = wrap_var(res)
            except TypeError as te:
                if 'AnsibleUndefined' in to_native(te):
                    errmsg = "Unable to look up a name or access an attribute in template string (%s).\n" % to_native(data)
                    errmsg += "Make sure your variable name does not contain invalid characters like '-': %s" % to_native(te)
                    raise AnsibleUndefinedVariable(errmsg, orig_exc=te)
                else:
                    display.debug("failing because of a type error, template data is: %s" % to_text(data))
                    raise AnsibleError("Unexpected templating type error occurred on (%s): %s" % (to_native(data), to_native(te)), orig_exc=te)
            finally:
                self.cur_context = cached_context

            if isinstance(res, string_types) and preserve_trailing_newlines:
                # The low level calls above do not preserve the newline
                # characters at the end of the input data, so we use the
                # calculate the difference in newlines and append them
                # to the resulting output for parity
                #
                # Using Environment's keep_trailing_newline instead would
                # result in change in behavior when trailing newlines
                # would be kept also for included templates, for example:
                # "Hello {% include 'world.txt' %}!" would render as
                # "Hello world\n!\n" instead of "Hello world!\n".
                res_newlines = _count_newlines_from_end(res)
                if data_newlines > res_newlines:
                    res += myenv.newline_sequence * (data_newlines - res_newlines)
                    if unsafe:
                        res = wrap_var(res)
            return res
        except (UndefinedError, AnsibleUndefinedVariable) as e:
            if fail_on_undefined:
                raise AnsibleUndefinedVariable(e, orig_exc=e)
            else:
                display.debug("Ignoring undefined failure: %s" % to_text(e))
                return data

    # for backwards compatibility in case anyone is using old private method directly
    _do_template = do_template
