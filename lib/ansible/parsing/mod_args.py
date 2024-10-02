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

from __future__ import annotations

import ansible.constants as C
from ansible.errors import AnsibleParserError, AnsibleError, AnsibleAssertionError
from ansible.module_utils.six import string_types
from ansible.module_utils.common.sentinel import Sentinel
from ansible.module_utils.common.text.converters import to_text
from ansible.parsing.splitter import parse_kv, split_args
from ansible.plugins.loader import module_loader, action_loader
from ansible.template import Templar
from ansible.utils.fqcn import add_internal_fqcns


# modules formated for user msg
_BUILTIN_RAW_PARAM_MODULES_SIMPLE = set([
    'include_vars',
    'include_tasks',
    'include_role',
    'import_tasks',
    'import_role',
    'add_host',
    'group_by',
    'set_fact',
    'meta',
])
FREEFORM_ACTIONS_SIMPLE = set(C.MODULE_REQUIRE_ARGS_SIMPLE)
FREEFORM_ACTIONS = frozenset(C.MODULE_REQUIRE_ARGS)
RAW_PARAM_MODULES_SIMPLE = _BUILTIN_RAW_PARAM_MODULES_SIMPLE.union(FREEFORM_ACTIONS_SIMPLE)
# For filtering out modules correctly below, use all permutations
RAW_PARAM_MODULES = frozenset(add_internal_fqcns(RAW_PARAM_MODULES_SIMPLE)).union(FREEFORM_ACTIONS)
BUILTIN_TASKS = frozenset(add_internal_fqcns((
    'meta',
    'include_tasks',
    'include_role',
    'import_tasks',
    'import_role'
)))


