# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import os
import time
import json
import pathlib
import signal
import subprocess
import sys
import traceback

from ansible import constants as C
from ansible.cli import scripts
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleConnectionFailure, AnsibleActionFail, AnsibleActionSkip
from ansible.executor.task_result import TaskResult
from ansible.executor.module_common import get_action_args_with_defaults
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import binary_type
from ansible.module_utils.common.text.converters import to_text, to_native
from ansible.module_utils.connection import write_to_stream
from ansible.module_utils.six import string_types
from ansible.playbook.conditional import Conditional
from ansible.playbook.task import Task
from ansible.plugins import get_plugin_class
from ansible.plugins.loader import become_loader, cliconf_loader, connection_loader, httpapi_loader, netconf_loader, terminal_loader
from ansible.template import Templar
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.utils.unsafe_proxy import to_unsafe_text, wrap_var
from ansible.vars.clean import namespace_facts, clean_facts
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

display = Display()


RETURN_VARS = [x for x in C.MAGIC_VARIABLE_MAPPING.items() if 'become' not in x and '_pass' not in x]

__all__ = ['TaskExecutor']


class TaskTimeoutError(BaseException):
    def __init__(self, message="", frame=None):

        if frame is not None:
            orig = frame
            root = pathlib.Path(__file__).parent
            while not pathlib.Path(frame.f_code.co_filename).is_relative_to(root):
                frame = frame.f_back

            self.frame = 'Interrupted at %s called from %s' % (orig, frame)

        super(TaskTimeoutError, self).__init__(message)


def task_timeout(signum, frame):
    raise TaskTimeoutError(frame=frame)


def remove_omit(task_args, omit_token):
    """
    Remove args with a value equal to the ``omit_token`` recursively
    to align with now having suboptions in the argument_spec
    """

    if not isinstance(task_args, dict):
        return task_args

    new_args = {}
    for i in task_args.items():
        if i[1] == omit_token:
            continue
        elif isinstance(i[1], dict):
            new_args[i[0]] = remove_omit(i[1], omit_token)
        elif isinstance(i[1], list):
            new_args[i[0]] = [remove_omit(v, omit_token) for v in i[1]]
        else:
            new_args[i[0]] = i[1]

    return new_args


