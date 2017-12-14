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
import contextlib
import datetime
import os
import pwd
import re
import time

from functools import wraps
from io import StringIO
from numbers import Number

try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

from jinja2 import Environment
from jinja2.exceptions import TemplateSyntaxError, UndefinedError
from jinja2.loaders import FileSystemLoader
from jinja2.runtime import Context, StrictUndefined
from jinja2.utils import concat as j2_concat

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleFilterError, AnsibleUndefinedVariable, AnsibleAssertionError
from ansible.module_utils.six import string_types, text_type
from ansible.module_utils._text import to_native, to_text, to_bytes
from ansible.plugins.loader import filter_loader, lookup_loader, test_loader
from ansible.template.safe_eval import safe_eval
from ansible.template.template import AnsibleJ2Template
from ansible.template.vars import AnsibleJ2Vars
from ansible.utils.unsafe_proxy import UnsafeProxy, wrap_var

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ['Templar', 'generate_ansible_template_vars']

# A regex for checking to see if a variable we're trying to
# expand is just a single variable name.

# Primitive Types which we don't want Jinja to convert to strings.
NON_TEMPLATED_TYPES = (bool, Number)

JINJA2_OVERRIDE = '#jinja2:'


def generate_ansible_template_vars(path):

    b_path = to_bytes(path)
    try:
        template_uid = pwd.getpwuid(os.stat(b_path).st_uid).pw_name
    except:
        template_uid = os.stat(b_path).st_uid

    temp_vars = {}
    temp_vars['template_host'] = os.uname()[1]
    temp_vars['template_path'] = b_path
    temp_vars['template_mtime'] = datetime.datetime.fromtimestamp(os.path.getmtime(b_path))
    temp_vars['template_uid'] = template_uid
    temp_vars['template_fullpath'] = os.path.abspath(path)
    temp_vars['template_run_date'] = datetime.datetime.now()

    managed_default = C.DEFAULT_MANAGED_STR
    managed_str = managed_default.format(
        host=temp_vars['template_host'],
        uid=temp_vars['template_uid'],
        file=temp_vars['template_path'],
    )
    temp_vars['ansible_managed'] = time.strftime(managed_str, time.localtime(os.path.getmtime(b_path)))

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