def _get_action_context(action_or_module, collection_list):
    module_context = module_loader.find_plugin_with_context(action_or_module, collection_list=collection_list)
    if module_context and module_context.resolved and module_context.action_plugin:
        action_or_module = module_context.action_plugin

    context = action_loader.find_plugin_with_context(action_or_module, collection_list=collection_list)
    if not context or not context.resolved:
        context = module_context
    return context


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

    # Standard YAML form for command-type modules. In this case, the args specified
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

    def __init__(self, task_ds=None, collection_list=None):
        task_ds = {} if task_ds is None else task_ds

        if not isinstance(task_ds, dict):
            raise AnsibleAssertionError("the type of 'task_ds' should be a dict, but is a %s" % type(task_ds))
        self._task_ds = task_ds
        self._collection_list = collection_list
        # delayed local imports to prevent circular import
        from ansible.playbook.task import Task
        from ansible.playbook.handler import Handler
        # store the valid Task/Handler attrs for quick access
        self._task_attrs = set(Task.fattributes)
        self._task_attrs.update(set(Handler.fattributes))
        # HACK: why are these not FieldAttributes on task with a post-validate to check usage?
        self._task_attrs.update(['local_action', 'static'])
        self._task_attrs = frozenset(self._task_attrs)

        self.resolved_action = None

    def _split_module_string(self, module_string):
        '''
        when module names are expressed like:
        action: copy src=a dest=b
        the first part of the string is the name of the module
        and the rest are strings pertaining to the arguments.
        '''

        tokens = split_args(module_string)
        if len(tokens) > 1:
            return (tokens[0].strip(), " ".join(tokens[1:]))
        else:
            return (tokens[0].strip(), "")

    def _normalize_parameters(self, thing, action=None, additional_args=None):
        '''
        arguments can be fuzzy.  Deal with all the forms.
        '''

        additional_args = {} if additional_args is None else additional_args

        # final args are the ones we'll eventually return, so first update
        # them with any additional args specified, which have lower priority
        # than those which may be parsed/normalized next
        final_args = dict()
        if additional_args:
            if isinstance(additional_args, string_types):
                templar = Templar(loader=None)
                if templar.is_template(additional_args):
                    final_args['_variable_params'] = additional_args
                else:
                    raise AnsibleParserError("Complex args containing variables cannot use bare variables (without Jinja2 delimiters), "
                                             "and must use the full variable style ('{{var_name}}')")
            elif isinstance(additional_args, dict):
                final_args.update(additional_args)
            else:
                raise AnsibleParserError('Complex args must be a dictionary or variable string ("{{var}}").')

        # how we normalize depends if we figured out what the module name is
        # yet.  If we have already figured it out, it's a 'new style' invocation.
        # otherwise, it's not

        if action is not None:
            args = self._normalize_new_style_args(thing, action)
        else:
            (action, args) = self._normalize_old_style_args(thing)

            # this can occasionally happen, simplify
            if args and 'args' in args:
                tmp_args = args.pop('args')
                if isinstance(tmp_args, string_types):
                    tmp_args = parse_kv(tmp_args)
                args.update(tmp_args)

        # only internal variables can start with an underscore, so
        # we don't allow users to set them directly in arguments
        if args and action not in FREEFORM_ACTIONS:
            for arg in args:
                arg = to_text(arg)
                if arg.startswith('_ansible_'):
                    err_msg = (
                        f"Invalid parameter specified beginning with keyword '_ansible_' for action '{action !s}': '{arg !s}'. "
                        "The prefix '_ansible_' is reserved for internal use only."
                    )
                    raise AnsibleError(err_msg)

        # finally, update the args we're going to return with the ones
        # which were normalized above
        if args:
            final_args.update(args)

        return (action, final_args)

    def _normalize_new_style_args(self, thing, action):
        '''
        deals with fuzziness in new style module invocations
        accepting key=value pairs and dictionaries, and returns
        a dictionary of arguments

        possible example inputs:
            'echo hi', 'shell'
            {'region': 'xyz'}, 'ec2'
        standardized outputs like:
            { _raw_params: 'echo hi', _uses_shell: True }
        '''

        if isinstance(thing, dict):
            # form is like: { xyz: { x: 2, y: 3 } }
            args = thing
        elif isinstance(thing, string_types):
            # form is like: copy: src=a dest=b
            check_raw = action in FREEFORM_ACTIONS
            args = parse_kv(thing, check_raw=check_raw)
        elif thing is None:
            # this can happen with modules which take no params, like ping:
            args = None
        else:
            raise AnsibleParserError("unexpected parameter type in action: %s" % type(thing), obj=self._task_ds)
        return args

    def _normalize_old_style_args(self, thing):
        '''
        deals with fuzziness in old-style (action/local_action) module invocations
        returns tuple of (module_name, dictionary_args)

        possible example inputs:
           { 'shell' : 'echo hi' }
           'shell echo hi'
           {'module': 'ec2', 'x': 1 }
        standardized outputs like:
           ('ec2', { 'x': 1} )
        '''

        action = None
        args = None

        if isinstance(thing, dict):
            # form is like:  action: { module: 'copy', src: 'a', dest: 'b' }
            thing = thing.copy()
            if 'module' in thing:
                action, module_args = self._split_module_string(thing['module'])
                args = thing.copy()
                check_raw = action in FREEFORM_ACTIONS
                args.update(parse_kv(module_args, check_raw=check_raw))
                del args['module']

        elif isinstance(thing, string_types):
            # form is like:  action: copy src=a dest=b
            (action, args) = self._split_module_string(thing)
            check_raw = action in FREEFORM_ACTIONS
            args = parse_kv(args, check_raw=check_raw)

        else:
            # need a dict or a string, so giving up
            raise AnsibleParserError("unexpected parameter type in action: %s" % type(thing), obj=self._task_ds)

        return (action, args)

    def parse(self, skip_action_validation=False):
        '''
        Given a task in one of the supported forms, parses and returns
        returns the action, arguments, and delegate_to values for the
        task, dealing with all sorts of levels of fuzziness.
        '''

        thing = None

        action = None
        delegate_to = self._task_ds.get('delegate_to', Sentinel)
        args = dict()

        # This is the standard YAML form for command-type modules. We grab
        # the args and pass them in as additional arguments, which can/will
        # be overwritten via dict updates from the other arg sources below
        additional_args = self._task_ds.get('args', dict())

        # We can have one of action, local_action, or module specified
        # action
        if 'action' in self._task_ds:
            # an old school 'action' statement
            thing = self._task_ds['action']
            action, args = self._normalize_parameters(thing, action=action, additional_args=additional_args)

        # local_action
        if 'local_action' in self._task_ds:
            # local_action is similar but also implies a delegate_to
            if action is not None:
                raise AnsibleParserError("action and local_action are mutually exclusive", obj=self._task_ds)
            thing = self._task_ds.get('local_action', '')
            delegate_to = 'localhost'
            action, args = self._normalize_parameters(thing, action=action, additional_args=additional_args)

        if action is not None and not skip_action_validation:
            context = _get_action_context(action, self._collection_list)
            if context is not None and context.resolved:
                self.resolved_action = context.resolved_fqcn

        # module: <stuff> is the more new-style invocation

        # filter out task attributes so we're only querying unrecognized keys as actions/modules
        non_task_ds = dict((k, v) for k, v in self._task_ds.items() if (k not in self._task_attrs) and (not k.startswith('with_')))

        # walk the filtered input dictionary to see if we recognize a module name
        for item, value in non_task_ds.items():
            context = None
            is_action_candidate = False
            if item in BUILTIN_TASKS:
                is_action_candidate = True
            elif skip_action_validation:
                is_action_candidate = True
            else:
                try:
                    context = _get_action_context(item, self._collection_list)
                except AnsibleError as e:
                    if e.obj is None:
                        e.obj = self._task_ds
                    raise e

                is_action_candidate = context.resolved and bool(context.redirect_list)

            if is_action_candidate:
                # finding more than one module name is a problem
                if action is not None:
                    raise AnsibleParserError("conflicting action statements: %s, %s" % (action, item), obj=self._task_ds)

                if context is not None and context.resolved:
                    self.resolved_action = context.resolved_fqcn

                action = item
                thing = value
                action, args = self._normalize_parameters(thing, action=action, additional_args=additional_args)

        # if we didn't see any module in the task at all, it's not a task really
        if action is None:
            if non_task_ds:  # there was one non-task action, but we couldn't find it
                bad_action = list(non_task_ds.keys())[0]
                raise AnsibleParserError("couldn't resolve module/action '{0}'. This often indicates a "
                                         "misspelling, missing collection, or incorrect module path.".format(bad_action),
                                         obj=self._task_ds)
            else:
                raise AnsibleParserError("no module/action detected in task.",
                                         obj=self._task_ds)
        elif args.get('_raw_params', '') != '' and action not in RAW_PARAM_MODULES:
            templar = Templar(loader=None)
            raw_params = args.pop('_raw_params')
            if templar.is_template(raw_params):
                args['_variable_params'] = raw_params
            else:
                raise AnsibleParserError(
                    "this task '%s' has extra params, which is only allowed in the following modules: %s" % (action, ", ".join(RAW_PARAM_MODULES_SIMPLE)),
                    obj=self._task_ds)

        return (action, args, delegate_to)
