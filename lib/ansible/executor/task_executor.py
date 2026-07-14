# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import itertools
import os
import time
import json
import pathlib
import subprocess
import sys

import traceback
import typing as t

from ansible import constants as C
from ansible._internal._task import TaskContext, UnifiedTaskResult
from ansible.cli import scripts
from ansible.errors import (
    AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleTaskError,
    AnsibleValueOmittedError,
)

from ansible._internal import _display_utils
from ansible._internal._datatag import _utils
from ansible.module_utils.datatag import native_type_name
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.common.text.converters import to_text, to_native
from ansible.module_utils.connection import write_to_stream
from ansible.playbook.play_context import PlayContext
from ansible.plugins import get_plugin_class
from ansible.plugins.action import ActionBase
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.loader import become_loader, cliconf_loader, connection_loader, httpapi_loader, netconf_loader, terminal_loader, PluginLoadContext
from ansible._internal._templating._jinja_plugins import _invoke_lookup, _DirectCall
from ansible._internal._templating._engine import TemplateEngine
from ansible.template import Templar
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars
from ansible.vars.clean import namespace_facts
from ansible.vars.manager import _clean_and_deprecate_top_level_facts, _INJECT_FACTS
from ansible._internal._errors import _task_timeout
from ansible._internal import _task
from ansible.playbook.task import Task
from ansible.executor.task_queue_manager import FinalQueue


display = Display()


_DELEGATED_CONNECTION_PLUGIN_VAR_NAMES = frozenset({
    'ansible_host',
    'ansible_port',
    'ansible_user',
    'ansible_connection',
})

__all__ = ['TaskExecutor']


