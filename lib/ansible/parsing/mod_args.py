# (c) 2014 Michael DeHaan, <michael@ansible.com>
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

from ansible.compat.six import iteritems, string_types

from ansible.errors import AnsibleParserError,AnsibleError
from ansible.plugins import module_loader
from ansible.parsing.splitter import parse_kv, split_args
from ansible.template import Templar

# For filtering out modules correctly below
RAW_PARAM_MODULES = ([
    'command',
    'shell',
    'script',
    'include',
    'include_vars',
    'add_host',
    'group_by',
    'set_fact',
    'raw',
    'meta',
])

class ModuleArgsParser:

    """
    There are several ways a module and argument set can be expressed:

    # legacy form (for a shell command)
    - action: shell echo hi

    # common shorthand for local actions vs delegate_to
    - local_action: shell echo hi

    # most commonly:
    - copy: src=a dest=b

    # legacy form
    - action: copy src=a dest=b

    # complex args form, for passing structured data
    - copy:
        src: a
        dest: b

    # gross, but technically legal
    - action:
        module: copy
        args:
          src: a
          dest: b

    # extra gross, but also legal. in this case, the args specified
    # will act as 'defaults' and will be overridden by any args specified
    # in one of the other formats (complex args under the action, or
    # parsed from the k=v string
    - command: 'pwd'
      args:
        chdir: '/tmp'


    This class has some of the logic to canonicalize these into the form

    - module: <module_name>
      delegate_to: <optional>
      args: <args>

    Args may also be munged for certain shell command parameters.
    """

    def __init__(self, task_ds=dict()):
        assert isinstance(task_ds, dict)
        self._task_ds = task_ds


    def _split_module_string(self, module_string):
        '''
        when module names are expressed like:
        action: copy src=a dest=b
        the first part of the string is the name of the module
        and the rest are strings pertaining to the arguments.
        '''

        tokens = split_args(module_string)
        if len(tokens) > 1:
            return (tokens[0], " ".join(tokens[1:]))
        else:
            return (tokens[0], "")


    def _handle_shell_weirdness(self, action, args):
        '''
        given an action name and an args dictionary, return the
        proper action name and args dictionary.  This mostly is due
        to shell/command being treated special and nothing else
        '''

        # don't handle non shell/command modules in this function
        # TODO: in terms of the whole app, should 'raw' also fit here?
        if action not in ['shell', 'command']:
            return (action, args)

        # the shell module really is the command module with an additional
        # parameter
        if action == 'shell':
            action = 'command'
            args['_uses_shell'] = True

        return (action, args)

    def _normalize_parameters(self, thing, action=None, additional_args=dict()):
        '''
        arguments can be fuzzy.  Deal with all the forms.
        '''

        # final args are the ones we'll eventually return, so first update
        # them with any additional args specified, which have lower priority
        # than those which may be parsed/normalized next
        final_args = dict()
        if additional_args:
            if isinstance(additional_args, string_types):
                templar = Templar(loader=None)
                if templar._contains_vars(additional_args):
                    final_args['_variable_params'] = additional_args
                else:
                    raise AnsibleParserError("Complex args containing variables cannot use bare variables, and must use the full variable style ('{{var_name}}')")
            elif isinstance(additional_args, dict):
                final_args.update(additional_args)
            else:
                raise AnsibleParserError('Complex args must be a dictionary or variable string ("{{var}}").')

        # how we normalize depends if we figured out what the module name is
        # yet.  If we have already figured it out, it's an 'old style' invocation.
        # otherwise, it's not

        if action is not None:
            args = self._normalize_old_style_args(thing, action)
        else:
            (action, args) = self._normalize_new_style_args(thing)

            # this can occasionally happen, simplify
            if args and 'args' in args:
                tmp_args = args.pop('args')
                if isinstance(tmp_args, string_types):
                    tmp_args = parse_kv(tmp_args)
                args.update(tmp_args)

        # only internal variables can start with an underscore, so
        # we don't allow users to set them directy in arguments
        if args and action not in ('command', 'shell', 'script', 'raw'):
            for arg in args:
                if arg.startswith('_ansible_'):
                    raise AnsibleError("invalid parameter specified for action '%s': '%s'" % (action, arg))

        # finally, update the args we're going to return with the ones
        # which were normalized above
        if args:
            final_args.update(args)

        return (action, final_args)

    def _normalize_old_style_args(self, thing, action):
        '''
        deals with fuzziness in old-style (action/local_action) module invocations
        returns tuple of (module_name, dictionary_args)

        possible example inputs:
            { 'local_action' : 'shell echo hi' }
            { 'action'       : 'shell echo hi' }
            { 'local_action' : { 'module' : 'ec2', 'x' : 1, 'y': 2 }}
        standardized outputs like:
            ( 'command', { _raw_params: 'echo hi', _uses_shell: True }
        '''

        if isinstance(thing, dict):
            # form is like: local_action: { module: 'xyz', x: 2, y: 3 } ... uncommon!
            args = thing
        elif isinstance(thing, string_types):
            # form is like: local_action: copy src=a dest=b ... pretty common
            check_raw = action in ('command', 'shell', 'script', 'raw')
            args = parse_kv(thing, check_raw=check_raw)
        elif thing is None:
            # this can happen with modules which take no params, like ping:
            args = None
        else:
            raise AnsibleParserError("unexpected parameter type in action: %s" % type(thing), obj=self._task_ds)
        return args

    def _normalize_new_style_args(self, thing):
        '''
        deals with fuzziness in new style module invocations
        accepting key=value pairs and dictionaries, and always returning dictionaries
        returns tuple of (module_name, dictionary_args)

        possible example inputs:
           { 'shell' : 'echo hi' }
           { 'ec2'   : { 'region' : 'xyz' }
           { 'ec2'   : 'region=xyz' }
        standardized outputs like:
           ('ec2', { region: 'xyz'} )
        '''

        action = None
        args = None

        actions_allowing_raw = ('command', 'shell', 'script', 'raw')
        if isinstance(thing, dict):
            # form is like:  copy: { src: 'a', dest: 'b' } ... common for structured (aka "complex") args
            thing = thing.copy()
            if 'module' in thing:
                action, module_args = self._split_module_string(thing['module'])
                args = thing.copy()
                check_raw = action in actions_allowing_raw
                args.update(parse_kv(module_args, check_raw=check_raw))
                del args['module']

        elif isinstance(thing, string_types):
            # form is like:  copy: src=a dest=b ... common shorthand throughout ansible
            (action, args) = self._split_module_string(thing)
            check_raw = action in actions_allowing_raw
            args = parse_kv(args, check_raw=check_raw)

        else:
            # need a dict or a string, so giving up
            raise AnsibleParserError("unexpected parameter type in action: %s" % type(thing), obj=self._task_ds)

        return (action, args)

    def parse(self):
        '''
        Given a task in one of the supported forms, parses and returns
        returns the action, arguments, and delegate_to values for the
        task, dealing with all sorts of levels of fuzziness.
        '''

        thing      = None

        action      = None
        delegate_to = self._task_ds.get('delegate_to', None)
        args        = dict()


        # this is the 'extra gross' scenario detailed above, so we grab
        # the args and pass them in as additional arguments, which can/will
        # be overwritten via dict updates from the other arg sources below
        additional_args = self._task_ds.get('args', dict())

        # We can have one of action, local_action, or module specified
        # action
        if 'action' in self._task_ds:
            # an old school 'action' statement
            thing = self._task_ds['action']
            action, args = self._normalize_parameters(thing, additional_args=additional_args)

        # local_action
        if 'local_action' in self._task_ds:
            # local_action is similar but also implies a delegate_to
            if action is not None:
                raise AnsibleParserError("action and local_action are mutually exclusive", obj=self._task_ds)
            thing = self._task_ds.get('local_action', '')
            delegate_to = 'localhost'
            action, args = self._normalize_parameters(thing, additional_args=additional_args)

        # module: <stuff> is the more new-style invocation

        # walk the input dictionary to see we recognize a module name
        for (item, value) in iteritems(self._task_ds):
            if item in module_loader or item == 'meta' or item == 'include':
                # finding more than one module name is a problem
                if action is not None:
                    raise AnsibleParserError("conflicting action statements", obj=self._task_ds)
                action = item
                thing = value
                action, args = self._normalize_parameters(value, action=action, additional_args=additional_args)

        # if we didn't see any module in the task at all, it's not a task really
        if action is None:
            if 'ping' not in module_loader:
                raise AnsibleParserError("The requested action was not found in configured module paths. "
                        "Additionally, core modules are missing. If this is a checkout, "
                        "run 'git submodule update --init --recursive' to correct this problem.",
                        obj=self._task_ds)

            else:
                raise AnsibleParserError("no action detected in task. This often indicates a misspelled module name, or incorrect module path.", obj=self._task_ds)
        elif args.get('_raw_params', '') != '' and action not in RAW_PARAM_MODULES:
            templar = Templar(loader=None)
            raw_params = args.pop('_raw_params')
            if templar._contains_vars(raw_params):
                args['_variable_params'] = raw_params
            else:
                raise AnsibleParserError("this task '%s' has extra params, which is only allowed in the following modules: %s" % (action, ", ".join(RAW_PARAM_MODULES)), obj=self._task_ds)

        # shell modules require special handling
        (action, args) = self._handle_shell_weirdness(action, args)

        return (action, args, delegate_to)
