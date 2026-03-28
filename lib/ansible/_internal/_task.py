from __future__ import annotations

import contextlib
import dataclasses
import enum
import functools
import types
import typing as t

from collections import abc as c

from ansible._internal import _display_utils
from ansible._internal._errors import _attribute_unavailable, _captured, _error_factory, _error_utils
from ansible._internal._templating import _engine
from ansible._internal._templating._chain_templar import ChainTemplar
from ansible._internal._worker import _inventory_rpc
from ansible._internal._datatag import _tags
from ansible.errors import AnsibleError, AnsibleTemplateError
from ansible.module_utils._internal._ambient_context import AmbientContextBase
from ansible.module_utils._internal import _dataclass_validation, _event_utils, _messages, _traceback
from ansible.module_utils.datatag import native_type_name, deprecator_from_collection_name, deprecate_value
from ansible.parsing import vault as _vault
from ansible.template import trust_as_template
from ansible.utils.display import Display
from ansible.utils import vars as _vars

if t.TYPE_CHECKING:
    from ansible.playbook.task import Task
    from ansible.inventory.host import Host
    from ansible.executor.task_executor import TaskExecutor

display = Display()

PRESERVE = frozenset(
    {
        '_ansible_no_log',
        'attempts',
        'changed',
        'deprecations',
        'exception',
        'retries',
        'warnings',
    }
)

POLYMORPHIC_RESULT_EXPRESSION = trust_as_template("_task.polymorphic_result")


class NoRecordedResultError(AnsibleError):
    """Error raised when requesting recorded results prior to any being recorded."""

    _default_message = "No task result has been recorded."


class NotALoopError(AnsibleError):
    """Error raised when attempting to access loop state when not in a loop."""

    _default_message = "The current task is not a loop."


@dataclasses.dataclass(kw_only=True, slots=True)
class CurrentTask:
    """
    Instances of this type are exposed to Jinja during register projections and playbook conditional expression eval.

    CAUTION: The shape and behavior of this type is effectively public API.
    """

    def _lazy_transform(self, value: t.Any) -> t.Any:
        """Lazily transform the given value."""
        return TaskContext.current().task_templar.template(value, lazy_options=_engine.LazyOptions.SKIP_TEMPLATES_AND_ACCESS)

    @property
    def result(self) -> c.Mapping[str, object]:
        task_ctx = TaskContext.current()

        try:
            return self._lazy_transform(task_ctx.latest_result)
        except NoRecordedResultError as ex:
            # RPFIX-5: UX: this causes multiple warnings/errors that need to be investigated, some likely from late addition of pre-task `when` projections
            # [WARNING]: An error occurred in a register expression: The _task.result property is unavailable: No task result has been recorded.
            # [WARNING]: An error occurred in a register expression: Error rendering expression: Type 'WarningSummary' is unsupported for variable storage.
            #     - shell: echo {{ item }}
            #       loop: [1,2,3]
            #       failed_when: blar.rc != 0
            #       register:
            #         blar: _task.result
            #
            #     - debug:
            #         var: blar
            # the template engine will turn this into an UndefinedMarker
            raise _attribute_unavailable.AttributeUnavailableError("The _task.result property is unavailable.") from ex

    @property
    def loop_result(self) -> c.Mapping[str, object]:
        task_ctx = TaskContext.current()

        try:
            # in-flight projections bypass the skipped conversions by setting finalize to False
            # RPFIX-5: IMPL: may need to fix Jinja's getattr/item AttributeError handling- if any code invoked beneath one of those raises AttributeError, Jinja
            #  blindly creates a new UndefinedMarker with "CurrentTask has no attr loop_result" and loses the original AttributeError detail. Repro this by
            #  tacking any bogus attr off the end of as_result_dict() here.
            return self._lazy_transform(task_ctx.build_loop_result(preview=True).as_result_dict())
        except NotALoopError as ex:
            raise _attribute_unavailable.AttributeUnavailableError("The _task.loop_result property is unavailable.") from ex

    @property
    def polymorphic_result(self) -> c.Mapping[str, object]:
        task_ctx = TaskContext.current()

        if task_ctx.has_loop_exited:
            return self._lazy_transform(task_ctx.build_loop_result().as_result_dict())

        try:
            return self._lazy_transform(task_ctx.latest_result)
        except NoRecordedResultError as ex:
            raise _attribute_unavailable.AttributeUnavailableError("The _task.polymorphic_result property is unavailable.") from ex


@dataclasses.dataclass(kw_only=True, slots=True)
class PendingChanges:
    """Changes which will be applied when the action completes, including on failure."""

    register_host_variables: dict[VariableLayer, dict[str, object]] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(kw_only=True)