class TaskExecutor:

    """
    This is the main worker class for the executor pipeline, which
    handles loading an action plugin to actually dispatch the task to
    a given host. This class roughly corresponds to the old Runner()
    class.
    """

    def __init__(
        self,
        host,
        play_context: PlayContext,
        loader,
        shared_loader_obj,
        final_q: FinalQueue,
        variable_manager,
    ) -> None:
        self._host = host
        self._play_context = play_context
        self._loader = loader
        self._shared_loader_obj = shared_loader_obj
        self._connection = None
        self._final_q = final_q
        self._variable_manager = variable_manager
        self._loop_eval_error: Exception | None = None

    @property
    def _task(self) -> Task:
        return TaskContext.current().task

    def run(self) -> UnifiedTaskResult:
        """
        The main executor entrypoint, where we determine if the specified
        task requires looping and either runs the task with self._run_loop()
        or self._execute(). After that, the returned results are parsed and
        returned as a dict.
        """

        display.debug("in run() - task %s" % self._task._uuid)

        task_ctx = TaskContext.current()

        try:
            try:
                items = self._get_loop_items()
            except AnsibleUndefinedVariable as e:
                # save the error raised here for use later
                items = None
                self._loop_eval_error = e

            if items is None:  # non-loop
                utr = self._execute()
            elif not items:  # empty loop
                with UnifiedTaskResult.create_and_record() as utr:
                    utr.set_skipped('No items in the list', include_skipped_reason=True)
                    utr.loop_results = []
            else:  # loop with values
                utr = self._run_loop(items)

            return utr
        except Exception as ex:
            utr = UnifiedTaskResult.create_from_action_exception(ex)

            self._task.update_result_no_log(task_ctx.task_templar, utr)

            if not isinstance(ex, AnsibleError):
                utr.msg = f'Unexpected failure during task execution: {utr.msg}'

            return utr
        finally:
            try:
                self._connection.close()
            except AttributeError:
                pass
            except Exception as e:
                display.debug(u"error closing connection: %s" % to_text(e))

    def _get_loop_items(self) -> list[t.Any] | None:
        """
        Loads a lookup plugin to handle the with_* portion of a task (if specified),
        and returns the items result.
        """
        task_ctx = TaskContext.current()

        # get search path for this task to pass to lookup plugins
        task_ctx.task_vars['ansible_search_path'] = self._task.get_search_path()

        # ensure basedir is always in (dwim already searches here but we need to display it)
        if self._loader.get_basedir() not in task_ctx.task_vars['ansible_search_path']:
            task_ctx.task_vars['ansible_search_path'].append(self._loader.get_basedir())

        items = None
        if self._task.loop_with:
            terms = self._task.loop

            if isinstance(terms, str):
                terms = task_ctx.task_templar.resolve_to_container(_utils.str_problematic_strip(terms))

            if not isinstance(terms, list):
                terms = [terms]

            @_DirectCall.mark
            def invoke_lookup() -> t.Any:
                """Scope-capturing wrapper around _invoke_lookup to avoid functools.partial obscuring its usage from type-checking tools."""
                return _invoke_lookup(
                    plugin_name=self._task.loop_with,
                    lookup_terms=terms,
                    lookup_kwargs=dict(wantlist=True),
                    invoked_as_with=True,
                )

            # Smuggle a special wrapped lookup invocation in as a local variable for its exclusive use when being evaluated as `with_(lookup)`.
            # This value will not be visible to other users of this templar or its `available_variables`.
            items = task_ctx.task_templar.evaluate_expression(
                expression=TrustedAsTemplate().tag("invoke_lookup()"),
                local_variables=dict(invoke_lookup=invoke_lookup),
            )

        elif self._task.loop is not None:
            items = task_ctx.task_templar.template(self._task.loop)

            if not isinstance(items, list):
                raise AnsibleError(
                    f"The `loop` value must resolve to a 'list', not {native_type_name(items)!r}.",
                    help_text="Provide a list of items/templates, or a template resolving to a list.",
                    obj=self._task.loop,
                )

        return items

    def _run_loop(self, items: list[t.Any]) -> UnifiedTaskResult:
        """
        Runs the task with the loop items specified and collates the result
        into an array named 'results' which is inserted into the final result
        along with the item for which the loop ran.
        """
        task_ctx = TaskContext.current()

        task_ctx._loop_items = items

        self._task.loop_control.post_validate(templar=task_ctx.task_templar)
        self._check_loop_control()

        loop_pause = self._task.loop_control.pause

        ran_once = False
        last_loop_task: Task | None = None

        for _item_index, _item in task_ctx.start_loop():
            # pause between loop iterations
            if loop_pause and ran_once:
                time.sleep(loop_pause)
            else:
                ran_once = True

            with task_ctx.loop_item_context(self):
                last_loop_task = self._task

                utr = self._execute()

                if self._task.loop_control and self._task.loop_control.break_when:
                    try:
                        utr.set_break_when_result(self._task._resolve_conditional(self._task.loop_control.break_when, task_ctx.task_vars))
                    except AnsibleError as ex:
                        # RPFIX-5: UX: This this bypasses AnsibleTaskError handling, resulting in less information than a normal task failure.
                        utr.set_break_when_result(ex)

                self._update_task_connection()

                if utr.failed or utr.unreachable:
                    self._final_q.send_callback('v2_runner_item_on_failed', self._host, self._task, utr)
                elif utr.skipped:
                    self._final_q.send_callback('v2_runner_item_on_skipped', self._host, self._task, utr)
                else:
                    if self._task.diff:
                        # non-loop diff dispatch is handled controller-side by the strategy
                        self._final_q.send_callback('v2_on_file_diff', self._host, self._task, utr)

                    self._final_q.send_callback('v2_runner_item_on_ok', self._host, self._task, utr)

            # update the connection value on the original task to reflect the resolved value
            self._update_task_connection()

        if last_loop_task:
            # FUTURE: hide this in Task/LoopContext once they're fully implemented
            # NOTE: run_once cannot contain loop vars because it's templated earlier also
            # This is saving the post-validated field from the last loop so the strategy can use the templated value post task execution
            self._task.run_once = last_loop_task.run_once
            self._task.action = last_loop_task.action

        return task_ctx.build_loop_result()

    def _check_loop_control(self) -> None:
        """Check loop_control configuration for potential problems."""
        task_ctx = TaskContext.current()

        loop_variables = dict(
            loop_var=self._task.loop_control.loop_var,
            index_var=self._task.loop_control.index_var,
        )

        # These reserved variables are set in TaskContext.start_loop,
        # so shouldn't be expected to already be in task variables.
        reserved_loop_variables = {
            "ansible_index_var",
            "ansible_loop",
            "ansible_loop_var",
        }

        duplicate_loop_variables = {
            key for key, group in itertools.groupby(sorted(value for value in loop_variables.values() if value)) if len(list(group)) > 1
        }

        for var_name, var_value in loop_variables.items():
            if not var_value:
                continue

            if var_value in task_ctx.task_vars:
                conflict = "already in use"
            elif var_value in reserved_loop_variables:
                conflict = "reserved"
            elif var_value in C.COMMON_CONNECTION_VARS:
                conflict = "reserved"
            elif var_value in duplicate_loop_variables:
                conflict = "used more than once"
            else:
                continue

            display.warning(
                msg=f"The variable {var_value!r} is {conflict}.",
                help_text=f"You should set the `{var_name}` value in the `loop_control` option for the task "
                          "to something else to avoid variable collisions and unexpected behavior.",
                obj=var_value,
            )

    def _calculate_delegate_to(self):
        """This method is responsible for effectively pre-validating Task.delegate_to and will
        happen before Task.post_validate is executed
        """
        task_ctx = TaskContext.current()

        delegated_vars, delegated_host_name = self._variable_manager.get_delegated_vars_and_hostname(task_ctx.task_templar, self._task, task_ctx.task_vars)
        # At the point this is executed it is safe to mutate self._task,
        # since `self._task` is either a copy referred to by `tmp_task` in `_run_loop`
        # or just a singular non-looped task

        self._task.delegate_to = delegated_host_name  # always override, since a templated result could be an omit (-> None)

        task_ctx.task_vars.update(delegated_vars)

    def _execute(self) -> UnifiedTaskResult:
        utr: UnifiedTaskResult

        task_ctx = TaskContext.current()

        with _display_utils.DeferredWarningContext(variables=task_ctx.task_vars) as warning_ctx:
            try:
                # DTFIX-FUTURE: improve error handling to prioritize the earliest exception, turning the remaining ones into warnings
                utr = self._execute_internal()
                utr.maybe_raise_on_result()
            except (Exception, _task_timeout.TaskTimeoutError) as ex:  # TaskTimeoutError is BaseException
                try:
                    raise AnsibleTaskError(obj=self._task.get_ds()) from ex
                except AnsibleTaskError as atex:
                    utr = UnifiedTaskResult.create_from_action_exception(atex, accept_result_contribution=True)

            self._task.update_result_no_log(task_ctx.task_templar, utr)

        # The warnings/deprecations in the result have already been captured in the DeferredWarningContext by _apply_task_result_compat.
        # The captured warnings/deprecations are a superset of the ones from the result, and may have been converted from a dict to a dataclass.
        # These are then used to supersede the entries in the result.

        utr.finalize_warnings(warning_ctx)

        return utr

    def _update_task_connection(self, task: Task | None = None) -> None:
        """If a connection plugin is loaded, ensure the resolved name is propagated back to the controller as the task's connection."""
        if not task:
            task = self._task

        # FUTURE: What value should be reported when there is no connection?
        #         This is currently not possible, but it should be.

        if isinstance(self._connection, ConnectionBase):
            task.connection = self._connection.ansible_name

    def _execute_internal(self) -> UnifiedTaskResult:
        """
        The primary workhorse of the executor system, this runs the task
        on the specified host (which may be the delegated_to host) and handles
        the retry/until and block rescue/always execution
        """
        task_ctx = TaskContext.current()

        self._calculate_delegate_to()

        context_validation_error = None

        task_vars_with_magic_vars = task_ctx.task_vars.copy()  # copy of task vars with connection vars erased/augmented for delegate_to

        try:
            # TODO: remove play_context as this does not take delegation nor loops correctly into account,
            # the task itself should hold the correct values for connection/shell/become/terminal plugin options to finalize.
            #  Kept for now for backwards compatibility and a few functions that are still exclusive to it.

            # apply the given task's information to the connection info,
            # which may override some fields already set by the play or
            # the options specified on the command line
            self._play_context = self._play_context.set_task_and_variable_override(task=self._task, variables=task_ctx.task_vars, templar=task_ctx.task_templar)

            # fields set from the play/task may be based on task vars, so we have to
            # do the same kind of post validation step on it here before we use it.
            self._play_context.post_validate(templar=task_ctx.task_templar)

            # now that the play context is finalized, if the remote_addr is not set
            # default to using the host's address field as the remote address
            if not self._play_context.remote_addr:
                self._play_context.remote_addr = self._host.address

            # We also add "magic" variables back into the tempvars dict to make sure
            self._play_context.update_vars(task_vars_with_magic_vars)

        except AnsibleError as e:
            # save the error, which we'll raise later if we don't end up
            # skipping this task during the conditional evaluation step
            context_validation_error = e

        # Evaluate the conditional (if any) for this task, which we do before running
        # the final task post-validation. We do this before the post validation due to
        # the fact that the conditional may specify that the task be skipped due to a
        # variable not being present which would otherwise cause validation to fail
        try:
            conditional_result, conditional_item = self._task._resolve_conditional_with_item(self._task.when, task_vars_with_magic_vars)

            if not conditional_result:
                return UnifiedTaskResult.record_conditional_false(conditional_item)
        except AnsibleError as e:
            # FUTURE: this error handling seems problematic; shouldn't a failed loop expression always be an error, rather than letting an item-oriented `when`
            #  expression be treated as a task-oriented one and sweeping the failure under the rug if it happens to be False? If so, this re-raise and the
            #  one just below it should be removed in favor of letting it fly from get_loop_items.
            try:
                # The original error's obj should contain the failed expression, which should be origin tagged.
                # This error is intended to provide additional context (the message) for the original error.
                # By repeating the original error's obj here, the error display will group the two errors together.
                raise AnsibleError("A 'when' expression failed.", obj=e.obj) from e
            except AnsibleError as ae:
                if self._loop_eval_error is None:
                    raise

                # Display the error from the conditional as well to prevent
                # losing information useful for debugging.
                display.error(ae)

            raise self._loop_eval_error

        # Not skipping, if we had loop error raised earlier we need to raise it now to halt the execution of this task
        if self._loop_eval_error is not None:
            raise self._loop_eval_error

        # if we ran into an error while setting up the PlayContext, raise it now, unless is known issue with delegation
        # and undefined vars (correct values are in cvars later on and connection plugins, if still error, blows up there)

        # DTFIX-FUTURE: this should probably be declaratively handled in post_validate (or better, get rid of play_context)
        if context_validation_error is not None:
            raiseit = True
            if self._task.delegate_to:
                if isinstance(context_validation_error, AnsibleParserError):
                    # parser error, might be cause by undef too
                    if isinstance(context_validation_error.__cause__, AnsibleUndefinedVariable):
                        raiseit = False
                elif isinstance(context_validation_error, AnsibleUndefinedVariable):
                    # DTFIX-FUTURE: should not be possible to hit this now (all are AnsibleFieldAttributeError)?
                    raiseit = False
            if raiseit:
                raise context_validation_error  # pylint: disable=raising-bad-type

        # Now we do final validation on the task, which sets all fields to their final values.
        self._task.post_validate(templar=task_ctx.task_templar.extend(variables=task_vars_with_magic_vars))  # should be handled by a context!

        # if this task is a TaskInclude, we just return now with a success code so the
        # main thread can expand the task list for the given host
        if self._task.action in C._ACTION_INCLUDE_TASKS:
            include_args = self._task.args.copy()
            include_file = include_args.pop('_raw_params', None)

            with UnifiedTaskResult.create_and_record() as utr:
                utr.include_file = include_file
                utr.include_args = include_args
                return utr

        # if this task is a IncludeRole, we just return now with a success code so the main thread can expand the task list for the given host
        elif self._task.action in C._ACTION_INCLUDE_ROLE:
            include_args = self._task.args.copy()

            with UnifiedTaskResult.create_and_record() as utr:
                utr.include_args = include_args
                return utr

        # setup cvars copy, used for all connection related templating
        if self._task.delegate_to:
            # use vars from delegated host (which already include task vars) instead of original host
            cvars = task_ctx.task_vars.get('ansible_delegated_vars', {}).get(self._task.delegate_to, {})
        else:
            # just use normal host vars
            cvars = task_ctx.task_vars

        connection_templar = task_ctx.task_templar.extend(variables=cvars)  # should be managed by a context!

        # use magic var if it exists, if not, let task inheritance do it's thing.
        if cvars.get('ansible_connection') is not None:
            current_connection = connection_templar.template(cvars['ansible_connection'])
        else:
            current_connection = self._task.connection

        # get the connection and the handler for this execution
        if (not self._connection or
                not getattr(self._connection, 'connected', False) or
                not self._connection.matches_name([current_connection]) or
                # pc compare, left here for old plugins, but should be irrelevant for those
                # using get_option, since they are cleared each iteration.
                self._play_context.remote_addr != self._connection._play_context.remote_addr):
            self._connection = self._get_connection(cvars, connection_templar, current_connection)
        else:
            # if connection is reused, its _play_context is no longer valid and needs
            # to be replaced with the one templated above, in case other data changed
            self._connection._play_context = self._play_context
            self._set_become_plugin(cvars, connection_templar, self._connection)

        plugin_vars = self._set_connection_options(cvars, connection_templar)

        # update with connection info (i.e ansible_host/ansible_user)
        self._connection.update_vars(task_ctx.task_vars)

        # TODO: eventually remove as pc is taken out of the resolution path
        # feed back into pc to ensure plugins not using get_option can get correct value
        self._connection._play_context = self._play_context.set_task_and_variable_override(
            task=self._task,
            variables=task_ctx.task_vars,
            templar=task_ctx.task_templar,
        )

        # TODO: eventually remove this block as this should be a 'consequence' of 'forced_local' modules, right now rely on remote_is_local connection
        # special handling for python interpreter for network_os, default to ansible python unless overridden
        if 'ansible_python_interpreter' not in cvars and 'ansible_network_os' in cvars and getattr(self._connection, '_remote_is_local', False):
            # this also avoids 'python discovery'
            cvars['ansible_python_interpreter'] = sys.executable

        # get handler
        self._handler, _module_context = self._get_action_handler_with_module_context(templar=task_ctx.task_templar)

        # self._connection should have its final value for this task/loop-item by this point; record on the task object
        self._update_task_connection()

        retries = 1  # includes the default actual run + retries set by user/default
        if self._task.retries is not None:
            retries += max(0, self._task.retries)
        elif self._task.until:
            retries += 3  # the default is not set in FA because we need to differentiate "unset" value

        delay = self._task.delay
        if delay < 0:
            delay = 1

        display.debug("starting attempt loop")
        for attempt in range(1, retries + 1):
            display.debug("running the handler")
            try:
                # FUTURE: exceptions raised anywhere here bypass failed_when, `until` retries, intra-loop register/register-projections
                with _task_timeout.TaskTimeoutError.alarm_timeout(self._task.timeout):
                    try:
                        task_ctx.pending_changes = _task.PendingChanges()

                        with UnifiedTaskResult.create_and_record(self._handler.run(task_vars=task_ctx.task_vars)) as utr:
                            utr.pending_changes = task_ctx.pending_changes
                    finally:
                        task_ctx.pending_changes = None

            finally:
                self._handler.cleanup()
            display.debug("handler run complete")

            if self._task.async_val > 0:
                if self._task.poll > 0 and not utr.skipped and not utr.failed:
                    utr = self._poll_async_result(utr=utr, templar=task_ctx.task_templar, task_vars=task_ctx.task_vars)

                    if utr.failed:
                        self._final_q.send_callback('v2_runner_on_async_failed', self._host, self._task, utr)
                    else:
                        self._final_q.send_callback('v2_runner_on_async_ok', self._host, self._task, utr)

            if utr.ansible_facts and _task.VariableLayer.CACHEABLE_FACT not in utr.pending_changes.register_host_variables:
                # For backward compatibility, if the action provided ansible_facts, use that as the CACHEABLE_FACT layer if the action did not provide one.
                utr.pending_changes.register_host_variables[_task.VariableLayer.CACHEABLE_FACT] = utr.ansible_facts

            # Variable layers should be reflected on task vars in the same way they will be handled by variable manager.
            # What occurs below is a partial re-implementation of variable manager, and thus does not fully reflect its behavior.
            # These updates are only done for the current host.

            if not self._task.delegate_to or not self._task.delegate_facts:
                if cacheable_fact_layer := utr.pending_changes.register_host_variables.get(_task.VariableLayer.CACHEABLE_FACT):
                    task_ctx.update_task_vars(dict(
                        ansible_facts=combine_vars(
                            task_ctx.task_vars.get('ansible_facts', {}),
                            namespace_facts(cacheable_fact_layer)['ansible_facts'],
                        ),
                    ))

                    if _INJECT_FACTS:
                        task_ctx.update_task_vars(_clean_and_deprecate_top_level_facts(cacheable_fact_layer))

                if include_vars_layer := utr.pending_changes.register_host_variables.get(_task.VariableLayer.INCLUDE_VARS):
                    task_ctx.update_task_vars(include_vars_layer)

                if ephemeral_fact_layer := utr.pending_changes.register_host_variables.get(_task.VariableLayer.EPHEMERAL_FACT):
                    task_ctx.update_task_vars(ephemeral_fact_layer)

            if register_vars_layer := utr.pending_changes.register_host_variables.get(_task.VariableLayer.REGISTER_VARS):
                task_ctx.update_task_vars(register_vars_layer)

            # Make attempts and retries available early to allow their use in changed/failed_when
            if retries > 1:
                utr.attempts = attempt

            # if we didn't skip this task, use the helpers to evaluate the changed/
            # failed_when properties
            if not utr.skipped:
                try:
                    if self._task.changed_when:
                        utr.set_changed_when_result(self._task._resolve_conditional(self._task.changed_when, task_ctx.task_vars))
                except AnsibleError as e:
                    utr.set_changed_when_result(e)
                else:
                    try:
                        if self._task.failed_when:
                            utr.set_failed_when_result(self._task._resolve_conditional(self._task.failed_when, task_ctx.task_vars))
                    except AnsibleError as e:
                        utr.set_failed_when_result(e)

            if retries > 1:
                try:
                    if self._task._resolve_conditional(self._task.until or [not utr.failed], task_ctx.task_vars):
                        break
                except AnsibleError as e:
                    # The original error's obj should contain the failed expression, which should be origin tagged.
                    # This error is intended to provide additional context (the message) for the original error.
                    # By repeating the original error's obj here, the error display will group the two errors together.
                    raise AnsibleError("An 'until' expression failed.", obj=e.obj) from e

                # no conditional check, or it failed, so sleep for the specified time
                if attempt < retries:
                    utr.retries = retries
                    utr.attempts = attempt + 1
                    display.debug('Retrying task, attempt %d of %d' % (attempt, retries))
                    self._final_q.send_callback('v2_runner_retry', self._host, self._task, utr)
                    time.sleep(delay)
                    self._handler = self._get_action_handler(templar=task_ctx.task_templar)
        else:
            if retries > 1:
                # we ran out of attempts, so mark the result as failed
                utr.attempts = retries - 1
                utr.failed = True

        # save the notification target in the result, if it was specified, as
        # this task may be running in a loop in which case the notification
        # may be item-specific, ie. "notify: service {{item}}"
        if self._task.notify is not None:
            utr.notify = self._task.notify

        # add the delegated vars to the result, so we can reference them
        # on the results side without having to do any further templating
        # also now add connection vars results when delegating
        if self._task.delegate_to:
            utr.delegated_host = self._task.delegate_to
            utr.callback_delegated_vars_subset = dict(
                ansible_delegated_host=self._task.delegate_to,
                ansible_connection=current_connection,
            )

            # note: here for callbacks that rely on this info to display delegation
            for plugin_var_name in plugin_vars:
                if plugin_var_name not in _DELEGATED_CONNECTION_PLUGIN_VAR_NAMES:
                    continue

                # FUTURE: this is horribly inefficient
                for plugin_option_name in C.config.get_plugin_options_from_var("connection", current_connection, plugin_var_name):
                    utr.callback_delegated_vars_subset[plugin_var_name] = self._connection.get_option(plugin_option_name)

        # and return
        display.debug("attempt loop complete, returning result")
        return utr

    def _poll_async_result(self, utr: UnifiedTaskResult, templar: TemplateEngine, task_vars: dict[str, t.Any]) -> UnifiedTaskResult:
        """
        Polls for the specified JID to be complete
        """
        async_jid = utr.async_job_id

        if async_jid is None:
            # RPFIX-9: FUTURE: why not raise?
            with UnifiedTaskResult.create_and_record() as utr:
                utr.failed = True
                utr.msg = "No job id was returned by the async task"

            return utr

        # Create a new pseudo-task to run the async_status module, and run
        # that (with a sleep for "poll" seconds between each retry) until the
        # async time limit is exceeded.

        async_task = Task.load(dict(
            action='async_status',
            args={'jid': async_jid},
            check_mode=self._task.check_mode,
            environment=self._task.environment,
            delegate_to=self._task.delegate_to,
        ))

        # ensure that the synthetic async task has the resolved connection recorded on it
        self._update_task_connection(async_task)

        # FIXME: this is no longer the case, normal takes care of all, see if this can just be generalized
        # Because this is an async task, the action handler is async. However,
        # we need the 'normal' action handler for the status check, so get it
        # now via the action_loader
        async_handler: ActionBase = self._shared_loader_obj.action_loader.get(
            'ansible.legacy.async_status',
            task=async_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=Templar._from_template_engine(templar),
            shared_loader_obj=self._shared_loader_obj,
        )

        time_left = self._task.async_val
        while time_left > 0:
            time.sleep(self._task.poll)

            try:
                with UnifiedTaskResult.create_and_record(async_handler.run(task_vars=task_vars)) as async_utr:
                    pass
                # We do not bail out of the loop in cases where the failure
                # is associated with a parsing error. The async_runner can
                # have issues which result in a half-written/unparsable result
                # file on disk, which manifests to the user as a timeout happening
                # before it's time to timeout.
                if async_utr.finished or (async_utr.failed and async_utr.ansible_parsed) or async_utr.skipped:
                    break
            except Exception as e:
                # Connections can raise exceptions during polling (eg, network bounce, reboot); these should be non-fatal.
                # On an exception, call the connection's reset method if it has one
                # (eg, drop/recreate WinRM connection; some reused connections are in a broken state)
                display.vvvv("Exception during async poll, retrying... (%s)" % to_text(e))
                display.debug("Async poll exception was:\n%s" % to_text(traceback.format_exc()))
                try:
                    async_handler._connection.reset()
                except AttributeError:
                    pass

                # Little hack to raise the exception if we've exhausted the timeout period
                time_left -= self._task.poll
                if time_left <= 0:
                    raise
            else:
                time_left -= self._task.poll
                self._final_q.send_callback('v2_runner_on_async_poll', self._host, async_task, async_utr)

        if not async_utr.finished:
            # RPFIX-9: FUTURE: why not raise?
            with UnifiedTaskResult.create_and_record() as async_failed_utr:
                async_failed_utr.failed = True
                async_failed_utr.async_result = async_utr.as_result_dict()

                if async_failed_utr.ansible_parsed:
                    async_failed_utr.msg = "async task did not complete within the requested time - %ss" % self._task.async_val
                else:
                    async_failed_utr.msg = "async task produced unparsable results"

            async_utr = async_failed_utr  # replace the actual async result with a synthesized failure
        else:
            # If the async task finished, automatically cleanup the temporary
            # status file left behind.
            cleanup_task = Task.load(
                {
                    'async_status': {
                        'jid': async_jid,
                        'mode': 'cleanup',
                    },
                    'check_mode': self._task.check_mode,
                    'environment': self._task.environment,
                    'delegate_to': self._task.delegate_to,
                }
            )
            cleanup_handler: ActionBase = self._shared_loader_obj.action_loader.get(
                'ansible.legacy.async_status',
                task=cleanup_task,
                connection=self._connection,
                play_context=self._play_context,
                loader=self._loader,
                templar=Templar._from_template_engine(templar),
                shared_loader_obj=self._shared_loader_obj,
            )
            cleanup_handler.run(task_vars=task_vars)
            cleanup_handler.cleanup(force=True)
            async_handler.cleanup(force=True)

        return async_utr

    def _get_become(self, name):
        become = become_loader.get(name)
        if not become:
            raise AnsibleError("Invalid become method specified, could not find matching plugin: '%s'. "
                               "Use `ansible-doc -t become -l` to list available plugins." % name)
        return become

    def _get_connection(self, cvars, templar, current_connection):
        """
        Reads the connection property for the host, and returns the
        correct connection object from the list of connection plugins
        """

        self._play_context.connection = current_connection

        conn_type = self._play_context.connection

        connection, plugin_load_context = self._shared_loader_obj.connection_loader.get_with_context(
            conn_type,
            self._play_context,
            new_stdin=None,  # No longer used, kept for backwards compat for plugins that explicitly accept this as an arg
            task_uuid=self._task._uuid,
            ansible_playbook_pid=to_text(os.getppid())
        )

        if not connection:
            raise AnsibleError("the connection plugin '%s' was not found" % conn_type)

        self._set_become_plugin(cvars, templar, connection)

        # Also backwards compat call for those still using play_context
        self._play_context.set_attributes_from_plugin(connection)

        return connection

    def _set_become_plugin(self, cvars, templar, connection):
        # load become plugin if needed
        if cvars.get('ansible_become') is not None:
            become = boolean(templar.template(cvars['ansible_become']))
        else:
            become = self._task.become

        if become:
            if cvars.get('ansible_become_method'):
                become_plugin = self._get_become(templar.template(cvars['ansible_become_method']))
            else:
                become_plugin = self._get_become(self._task.become_method)

        else:
            # If become is not enabled on the task it needs to be removed from the connection plugin
            # https://github.com/ansible/ansible/issues/78425
            become_plugin = None

        try:
            connection.set_become_plugin(become_plugin)
        except AttributeError:
            # Older connection plugin that does not support set_become_plugin
            pass

        if become_plugin:
            if getattr(connection.become, 'require_tty', False) and not getattr(connection, 'has_tty', False):
                raise AnsibleError(
                    "The '%s' connection does not provide a TTY which is required for the selected "
                    "become plugin: %s." % (connection._load_name, become_plugin.name)
                )

            # Backwards compat for connection plugins that don't support become plugins
            # Just do this unconditionally for now, we could move it inside of the
            # AttributeError above later
            self._play_context.set_become_plugin(become_plugin.name)

    def _set_plugin_options(self, plugin_type, variables, templar, task_keys):
        try:
            plugin = getattr(self._connection, '_%s' % plugin_type)
        except AttributeError:
            # Some plugins are assigned to private attrs, ``become`` is not
            plugin = getattr(self._connection, plugin_type)

        # network_cli's "real" connection plugin is not named connection
        # to avoid the confusion of having connection.connection
        if plugin_type == "ssh_type_conn":
            plugin_type = "connection"
        option_vars = C.config.get_plugin_vars(plugin_type, plugin._load_name)
        options = {}
        for k in option_vars:
            if k in variables:
                try:
                    options[k] = templar.template(variables[k])
                except AnsibleValueOmittedError:
                    pass

        # TODO move to task method?
        plugin.set_options(task_keys=task_keys, var_options=options)

        return option_vars

    def _set_connection_options(self, variables, templar):

        # keep list of variable names possibly consumed
        varnames = []

        # grab list of usable vars for this plugin
        option_vars = C.config.get_plugin_vars('connection', self._connection._load_name)
        varnames.extend(option_vars)

        task_keys = self._task.dump_attrs()

        # The task_keys 'timeout' attr is the task's timeout, not the connection timeout.
        # The connection timeout is threaded through the play_context for now.
        task_keys['timeout'] = self._play_context.timeout

        if self._play_context.password:
            # The connection password is threaded through the play_context for
            # now. This is something we ultimately want to avoid, but the first
            # step is to get connection plugins pulling the password through the
            # config system instead of directly accessing play_context.
            task_keys['password'] = self._play_context.password

        # Prevent task retries from overriding connection retries
        del task_keys['retries']

        # set options with 'templated vars' specific to this plugin and dependent ones
        var_options = self._connection._resolve_option_variables(variables, templar)
        self._connection.set_options(task_keys=task_keys, var_options=var_options)
        varnames.extend(self._set_plugin_options('shell', variables, templar, task_keys))

        if self._connection.become is not None:
            if self._play_context.become_pass:
                # FIXME: eventually remove from task and play_context, here for backwards compat
                # keep out of play objects to avoid accidental disclosure, only become plugin should have
                # The become pass is already in the play_context if given on
                # the CLI (-K). Make the plugin aware of it in this case.
                task_keys['become_pass'] = self._play_context.become_pass

            varnames.extend(self._set_plugin_options('become', variables, templar, task_keys))

            # FOR BACKWARDS COMPAT:
            for option in ('become_user', 'become_flags', 'become_exe', 'become_pass'):
                try:
                    setattr(self._play_context, option, self._connection.become.get_option(option))
                except KeyError:
                    pass  # some plugins don't support all base flags
            self._play_context.prompt = self._connection.become.prompt

        # deals with networking sub_plugins (network_cli/httpapi/netconf)
        sub = getattr(self._connection, '_sub_plugin', None)
        if sub and sub.get('type') != 'external':
            plugin_type = get_plugin_class(sub.get("obj"))
            varnames.extend(self._set_plugin_options(plugin_type, variables, templar, task_keys))
        sub_conn = getattr(self._connection, 'ssh_type_conn', None)
        if sub_conn is not None:
            varnames.extend(self._set_plugin_options("ssh_type_conn", variables, templar, task_keys))

        return varnames

    def _get_action_handler(self, templar: TemplateEngine) -> ActionBase:
        """
        Returns the correct action plugin to handle the requestion task action
        """
        return self._get_action_handler_with_module_context(templar)[0]

    def _get_action_handler_with_module_context(self, templar: TemplateEngine) -> tuple[ActionBase, PluginLoadContext]:
        """
        Returns the correct action plugin to handle the requestion task action and the module context
        """
        module_collection, separator, module_name = self._task.action.rpartition(".")
        module_prefix = module_name.split('_')[0]
        if module_collection:
            # For network modules, which look for one action plugin per platform, look for the
            # action plugin in the same collection as the module by prefixing the action plugin
            # with the same collection.
            network_action = "{0}.{1}".format(module_collection, module_prefix)
        else:
            network_action = module_prefix

        collections = self._task.collections

        # Check if the module has specified an action handler
        module = self._shared_loader_obj.module_loader.find_plugin_with_context(
            self._task.action, collection_list=collections
        )
        if not module.resolved or not module.action_plugin:
            module = None
        if module is not None:
            handler_name = module.action_plugin
        # let action plugin override module, fallback to 'normal' action plugin otherwise
        elif self._shared_loader_obj.action_loader.has_plugin(self._task.action, collection_list=collections):
            handler_name = self._task.action
        elif module_prefix in C.NETWORK_GROUP_MODULES and self._shared_loader_obj.action_loader.has_plugin(network_action, collection_list=collections):
            handler_name = network_action
            display.vvvv("Using network group action {handler} for {action}".format(handler=handler_name,
                                                                                    action=self._task.action),
                         host=self._play_context.remote_addr)
        else:
            # use ansible.legacy.normal to allow (historic) local action_plugins/ override without collections search
            handler_name = 'ansible.legacy.normal'
            collections = None  # until then, we don't want the task's collection list to be consulted; use the builtin

        # networking/psersistent connections handling
        if any(((self._connection.supports_persistence and C.USE_PERSISTENT_CONNECTIONS), self._connection.force_persistence)):

            # check handler in case we dont need to do all the work to setup persistent connection
            handler_class = self._shared_loader_obj.action_loader.get(handler_name, class_only=True)
            if getattr(handler_class, '_requires_connection', True):
                # for persistent connections, initialize socket path and start connection manager
                self._play_context.timeout = self._connection.get_option('persistent_command_timeout')
                display.vvvv('attempting to start connection', host=self._play_context.remote_addr)
                display.vvvv('using connection plugin %s' % self._connection.transport, host=self._play_context.remote_addr)

                options = self._connection.get_options()
                socket_path = start_connection(self._play_context, options, self._task._uuid)
                display.vvvv('local domain socket path is %s' % socket_path, host=self._play_context.remote_addr)
                setattr(self._connection, '_socket_path', socket_path)
            else:
                # TODO: set self._connection to dummy/noop connection, using local for now
                self._connection = self._get_connection({}, templar, 'local')

        handler = self._shared_loader_obj.action_loader.get(
            handler_name,
            task=self._task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=Templar._from_template_engine(templar),
            shared_loader_obj=self._shared_loader_obj,
            collection_list=collections
        )

        if not handler:
            raise AnsibleError("the handler '%s' was not found" % handler_name)

        return handler, module


