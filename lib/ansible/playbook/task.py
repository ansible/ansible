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

from ansible.compat.six import iteritems, string_types

from ansible.errors import AnsibleError, AnsibleParserError

from ansible.parsing.mod_args import ModuleArgsParser
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleMapping, AnsibleUnicode

from ansible.plugins import lookup_loader
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.become import Become
from ansible.playbook.block import Block
from ansible.playbook.conditional import Conditional
from ansible.playbook.role import Role
from ansible.playbook.taggable import Taggable

from ansible.utils.unicode import to_str

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['Task']


class Task(Base, Conditional, Taggable, Become):

    """
    A task is a language feature that represents a call to a module, with given arguments and other parameters.
    A handler is a subclass of a task.

    Usage:

       Task.load(datastructure) -> Task
       Task.something(...)
    """

    # =================================================================================
    # ATTRIBUTES
    # load_<attribute_name> and
    # validate_<attribute_name>
    # will be used if defined
    # might be possible to define others

    _args                 = FieldAttribute(isa='dict', default=dict())
    _action               = FieldAttribute(isa='string')

    _any_errors_fatal     = FieldAttribute(isa='bool')
    _async                = FieldAttribute(isa='int', default=0)
    _changed_when         = FieldAttribute(isa='list', default=[])
    _delay                = FieldAttribute(isa='int', default=5)
    _delegate_to          = FieldAttribute(isa='string')
    _delegate_facts       = FieldAttribute(isa='bool', default=False)
    _failed_when          = FieldAttribute(isa='list', default=[])
    _first_available_file = FieldAttribute(isa='list')
    _loop                 = FieldAttribute(isa='string', private=True)
    _loop_args            = FieldAttribute(isa='list', private=True)
    _name                 = FieldAttribute(isa='string', default='')
    _notify               = FieldAttribute(isa='list')
    _poll                 = FieldAttribute(isa='int')
    _register             = FieldAttribute(isa='string')
    _retries              = FieldAttribute(isa='int', default=3)
    _until                = FieldAttribute(isa='list', default=[])

    def __init__(self, block=None, role=None, task_include=None):
        ''' constructors a task, without the Task.load classmethod, it will be pretty blank '''

        self._block        = block
        self._role         = role
        self._task_include = task_include

        super(Task, self).__init__()

    def get_path(self):
        ''' return the absolute path of the task with its line number '''

        if hasattr(self, '_ds'):
            return "%s:%s" % (self._ds._data_source, self._ds._line_number)

    def get_name(self):
        ''' return the name of the task '''

        if self._role and self.name:
            return "%s : %s" % (self._role.get_name(), self.name)
        elif self.name:
            return self.name
        else:
            if self._role:
                return "%s : %s" % (self._role.get_name(), self.action)
            else:
                return "%s" % (self.action,)

    def _merge_kv(self, ds):
        if ds is None:
            return ""
        elif isinstance(ds, string_types):
            return ds
        elif isinstance(ds, dict):
            buf = ""
            for (k,v) in iteritems(ds):
                if k.startswith('_'):
                    continue
                buf = buf + "%s=%s " % (k,v)
            buf = buf.strip()
            return buf

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):
        t = Task(block=block, role=role, task_include=task_include)
        return t.load_data(data, variable_manager=variable_manager, loader=loader)

    def __repr__(self):
        ''' returns a human readable representation of the task '''
        if self.get_name() == 'meta':
            return "TASK: meta (%s)" % self.args['_raw_params']
        else:
            return "TASK: %s" % self.get_name()

    def _preprocess_loop(self, ds, new_ds, k, v):
        ''' take a lookup plugin name and store it correctly '''

        loop_name = k.replace("with_", "")
        if new_ds.get('loop') is not None:
            raise AnsibleError("duplicate loop in task: %s" % loop_name, obj=ds)
        if v is None:
            raise AnsibleError("you must specify a value when using %s" % k, obj=ds)
        new_ds['loop'] = loop_name
        new_ds['loop_args'] = v

    def preprocess_data(self, ds):
        '''
        tasks are especially complex arguments so need pre-processing.
        keep it short.
        '''

        assert isinstance(ds, dict)

        # the new, cleaned datastructure, which will have legacy
        # items reduced to a standard structure suitable for the
        # attributes of the task class
        new_ds = AnsibleMapping()
        if isinstance(ds, AnsibleBaseYAMLObject):
            new_ds.ansible_pos = ds.ansible_pos

        # use the args parsing class to determine the action, args,
        # and the delegate_to value from the various possible forms
        # supported as legacy
        args_parser = ModuleArgsParser(task_ds=ds)
        try:
            (action, args, delegate_to) = args_parser.parse()
        except AnsibleParserError as e:
            raise AnsibleParserError(to_str(e), obj=ds)

        # the command/shell/script modules used to support the `cmd` arg,
        # which corresponds to what we now call _raw_params, so move that
        # value over to _raw_params (assuming it is empty)
        if action in ('command', 'shell', 'script'):
            if 'cmd' in args:
                if args.get('_raw_params', '') != '':
                    raise AnsibleError("The 'cmd' argument cannot be used when other raw parameters are specified."
                            " Please put everything in one or the other place.", obj=ds)
                args['_raw_params'] = args.pop('cmd')

        new_ds['action']      = action
        new_ds['args']        = args
        new_ds['delegate_to'] = delegate_to

        # we handle any 'vars' specified in the ds here, as we may
        # be adding things to them below (special handling for includes).
        # When that deprecated feature is removed, this can be too.
        if 'vars' in ds:
            # _load_vars is defined in Base, and is used to load a dictionary
            # or list of dictionaries in a standard way
            new_ds['vars'] = self._load_vars(None, ds.pop('vars'))
        else:
            new_ds['vars'] = dict()

        for (k,v) in iteritems(ds):
            if k in ('action', 'local_action', 'args', 'delegate_to') or k == action or k == 'shell':
                # we don't want to re-assign these values, which were
                # determined by the ModuleArgsParser() above
                continue
            elif k.replace("with_", "") in lookup_loader:
                self._preprocess_loop(ds, new_ds, k, v)
            else:
                # pre-2.0 syntax allowed variables for include statements at the
                # top level of the task, so we move those into the 'vars' dictionary
                # here, and show a deprecation message as we will remove this at
                # some point in the future.
                if action == 'include' and k not in self._get_base_attributes() and k not in self.DEPRECATED_ATTRIBUTES:
                    display.deprecated("Specifying include variables at the top-level of the task is deprecated."
                            " Please see:\nhttp://docs.ansible.com/ansible/playbooks_roles.html#task-include-files-and-encouraging-reuse\n\n"
                            " for currently supported syntax regarding included files and variables")
                    new_ds['vars'][k] = v
                else:
                    new_ds[k] = v

        return super(Task, self).preprocess_data(new_ds)

    def post_validate(self, templar):
        '''
        Override of base class post_validate, to also do final validation on
        the block and task include (if any) to which this task belongs.
        '''

        if self._block:
            self._block.post_validate(templar)
        if self._task_include:
            self._task_include.post_validate(templar)

        super(Task, self).post_validate(templar)

    def _post_validate_register(self, attr, value, templar):
        '''
        Override post validation for the register args field, which is not
        supposed to be templated
        '''
        return value

    def _post_validate_loop_args(self, attr, value, templar):
        '''
        Override post validation for the loop args field, which is templated
        specially in the TaskExecutor class when evaluating loops.
        '''
        return value

    def _post_validate_environment(self, attr, value, templar):
        '''
        Override post validation of vars on the play, as we don't want to
        template these too early.
        '''
        if value is None:
            return dict()

        elif isinstance(value, list):
            if  len(value) == 1:
                return templar.template(value[0], convert_bare=True)
            else:
                env = []
                for env_item in value:
                    if isinstance(env_item, (string_types, AnsibleUnicode)) and env_item in templar._available_variables.keys():
                        env[env_item] =  templar.template(env_item, convert_bare=True)
        elif isinstance(value, dict):
            env = dict()
            for env_item in value:
                if isinstance(env_item, (string_types, AnsibleUnicode)) and env_item in templar._available_variables.keys():
                    env[env_item] =  templar.template(value[env_item], convert_bare=True)

        # at this point it should be a simple string
        return templar.template(value, convert_bare=True)

    def _post_validate_changed_when(self, attr, value, templar):
        '''
        changed_when is evaluated after the execution of the task is complete,
        and should not be templated during the regular post_validate step.
        '''
        return value

    def _post_validate_failed_when(self, attr, value, templar):
        '''
        failed_when is evaluated after the execution of the task is complete,
        and should not be templated during the regular post_validate step.
        '''
        return value

    def _post_validate_until(self, attr, value, templar):
        '''
        until is evaluated after the execution of the task is complete,
        and should not be templated during the regular post_validate step.
        '''
        return value

    def get_vars(self):
        all_vars = dict()
        if self._block:
            all_vars.update(self._block.get_vars())
        if self._task_include:
            all_vars.update(self._task_include.get_vars())

        all_vars.update(self.vars)

        if 'tags' in all_vars:
            del all_vars['tags']
        if 'when' in all_vars:
            del all_vars['when']

        return all_vars

    def get_include_params(self):
        all_vars = dict()
        if self._task_include:
            all_vars.update(self._task_include.get_include_params())
        if self.action == 'include':
            all_vars.update(self.vars)
        return all_vars

    def copy(self, exclude_block=False):
        new_me = super(Task, self).copy()

        new_me._block = None
        if self._block and not exclude_block:
            new_me._block = self._block.copy()

        new_me._role = None
        if self._role:
            new_me._role = self._role

        new_me._task_include = None
        if self._task_include:
            new_me._task_include = self._task_include.copy(exclude_block=exclude_block)

        return new_me

    def serialize(self):
        data = super(Task, self).serialize()

        if self._block:
            data['block'] = self._block.serialize()

        if self._role:
            data['role'] = self._role.serialize()

        if self._task_include:
            data['task_include'] = self._task_include.serialize()

        return data

    def deserialize(self, data):

        # import is here to avoid import loops
        #from ansible.playbook.task_include import TaskInclude

        block_data = data.get('block')

        if block_data:
            b = Block()
            b.deserialize(block_data)
            self._block = b
            del data['block']

        role_data = data.get('role')
        if role_data:
            r = Role()
            r.deserialize(role_data)
            self._role = r
            del data['role']

        ti_data = data.get('task_include')
        if ti_data:
            #ti = TaskInclude()
            ti = Task()
            ti.deserialize(ti_data)
            self._task_include = ti
            del data['task_include']

        super(Task, self).deserialize(data)

    def evaluate_conditional(self, templar, all_vars):
        if self._block is not None:
            if not self._block.evaluate_conditional(templar, all_vars):
                return False
        if self._task_include is not None:
            if not self._task_include.evaluate_conditional(templar, all_vars):
                return False
        return super(Task, self).evaluate_conditional(templar, all_vars)

    def set_loader(self, loader):
        '''
        Sets the loader on this object and recursively on parent, child objects.
        This is used primarily after the Task has been serialized/deserialized, which
        does not preserve the loader.
        '''

        self._loader = loader

        if self._block:
            self._block.set_loader(loader)
        if self._task_include:
            self._task_include.set_loader(loader)

    def _get_parent_attribute(self, attr, extend=False):
        '''
        Generic logic to get the attribute or parent attribute for a task value.
        '''
        value = None
        try:
            value = self._attributes[attr]

            if self._block and (value is None or extend):
                parent_value = getattr(self._block, attr)
                if extend:
                    value = self._extend_value(value, parent_value)
                else:
                    value = parent_value
            if self._task_include and (value is None or extend):
                parent_value = getattr(self._task_include, attr)
                if extend:
                    value = self._extend_value(value, parent_value)
                else:
                    value = parent_value
        except KeyError:
            pass

        return value

    def _get_attr_environment(self):
        '''
        Override for the 'tags' getattr fetcher, used from Base.
        '''
        environment = self._attributes['environment']
        parent_environment = self._get_parent_attribute('environment', extend=True)
        if parent_environment is not None:
            environment = self._extend_value(environment, parent_environment)
        return environment

    def _get_attr_any_errors_fatal(self):
        '''
        Override for the 'tags' getattr fetcher, used from Base.
        '''
        return self._get_parent_attribute('any_errors_fatal')