class TaskContext(AmbientContextBase):
    """Ambient context that wraps task execution on workers. It provides access to the currently executing task."""

    @classmethod
    def create(cls, task: Task, task_vars: dict[str, t.Any], host_name: str) -> t.Self:
        task_vars.update(_task=CurrentTask())

        return cls(
            _task=task,
            _base_task_vars=task_vars,
            _active_task_vars=task_vars,  # starts out as a reference, but becomes a copy of _base_task_vars when starting a loop item
            _host_name=host_name,
        )

    def get_register_projections(self) -> dict[str, _engine.TemplateExpressionWrapper] | None:
        if not self._task.register:
            return None

        return {var_name: _engine.TemplateExpressionWrapper(expression=expression) for var_name, expression in self._task.register.items()}

    @functools.cached_property
    def inventory_rpc_client(self) -> _inventory_rpc.InventoryRPC:
        return _inventory_rpc.InventoryRPC.get_client()

    @property
    def host_name(self) -> str:
        return self._host_name

    @property
    def task(self) -> Task:
        return self._task

    @property
    def task_vars(self) -> dict[str, t.Any]:
        return self._active_task_vars

    @property
    def is_loop(self) -> bool:
        return self._loop_items is not None

    @property
    def has_loop_exited(self) -> bool:
        return self._has_loop_exited

    @property
    def current_item(self) -> object:
        return self._item

    @property
    def current_item_label(self) -> object:
        return self.task.loop_control.label or self.task_templar.variable_name_as_template(self._loop_var)

    _task: Task
    _base_task_vars: dict[str, t.Any]
    _active_task_vars: dict[str, t.Any]
    _host_name: str
    _registered_vars_enabled = False
    _raw_loop_results: list[UnifiedTaskResult] = dataclasses.field(default_factory=list)
    _loop_items: list[object] | None = None
    _has_loop_exited: bool = False
    _loop_var: str | None = None
    _item: object | None = None
    _item_index: int | None = None
    _index_var: str | None = None
    _loop_extended: dict[str, object] | None = None
    _templar: _engine.TemplateEngine | None = None
    _break_when_triggered: bool = False
    _inventory_rpc_client: _inventory_rpc.InventoryRPC | None = None

    pending_changes: PendingChanges | None = None
    """Pending changes which will be applied only if the current task succeeds."""

    @contextlib.contextmanager
    def loop_item_context(self, te: TaskExecutor) -> t.Generator[None]:
        original_task = self.task
        original_play_context = te._play_context

        loop_item_task = self.task.copy(exclude_parent=True, exclude_tasks=True)
        loop_item_task._parent = self.task._parent
        loop_item_play_context = te._play_context.copy()

        self._task = loop_item_task
        te._play_context = loop_item_play_context

        try:
            yield
        finally:
            self._task = original_task
            te._play_context = original_play_context

    def start_loop(self) -> t.Generator[tuple[int, object]]:
        self._loop_var = loop_var = t.cast(str, self.task.loop_control.loop_var)
        self._index_var = index_var = t.cast(str, self.task.loop_control.index_var)

        extended = t.cast(bool, self.task.loop_control.extended)
        extended_allitems = t.cast(bool, self.task.loop_control.extended_allitems)

        items = self._loop_items
        items_len = len(items)

        for item_index, item in enumerate(self._loop_items):
            self._active_task_vars = self._base_task_vars.copy()  # isolate changes to task vars between loop items
            self._templar = None  # we're changing the values used to calculate the templar, null it out so the next requester re-creates it

            self._item = item
            self._item_index = item_index

            loop_vars: dict[str, object] = dict(
                ansible_loop_var=loop_var,
            )

            loop_vars[loop_var] = item

            if index_var:
                loop_vars['ansible_index_var'] = index_var
                loop_vars[index_var] = item_index

            if extended:
                ansible_loop: dict[str, object] = {
                    'index': item_index + 1,
                    'index0': item_index,
                    'first': item_index == 0,
                    'last': item_index + 1 == items_len,
                    'length': items_len,
                    'revindex': items_len - item_index,
                    'revindex0': items_len - item_index - 1,
                }

                if extended_allitems:
                    ansible_loop['allitems'] = items

                try:
                    ansible_loop['nextitem'] = items[item_index + 1]
                except IndexError:
                    pass

                if item_index - 1 >= 0:
                    ansible_loop['previtem'] = items[item_index - 1]

                self._loop_extended = loop_vars['ansible_loop'] = ansible_loop

            self.task_vars.update(loop_vars)

            yield item_index, item

            if self._break_when_triggered:
                break

        self._has_loop_exited = True

    @property
    def task_templar(self) -> _engine.TemplateEngine:
        if not self._templar:
            self._templar = _engine.TemplateEngine(loader=self.task._loader, variables=self.task_vars)

        return self._templar

    @property
    def latest_result(self) -> c.MutableMapping[str, object]:
        if not self._raw_loop_results:
            raise NoRecordedResultError()

        return self._raw_loop_results[-1].as_result_dict()

    def _record_result(self, utr: UnifiedTaskResult) -> None:
        # CAUTION: This method can be called *before* start_loop when validation errors occur.
        #          That results in various instance attributes not being set.
        #          It also means that `self.task.loop_control` may have invalid values.

        self._enable_registered_vars()

        if isinstance(self.task.ignore_errors, bool):
            # HACK: avoid setting to True due to template failures -- this should go away once field attribute templating is fixed
            utr.ignore_errors = self.task.ignore_errors

        if isinstance(self.task.ignore_unreachable, bool):
            # HACK: avoid setting to True due to template failures -- this should go away once field attribute templating is fixed
            utr.ignore_unreachable = self.task.ignore_unreachable

        # _item_index will be None if start_loop was not called due to a field attribute error
        if not TaskContext.current().is_loop or self._item_index is None:
            self._raw_loop_results.clear()
            self._raw_loop_results.append(utr)

            return

        if TaskContext.current().has_loop_exited:
            return

        # now update the result with the item info, and append the result
        # to the list of results
        utr.loop_item = self._item
        utr.loop_var = self._loop_var
        utr.loop_extended = self._loop_extended

        if self._index_var:
            utr.loop_index = self._item_index
            utr.loop_index_var = self._index_var

        item_index = self._item_index
        result_count = len(self._raw_loop_results)

        if item_index == result_count:
            self._raw_loop_results.append(utr)  # add new result
        elif item_index + 1 == result_count:
            self._raw_loop_results[item_index] = utr  # replace existing result
        else:
            raise RuntimeError(f'Item index {item_index} does not match {result_count}.')

        self._populate_item_label(utr)

    def _populate_item_label(self, utr: UnifiedTaskResult) -> None:
        # gets templated here unlike rest of loop_control fields, depends on loop_var above
        item_label: object = ...

        if item_label_template := self.task.loop_control.label:
            try:
                item_label = self.task_templar.template(item_label_template)
            except AnsibleTemplateError as ex:
                display.error_as_warning('Failed to template loop_control label.', ex, obj=item_label_template)

        if item_label is ...:
            if self._loop_var is None:
                # _loop_var will be None if start_loop was not called due to a field attribute error (even if the error is for another field)
                item_label = ''
            else:
                item_label = self.task_templar.resolve_variable_expression(self._loop_var)

        utr.loop_item_label = item_label

    def build_loop_result(self, preview: bool = False) -> UnifiedTaskResult:
        if not self.is_loop:
            raise NotALoopError()

        if not preview and (self._item_index is None or len(self._raw_loop_results) not in (self._item_index, self._item_index + 1)):
            # RPFIX-9: FUTURE: can we ditch preview while retaining this safety check?
            # Loop results can be queried before or after loop results are recorded, so we need to accept a range of results.
            raise RuntimeError(f"Mismatch between item index {self._item_index} and loop result count {len(self._raw_loop_results)}.")

        # create the overall result item
        utr = UnifiedTaskResult.from_action_result_dict()
        utr.loop_results = self._raw_loop_results

        # RPFIX-5: IMPL: all the fields set in this loop could be converted to properties
        for item in self._raw_loop_results:
            if item.no_log:
                utr.no_log = True  # ensure no_log processing recognizes at least one item needs to be censored

            utr._extend_warnings(item.warnings)
            utr._extend_deprecations(item.deprecations)

        if all(item.skipped for item in self._raw_loop_results):
            utr.set_skipped()
            utr.msg = 'All items skipped'
        elif utr.failed:
            utr.msg = 'One or more items failed'
        else:
            utr.msg = 'All items completed'

        return utr

    def update_task_vars(self, variables: dict[str, t.Any]) -> None:
        """Update task variables for both the active task and, in the case of loops, subsequent tasks."""
        for key, value in variables.items():
            self._base_task_vars[key] = self._active_task_vars[key] = value

    def _enable_registered_vars(self) -> None:
        """
        Inject registered variable expressions into task vars.
        This needs to be done one time after the action handler runs, or if a task results in no action running.
        Unlike other modifications to task vars, these changes will be persisted between loop items.
        """
        if self._registered_vars_enabled:
            return

        if register_projections := self.get_register_projections():
            self.update_task_vars(register_projections)

        self._registered_vars_enabled = True