def tests_as_filters_warning(name, func):
    '''
    Closure to enable displaying a deprecation warning when tests are used as a filter

    This closure is only used when registering ansible provided tests as filters

    This function should be removed in 2.9 along with registering ansible provided tests as filters
    in Templar._get_filters
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        display.deprecated(
            'Using tests as filters is deprecated. Instead of using `result|%(name)s` instead use '
            '`result is %(name)s`' % dict(name=name),
            version='2.9'
        )
        return func(*args, **kwargs)
    return wrapper


class AnsibleContext(Context):
    '''
    A custom context, which intercepts resolve() calls and sets a flag
    internally if any variable lookup returns an AnsibleUnsafe value. This
    flag is checked post-templating, and (when set) will result in the
    final templated result being wrapped via UnsafeProxy.
    '''
    def __init__(self, *args, **kwargs):
        super(AnsibleContext, self).__init__(*args, **kwargs)
        self.unsafe = False

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
        elif isinstance(val, string_types) and hasattr(val, '__UNSAFE__'):
            return True
        return False

    def _update_unsafe(self, val):
        if val is not None and not self.unsafe and self._is_unsafe(val):
            self.unsafe = True

    def resolve(self, key):
        '''
        The intercepted resolve(), which uses the helper above to set the
        internal flag whenever an unsafe variable value is returned.
        '''
        val = super(AnsibleContext, self).resolve(key)
        self._update_unsafe(val)
        return val

    def resolve_or_missing(self, key):
        val = super(AnsibleContext, self).resolve_or_missing(key)
        self._update_unsafe(val)
        return val


class AnsibleEnvironment(Environment):
    '''
    Our custom environment, which simply allows us to override the class-level
    values for the Template and Context classes used by jinja2 internally.
    '''
    context_class = AnsibleContext
    template_class = AnsibleJ2Template


class Templar:
    '''
    The main class for templating, with the main entry-point of template().
    '''

    def __init__(self, loader, shared_loader_obj=None, variables=None):
        variables = {} if variables is None else variables

        self._loader = loader
        self._filters = None
        self._tests = None
        self._available_variables = variables
        self._cached_result = {}

        if loader:
            self._basedir = loader.get_basedir()
        else:
            self._basedir = './'

        if shared_loader_obj:
            self._filter_loader = getattr(shared_loader_obj, 'filter_loader')
            self._test_loader = getattr(shared_loader_obj, 'test_loader')
            self._lookup_loader = getattr(shared_loader_obj, 'lookup_loader')
        else:
            self._filter_loader = filter_loader
            self._test_loader = test_loader
            self._lookup_loader = lookup_loader

        # flags to determine whether certain failures during templating
        # should result in fatal errors being raised
        self._fail_on_lookup_errors = True
        self._fail_on_filter_errors = True
        self._fail_on_undefined_errors = C.DEFAULT_UNDEFINED_VAR_BEHAVIOR

        self.environment = AnsibleEnvironment(
            trim_blocks=True,
            undefined=StrictUndefined,
            extensions=self._get_extensions(),
            finalize=self._finalize,
            loader=FileSystemLoader(self._basedir),
        )

        # the current rendering context under which the templar class is working
        self.cur_context = None

        self.SINGLE_VAR = re.compile(r"^%s\s*(\w*)\s*%s$" % (self.environment.variable_start_string, self.environment.variable_end_string))

        self._clean_regex = re.compile(r'(?:%s|%s|%s|%s)' % (
            self.environment.variable_start_string,
            self.environment.block_start_string,
            self.environment.block_end_string,
            self.environment.variable_end_string
        ))
        self._no_type_regex = re.compile(r'.*\|\s*(?:%s)\s*(?:%s)?$' % ('|'.join(C.STRING_TYPE_FILTERS), self.environment.variable_end_string))

    def _get_filters(self):
        '''
        Returns filter plugins, after loading and caching them if need be
        '''

        if self._filters is not None:
            return self._filters.copy()

        plugins = [x for x in self._filter_loader.all()]

        self._filters = dict()
        for fp in plugins:
            self._filters.update(fp.filters())

        # TODO: Remove registering tests as filters in 2.9
        for name, func in self._get_tests().items():
            self._filters[name] = tests_as_filters_warning(name, func)

        return self._filters.copy()

    def _get_tests(self):
        '''
        Returns tests plugins, after loading and caching them if need be
        '''

        if self._tests is not None:
            return self._tests.copy()

        plugins = [x for x in self._test_loader.all()]

        self._tests = dict()
        for fp in plugins:
            self._tests.update(fp.tests())

        return self._tests.copy()

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

    def _clean_data(self, orig_data):
        ''' remove jinja2 template tags from data '''

        if hasattr(orig_data, '__ENCRYPTED__'):
            ret = orig_data

        elif isinstance(orig_data, list):
            clean_list = []
            for list_item in orig_data:
                clean_list.append(self._clean_data(list_item))
            ret = clean_list

        elif isinstance(orig_data, dict):
            clean_dict = {}
            for k in orig_data:
                clean_dict[self._clean_data(k)] = self._clean_data(orig_data[k])
            ret = clean_dict

        elif isinstance(orig_data, string_types):
            # This will error with str data (needs unicode), but all strings should already be converted already.
            # If you get exception, the problem is at the data origin, do not add to_text here.
            with contextlib.closing(StringIO(orig_data)) as data:
                # these variables keep track of opening block locations, as we only
                # want to replace matched pairs of print/block tags
                print_openings = []
                block_openings = []
                for mo in self._clean_regex.finditer(orig_data):
                    token = mo.group(0)
                    token_start = mo.start(0)

                    if token[0] == self.environment.variable_start_string[0]:
                        if token == self.environment.block_start_string:
                            block_openings.append(token_start)
                        elif token == self.environment.variable_start_string:
                            print_openings.append(token_start)

                    elif token[1] == self.environment.variable_end_string[1]:
                        prev_idx = None
                        if token == self.environment.block_end_string and block_openings:
                            prev_idx = block_openings.pop()
                        elif token == self.environment.variable_end_string and print_openings:
                            prev_idx = print_openings.pop()

                        if prev_idx is not None:
                            # replace the opening
                            data.seek(prev_idx, os.SEEK_SET)
                            data.write(to_text(self.environment.comment_start_string))
                            # replace the closing
                            data.seek(token_start, os.SEEK_SET)
                            data.write(to_text(self.environment.comment_end_string))

                    else:
                        raise AnsibleError("Error while cleaning data for safety: unhandled regex match")

                ret = data.getvalue()
        else:
            ret = orig_data

        return ret

    def set_available_variables(self, variables):
        '''
        Sets the list of template variables this Templar instance will use
        to template things, so we don't have to pass them around between
        internal methods. We also clear the template cache here, as the variables
        are being changed.
        '''

        if not isinstance(variables, dict):
            raise AnsibleAssertionError("the type of 'variables' should be a dict but was a %s" % (type(variables)))
        self._available_variables = variables
        self._cached_result = {}

    def template(self, variable, convert_bare=False, preserve_trailing_newlines=True, escape_backslashes=True, fail_on_undefined=None, overrides=None,
                 convert_data=True, static_vars=None, cache=True, bare_deprecated=True, disable_lookups=False):
        '''
        Templates (possibly recursively) any given data as input. If convert_bare is
        set to True, the given data will be wrapped as a jinja2 variable ('{{foo}}')
        before being sent through the template engine.
        '''
        static_vars = [''] if static_vars is None else static_vars

        # Don't template unsafe variables, just return them.
        if hasattr(variable, '__UNSAFE__'):
            return variable

        if fail_on_undefined is None:
            fail_on_undefined = self._fail_on_undefined_errors

        try:
            if convert_bare:
                variable = self._convert_bare_variable(variable, bare_deprecated=bare_deprecated)

            if isinstance(variable, string_types):
                result = variable

                if self._contains_vars(variable):
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

                    # Using a cache in order to prevent template calls with already templated variables
                    sha1_hash = None
                    if cache:
                        variable_hash = sha1(text_type(variable).encode('utf-8'))
                        options_hash = sha1(
                            (
                                text_type(preserve_trailing_newlines) +
                                text_type(escape_backslashes) +
                                text_type(fail_on_undefined) +
                                text_type(overrides)
                            ).encode('utf-8')
                        )
                        sha1_hash = variable_hash.hexdigest() + options_hash.hexdigest()
                    if cache and sha1_hash in self._cached_result:
                        result = self._cached_result[sha1_hash]
                    else:
                        result = self.do_template(
                            variable,
                            preserve_trailing_newlines=preserve_trailing_newlines,
                            escape_backslashes=escape_backslashes,
                            fail_on_undefined=fail_on_undefined,
                            overrides=overrides,
                            disable_lookups=disable_lookups,
                        )

                        unsafe = hasattr(result, '__UNSAFE__')
                        if convert_data and not self._no_type_regex.match(variable):
                            # if this looks like a dictionary or list, convert it to such using the safe_eval method
                            if (result.startswith("{") and not result.startswith(self.environment.variable_start_string)) or \
                                    result.startswith("[") or result in ("True", "False"):
                                eval_results = safe_eval(result, locals=self._available_variables, include_exceptions=True)
                                if eval_results[1] is None:
                                    result = eval_results[0]
                                    if unsafe:
                                        result = wrap_var(result)
                                else:
                                    # FIXME: if the safe_eval raised an error, should we do something with it?
                                    pass

                        # we only cache in the case where we have a single variable
                        # name, to make sure we're not putting things which may otherwise
                        # be dynamic in the cache (filters, lookups, etc.)
                        if cache:
                            self._cached_result[sha1_hash] = result

                return result

            elif isinstance(variable, (list, tuple)):
                return [self.template(
                    v,
                    preserve_trailing_newlines=preserve_trailing_newlines,
                    fail_on_undefined=fail_on_undefined,
                    overrides=overrides,
                    disable_lookups=disable_lookups,
                ) for v in variable]
            elif isinstance(variable, dict):
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

        except AnsibleFilterError:
            if self._fail_on_filter_errors:
                raise
            else:
                return variable

    def is_template(self, data):
        ''' lets us know if data has a template'''
        if isinstance(data, string_types):
            try:
                new = self.do_template(data, fail_on_undefined=True)
            except (AnsibleUndefinedVariable, UndefinedError):
                return True
            except:
                return False
            return (new != data)
        elif isinstance(data, (list, tuple)):
            for v in data:
                if self.is_template(v):
                    return True
        elif isinstance(data, dict):
            for k in data:
                if self.is_template(k) or self.is_template(data[k]):
                    return True
        return False

    def templatable(self, data):
        '''
        returns True if the data can be templated w/o errors
        '''
        templatable = True
        try:
            self.template(data)
        except:
            templatable = False
        return templatable

    def _contains_vars(self, data):
        '''
        returns True if the data contains a variable pattern
        '''
        if isinstance(data, string_types):
            for marker in (self.environment.block_start_string, self.environment.variable_start_string, self.environment.comment_start_string):
                if marker in data:
                    return True
        return False

    def _convert_bare_variable(self, variable, bare_deprecated):
        '''
        Wraps a bare string, which may have an attribute portion (ie. foo.bar)
        in jinja2 variable braces so that it is evaluated properly.
        '''

        if isinstance(variable, string_types):
            contains_filters = "|" in variable
            first_part = variable.split("|")[0].split(".")[0].split("[")[0]
            if (contains_filters or first_part in self._available_variables) and self.environment.variable_start_string not in variable:
                if bare_deprecated:
                    display.deprecated("Using bare variables is deprecated."
                                       " Update your playbooks so that the environment value uses the full variable syntax ('%s%s%s')" %
                                       (self.environment.variable_start_string, variable, self.environment.variable_end_string), version='2.7')
                return "%s%s%s" % (self.environment.variable_start_string, variable, self.environment.variable_end_string)

        # the variable didn't meet the conditions to be converted,
        # so just return it as-is
        return variable

    def _finalize(self, thing):
        '''
        A custom finalize method for jinja2, which prevents None from being returned
        '''
        return thing if thing is not None else ''

    def _fail_lookup(self, name, *args, **kwargs):
        raise AnsibleError("The lookup `%s` was found, however lookups were disabled from templating" % name)

    def _query_lookup(self, name, *args, **kwargs):
        ''' wrapper for lookup, force wantlist true'''
        kwargs['wantlist'] = True
        return self._lookup(name, *args, **kwargs)

    def _lookup(self, name, *args, **kwargs):
        instance = self._lookup_loader.get(name.lower(), loader=self._loader, templar=self)

        if instance is not None:
            wantlist = kwargs.pop('wantlist', False)
            allow_unsafe = kwargs.pop('allow_unsafe', C.DEFAULT_ALLOW_UNSAFE_LOOKUPS)

            from ansible.utils.listify import listify_lookup_plugin_terms
            loop_terms = listify_lookup_plugin_terms(terms=args, templar=self, loader=self._loader, fail_on_undefined=True, convert_bare=False)
            # safely catch run failures per #5059
            try:
                ran = instance.run(loop_terms, variables=self._available_variables, **kwargs)
            except (AnsibleUndefinedVariable, UndefinedError) as e:
                raise AnsibleUndefinedVariable(e)
            except Exception as e:
                if self._fail_on_lookup_errors:
                    raise AnsibleError("An unhandled exception occurred while running the lookup plugin '%s'. Error was a %s, "
                                       "original message: %s" % (name, type(e), e))
                ran = None

            if ran and not allow_unsafe:
                if wantlist:
                    ran = wrap_var(ran)
                else:
                    try:
                        ran = UnsafeProxy(",".join(ran))
                    except TypeError:
                        if isinstance(ran, list) and len(ran) == 1:
                            ran = wrap_var(ran[0])
                        else:
                            ran = wrap_var(ran)

                if self.cur_context:
                    self.cur_context.unsafe = True
            return ran
        else:
            raise AnsibleError("lookup plugin (%s) not found" % name)

    def do_template(self, data, preserve_trailing_newlines=True, escape_backslashes=True, fail_on_undefined=None, overrides=None, disable_lookups=False):
        # For preserving the number of input newlines in the output (used
        # later in this method)
        data_newlines = _count_newlines_from_end(data)

        if fail_on_undefined is None:
            fail_on_undefined = self._fail_on_undefined_errors

        try:
            # allows template header overrides to change jinja2 options.
            if overrides is None:
                myenv = self.environment.overlay()
            else:
                myenv = self.environment.overlay(overrides)

            # Get jinja env overrides from template
            if data.startswith(JINJA2_OVERRIDE):
                eol = data.find('\n')
                line = data[len(JINJA2_OVERRIDE):eol]
                data = data[eol + 1:]
                for pair in line.split(','):
                    (key, val) = pair.split(':')
                    key = key.strip()
                    setattr(myenv, key, ast.literal_eval(val.strip()))

            # Adds Ansible custom filters and tests
            myenv.filters.update(self._get_filters())
            myenv.tests.update(self._get_tests())

            if escape_backslashes:
                # Allow users to specify backslashes in playbooks as "\\" instead of as "\\\\".
                data = _escape_backslashes(data, myenv)

            try:
                t = myenv.from_string(data)
            except TemplateSyntaxError as e:
                raise AnsibleError("template error while templating string: %s. String: %s" % (to_native(e), to_native(data)))
            except Exception as e:
                if 'recursion' in to_native(e):
                    raise AnsibleError("recursive loop detected in template string: %s" % to_native(data))
                else:
                    return data

            if disable_lookups:
                t.globals['query'] = t.globals['q'] = t.globals['lookup'] = self._fail_lookup
            else:
                t.globals['lookup'] = self._lookup
                t.globals['query'] = t.globals['q'] = self._query_lookup

            t.globals['finalize'] = self._finalize

            jvars = AnsibleJ2Vars(self, t.globals)

            self.cur_context = new_context = t.new_context(jvars, shared=True)
            rf = t.root_render_func(new_context)

            try:
                res = j2_concat(rf)
                if new_context.unsafe:
                    res = wrap_var(res)
            except TypeError as te:
                if 'StrictUndefined' in to_native(te):
                    errmsg = "Unable to look up a name or access an attribute in template string (%s).\n" % to_native(data)
                    errmsg += "Make sure your variable name does not contain invalid characters like '-': %s" % to_native(te)
                    raise AnsibleUndefinedVariable(errmsg)
                else:
                    display.debug("failing because of a type error, template data is: %s" % to_native(data))
                    raise AnsibleError("Unexpected templating type error occurred on (%s): %s" % (to_native(data), to_native(te)))

            if preserve_trailing_newlines:
                # The low level calls above do not preserve the newline
                # characters at the end of the input data, so we use the
                # calculate the difference in newlines and append them
                # to the resulting output for parity
                #
                # jinja2 added a keep_trailing_newline option in 2.7 when
                # creating an Environment.  That would let us make this code
                # better (remove a single newline if
                # preserve_trailing_newlines is False).  Once we can depend on
                # that version being present, modify our code to set that when
                # initializing self.environment and remove a single trailing
                # newline here if preserve_newlines is False.
                res_newlines = _count_newlines_from_end(res)
                if data_newlines > res_newlines:
                    res += self.environment.newline_sequence * (data_newlines - res_newlines)
            return res
        except (UndefinedError, AnsibleUndefinedVariable) as e:
            if fail_on_undefined:
                raise AnsibleUndefinedVariable(e)
            else:
                display.debug("Ignoring undefined failure: %s" % to_text(e))
                return data

    # for backwards compatibility in case anyone is using old private method directly
    _do_template = do_template
