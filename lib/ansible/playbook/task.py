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

from __future__ import annotations

import typing as t

from ansible import constants as C
from ansible.module_utils.common.sentinel import Sentinel
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleAssertionError, AnsibleValueOmittedError
from ansible.executor.module_common import _get_action_arg_defaults
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.parsing.mod_args import ModuleArgsParser, RAW_PARAM_MODULES
from ansible.plugins.action import ActionBase
from ansible.plugins.loader import action_loader, module_loader, lookup_loader
from ansible.playbook.attribute import NonInheritableFieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.block import Block
from ansible.playbook.collectionsearch import CollectionSearch
from ansible.playbook.conditional import Conditional
from ansible.playbook.delegatable import Delegatable
from ansible.playbook.loop_control import LoopControl
from ansible.playbook.notifiable import Notifiable
from ansible.playbook.taggable import Taggable
from ansible._internal import _task
from ansible._internal._templating import _marker_behaviors
from ansible._internal._templating._jinja_bits import is_possibly_all_template, is_possibly_template
from ansible._internal._templating._engine import TemplateEngine, TemplateOptions
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.display import Display

from ansible.utils.vars import validate_variable_name

__all__ = ['Task']

display = Display()


class Task(Base, Conditional, Taggable, CollectionSearch, Notifiable, Delegatable):

    """
    A task is a language feature that represents a call to a module, with given arguments and other parameters.
    A handler is a subclass of a task.

    Usage:

       Task.load(datastructure) -> Task
       Task.something(...)
    """

    _post_validate_object = True

    # =================================================================================
    # ATTRIBUTES
    # load_<attribute_name> and
    # validate_<attribute_name>
    # will be used if defined
    # might be possible to define others

    # NOTE: ONLY set defaults on task attributes that are not inheritable,
    # inheritance is only triggered if the 'current value' is Sentinel,
    # default can be set at play/top level object and inheritance will take it's course.

    args = t.cast(dict, NonInheritableFieldAttribute(isa='dict', default=dict))
    action = t.cast(str, NonInheritableFieldAttribute(isa='string'))

    async_val = NonInheritableFieldAttribute(isa='int', default=0, alias='async')
    changed_when = NonInheritableFieldAttribute(isa='list', default=list)
    delay = NonInheritableFieldAttribute(isa='float', default=5)
    failed_when = NonInheritableFieldAttribute(isa='list', default=list)
    loop = NonInheritableFieldAttribute(isa='list')
    loop_control = NonInheritableFieldAttribute(isa='class', class_type=LoopControl, default=LoopControl)
    poll = NonInheritableFieldAttribute(isa='int', default=C.DEFAULT_POLL_INTERVAL)
    register = NonInheritableFieldAttribute(isa='string', static=True)
    retries = NonInheritableFieldAttribute(isa='int')  # default is set in TaskExecutor
    until = NonInheritableFieldAttribute(isa='list', default=list)

    # deprecated, used to be loop and loop_args but loop has been repurposed
    loop_with = NonInheritableFieldAttribute(isa='string', private=True)

    def __init__(self, block=None, role=None, task_include=None) -> None:
        """ constructors a task, without the Task.load classmethod, it will be pretty blank """

        self._role = role
        self._parent = None
        self.implicit = False
        self._resolved_action: str | None = None

        if task_include:
            self._parent = task_include
        else:
            self._parent = block

        super(Task, self).__init__()

    _resolved_action_warning = (
        "A plugin is sampling the task's resolved_action when it is not resolved. "
        "This can be caused by callback plugins using the resolved_action attribute too "
        "early (such as in v2_playbook_on_task_start for a task using the action/local_action "
        "keyword), or too late (such as in v2_runner_on_ok for a task with a loop). "
        "To maximize compatibility with user features, callback plugins should "
        "only use this attribute in v2_runner_on_ok/v2_runner_on_failed for tasks "
        "without a loop, and v2_runner_item_on_ok/v2_runner_item_on_failed otherwise."
    )

    @property
    def resolved_action(self) -> str | None:
        """The templated and resolved FQCN of the task action or None.

        If the action is a template, callback plugins can only use this value in certain methods.
        - v2_runner_on_ok and v2_runner_on_failed if there's no task loop
        - v2_runner_item_on_ok and v2_runner_item_on_failed if there is a task loop
        """
        # Consider deprecating this because it's difficult to use?
        # Moving it to the task result would improve the no-loop limitation on v2_runner_on_ok
        # but then wouldn't be accessible to v2_playbook_on_task_start, *_on_skipped, etc.
        if self._resolved_action is not None:
            return self._resolved_action
        if not is_possibly_template(self.action):
            try:
                return self._resolve_action(self.action)
            except AnsibleParserError:
                display.warning(self._resolved_action_warning, obj=self.action)
        else:
            display.warning(self._resolved_action_warning, obj=self.action)
        return None

    def get_name(self, include_role_fqcn=True):
        """ return the name of the task """

        if self._role:
            role_name = self._role.get_name(include_role_fqcn=include_role_fqcn)

        if self._role and self.name:
            return "%s : %s" % (role_name, self.name)
        elif self.name:
            return self.name
        else:
            if self._role:
                return "%s : %s" % (role_name, self.action)
            else:
                return "%s" % (self.action,)

    def _merge_kv(self, ds):
        if ds is None:
            return ""
        elif isinstance(ds, str):
            return ds
        elif isinstance(ds, dict):
            buf = ""
            for (k, v) in ds.items():
                if k.startswith('_'):
                    continue
                buf = buf + "%s=%s " % (k, v)
            buf = buf.strip()
            return buf

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):
        task = Task(block=block, role=role, task_include=task_include)
        return task.load_data(data, variable_manager=variable_manager, loader=loader)

    def _post_validate_module_defaults(self, attr: str, value: t.Any, templar: TemplateEngine) -> t.Any:
        """Override module_defaults post validation to disable templating, which is handled by args post validation."""
        return value

    def _post_validate_args(self, attr: str, value: t.Any, templar: TemplateEngine) -> dict[str, t.Any]:
        try:
            self.action = templar.template(self.action)
        except AnsibleValueOmittedError:
            # some strategies may trigger this error when templating task.action, but backstop here if not
            raise AnsibleParserError("Omit is not valid for the `action` keyword.", obj=self.action) from None

        action_context = action_loader.get_with_context(self.action, collection_list=self.collections, class_only=True)

        if not action_context.plugin_load_context.resolved:
            module_or_action_context = module_loader.find_plugin_with_context(self.action, collection_list=self.collections)

            if not module_or_action_context.resolved:
                raise AnsibleError(f"Cannot resolve {self.action!r} to an action or module.", obj=self.action)

            action_context = action_loader.get_with_context('ansible.legacy.normal', collection_list=self.collections, class_only=True)
        else:
            module_or_action_context = action_context.plugin_load_context

        self._resolved_action = module_or_action_context.resolved_fqcn

        action_type: type[ActionBase] = action_context.object

        vp = value.pop('_variable_params', None)

        supports_raw_params = action_type.supports_raw_params or module_or_action_context.resolved_fqcn in RAW_PARAM_MODULES

        if supports_raw_params:
            raw_params_to_finalize = None
        else:
            raw_params_to_finalize = value.pop('_raw_params', None)  # always str or None

            # TaskArgsFinalizer performs more thorough type checking, but this provides a friendlier error message for a subset of detected cases.
            if raw_params_to_finalize and not is_possibly_all_template(raw_params_to_finalize):
                raise AnsibleError(f'Action {module_or_action_context.resolved_fqcn!r} does not support raw params.', obj=self.action)

        args_finalizer = _task.TaskArgsFinalizer(
            _get_action_arg_defaults(module_or_action_context.resolved_fqcn, self, templar),
            vp,
            raw_params_to_finalize,
            value,
            templar=templar,
        )

        try:
            with action_type.get_finalize_task_args_context() as finalize_context:
                args = args_finalizer.finalize(action_type.finalize_task_arg, context=finalize_context)
        except Exception as ex:
            raise AnsibleError(f'Finalization of task args for {module_or_action_context.resolved_fqcn!r} failed.', obj=self.action) from ex

        if self._origin:
            args = self._origin.tag(args)

        return args

    def _get_meta(self) -> str | None:
        # FUTURE: validate meta and return an enum instead of a str
        # meta currently does not support being templated, so we can cheat
        if self.action in C._ACTION_META:
            return self.args.get('_raw_params')

        return None

    def __repr__(self):
        """ returns a human-readable representation of the task """
        if meta := self._get_meta():
            return f"TASK: meta ({meta})"
        else:
            return "TASK: %s" % self.get_name()

    def _preprocess_with_loop(self, ds, new_ds, k, v):
        """ take a lookup plugin name and store it correctly """

        loop_name = k.removeprefix("with_")
        if new_ds.get('loop') is not None or new_ds.get('loop_with') is not None:
            raise AnsibleError("duplicate loop in task: %s" % loop_name, obj=ds)
        if v is None:
            raise AnsibleError("you must specify a value when using %s" % k, obj=ds)
        new_ds['loop_with'] = loop_name
        new_ds['loop'] = v

    def preprocess_data(self, ds):
        """
        tasks are especially complex arguments so need pre-processing.
        keep it short.
        """

        if not isinstance(ds, dict):
            raise AnsibleAssertionError('ds (%s) should be a dict but was a %s' % (ds, type(ds)))

        # the new, cleaned datastructure, which will have legacy items reduced to a standard structure suitable for the
        # attributes of the task class; copy any tagged data to preserve things like origin
        new_ds = AnsibleTagHelper.tag_copy(ds, {})

        # since this affects the task action parsing, we have to resolve in preprocess instead of in typical validator
        default_collection = AnsibleCollectionConfig.default_collection

        collections_list = ds.get('collections')
        if collections_list is None:
            # use the parent value if our ds doesn't define it
            collections_list = self.collections
        else:
            # Validate this untemplated field early on to guarantee we are dealing with a list.
            # This is also done in CollectionSearch._load_collections() but this runs before that call.
            collections_list = self.get_validated_value('collections', self.fattributes.get('collections'), collections_list, None)

        if default_collection and not self._role:  # FIXME: and not a collections role
            if collections_list:
                if default_collection not in collections_list:
                    collections_list.insert(0, default_collection)
            else:
                collections_list = [default_collection]

        if collections_list and 'ansible.builtin' not in collections_list and 'ansible.legacy' not in collections_list:
            collections_list.append('ansible.legacy')

        if collections_list:
            ds['collections'] = collections_list

        # use the args parsing class to determine the action, args,
        # and the delegate_to value from the various possible forms
        # supported as legacy
        args_parser = ModuleArgsParser(task_ds=ds, collection_list=collections_list)
        try:
            (action, args, delegate_to) = args_parser.parse()
        except AnsibleParserError as ex:
            # if the raises exception was created with obj=ds args, then it includes the detail
            # so we dont need to add it so we can just re raise.
            if ex.obj:
                raise
            # But if it wasn't, we can add the yaml object now to get more detail
            raise AnsibleParserError("Error parsing task arguments.", obj=ds) from ex

        if args_parser._resolved_action is not None:
            self._resolved_action = args_parser._resolved_action

        new_ds['action'] = action
        new_ds['args'] = args
        new_ds['delegate_to'] = delegate_to

        # we handle any 'vars' specified in the ds here, as we may
        # be adding things to them below (special handling for includes).
        # When that deprecated feature is removed, this can be too.
        if 'vars' in ds:
            # _load_vars is defined in Base, and is used to load a dictionary
            # or list of dictionaries in a standard way
            new_ds['vars'] = self._load_vars(None, ds.get('vars'))
        else:
            new_ds['vars'] = dict()

        for (k, v) in ds.items():
            if k in ('action', 'local_action', 'args', 'delegate_to') or k == action or k == 'shell':
                # we don't want to re-assign these values, which were determined by the ModuleArgsParser() above
                continue
            elif k.startswith('with_') and k.removeprefix("with_") in lookup_loader:
                # transform into loop property
                self._preprocess_with_loop(ds, new_ds, k, v)
            elif C.INVALID_TASK_ATTRIBUTE_FAILED or k in self.fattributes:
                new_ds[k] = v
            else:
                display.warning("Ignoring invalid attribute: %s" % k)

        return super(Task, self).preprocess_data(new_ds)

    def _load_loop_control(self, attr, ds):
        if not isinstance(ds, dict):
            raise AnsibleParserError(
                "the `loop_control` value must be specified as a dictionary and cannot "
                "be a variable itself (though it can contain variables)",
                obj=ds,
            )

        return LoopControl.load(data=ds, variable_manager=self._variable_manager, loader=self._loader)

    def _validate_attributes(self, ds):
        try:
            super(Task, self)._validate_attributes(ds)
        except AnsibleParserError as e:
            e.message += '\nThis error can be suppressed as a warning using the "invalid_task_attribute_failed" configuration'
            raise e

    def _validate_changed_when(self, attr, name, value):
        if not isinstance(value, list):
            setattr(self, name, [value])

    def _validate_failed_when(self, attr, name, value):
        if not isinstance(value, list):
            setattr(self, name, [value])

    def _validate_register(self, attr, name, value):
        if value is not None:
            try:
                validate_variable_name(value)
            except Exception as ex:
                raise AnsibleParserError("Invalid 'register' specified.", obj=value) from ex

    def post_validate(self, templar):
        """
        Override of base class post_validate, to also do final validation on
        the block and task include (if any) to which this task belongs.
        """

        if self._parent:
            self._parent.post_validate(templar)

        super(Task, self).post_validate(templar)

    def _post_validate_loop(self, attr, value, templar):
        """
        Override post validation for the loop field, which is templated
        specially in the TaskExecutor class when evaluating loops.
        """
        return value

    def _post_validate_name(self, attr, value, templar):
        """
        Override post-validation behavior for `name` to be best-effort for the vars available.
        Direct access via `post_validate_attribute` writes the value back to provide a stable value.
        This value is individually post-validated early by strategies for the benefit of callbacks.
        """
        with _marker_behaviors.ReplacingMarkerBehavior.warning_context() as replacing_behavior:
            self.name = templar.extend(marker_behavior=replacing_behavior).template(value, options=TemplateOptions(value_for_omit=None))

        return self.name

    def _post_validate_environment(self, attr, value, templar):
        """
        Override post validation of vars on the play, as we don't want to
        template these too early.
        """
        env = {}

        # FUTURE: kill this with fire
        def _parse_env_kv(k, v):
            try:
                env[k] = templar.template(v)
            except AnsibleValueOmittedError:
                # skip this value
                return
            except AnsibleUndefinedVariable as e:
                error = to_native(e)
                if self.action in C._ACTION_FACT_GATHERING and 'ansible_facts.env' in error or 'ansible_env' in error:
                    # ignore as fact gathering is required for 'env' facts
                    return
                raise

        # NB: the environment FieldAttribute definition ensures that value is always a list
        for env_item in value:
            if isinstance(env_item, dict):
                for k in env_item:
                    _parse_env_kv(k, env_item[k])
            else:
                try:
                    isdict = templar.template(env_item)
                except AnsibleValueOmittedError:
                    continue

                if isinstance(isdict, dict):
                    env |= isdict
                else:
                    display.warning("could not parse environment value, skipping: %s" % value)

        return env

    def _post_validate_changed_when(self, attr, value, templar):
        """
        changed_when is evaluated after the execution of the task is complete,
        and should not be templated during the regular post_validate step.
        """
        return value

    def _post_validate_failed_when(self, attr, value, templar):
        """
        failed_when is evaluated after the execution of the task is complete,
        and should not be templated during the regular post_validate step.
        """
        return value

    def _post_validate_until(self, attr, value, templar):
        """
        until is evaluated after the execution of the task is complete,
        and should not be templated during the regular post_validate step.
        """
        return value

    def get_vars(self):
        all_vars = dict()
        if self._parent:
            all_vars |= self._parent.get_vars()

        all_vars |= self.vars

        if 'tags' in all_vars:
            del all_vars['tags']
        if 'when' in all_vars:
            del all_vars['when']

        return all_vars

    def get_include_params(self):
        all_vars = dict()
        if self._parent:
            all_vars |= self._parent.get_include_params()
        if self.action in C._ACTION_ALL_INCLUDES:
            all_vars |= self.vars
        return all_vars

    def copy(self, exclude_parent: bool = False, exclude_tasks: bool = False) -> Task:
        new_me = super(Task, self).copy()

        new_me._parent = None
        if self._parent and not exclude_parent:
            new_me._parent = self._parent.copy(exclude_tasks=exclude_tasks)

        new_me._role = None
        if self._role:
            new_me._role = self._role

        new_me.implicit = self.implicit
        new_me._resolved_action = self._resolved_action
        new_me._uuid = self._uuid

        return new_me

    def set_loader(self, loader):
        """
        Sets the loader on this object and recursively on parent, child objects.
        This is used primarily after the Task has been serialized/deserialized, which
        does not preserve the loader.
        """

        self._loader = loader

        if self._parent:
            self._parent.set_loader(loader)

    def _get_parent_attribute(self, attr, omit=False):
        """
        Generic logic to get the attribute or parent attribute for a task value.
        """
        fattr = self.fattributes[attr]

        extend = fattr.extend
        prepend = fattr.prepend

        try:
            # omit self, and only get parent values
            if omit:
                value = Sentinel
            else:
                value = getattr(self, f'_{attr}', Sentinel)

            # If parent is static, we can grab attrs from the parent
            # otherwise, defer to the grandparent
            if getattr(self._parent, 'statically_loaded', True):
                _parent = self._parent
            else:
                _parent = self._parent._parent

            if _parent and (value is Sentinel or extend):
                if getattr(_parent, 'statically_loaded', True):
                    # vars are always inheritable, other attributes might not be for the parent but still should be for other ancestors
                    if attr != 'vars' and hasattr(_parent, '_get_parent_attribute'):
                        parent_value = _parent._get_parent_attribute(attr)
                    else:
                        parent_value = getattr(_parent, f'_{attr}', Sentinel)

                    if extend:
                        value = self._extend_value(value, parent_value, prepend)
                    else:
                        value = parent_value
        except KeyError:
            pass

        return value

    def all_parents_static(self):
        if self._parent:
            return self._parent.all_parents_static()
        return True

    def get_first_parent_include(self):
        from ansible.playbook.task_include import TaskInclude
        if self._parent:
            if isinstance(self._parent, TaskInclude):
                return self._parent
            return self._parent.get_first_parent_include()
        return None

    def get_play(self):
        parent = self._parent
        while not isinstance(parent, Block):
            parent = parent._parent
        return parent._play

    def dump_attrs(self):
        """Override to smuggle important non-FieldAttribute values back to the controller."""
        attrs = super().dump_attrs()
        attrs.update(_resolved_action=self._resolved_action)
        return attrs

    def from_attrs(self, attrs):
        super().from_attrs(attrs)

        # from_attrs is only used to create a finalized task
        # from attrs from the Worker/TaskExecutor
        # Those attrs are finalized and squashed in the TE
        # and controller side use needs to reflect that
        self._finalized = True
        self._squashed = True

    def _resolve_conditional(
        self,
        conditional: list[str | bool],
        variables: dict[str, t.Any],
        *,
        result_context: dict[str, t.Any] | None = None,
    ) -> bool:
        """Loops through the conditionals set on this object, returning False if any of them evaluate as such, as well as the condition that was False."""
        engine = TemplateEngine(self._loader, variables=variables)

        for item in conditional:
            if not engine.evaluate_conditional(item):
                if result_context is not None:
                    result_context.update(false_condition=item)

                return False

        return True