TaskArgsFinalizerCallback = t.Callable[[str, t.Any, _engine.TemplateEngine, t.Any], t.Any]
"""Type alias for the shape of the `ActionBase.finalize_task_arg` method."""


class TaskArgsChainTemplar(ChainTemplar):
    """
    A ChainTemplar that carries a user-provided context object, optionally provided by `ActionBase.get_finalize_task_args_context`.
    TaskArgsFinalizer provides the context to each `ActionBase.finalize_task_arg` call to allow for more complex/stateful customization.
    """

    def __init__(self, *sources: c.Mapping, templar: _engine.TemplateEngine, callback: TaskArgsFinalizerCallback, context: t.Any) -> None:
        super().__init__(*sources, templar=templar)

        self.callback = callback
        self.context = context

    def template(self, key: t.Any, value: t.Any) -> t.Any:
        return self.callback(key, value, self.templar, self.context)


class TaskArgsFinalizer:
    """Invoked during task args finalization; allows actions to override default arg processing (e.g., templating)."""

    def __init__(self, *args: c.Mapping[str, t.Any] | str | None, templar: _engine.TemplateEngine) -> None:
        self._args_layers = [arg for arg in args if arg is not None]
        self._templar = templar

    def finalize(self, callback: TaskArgsFinalizerCallback, context: t.Any) -> dict[str, t.Any]:
        from ansible import constants

        resolved_layers: list[c.Mapping[str, t.Any]] = []

        for layer in self._args_layers:
            if isinstance(layer, (str, _vault.EncryptedString)):  # EncryptedString can hide a template
                if constants.config.get_config_value('INJECT_FACTS_AS_VARS'):
                    display.warning(
                        "Using a template for task args is unsafe in some situations "
                        "(see https://docs.ansible.com/ansible/devel/reference_appendices/faq.html#argsplat-unsafe).",
                        obj=layer,
                    )

                resolved_layer = self._templar.resolve_to_container(layer, options=_engine.TemplateOptions(value_for_omit={}))
            else:
                resolved_layer = layer

            if not isinstance(resolved_layer, dict):
                raise AnsibleError(f'Task args must resolve to a {native_type_name(dict)!r} not {native_type_name(resolved_layer)!r}.', obj=layer)

            resolved_layers.append(resolved_layer)

        ct = TaskArgsChainTemplar(*reversed(resolved_layers), templar=self._templar, callback=callback, context=context)

        return ct.as_dict()


class Source(enum.Enum):
    ACTION = enum.auto()
    ANY = enum.auto()


class Destination(enum.Enum):
    CALLBACK = enum.auto()
    NOT_CALLBACK = enum.auto()
    ANY = enum.auto()


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class FieldSettings:
    key: str | None = None
    source: Source | None = None
    destination: Destination | None = None
    conversion_func: t.Callable[[object], object] | None = None


_type = type


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class ResolvedField:
    name: str
    type: type
    optional: bool
    field: dataclasses.Field | None
    metadata: FieldSettings

    @classmethod
    def from_field(cls, type_hints: dict[str, t.Any], metadata: FieldSettings, dc_field: dataclasses.Field) -> t.Self:
        resolved_type = type_hints[dc_field.name]

        if isinstance(resolved_type, types.UnionType):
            args = resolved_type.__args__

            if len(args) == 2 and args[0] is types.NoneType:
                resolved_type = args[1]
                optional = True
            elif len(args) == 2 and args[1] is types.NoneType:
                resolved_type = args[0]
                optional = True
            else:
                raise NotImplementedError(f"Unexpected union type args: {args}")
        else:
            optional = False

        if isinstance(resolved_type, types.GenericAlias):
            resolved_type = t.get_origin(resolved_type)
        elif (orig_bases := types.get_original_bases(resolved_type)) and orig_bases[0] is t.TypedDict:
            resolved_type = dict

        return cls(
            name=dc_field.name,
            type=resolved_type,
            optional=optional,
            field=dc_field,
            metadata=metadata,
        )

    @property
    def result_key(self) -> str:
        return self.metadata.key or self.name


def export_only(
    key: str | None = None,
    *,
    destination: Destination = Destination.ANY,
    conversion_func: t.Callable[[object], object] | None = None,
) -> dict[str, t.Any]:
    return field(
        key,
        source=None,
        destination=destination,
        conversion_func=conversion_func,
    )


def import_export(
    key: str | None = None,
    *,
    source: Source = Source.ANY,
    destination: Destination = Destination.ANY,
    conversion_func: t.Callable[[object], object] | None = None,
) -> dict[str, t.Any]:
    return field(
        key,
        source=source,
        destination=destination,
        conversion_func=conversion_func,
    )


def field(
    key: str | None = None,
    *,
    source: Source | None = None,
    destination: Destination | None = None,
    conversion_func: t.Callable[[object], object] | None = None,
) -> dict[str, t.Any]:
    return dict(
        ansible=FieldSettings(
            key=key,
            source=source,
            destination=destination,
            conversion_func=conversion_func,
        )
    )


_DEFAULT_FIELD_SETTINGS = FieldSettings()


