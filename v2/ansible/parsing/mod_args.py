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

import exceptions

from ansible.errors import AnsibleError
from ansible.plugins import module_finder
from ansible.parsing.splitter import parse_kv

class ModuleArgsParser(object):

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

    This class exists so other things don't have to remember how this
    all works.  Pass it "part1" and "part2", and the parse function
    will tell you about the modules in a predictable way.
    """

    def __init__(self):
        self._ds = None

    def _get_delegate_to(self):
        '''
        Returns the value of the delegate_to key from the task datastructure,
        or None if the value was not directly specified
        '''
        return self._ds.get('delegate_to')

    def _get_old_style_action(self):
        '''
        Searches the datastructure for 'action:' or 'local_action:' keywords.
        When local_action is found, the delegate_to value is set to the localhost
        IP, otherwise delegate_to is left as None.

        Inputs:
        - None

        Outputs:
        - None (if neither keyword is found), or a dictionary containing:
          action:
            the module name to be executed
          args:
            a dictionary containing the arguments to the module
          delegate_to:
            None or 'localhost'
        '''

        # determine if this is an 'action' or 'local_action'
        if 'action' in self._ds:
            action_data = self._ds.get('action', '')
            delegate_to = None
        elif 'local_action' in self._ds:
            action_data = self._ds.get('local_action', '')
            delegate_to = 'localhost'
        else:
            return None

        # now we get the arguments for the module, which may be a
        # string of key=value pairs, a dictionary of values, or a
        # dictionary with a special 'args:' value in it
        if isinstance(action_data, dict):
            action = self._get_specified_module(action_data)
            args = dict()
            if 'args' in action_data:
                args = self._get_args_from_ds(action, action_data)
                del action_data['args']
            other_args = action_data.copy()
            # remove things we don't want in the args
            if 'module' in other_args:
                del other_args['module']
            args.update(other_args)
        elif isinstance(action_data, basestring):
            action_data = action_data.strip()
            if not action_data:
                # TODO: change to an AnsibleParsingError so that the
                #       filename/line number can be reported in the error
                raise AnsibleError("when using 'action:' or 'local_action:', the module name must be specified")
            else:
                # split up the string based on spaces, where the first
                # item specified must be a valid module name
                parts = action_data.split(' ', 1)
                action = parts[0]
                if action not in module_finder:
                    # TODO: change to an AnsibleParsingError so that the
                    #       filename/line number can be reported in the error
                    raise AnsibleError("the module '%s' was not found in the list of loaded modules")
                if len(parts) > 1:
                    args = self._get_args_from_action(action, ' '.join(parts[1:]))
                else:
                    args = {}
        else:
            # TODO: change to an AnsibleParsingError so that the
            #       filename/line number can be reported in the error
            raise AnsibleError('module args must be specified as a dictionary or string')

        return dict(action=action, args=args, delegate_to=delegate_to)

    def _get_new_style_action(self):
        '''
        Searches the datastructure for 'module_name:', where the module_name is a
        valid module loaded by the module_finder plugin.

        Inputs:
        - None

        Outputs:
        - None (if no valid module is found), or a dictionary containing:
          action:
            the module name to be executed
          args:
            a dictionary containing the arguments to the module
          delegate_to:
            None
        '''

        # for all keys in the datastructure, check to see if the value
        # corresponds to a module found by the module_finder plugin
        action = None
        for item in self._ds:
            if item in module_finder:
                action = item
                break
        else:
            # none of the keys matched a known module name
            return None

        # now we get the arguments for the module, which may be a
        # string of key=value pairs, a dictionary of values, or a
        # dictionary with a special 'args:' value in it
        action_data = self._ds.get(action, '')
        if isinstance(action_data, dict):
            args = dict()
            if 'args' in action_data:
                args = self._get_args_from_ds(action, action_data)
                del action_data['args']
            other_args = action_data.copy()
            # remove things we don't want in the args
            if 'module' in other_args:
                del other_args['module']
            args.update(other_args)
        else:
            args = self._get_args_from_action(action, action_data.strip())

        return dict(action=action, args=args, delegate_to=None)

    def _get_args_from_ds(self, action, action_data):
        '''
        Gets the module arguments from the 'args' value of the
        action_data, when action_data is a dict. The value of
        'args' can be either a string or a dictionary itself, so
        we use parse_kv() to split up the key=value pairs when
        a string is found.

        Inputs:
        - action_data:
            a dictionary of values, which may or may not contain a
            key named 'args'

        Outputs:
        - a dictionary of values, representing the arguments to the
          module action specified
        '''
        args = action_data.get('args', {}).copy()
        if isinstance(args, basestring):
            if action in ('command', 'shell'):
                args = parse_kv(args, check_raw=True)
            else:
                args = parse_kv(args)
        return args

    def _get_args_from_action(self, action, action_data):
        '''
        Gets the module arguments from the action data when it is
        specified as a string of key=value pairs. Special handling
        is used for the command/shell modules, which allow free-
        form syntax for the options.

        Inputs:
        - action:
            the module to be executed
        - action_data:
            a string of key=value pairs (and possibly free-form arguments)

        Outputs:
        - A dictionary of values, representing the arguments to the
          module action specified OR a string of key=value pairs (when
          the module action is command or shell)
        '''
        tokens = action_data.split()
        if len(tokens) == 0:
            return {}
        else:
            joined = " ".join(tokens)
            if action in ('command', 'shell'):
                return parse_kv(joined, check_raw=True)
            else:
                return parse_kv(joined)

    def _get_specified_module(self, action_data):
        '''
        gets the module if specified directly in the arguments, ie:
        - action:
            module: foo

        Inputs:
        - action_data:
            a dictionary of values, which may or may not contain the
            key 'module'

        Outputs:
        - a string representing the module specified in the data, or
          None if that key was not found
        '''
        return action_data.get('module')

    def parse(self, ds):
        '''
        Given a task in one of the supported forms, parses and returns
        returns the action, arguments, and delegate_to values for the
        task.

        Inputs:
        - ds:
            a dictionary datastructure representing the task as parsed
            from a YAML file

        Outputs:
        - A tuple containing 3 values:
          action:
            the action (module name) to be executed
          args:
            the args for the action
          delegate_to:
            the delegate_to option (which may be None, if no delegate_to
            option was specified and this is not a local_action)
        '''

        assert type(ds) == dict

        self._ds = ds
 
        # first we try to get the module action/args based on the
        # new-style format, where the module name is the key
        result = self._get_new_style_action()
        if result is None:
            # failing that, we resort to checking for the old-style syntax,
            # where 'action' or 'local_action' is the key
            result = self._get_old_style_action()
            if result is None:
                # TODO: change to an AnsibleParsingError so that the
                #       filename/line number can be reported in the error
                raise AnsibleError('no action specified for this task')

        # if the action is set to 'shell', we switch that to 'command' and
        # set the special parameter '_uses_shell' to true in the args dict
        if result['action'] == 'shell':
            result['action'] = 'command'
            result['args']['_uses_shell'] = True

        # finally, we check to see if a delegate_to value was specified
        # in the task datastructure (and raise an error for local_action,
        # which essentially means we're delegating to localhost)
        specified_delegate_to = self._get_delegate_to()
        if specified_delegate_to is not None:
            if result['delegate_to'] is not None:
                # TODO: change to an AnsibleParsingError so that the
                #       filename/line number can be reported in the error
                raise AnsibleError('delegate_to cannot be used with local_action')
            else:
               result['delegate_to'] = specified_delegate_to

        return (result['action'], result['args'], result['delegate_to'])