class TaskExecutor:

    """
    This is the main worker class for the executor pipeline, which
    handles loading an action plugin to actually dispatch the task to
    a given host. This class roughly corresponds to the old Runner()
    class.
    """

    def __init__(self, host, task, job_vars, play_context, new_stdin, loader, shared_loader_obj, final_q, variable_manager):
        self._host = host
        self._task = task
        self._job_vars = job_vars
        self._play_context = play_context
        self._new_stdin = new_stdin
        self._loader = loader
        self._shared_loader_obj = shared_loader_obj
        self._connection = None
        self._final_q = final_q
        self._variable_manager = variable_manager
        self._loop_eval_error = None

        self._task.squash()

    def run(self):
        """
        The main executor entrypoint, where we determine if the specified
        task requires looping and either runs the task with self._run_loop()
        or self._execute(). After that, the returned results are parsed and
        returned as a dict.
        """

        display.debug("in run() - task %s" % self._task._uuid)

        try:
            try:
                items = self._get_loop_items()
            except AnsibleUndefinedVariable as e:
                # save the error raised here for use later
                items = None
                self._loop_eval_error = e

            if items is not None:
                if len(items) > 0:
                    item_results = self._run_loop(items)

                    # create the overall result item
                    res = dict(results=item_results)

                    # loop through the item results and set the global changed/failed/skipped result flags based on any item.
                    res['skipped'] = True
                    for item in item_results:
                        if 'changed' in item and item['changed'] and not res.get('changed'):
                            res['changed'] = True
                        if res['skipped'] and ('skipped' not in item or ('skipped' in item and not item['skipped'])):
                            res['skipped'] = False
                        if 'failed' in item and item['failed']:
                            item_ignore = item.pop('_ansible_ignore_errors')
                            if not res.get('failed'):
                                res['failed'] = True
                                res['msg'] = 'One or more items failed'
                                self._task.ignore_errors = item_ignore
                            elif self._task.ignore_errors and not item_ignore:
                                self._task.ignore_errors = item_ignore
                        if 'unreachable' in item and item['unreachable']:
                            item_ignore_unreachable = item.pop('_ansible_ignore_unreachable')
                            if not res.get('unreachable'):
                                res['unreachable'] = True
                                self._task.ignore_unreachable = item_ignore_unreachable
                            elif self._task.ignore_unreachable and not item_ignore_unreachable:
                                self._task.ignore_unreachable = item_ignore_unreachable

                        # ensure to accumulate these
                        for array in ['warnings', 'deprecations']:
                            if array in item and item[array]:
                                if array not in res:
                                    res[array] = []
                                if not isinstance(item[array], list):
                                    item[array] = [item[array]]
                                res[array] = res[array] + item[array]
                                del item[array]

                    if not res.get('failed', False):
                        res['msg'] = 'All items completed'
                    if res['skipped']:
                        res['msg'] = 'All items skipped'
                else:
                    res = dict(changed=False, skipped=True, skipped_reason='No items in the list', results=[])
            else:
                display.debug("calling self._execute()")
                res = self._execute()
                display.debug("_execute() done")

            # make sure changed is set in the result, if it's not present
            if 'changed' not in res:
                res['changed'] = False

            def _clean_res(res, errors='surrogate_or_strict'):
                if isinstance(res, binary_type):
                    return to_unsafe_text(res, errors=errors)
                elif isinstance(res, dict):
                    for k in res:
                        try:
                            res[k] = _clean_res(res[k], errors=errors)
                        except UnicodeError:
                            if k == 'diff':
                                # If this is a diff, substitute a replacement character if the value
                                # is undecodable as utf8.  (Fix #21804)
                                display.warning("We were unable to decode all characters in the module return data."
                                                " Replaced some in an effort to return as much as possible")
                                res[k] = _clean_res(res[k], errors='surrogate_then_replace')
                            else:
                                raise
                elif isinstance(res, list):
                    for idx, item in enumerate(res):
                        res[idx] = _clean_res(item, errors=errors)
                return res

            display.debug("dumping result to json")
            res = _clean_res(res)
            display.debug("done dumping result, returning")
            return res
        except AnsibleError as e:
            return dict(failed=True, msg=wrap_var(to_text(e, nonstring='simplerepr')), _ansible_no_log=self._play_context.no_log)
        except Exception as e:
            return dict(failed=True, msg=wrap_var('Unexpected failure during module execution: %s' % (to_native(e, nonstring='simplerepr'))),
                        exception=to_text(traceback.format_exc()), stdout='', _ansible_no_log=self._play_context.no_log)
        finally:
            try:
                self._connection.close()
            except AttributeError:
                pass
            except Exception as e:
                display.debug(u"error closing connection: %s" % to_text(e))

    def _get_loop_items(self):
        """
        Loads a lookup plugin to handle the with_* portion of a task (if specified),
        and returns the items result.
        """

        # get search path for this task to pass to lookup plugins
        self._job_vars['ansible_search_path'] = self._task.get_search_path()

        # ensure basedir is always in (dwim already searches here but we need to display it)
        if self._loader.get_basedir() not in self._job_vars['ansible_search_path']:
            self._job_vars['ansible_search_path'].append(self._loader.get_basedir())

        templar = Templar(loader=self._loader, variables=self._job_vars)
        items = None
        if self._task.loop_with:
            if self._task.loop_with in self._shared_loader_obj.lookup_loader:

                # TODO: hardcoded so it fails for non first_found lookups, but this should be generalized for those that don't do their own templating
                # lookup prop/attribute?
                fail = bool(self._task.loop_with != 'first_found')
                loop_terms = listify_lookup_plugin_terms(terms=self._task.loop, templar=templar, fail_on_undefined=fail, convert_bare=False)

                # get lookup
                mylookup = self._shared_loader_obj.lookup_loader.get(self._task.loop_with, loader=self._loader, templar=templar)

                # give lookup task 'context' for subdir (mostly needed for first_found)
                for subdir in ['template', 'var', 'file']:  # TODO: move this to constants?
                    if subdir in self._task.action:
                        break
                setattr(mylookup, '_subdir', subdir + 's')

                # run lookup
                items = wrap_var(mylookup.run(terms=loop_terms, variables=self._job_vars, wantlist=True))
            else:
                raise AnsibleError("Unexpected failure in finding the lookup named '%s' in the available lookup plugins" % self._task.loop_with)

        elif self._task.loop is not None:
            items = templar.template(self._task.loop)
            if not isinstance(items, list):
                raise AnsibleError(
                    "Invalid data passed to 'loop', it requires a list, got this instead: %s."
                    " Hint: If you passed a list/dict of just one element,"
                    " try adding wantlist=True to your lookup invocation or use q/query instead of lookup." % items
                )

        return items

    def _run_loop(self, items):
        """
        Runs the task with the loop items specified and collates the result
        into an array named 'results' which is inserted into the final result
        along with the item for which the loop ran.
        """
        task_vars = self._job_vars
        templar = Templar(loader=self._loader, variables=task_vars)

        self._task.loop_control.post_validate(templar=templar)

        loop_var = self._task.loop_control.loop_var
        index_var = self._task.loop_control.index_var
        loop_pause = self._task.loop_control.pause
        extended = self._task.loop_control.extended
        extended_allitems = self._task.loop_control.extended_allitems
        # ensure we always have a label
        label = self._task.loop_control.label or '{{' + loop_var + '}}'

        if loop_var in task_vars:
            display.warning(u"%s: The loop variable '%s' is already in use. "
                            u"You should set the `loop_var` value in the `loop_control` option for the task"
                            u" to something else to avoid variable collisions and unexpected behavior." % (self._task, loop_var))

        ran_once = False
        task_fields = None
        no_log = False
        items_len = len(items)
        results = []
        for item_index, item in enumerate(items):
            task_vars['ansible_loop_var'] = loop_var

            task_vars[loop_var] = item
            if index_var:
                task_vars['ansible_index_var'] = index_var
                task_vars[index_var] = item_index

            if extended:
                task_vars['ansible_loop'] = {
                    'index': item_index + 1,
                    'index0': item_index,
                    'first': item_index == 0,
                    'last': item_index + 1 == items_len,
                    'length': items_len,
                    'revindex': items_len - item_index,
                    'revindex0': items_len - item_index - 1,
                }
                if extended_allitems:
                    task_vars['ansible_loop']['allitems'] = items
                try:
                    task_vars['ansible_loop']['nextitem'] = items[item_index + 1]
                except IndexError:
                    pass
                if item_index - 1 >= 0:
                    task_vars['ansible_loop']['previtem'] = items[item_index - 1]

            # Update template vars to reflect current loop iteration
            templar.available_variables = task_vars

            # pause between loop iterations
            if loop_pause and ran_once:
                time.sleep(loop_pause)
            else:
                ran_once = True

            try:
                tmp_task = self._task.copy(exclude_parent=True, exclude_tasks=True)
                tmp_task._parent = self._task._parent
                tmp_play_context = self._play_context.copy()
            except AnsibleParserError as e:
                results.append(dict(failed=True, msg=to_text(e)))
                continue

            # now we swap the internal task and play context with their copies,
            # execute, and swap them back so we can do the next iteration cleanly
            (self._task, tmp_task) = (tmp_task, self._task)
            (self._play_context, tmp_play_context) = (tmp_play_context, self._play_context)
            res = self._execute(variables=task_vars)

            if self._task.register:
                # Ensure per loop iteration results are registered in case `_execute()`
                # returns early (when conditional, failure, ...).
                # This is needed in case the registered variable is used in the loop label template.
                task_vars[self._task.register] = res

            task_fields = self._task.dump_attrs()
            (self._task, tmp_task) = (tmp_task, self._task)
            (self._play_context, tmp_play_context) = (tmp_play_context, self._play_context)

            # update 'general no_log' based on specific no_log
            no_log = no_log or tmp_task.no_log

            # now update the result with the item info, and append the result
            # to the list of results
            res[loop_var] = item
            res['ansible_loop_var'] = loop_var
            if index_var:
                res[index_var] = item_index
                res['ansible_index_var'] = index_var
            if extended:
                res['ansible_loop'] = task_vars['ansible_loop']

            res['_ansible_item_result'] = True
            res['_ansible_ignore_errors'] = task_fields.get('ignore_errors')
            res['_ansible_ignore_unreachable'] = task_fields.get('ignore_unreachable')

            # gets templated here unlike rest of loop_control fields, depends on loop_var above
            try:
                res['_ansible_item_label'] = templar.template(label)
            except AnsibleUndefinedVariable as e:
                res.update({
                    'failed': True,
                    'msg': 'Failed to template loop_control.label: %s' % to_text(e)
                })

            # if plugin is loaded, get resolved name, otherwise leave original task connection
            if self._connection and not isinstance(self._connection, string_types):
                task_fields['connection'] = getattr(self._connection, 'ansible_name')

            tr = TaskResult(
                self._host.name,
                self._task._uuid,
                res,
                task_fields=task_fields,
            )

            if tr.is_failed() or tr.is_unreachable():
                self._final_q.send_callback('v2_runner_item_on_failed', tr)
            elif tr.is_skipped():
                self._final_q.send_callback('v2_runner_item_on_skipped', tr)
            else:
                if getattr(self._task, 'diff', False):
                    self._final_q.send_callback('v2_on_file_diff', tr)
                if self._task.action not in C._ACTION_INVENTORY_TASKS:
                    self._final_q.send_callback('v2_runner_item_on_ok', tr)

            results.append(res)

            # break loop if break_when conditions are met
            if self._task.loop_control and self._task.loop_control.break_when:
                cond = Conditional(loader=self._loader)
                cond.when = self._task.loop_control.get_validated_value(
                    'break_when', self._task.loop_control.fattributes.get('break_when'), self._task.loop_control.break_when, templar
                )
                if cond.evaluate_conditional(templar, task_vars):
                    # delete loop vars before exiting loop
                    del task_vars[loop_var]
                    break

            # done with loop var, remove for next iteration
            del task_vars[loop_var]

            # clear 'connection related' plugin variables for next iteration
            if self._connection:
                clear_plugins = {
                    'connection': self._connection._load_name,
                    'shell': self._connection._shell._load_name
                }
                if self._connection.become:
                    clear_plugins['become'] = self._connection.become._load_name

                for plugin_type, plugin_name in clear_plugins.items():
                    for var in C.config.get_plugin_vars(plugin_type, plugin_name):
                        if var in task_vars and var not in self._job_vars:
                            del task_vars[var]

        self._task.no_log = no_log
        # NOTE: run_once cannot contain loop vars because it's templated earlier also
        # This is saving the post-validated field from the last loop so the strategy can use the templated value post task execution
        self._task.run_once = task_fields.get('run_once')
        self._task.action = task_fields.get('action')

        return results

    def _calculate_delegate_to(self, templar, variables):
        """This method is responsible for effectively pre-validating Task.delegate_to and will
        happen before Task.post_validate is executed
        """
        delegated_vars, delegated_host_name = self._variable_manager.get_delegated_vars_and_hostname(templar, self._task, variables)
        # At the point this is executed it is safe to mutate self._task,
        # since `self._task` is either a copy referred to by `tmp_task` in `_run_loop`
        # or just a singular non-looped task
        if delegated_host_name:
            self._task.delegate_to = delegated_host_name
            variables.update(delegated_vars)

    def _execute(self, variables=None):
        """
        The primary workhorse of the executor system, this runs the task
        on the specified host (which may be the delegated_to host) and handles
        the retry/until and block rescue/always execution
        """

        if variables is None:
            variables = self._job_vars

        templar = Templar(loader=self._loader, variables=variables)

        self._calculate_delegate_to(templar, variables)

        context_validation_error = None

        # a certain subset of variables exist.
        tempvars = variables.copy()

        try:
            # TODO: remove play_context as this does not take delegation nor loops correctly into account,
            # the task itself should hold the correct values for connection/shell/become/terminal plugin options to finalize.
            #  Kept for now for backwards compatibility and a few functions that are still exclusive to it.

            # apply the given task's information to the connection info,
            # which may override some fields already set by the play or
            # the options specified on the command line
            self._play_context = self._play_context.set_task_and_variable_override(task=self._task, variables=variables, templar=templar)

            # fields set from the play/task may be based on variables, so we have to
            # do the same kind of post validation step on it here before we use it.
            self._play_context.post_validate(templar=templar)

            # now that the play context is finalized, if the remote_addr is not set
            # default to using the host's address field as the remote address
            if not self._play_context.remote_addr:
                self._play_context.remote_addr = self._host.address

            # We also add "magic" variables back into the variables dict to make sure
            self._play_context.update_vars(tempvars)

        except AnsibleError as e:
            # save the error, which we'll raise later if we don't end up
            # skipping this task during the conditional evaluation step
            context_validation_error = e

        no_log = self._play_context.no_log

        # Evaluate the conditional (if any) for this task, which we do before running
        # the final task post-validation. We do this before the post validation due to
        # the fact that the conditional may specify that the task be skipped due to a
        # variable not being present which would otherwise cause validation to fail
        try:
            conditional_result, false_condition = self._task.evaluate_conditional_with_result(templar, tempvars)
            if not conditional_result:
                display.debug("when evaluation is False, skipping this task")
                return dict(changed=False, skipped=True, skip_reason='Conditional result was False',
                            false_condition=false_condition, _ansible_no_log=no_log)
        except AnsibleError as e:
            # loop error takes precedence
            if self._loop_eval_error is not None:
                # Display the error from the conditional as well to prevent
                # losing information useful for debugging.
                display.v(to_text(e))
                raise self._loop_eval_error  # pylint: disable=raising-bad-type
            raise

        # Not skipping, if we had loop error raised earlier we need to raise it now to halt the execution of this task
        if self._loop_eval_error is not None:
            raise self._loop_eval_error  # pylint: disable=raising-bad-type

        # if we ran into an error while setting up the PlayContext, raise it now, unless is known issue with delegation
        # and undefined vars (correct values are in cvars later on and connection plugins, if still error, blows up there)
        if context_validation_error is not None:
            raiseit = True
            if self._task.delegate_to:
                if isinstance(context_validation_error, AnsibleUndefinedVariable):
                    raiseit = False
                elif isinstance(context_validation_error, AnsibleParserError):
                    # parser error, might be cause by undef too
                    orig_exc = getattr(context_validation_error, 'orig_exc', None)
                    if isinstance(orig_exc, AnsibleUndefinedVariable):
                        raiseit = False
            if raiseit:
                raise context_validation_error  # pylint: disable=raising-bad-type

        # set templar to use temp variables until loop is evaluated
        templar.available_variables = tempvars

        # if this task is a TaskInclude, we just return now with a success code so the
        # main thread can expand the task list for the given host
        if self._task.action in C._ACTION_INCLUDE_TASKS:
            include_args = self._task.args.copy()
            include_file = include_args.pop('_raw_params', None)
            if not include_file:
                return dict(failed=True, msg="No include file was specified to the include")

            include_file = templar.template(include_file)
            return dict(include=include_file, include_args=include_args)

        # if this task is a IncludeRole, we just return now with a success code so the main thread can expand the task list for the given host
        elif self._task.action in C._ACTION_INCLUDE_ROLE:
            include_args = self._task.args.copy()
            return dict(include_args=include_args)

        # Now we do final validation on the task, which sets all fields to their final values.
        try:
            self._task.post_validate(templar=templar)
        except AnsibleError:
            raise
        except Exception:
            return dict(changed=False, failed=True, _ansible_no_log=no_log, exception=to_text(traceback.format_exc()))
        if '_variable_params' in self._task.args:
            variable_params = self._task.args.pop('_variable_params')
            if isinstance(variable_params, dict):
                if C.INJECT_FACTS_AS_VARS:
                    display.warning("Using a variable for a task's 'args' is unsafe in some situations "
                                    "(see https://docs.ansible.com/ansible/devel/reference_appendices/faq.html#argsplat-unsafe)")
                variable_params.update(self._task.args)
                self._task.args = variable_params
            else:
                # if we didn't get a dict, it means there's garbage remaining after k=v parsing, just give up
                # see https://github.com/ansible/ansible/issues/79862
                raise AnsibleError(f"invalid or malformed argument: '{variable_params}'")

        # update no_log to task value, now that we have it templated
        no_log = self._task.no_log

        # free tempvars up, not used anymore, cvars and vars_copy should be mainly used after this point
        # updating the original 'variables' at the end
        tempvars = {}

        # setup cvars copy, used for all connection related templating
        if self._task.delegate_to:
            # use vars from delegated host (which already include task vars) instead of original host
            cvars = variables.get('ansible_delegated_vars', {}).get(self._task.delegate_to, {})
        else:
            # just use normal host vars
            cvars = variables

        templar.available_variables = cvars

        # use magic var if it exists, if not, let task inheritance do it's thing.
        if cvars.get('ansible_connection') is not None:
            current_connection = templar.template(cvars['ansible_connection'])
        else:
            current_connection = self._task.connection

        # get the connection and the handler for this execution
        if (not self._connection or
                not getattr(self._connection, 'connected', False) or
                not self._connection.matches_name([current_connection]) or
                # pc compare, left here for old plugins, but should be irrelevant for those
                # using get_option, since they are cleared each iteration.
                self._play_context.remote_addr != self._connection._play_context.remote_addr):
            self._connection = self._get_connection(cvars, templar, current_connection)
        else:
            # if connection is reused, its _play_context is no longer valid and needs
            # to be replaced with the one templated above, in case other data changed
            self._connection._play_context = self._play_context
            self._set_become_plugin(cvars, templar, self._connection)

        plugin_vars = self._set_connection_options(cvars, templar)

        # make a copy of the job vars here, as we update them here and later,
        # but don't want to pollute original
        vars_copy = variables.copy()
        # update with connection info (i.e ansible_host/ansible_user)
        self._connection.update_vars(vars_copy)
        templar.available_variables = vars_copy

        # TODO: eventually remove as pc is taken out of the resolution path
        # feed back into pc to ensure plugins not using get_option can get correct value
        self._connection._play_context = self._play_context.set_task_and_variable_override(task=self._task, variables=vars_copy, templar=templar)

        # TODO: eventually remove this block as this should be a 'consequence' of 'forced_local' modules, right now rely on remote_is_local connection
        # special handling for python interpreter for network_os, default to ansible python unless overridden
        if 'ansible_python_interpreter' not in cvars and 'ansible_network_os' in cvars and getattr(self._connection, '_remote_is_local', False):
            # this also avoids 'python discovery'
            cvars['ansible_python_interpreter'] = sys.executable

        # get handler
        self._handler, module_context = self._get_action_handler_with_module_context(templar=templar)

        if module_context is not None:
            module_defaults_fqcn = module_context.resolved_fqcn
        else:
            module_defaults_fqcn = self._task.resolved_action

        # Apply default params for action/module, if present
        self._task.args = get_action_args_with_defaults(
            module_defaults_fqcn, self._task.args, self._task.module_defaults, templar,
            action_groups=self._task._parent._play._action_groups
        )

        # And filter out any fields which were set to default(omit), and got the omit token value
        omit_token = variables.get('omit')
        if omit_token is not None:
            self._task.args = remove_omit(self._task.args, omit_token)

        retries = 1  # includes the default actual run + retries set by user/default
        if self._task.retries is not None:
            retries += max(0, self._task.retries)
        elif self._task.until:
            retries += 3  # the default is not set in FA because we need to differentiate "unset" value

        delay = self._task.delay
        if delay < 0:
            delay = 1

        display.debug("starting attempt loop")
        result = None
        for attempt in range(1, retries + 1):
            display.debug("running the handler")
            try:
                if self._task.timeout:
                    old_sig = signal.signal(signal.SIGALRM, task_timeout)
                    signal.alarm(self._task.timeout)
                result = self._handler.run(task_vars=vars_copy)
            except (AnsibleActionFail, AnsibleActionSkip) as e:
                return e.result
            except AnsibleConnectionFailure as e:
                return dict(unreachable=True, msg=to_text(e))
            except TaskTimeoutError as e:
                msg = 'The %s action failed to execute in the expected time frame (%d) and was terminated' % (self._task.action, self._task.timeout)
                return dict(failed=True, msg=msg, timedout={'frame': e.frame, 'period': self._task.timeout})
            finally:
                if self._task.timeout:
                    signal.alarm(0)
                    old_sig = signal.signal(signal.SIGALRM, old_sig)
                self._handler.cleanup()
            display.debug("handler run complete")

            # propagate no log to result- the action can set this, so only overwrite it with the task's value if missing or falsey
            result["_ansible_no_log"] = bool(no_log or result.get('_ansible_no_log', False))

            if self._task.action not in C._ACTION_WITH_CLEAN_FACTS:
                result = wrap_var(result)

            # update the local copy of vars with the registered value, if specified,
            # or any facts which may have been generated by the module execution
            if self._task.register:
                vars_copy[self._task.register] = result

            if self._task.async_val > 0:
                if self._task.poll > 0 and not result.get('skipped') and not result.get('failed'):
                    result = self._poll_async_result(result=result, templar=templar, task_vars=vars_copy)
                    if result.get('failed'):
                        self._final_q.send_callback(
                            'v2_runner_on_async_failed',
                            TaskResult(self._host.name,
                                       self._task._uuid,
                                       result,
                                       task_fields=self._task.dump_attrs()))
                    else:
                        self._final_q.send_callback(
                            'v2_runner_on_async_ok',
                            TaskResult(self._host.name,
                                       self._task._uuid,
                                       result,
                                       task_fields=self._task.dump_attrs()))

                # ensure no log is preserved
                result["_ansible_no_log"] = no_log

            # helper methods for use below in evaluating changed/failed_when
            def _evaluate_changed_when_result(result):
                if self._task.changed_when is not None and self._task.changed_when:
                    cond = Conditional(loader=self._loader)
                    cond.when = self._task.changed_when
                    result['changed'] = cond.evaluate_conditional(templar, vars_copy)

            def _evaluate_failed_when_result(result):
                if self._task.failed_when:
                    cond = Conditional(loader=self._loader)
                    cond.when = self._task.failed_when
                    failed_when_result = cond.evaluate_conditional(templar, vars_copy)
                    result['failed_when_result'] = result['failed'] = failed_when_result
                else:
                    failed_when_result = False
                return failed_when_result

            if 'ansible_facts' in result and self._task.action not in C._ACTION_DEBUG:
                if self._task.action in C._ACTION_WITH_CLEAN_FACTS:
                    if self._task.delegate_to and self._task.delegate_facts:
                        if '_ansible_delegated_vars' in vars_copy:
                            vars_copy['_ansible_delegated_vars'].update(result['ansible_facts'])
                        else:
                            vars_copy['_ansible_delegated_vars'] = result['ansible_facts']
                    else:
                        vars_copy.update(result['ansible_facts'])
                else:
                    # TODO: cleaning of facts should eventually become part of taskresults instead of vars
                    af = wrap_var(result['ansible_facts'])
                    vars_copy['ansible_facts'] = combine_vars(vars_copy.get('ansible_facts', {}), namespace_facts(af))
                    if C.INJECT_FACTS_AS_VARS:
                        vars_copy.update(clean_facts(af))

            # set the failed property if it was missing.
            if 'failed' not in result:
                # rc is here for backwards compatibility and modules that use it instead of 'failed'
                if 'rc' in result and result['rc'] not in [0, "0"]:
                    result['failed'] = True
                else:
                    result['failed'] = False

            # Make attempts and retries available early to allow their use in changed/failed_when
            if retries > 1:
                result['attempts'] = attempt

            # set the changed property if it was missing.
            if 'changed' not in result:
                result['changed'] = False

            if self._task.action not in C._ACTION_WITH_CLEAN_FACTS:
                result = wrap_var(result)

            # re-update the local copy of vars with the registered value, if specified,
            # or any facts which may have been generated by the module execution
            # This gives changed/failed_when access to additional recently modified
            # attributes of result
            if self._task.register:
                vars_copy[self._task.register] = result

            # if we didn't skip this task, use the helpers to evaluate the changed/
            # failed_when properties
            if 'skipped' not in result:
                condname = 'changed'

                try:
                    _evaluate_changed_when_result(result)
                    condname = 'failed'
                    _evaluate_failed_when_result(result)
                except AnsibleError as e:
                    result['failed'] = True
                    result['%s_when_result' % condname] = to_text(e)

            if retries > 1:
                cond = Conditional(loader=self._loader)
                cond.when = self._task.until or [not result['failed']]
                if cond.evaluate_conditional(templar, vars_copy):
                    break
                else:
                    # no conditional check, or it failed, so sleep for the specified time
                    if attempt < retries:
                        result['_ansible_retry'] = True
                        result['retries'] = retries
                        display.debug('Retrying task, attempt %d of %d' % (attempt, retries))
                        self._final_q.send_callback(
                            'v2_runner_retry',
                            TaskResult(
                                self._host.name,
                                self._task._uuid,
                                result,
                                task_fields=self._task.dump_attrs()
                            )
                        )
                        time.sleep(delay)
                        self._handler = self._get_action_handler(templar=templar)
        else:
            if retries > 1:
                # we ran out of attempts, so mark the result as failed
                result['attempts'] = retries - 1
                result['failed'] = True

        if self._task.action not in C._ACTION_WITH_CLEAN_FACTS:
            result = wrap_var(result)

        # do the final update of the local variables here, for both registered
        # values and any facts which may have been created
        if self._task.register:
            variables[self._task.register] = result

        if 'ansible_facts' in result and self._task.action not in C._ACTION_DEBUG:
            if self._task.action in C._ACTION_WITH_CLEAN_FACTS:
                variables.update(result['ansible_facts'])
            else:
                # TODO: cleaning of facts should eventually become part of taskresults instead of vars
                af = wrap_var(result['ansible_facts'])
                variables['ansible_facts'] = combine_vars(variables.get('ansible_facts', {}), namespace_facts(af))
                if C.INJECT_FACTS_AS_VARS:
                    variables.update(clean_facts(af))

        # save the notification target in the result, if it was specified, as
        # this task may be running in a loop in which case the notification
        # may be item-specific, ie. "notify: service {{item}}"
        if self._task.notify is not None:
            result['_ansible_notify'] = self._task.notify

        # add the delegated vars to the result, so we can reference them
        # on the results side without having to do any further templating
        # also now add connection vars results when delegating
        if self._task.delegate_to:
            result["_ansible_delegated_vars"] = {'ansible_delegated_host': self._task.delegate_to}
            for k in plugin_vars:
                result["_ansible_delegated_vars"][k] = cvars.get(k)

            # note: here for callbacks that rely on this info to display delegation
            for requireshed in ('ansible_host', 'ansible_port', 'ansible_user', 'ansible_connection'):
                if requireshed not in result["_ansible_delegated_vars"] and requireshed in cvars:
                    result["_ansible_delegated_vars"][requireshed] = cvars.get(requireshed)

        # and return
        display.debug("attempt loop complete, returning result")
        return result

    def _poll_async_result(self, result, templar, task_vars=None):
        """
        Polls for the specified JID to be complete
        """

        if task_vars is None:
            task_vars = self._job_vars

        async_jid = result.get('ansible_job_id')
        if async_jid is None:
            return dict(failed=True, msg="No job id was returned by the async task")

        # Create a new pseudo-task to run the async_status module, and run
        # that (with a sleep for "poll" seconds between each retry) until the
        # async time limit is exceeded.

        async_task = Task.load(dict(
            action='async_status',
            args={'jid': async_jid},
            check_mode=self._task.check_mode,
            environment=self._task.environment,
        ))

        # FIXME: this is no longer the case, normal takes care of all, see if this can just be generalized
        # Because this is an async task, the action handler is async. However,
        # we need the 'normal' action handler for the status check, so get it
        # now via the action_loader
        async_handler = self._shared_loader_obj.action_loader.get(
            'ansible.legacy.async_status',
            task=async_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=templar,
            shared_loader_obj=self._shared_loader_obj,
        )

        time_left = self._task.async_val
        while time_left > 0:
            time.sleep(self._task.poll)

            try:
                async_result = async_handler.run(task_vars=task_vars)
                # We do not bail out of the loop in cases where the failure
                # is associated with a parsing error. The async_runner can
                # have issues which result in a half-written/unparseable result
                # file on disk, which manifests to the user as a timeout happening
                # before it's time to timeout.
                if (int(async_result.get('finished', 0)) == 1 or
                        ('failed' in async_result and async_result.get('_ansible_parsed', False)) or
                        'skipped' in async_result):
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
                self._final_q.send_callback(
                    'v2_runner_on_async_poll',
                    TaskResult(
                        self._host.name,
                        async_task._uuid,
                        async_result,
                        task_fields=async_task.dump_attrs(),
                    ),
                )

        if int(async_result.get('finished', 0)) != 1:
            if async_result.get('_ansible_parsed'):
                return dict(failed=True, msg="async task did not complete within the requested time - %ss" % self._task.async_val, async_result=async_result)
            else:
                return dict(failed=True, msg="async task produced unparseable results", async_result=async_result)
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
                }
            )
            cleanup_handler = self._shared_loader_obj.action_loader.get(
                'ansible.legacy.async_status',
                task=cleanup_task,
                connection=self._connection,
                play_context=self._play_context,
                loader=self._loader,
                templar=templar,
                shared_loader_obj=self._shared_loader_obj,
            )
            cleanup_handler.run(task_vars=task_vars)
            cleanup_handler.cleanup(force=True)
            async_handler.cleanup(force=True)
            return async_result

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

        # TODO: play context has logic to update the connection for 'smart'
        # (default value, will chose between ssh and paramiko) and 'persistent'
        # (really paramiko), eventually this should move to task object itself.
        conn_type = self._play_context.connection

        connection, plugin_load_context = self._shared_loader_obj.connection_loader.get_with_context(
            conn_type,
            self._play_context,
            self._new_stdin,
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
                options[k] = templar.template(variables[k])
        # TODO move to task method?
        plugin.set_options(task_keys=task_keys, var_options=options)

        return option_vars

    def _set_connection_options(self, variables, templar):

        # keep list of variable names possibly consumed
        varnames = []

        # grab list of usable vars for this plugin
        option_vars = C.config.get_plugin_vars('connection', self._connection._load_name)
        varnames.extend(option_vars)

        # create dict of 'templated vars'
        options = {'_extras': {}}
        for k in option_vars:
            if k in variables:
                options[k] = templar.template(variables[k])

        # add extras if plugin supports them
        if getattr(self._connection, 'allow_extras', False):
            for k in variables:
                if k.startswith('ansible_%s_' % self._connection.extras_prefix) and k not in options:
                    options['_extras'][k] = templar.template(variables[k])

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
        self._connection.set_options(task_keys=task_keys, var_options=options)
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

    def _get_action_handler(self, templar):
        """
        Returns the correct action plugin to handle the requestion task action
        """
        return self._get_action_handler_with_module_context(templar)[0]

    def _get_action_handler_with_module_context(self, templar):
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
        elif all((module_prefix in C.NETWORK_GROUP_MODULES, self._shared_loader_obj.action_loader.has_plugin(network_action, collection_list=collections))):
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
            templar=templar,
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
    write_to_stream(p.stdin, play_context.serialize())

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