def _convert_no_log(value: object) -> bool:
    if not isinstance(value, bool):
        # RPFIX-5: UX: do we want to keep any kind of custom warning regarding this value always being True when not a bool?
        # display.warning(f'Invalid _ansible_no_log value of type {type(value).__name__!r} in task result, output will be masked.')
        value = True

    return value


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class AddHost:
    host_name: str
    host_vars: dict[str, object] | None = None
    parent_group_names: list[str] | None = None

    def __post_init__(self): ...

    @classmethod
    def from_dict(cls, value: object) -> AddHost | None:
        if isinstance(value, dict):
            if groups := value.pop('groups'):
                value['parent_group_names'] = groups

            try:
                return cls(**value)
            except Exception as ex:
                display.error_as_warning('Ignoring invalid add_host value in task result.', exception=ex)

        return None


_dataclass_validation.inject_post_init_validation(AddHost, allow_subclasses=True)


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class AddGroup:
    group_name: str
    parent_group_names: list[str]

    def __post_init__(self): ...


_dataclass_validation.inject_post_init_validation(AddGroup, allow_subclasses=True)


class StatsDict(t.TypedDict):
    data: dict[str, object]
    per_host: t.NotRequired[object | None]  # really bool, but no validation
    aggregate: t.NotRequired[object | None]  # really bool, but no validation


def _convert_stats(value: t.Any) -> StatsDict | None:
    if not isinstance(value, dict) or not isinstance(value.get('data'), dict):
        display.warning('Ignoring invalid ansible_stats value in task result.')
        value = None

    return value


def _convert_warnings(value: object) -> list[_messages.WarningSummary] | None:
    if not value:
        return None

    if not isinstance(value, list):
        display.warning(f"Task result `warnings` was {native_type_name(value)} instead of {native_type_name(list)} and has been discarded.")
        return None

    warnings: list[_messages.WarningSummary] = []

    for warning in value:
        if not isinstance(warning, _messages.WarningSummary):
            # translate non-WarningMessageDetail messages
            warning = _messages.WarningSummary(
                event=_messages.Event(
                    msg=str(warning),
                ),
            )

        if warning_ctx := _display_utils.DeferredWarningContext.current(optional=True):
            warning_ctx.capture(warning)
        else:
            warnings.append(warning)

    return warnings


def _convert_deprecations(value: object) -> list[_messages.DeprecationSummary] | None:
    if not value:
        return None

    if not isinstance(value, list):
        display.warning(f"Task result `deprecations` was {native_type_name(value)} instead of {native_type_name(list)} and has been discarded.")
        return None

    deprecations: list[_messages.DeprecationSummary] = []

    for deprecation in value:
        if not isinstance(deprecation, _messages.DeprecationSummary):
            # translate non-DeprecationSummary message dicts
            try:
                if (collection_name := deprecation.pop('collection_name', ...)) is not ...:
                    # deprecated: description='enable the deprecation message for collection_name' core_version='2.23'
                    # CAUTION: This deprecation cannot be enabled until the replacement (deprecator) has been documented, and the schema finalized.
                    # self.deprecated('The `collection_name` key in the `deprecations` dictionary is deprecated.', version='2.27')
                    deprecation.update(deprecator=deprecator_from_collection_name(collection_name))

                deprecation = _messages.DeprecationSummary(
                    event=_messages.Event(
                        msg=deprecation.pop('msg'),
                    ),
                    **deprecation,
                )
            except Exception as ex:
                display.error_as_warning("Task result `deprecations` contained an invalid item.", exception=ex)

        if warning_ctx := _display_utils.DeferredWarningContext.current(optional=True):
            warning_ctx.capture(deprecation)
        else:
            deprecations.append(deprecation)

    return deprecations


DROP_AND_WARN = ResolvedField(name='__drop__', type=str, optional=True, field=None, metadata=FieldSettings())


class VariableLayer(enum.IntEnum):
    """
    Variable layer at which variables are registered.

    CAUTION: This enum is exposed as public API in ActionBase.
    """

    # IMPORTANT: The order of these enum values determines the order in which they will be applied to variable manager.
    #            This matters for precedence of layers for which variable manager does not independently track.

    CACHEABLE_FACT = enum.auto()
    INCLUDE_VARS = enum.auto()
    EPHEMERAL_FACT = enum.auto()
    REGISTER_VARS = enum.auto()