CLI_STUB_NAME = 'ansible_connection_cli_stub.py'


def start_connection(play_context, options, task_uuid):
    """
    Starts the persistent connection
    """

    env = os.environ.copy()
    env.update({
        # HACK; most of these paths may change during the controller's lifetime
        # (eg, due to late dynamic role includes, multi-playbook execution), without a way
        # to invalidate/update, the persistent connection helper won't always see the same plugins the controller
        # can.
        'ANSIBLE_BECOME_PLUGINS': become_loader.print_paths(),
        'ANSIBLE_CLICONF_PLUGINS': cliconf_loader.print_paths(),
        'ANSIBLE_COLLECTIONS_PATH': to_native(os.pathsep.join(AnsibleCollectionConfig.collection_paths)),
        'ANSIBLE_CONNECTION_PLUGINS': connection_loader.print_paths(),
        'ANSIBLE_HTTPAPI_PLUGINS': httpapi_loader.print_paths(),
        'ANSIBLE_NETCONF_PLUGINS': netconf_loader.print_paths(),
        'ANSIBLE_TERMINAL_PLUGINS': terminal_loader.print_paths(),
    })
    verbosity = []
    if display.verbosity:
        verbosity.append('-%s' % ('v' * display.verbosity))

    if not (cli_stub_path := C.config.get_config_value('_ANSIBLE_CONNECTION_PATH')):
        cli_stub_path = str(pathlib.Path(scripts.__file__).parent / CLI_STUB_NAME)

    p = subprocess.Popen(
        [sys.executable, cli_stub_path, *verbosity, to_text(os.getppid()), to_text(task_uuid)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    )

    write_to_stream(p.stdin, options)
    write_to_stream(p.stdin, play_context.dump_attrs())

    (stdout, stderr) = p.communicate()

    if p.returncode == 0:
        result = json.loads(to_text(stdout, errors='surrogate_then_replace'))
    else:
        try:
            result = json.loads(to_text(stderr, errors='surrogate_then_replace'))
        except json.decoder.JSONDecodeError:
            result = {'error': to_text(stderr, errors='surrogate_then_replace')}

    if 'messages' in result:
        for level, message in result['messages']:
            if level == 'log':
                display.display(message, log_only=True)
            elif level in ('debug', 'v', 'vv', 'vvv', 'vvvv', 'vvvvv', 'vvvvvv'):
                getattr(display, level)(message, host=play_context.remote_addr)
            else:
                if hasattr(display, level):
                    getattr(display, level)(message)
                else:
                    display.vvvv(message, host=play_context.remote_addr)

    if 'error' in result:
        if display.verbosity > 2:
            if result.get('exception'):
                msg = "The full traceback is:\n" + result['exception']
                display.display(msg, color=C.COLOR_ERROR)
        raise AnsibleError(result['error'])

    return result['socket_path']