@dataclasses.dataclass(kw_only=True, slots=True)
class UnifiedTaskResult:
    _changed: bool | None = dataclasses.field(default=None, metadata=import_export("changed"))

    @property
    def changed(self) -> bool:
        if self._changed is not None or self.loop_results is None:
            return bool(self._changed)

        return any(loop_result.changed for loop_result in self.loop_results)

    @changed.setter
    def changed(self, value: bool) -> None:
        self._changed = value

    _failed: bool | None = dataclasses.field(default=None, metadata=import_export("failed", destination=Destination.NOT_CALLBACK))

    @property
    def failed(self) -> bool:
        if self._failed is None and self.rc is not None and self.rc != 0:
            return True

        if self.failed_when_result is not None:
            return bool(self.failed_when_result)

        if self.loop_results and any(loop_result.failed_when_result is not None for loop_result in self.loop_results):
            return any(loop_result.failed_when_result for loop_result in self.loop_results)

        if self._failed is not None or self.loop_results is None:
            return bool(self._failed)

        return any(loop_result.failed for loop_result in self.loop_results)

    @failed.setter
    def failed(self, value: bool) -> None:
        self._failed = value

    _unreachable: bool | None = dataclasses.field(default=None, metadata=import_export("unreachable"))

    @property
    def unreachable(self) -> bool | None:
        if self._unreachable is not None or self.loop_results is None:
            result = bool(self._unreachable)
        else:
            result = any(loop_result.unreachable for loop_result in self.loop_results)

        return result or None

    @unreachable.setter
    def unreachable(self, value: bool) -> None:
        self._unreachable = value

    _skipped: bool | None = dataclasses.field(default=None, metadata=import_export("skipped", destination=Destination.NOT_CALLBACK))

    @property
    def skipped(self) -> bool | None:
        if self._skipped is not None or self.loop_results is None:
            result = bool(self._skipped)
        else:
            # Loop tasks are only considered skipped if all items were skipped.
            result = all(loop_result.skipped for loop_result in self.loop_results)

        return result or None

    @skipped.setter
    def skipped(self, value: bool) -> None:
        self._skipped = value

    _ignore_errors: bool = False  # formerly _ansible_ignore_errors

    @property
    def ignore_errors(self) -> bool:
        return self._ignore_errors if self.loop_results is None else any(loop_result._ignore_errors for loop_result in self.loop_results)

    @ignore_errors.setter
    def ignore_errors(self, value: bool) -> None:
        self._ignore_errors = value

    _ignore_unreachable: bool = False  # formerly _ansible_ignore_unreachable

    @property
    def ignore_unreachable(self) -> bool:
        return self._ignore_unreachable if self.loop_results is None else any(loop_result._ignore_unreachable for loop_result in self.loop_results)

    @ignore_unreachable.setter
    def ignore_unreachable(self, value: bool) -> None:
        self._ignore_unreachable = value

    _warnings: list[_messages.WarningSummary] | None = dataclasses.field(
        default=None,
        metadata=import_export("warnings", conversion_func=_convert_warnings),
    )

    @property
    def warnings(self) -> list[_messages.WarningSummary] | None:
        if (current_warnings := self._warnings) is None and (warning_ctx := _display_utils.DeferredWarningContext.current(optional=True)):
            current_warnings = warning_ctx.get_warnings()

        return current_warnings

    _deprecations: list[_messages.DeprecationSummary] | None = dataclasses.field(
        default=None,
        metadata=import_export("deprecations", conversion_func=_convert_deprecations),
    )

    @property
    def deprecations(self) -> list[_messages.DeprecationSummary] | None:
        if (current_deprecations := self._deprecations) is None and (warning_ctx := _display_utils.DeferredWarningContext.current(optional=True)):
            current_deprecations = warning_ctx.get_deprecation_warnings()

        return current_deprecations

    ansible_facts: dict[str, t.Any] | None = dataclasses.field(default=None, metadata=import_export())
    async_result: dict[str, t.Any] | None = dataclasses.field(default=None, metadata=export_only())
    ansible_parsed: bool | None = None  # formerly _ansible_parsed
    invocation: dict[str, t.Any] | None = dataclasses.field(default=None, metadata=import_export(destination=Destination.CALLBACK))
    exception: _messages.ErrorSummary | None = dataclasses.field(default=None, metadata=import_export())
    finished: bool | None = dataclasses.field(default=None, metadata=import_export())
    msg: object | None = dataclasses.field(default=None, metadata=import_export())
    no_log: bool | None = dataclasses.field(
        default=None, metadata=import_export("_ansible_no_log", conversion_func=_convert_no_log, source=Source.ACTION, destination=Destination.CALLBACK)
    )
    verbose_always: bool | None = dataclasses.field(
        default=None, metadata=import_export("_ansible_verbose_always", source=Source.ACTION, destination=Destination.CALLBACK)
    )
    verbose_override: bool | None = dataclasses.field(
        default=None, metadata=import_export("_ansible_verbose_override", source=Source.ACTION, destination=Destination.CALLBACK)
    )
    rc: int | None = dataclasses.field(default=None, metadata=import_export())
    suppress_tmpdir_delete: bool | None = dataclasses.field(default=None, metadata=field("_ansible_suppress_tmpdir_delete", source=Source.ANY))
    module_stderr: str | None = dataclasses.field(default=None, metadata=export_only())
    module_stdout: str | None = dataclasses.field(default=None, metadata=export_only())
    result_data: dict[str, object] = dataclasses.field(default_factory=dict)
    is_module: bool
    attempts: int | None = dataclasses.field(default=None, metadata=export_only())
    retries: int | None = dataclasses.field(default=None, metadata=export_only())
    notify: list[str] = dataclasses.field(default_factory=list)
    delegated_host: str | None = None
    callback_delegated_vars_subset: dict[str, object] | None = dataclasses.field(
        default=None, metadata=export_only("_ansible_delegated_vars", destination=Destination.CALLBACK)
    )
    diff: object | None = dataclasses.field(default=None, metadata=import_export())  # RPFIX-9: FUTURE: validation with custom conversion func
    pending_changes: PendingChanges = dataclasses.field(default_factory=PendingChanges)
    """Changes which will be applied when the action completes, including on failure."""
    stats: StatsDict | None = dataclasses.field(default=None, metadata=import_export('ansible_stats', conversion_func=_convert_stats))
    async_job_id: str | None = dataclasses.field(default=None, metadata=import_export('ansible_job_id'))
    include_file: str | None = None
    include_args: dict[str, object] | None = None  # RPFIX-9: FUTURE: make this a dataclass
    registered_values: c.Mapping[str, object] | None = None
    """Values to register unconditionally, including on failure or when skipped."""

    skip_reason: str | None = dataclasses.field(default=None, metadata=export_only())
    skipped_reason: str | None = dataclasses.field(default=None, metadata=export_only())
    """The `skipped_reason` field is deprecated. Use `skip_reason` instead."""

    false_condition: object | None = dataclasses.field(default=None, metadata=export_only())

    changed_when_result: object | None = dataclasses.field(default=None, metadata=export_only())  # RPFIX-9: FUTURE: `bool | str` once validator supports that
    failed_when_result: object | None = dataclasses.field(default=None, metadata=export_only())  # RPFIX-9: FUTURE: `bool | str` once validator supports that
    break_when_result: object | None = dataclasses.field(default=None, metadata=export_only())  # RPFIX-9: FUTURE: `bool | str` once validator supports that

    changed_when_suppressed_exception: _messages.ErrorSummary | None = dataclasses.field(default=None, metadata=export_only())
    failed_when_suppressed_exception: _messages.ErrorSummary | None = dataclasses.field(default=None, metadata=export_only())
    break_when_suppressed_exception: _messages.ErrorSummary | None = dataclasses.field(default=None, metadata=export_only())

    loop_var: str | None = dataclasses.field(default=None, metadata=export_only('ansible_loop_var'))
    loop_index_var: str | None = dataclasses.field(default=None, metadata=export_only('ansible_index_var'))
    loop_item_label: object | None = dataclasses.field(default=None, metadata=export_only('_ansible_item_label', destination=Destination.CALLBACK))
    loop_item: object | None = dataclasses.field(default=None, metadata=export_only())  # exported as self.loop_var value
    loop_index: object | None = dataclasses.field(default=None, metadata=export_only())  # exported as self.loop_index_var value
    loop_extended: dict[str, object] | None = dataclasses.field(default=None, metadata=export_only('ansible_loop'))
    loop_results: list[t.Self] | None = None

    @classmethod
    @functools.cache
    def get_result_key_to_resolved_field_mapping(cls, source_is_module: bool) -> dict[str, ResolvedField]:
        mapping = {}
        type_hints = t.get_type_hints(cls)

        for dc_field in dataclasses.fields(cls):
            metadata = t.cast(FieldSettings, dc_field.metadata.get('ansible', _DEFAULT_FIELD_SETTINGS))
            resolved_field = ResolvedField.from_field(type_hints, metadata, dc_field)

            if metadata.source is Source.ACTION and source_is_module:
                mapping[resolved_field.result_key] = DROP_AND_WARN
            elif metadata.source is Source.ACTION or metadata.source is Source.ANY:
                mapping[resolved_field.result_key] = resolved_field

        return mapping

    @classmethod
    @functools.cache
    def _get_field_name_to_result_key_mapping(cls, *, for_callback: bool, for_round_trip: bool) -> dict[str, str]:
        mapping = {}

        for dc_field in dataclasses.fields(cls):
            metadata = t.cast(FieldSettings, dc_field.metadata.get('ansible', _DEFAULT_FIELD_SETTINGS))

            if (
                metadata.destination is Destination.ANY
                or ((for_round_trip or for_callback) and metadata.destination is Destination.CALLBACK)
                or ((for_round_trip or not for_callback) and metadata.destination is Destination.NOT_CALLBACK)
            ):
                key = metadata.key or dc_field.name
                field_name = key if hasattr(cls, key) else dc_field.name  # properties matching the exported key take precedence over the field during export

                mapping[field_name] = key

        return mapping

    @classmethod
    def from_action_result_dict(cls, result: dict[str, object] | None = None) -> t.Self:
        return cls._from_result_dict(result or {}, source_is_module=False)

    @classmethod
    def _from_result_dict(cls, result: dict[str, object], source_is_module: bool) -> t.Self:
        if not isinstance(result, dict):
            raise TypeError(f'Malformed result. Received {type(result)} instead of {dict}.')

        fields = cls.get_result_key_to_resolved_field_mapping(source_is_module=source_is_module)
        result_data: dict[str, object] = {}
        kwargs: dict[str, t.Any] = dict(
            result_data=result_data,
        )

        for key, value in result.items():
            if resolved_field := fields.get(key):
                if resolved_field is DROP_AND_WARN:
                    display.warning(f"Removed reserved key {key!r} from module result.", obj=value)
                else:
                    kwargs[resolved_field.name] = cls.convert_field(resolved_field, value)
            elif source_is_module and key.startswith('_ansible_'):
                display.warning(f"Removed reserved key {key!r} from module result.", obj=value)
            else:
                result_data[key] = value

        return cls(is_module=source_is_module, **kwargs)

    def _result_key_magic(self, key: str) -> str:
        match key:
            case "loop_item":
                return self.loop_var or 'item'  # RPFIX-9: FUTURE: centralize the default logic

            case "loop_index":
                return self.loop_index_var

            case _:
                return key

    def as_result_dict(self, *, for_callback: bool = False, for_round_trip: bool = False, censor_callback_result: bool = False) -> dict[str, object]:
        result: dict[str, t.Any] = {
            self._result_key_magic(result_key): value
            for field_name, result_key in self._get_field_name_to_result_key_mapping(for_callback=for_callback, for_round_trip=for_round_trip).items()
            if (value := getattr(self, field_name)) is not None
        }

        result.update(self.result_data)

        # RPFIX-5: IMPL: is this where we want stdout/stderr handling?
        # pre-split stdout/stderr into lines if needed

        if 'stdout' in result and 'stdout_lines' not in result:
            # if the value is 'False', a default won't catch it.
            txt = result.get('stdout', None) or ''
            result.update(stdout_lines=txt.splitlines())

        if 'stderr' in result and 'stderr_lines' not in result:
            # if the value is 'False', a default won't catch it.
            txt = result.get('stderr', None) or ''
            result.update(stderr_lines=txt.splitlines())

        if for_callback:
            if censor_callback_result:
                result = {key: value for key in PRESERVE if (value := result.get(key, ...)) is not ...}
                result.update(censored="the output has been hidden due to the fact that 'no_log: true' was specified for this result")

        if self.loop_results is not None:
            # loop results need to be added after censor_result on the outer result since it's currently naive about whether it's looking at a loop item or not
            result.update(
                results=[
                    loop_result.as_result_dict(
                        for_callback=for_callback,
                        for_round_trip=for_round_trip,
                        censor_callback_result=censor_callback_result or loop_result.no_log,
                    )
                    for loop_result in self.loop_results
                ]
            )

        if for_callback:
            result = _vars.transform_to_native_types(result)

        return result

    def finalize_registered_values(self) -> None:
        task_ctx = TaskContext.current()

        if not (register_projections := task_ctx.get_register_projections()):
            return

        registered_values = {}
        registered_errors = []

        for var_name, expression in register_projections.items():
            try:
                registered_values[var_name] = task_ctx.task_templar.template(expression)
            except Exception as ex:
                event = _error_factory.ControllerEventFactory.from_exception(ex, False)
                event_message = _event_utils.format_event_brief_message(event)
                undef_message = f"The variable {var_name!r} is undefined because its register expression failed: {event_message}"
                undef_value = trust_as_template(f"{{{{ undef({undef_message!r}) }}}}")

                if expression_origin := _tags.Origin.get_tag(expression.expression):
                    undef_value = expression_origin.tag(undef_value)

                registered_values[var_name] = undef_value

                try:
                    raise Exception(f"Register projection {var_name!r} failed.") from ex
                except Exception as ex:
                    registered_errors.append(ex)

        # RPFIX-9: FUTURE: merge registered_values into the pending VariableLayer.REGISTER_VARS layer instead of having a separate field
        self.registered_values = registered_values

        if not registered_errors:
            return

        chain = (
            _messages.EventChain(
                msg_reason="The original task error before register failed was:",
                traceback_reason="The above exception occurred before the following exception:",
                event=self.exception.event,
            )
            if self.exception
            else None
        )

        try:
            raise ExceptionGroup(
                f"Task failed due to errors in {len(registered_errors)} out of {len(register_projections)} register projections.",
                registered_errors,
            )
        except ExceptionGroup as ex:
            event = _error_factory.ControllerEventFactory.from_exception(ex, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR))
            event = dataclasses.replace(event, chain=chain)

            self.failed = True
            self.exception = _messages.ErrorSummary(
                event=event,
            )

    def _extend_warnings(self, warnings: c.Iterable[_messages.WarningSummary] | None) -> None:
        if not warnings:
            return

        if self._warnings is None:
            self._warnings = []

        self._warnings.extend(warnings)

    def _extend_deprecations(self, deprecations: c.Iterable[_messages.DeprecationSummary]) -> None:
        if not deprecations:
            return

        if self._deprecations is None:
            self._deprecations = []

        self._deprecations.extend(deprecations)

    @classmethod
    def convert_field(cls, resolved_field: ResolvedField, value: object) -> object:
        if value is None:
            return None if resolved_field.optional else resolved_field.field.default

        if resolved_field.type is _messages.ErrorSummary:
            return value  # RPFIX-5: VALIDATION: defer conversion to __post_init__

        # RPFIX-5: VALIDATION: this doesn't handle special types like exception which require extra conversion

        if not resolved_field.metadata.conversion_func and isinstance(value, resolved_field.type):
            return value

        # RPFIX-5: VALIDATION: this type checking doesn't validate types within containers (mapping, dict, etc.)

        help_text = f"Values for result key {resolved_field.result_key!r} must be of type {native_type_name(resolved_field.type)}."

        conversion_func = resolved_field.metadata.conversion_func or resolved_field.type

        try:
            result = conversion_func(value)
        except Exception:
            result = resolved_field.field.default
            display.warning(
                f'Value for result key {resolved_field.result_key!r} of type {native_type_name(value)} was replaced with {result}.',
                obj=value,
                help_text=help_text,
            )
        else:
            if not isinstance(value, resolved_field.type):
                # RPFIX-5: UX: this will still give duplicate warnings -- probably just need to be explicit and have conversion funcs do warnings
                display.warning(
                    msg=f'Value for result key {resolved_field.result_key!r} of type {native_type_name(value)} '
                    f'was converted to {native_type_name(resolved_field.type)}.',
                    obj=value,
                    help_text=help_text,
                )

        return result

    def __post_init__(self) -> None:
        # Normalize the result `exception`, if any, to be a `CapturedErrorSummary` instance.
        # If a new `CapturedErrorSummary` was created, the `error_type` will be `cls`.
        # The `exception` key will be removed if falsey.
        # A `CapturedErrorSummary` instance will be returned if `failed` is truthy.
        if isinstance(self.exception, _captured.CapturedErrorSummary):
            self.is_module = self.exception.is_module
        elif isinstance(self.exception, _messages.ErrorSummary):
            self.exception = _captured.CapturedErrorSummary(
                event=self.exception.event,
                error_context=self._captured_error_context,
                error_message=self._captured_error_message,
                is_module=self.is_module,
            )
        elif self.failed or self.exception:
            # RPFIX-5: UX: warn/deprecate if exception is present without failed being True (and do what with failed?)

            # translate non-ErrorSummary errors
            self.exception = _captured.CapturedErrorSummary(
                event=_messages.Event(
                    msg=str(self.msg or 'Unknown error.'),
                    formatted_traceback=_normalize_traceback(self.exception),
                ),
                error_context=self._captured_error_context,
                error_message=self._captured_error_message,
                is_module=self.is_module,
            )
        else:
            self.exception = None

    @classmethod
    def from_module_result_dict(cls, result: dict[str, object]) -> t.Self:
        if (results := result.get('results', ...)) is not ... and (not isinstance(results, c.Sequence) or isinstance(results, str)):
            # deprecated: description='deprecate the value of ansible_module_results' core_version='2.25'
            # results = deprecate_value(
            #     value=results,
            #     msg="The 'ansible_module_results' result key is deprecated.",
            #     help_text="Use the 'results' result key instead.",
            #     version="2.29",
            # )

            result['ansible_module_results'] = results

        return cls._from_result_dict(result, source_is_module=True)

    @staticmethod
    def create_from_module_exception(exception: BaseException, accept_result_contribution: bool = False) -> UnifiedTaskResult:
        """Return a failed task result dict from the given exception."""
        return UnifiedTaskResult._create_from_exception(exception, accept_result_contribution=accept_result_contribution, source_is_module=True)

    @staticmethod
    def _create_from_exception(exception: BaseException, *, accept_result_contribution: bool = False, source_is_module: bool) -> UnifiedTaskResult:
        """Return a failed task result dict from the given exception."""
        event = _error_factory.ControllerEventFactory.from_exception(exception, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR))

        omit_failed_key = False
        omit_exception_key = False
        utr = UnifiedTaskResult(is_module=source_is_module)

        if accept_result_contribution:
            while exception:
                if isinstance(exception, _error_utils.ContributesToTaskResult):
                    utr = exception.as_task_result(utr)
                    omit_failed_key = exception.omit_failed_key
                    omit_exception_key = exception.omit_exception_key
                    break

                exception = exception.__cause__

        if omit_failed_key:
            utr.failed = None
        else:
            utr.failed = True

        if omit_exception_key:
            utr.exception = None
        else:
            utr.exception = _messages.ErrorSummary(event=event)

        if not utr.msg:
            # if nothing contributed `msg`, generate one from the exception messages
            utr.msg = _event_utils.format_event_brief_message(event)

        return utr

    def finalize_warnings(self, warning_ctx: _display_utils.DeferredWarningContext) -> None:
        if warnings := warning_ctx.get_warnings():
            self._warnings = warnings

        if deprecation_warnings := warning_ctx.get_deprecation_warnings():
            self._deprecations = deprecation_warnings

    @property
    def _captured_error_message(self) -> str:
        return 'Module failed.' if self.is_module else 'Action failed.'

    @property
    def _captured_error_context(self) -> str:
        return 'target' if self.is_module else 'action'

    def set_fact(self, key: str, value: object) -> None:
        if self.ansible_facts is None:
            self.ansible_facts = {}

        self.ansible_facts[key] = value

    def remove_internal_keys(self):
        # cleanse fact values that are allowed from actions but not modules
        if self.ansible_facts:
            for key in list(self.ansible_facts):
                # RPFIX-5: IMPL: move this into the control plane and inject into the results as needed
                if key.startswith('discovered_interpreter_') or key.startswith('ansible_discovered_interpreter_'):
                    self.ansible_facts.pop(key)

    @staticmethod
    def create_from_action_exception(exception: BaseException, accept_result_contribution: bool = False) -> UnifiedTaskResult:
        """Return a failed task result dict from the given exception."""
        utr = UnifiedTaskResult._create_from_exception(exception, accept_result_contribution=accept_result_contribution, source_is_module=False)

        TaskContext.current()._record_result(utr)

        return utr

    @classmethod
    @contextlib.contextmanager
    def create_and_record(cls, result: dict[str, t.Any] | None = None) -> t.Generator[t.Self]:
        utr = cls.from_action_result_dict(result or {})
        yield utr
        TaskContext.current()._record_result(utr)

    def maybe_raise_on_result(self) -> None:
        """Raise an exception if the result indicated failure."""
        if self.exception and self.failed:  # even though error detail was normalized, only raise it if the result indicated failure
            raise _captured.AnsibleResultCapturedError(self.exception.event, self)

    def set_skipped(self, reason: str | None = None, include_skipped_reason: bool = False) -> None:
        self.changed = False
        self.skipped = True

        if reason:
            self.skip_reason = reason

        if include_skipped_reason:
            self.skipped_reason = deprecate_value(
                value=reason,
                msg="The 'skipped_reason' value is deprecated.",
                help_text="Use 'skip_reason' instead.",
                version="2.24",
            )

    @classmethod
    def record_conditional_false(cls, conditional_expression: object) -> t.Self:
        with cls.create_and_record() as utr:
            utr.set_skipped('Conditional result was False')
            utr.false_condition = conditional_expression

        return utr

    def set_break_when_result(self, value: bool | AnsibleError) -> None:
        task_ctx = TaskContext.current()

        result: bool | str

        if isinstance(value, bool):
            result = value
            break_when = value
        else:
            result = str(value)

            try:
                # The original error's obj should contain the failed expression, which should be origin tagged.
                # This error is intended to provide additional context (the message) for the original error.
                # By repeating the original error's obj here, the error display will group the two errors together.
                raise AnsibleError("A 'break_when' expression failed.", obj=value.obj) from value
            except Exception as ex:
                wrapped_ex = ex

            break_when = True

            if self.exception:
                self.break_when_suppressed_exception = self.exception

            self.failed = True
            self.exception = _messages.ErrorSummary(
                # pylint: disable=used-before-assignment
                event=_error_factory.ControllerEventFactory.from_exception(wrapped_ex, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR)),
            )

        if break_when:
            task_ctx._break_when_triggered = True
            task_ctx._has_loop_exited = True

        self.break_when_result = result

    def set_changed_when_result(self, value: bool | AnsibleError) -> None:
        result: bool | str

        if isinstance(value, bool):
            result = value

            self.changed = value
        else:
            if self.exception:
                self.changed_when_suppressed_exception = self.exception

            result = str(value)

            try:
                # The original error's obj should contain the failed expression, which should be origin tagged.
                # This error is intended to provide additional context (the message) for the original error.
                # By repeating the original error's obj here, the error display will group the two errors together.
                raise AnsibleError("A 'changed_when' expression failed.", obj=value.obj) from value
            except Exception as ex:
                wrapped_ex = ex

            self.failed = True
            self.exception = _messages.ErrorSummary(
                # pylint: disable=used-before-assignment
                event=_error_factory.ControllerEventFactory.from_exception(wrapped_ex, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR)),
            )

        self.changed_when_result = result

    def set_failed_when_result(self, value: bool | AnsibleError) -> None:
        # RPFIX-5: DOC: document exception suppression logic in changelog et al
        #  The use of any failed_when expression will suppress the existing value of `exception` and store it in `failed_when_suppressed_exception`,
        #  regardless if the expression result is True, False, or an exception. For True and exception, the `exception` value in the task result becomes
        #  one generated (or caused) by failed_when.

        if self.exception:
            self.failed_when_suppressed_exception = self.exception
            self.exception = None

        result: bool | str

        if isinstance(value, bool):
            result = value

            self.failed = value

            if value:
                event = _messages.Event(
                    msg="A 'failed_when' expression evaluated to 'True'.",
                    # RPFIX-5: UX: We should be able to show more useful information here than just a static message,
                    #  including any shadowed msg we may have had and the (origin-tagged) failed_when expression itself.
                    # chain=None if self.msg is None else _messages.EventChain(
                    #     msg_reason='DO THINGS HERE',
                    #     traceback_reason='DO THINGS HERE',
                    #     event=_messages.Event(
                    #         msg=str(self.msg),
                    #         help_text="This was the original 'msg' before 'failed_when' was evaluated.",
                    #     ),
                    # ),
                )

                self.exception = _messages.ErrorSummary(
                    event=event,
                )
        else:
            result = str(value)

            try:
                # The original error's obj should contain the failed expression, which should be origin tagged.
                # This error is intended to provide additional context (the message) for the original error.
                # By repeating the original error's obj here, the error display will group the two errors together.
                raise AnsibleError("A 'failed_when' expression failed.", obj=value.obj) from value
            except Exception as ex:
                wrapped_ex = ex

            self.failed = True
            self.exception = _messages.ErrorSummary(
                # pylint: disable=used-before-assignment
                event=_error_factory.ControllerEventFactory.from_exception(wrapped_ex, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR)),
            )

        self.failed_when_result = result


def _normalize_traceback(value: object | None) -> str | None:
    """Normalize the provided traceback value, returning None if it is falsey."""
    if not value:
        return None

    value = str(value).rstrip()

    if not value:
        return None

    return value + '\n'


@t.final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class WireTaskResult:
    host_name: str
    task_uuid: str
    task_fields: c.Mapping[str, object]
    utr: UnifiedTaskResult

    @classmethod
    def create(cls, host: Host, task: Task, utr: UnifiedTaskResult) -> t.Self:
        return cls(
            host_name=host.name,
            task_uuid=task._uuid,
            utr=utr,
            task_fields=task.dump_attrs(),
        )


@t.final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class HostTaskResult:
    host: Host
    task: Task
    utr: UnifiedTaskResult
