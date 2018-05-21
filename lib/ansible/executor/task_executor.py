# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pty
import time
import json
import subprocess
import sys
import traceback

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleConnectionFailure, AnsibleActionFail, AnsibleActionSkip
from ansible.executor.task_result import TaskResult
from ansible.module_utils.six import iteritems, string_types, binary_type
from ansible.module_utils.six.moves import cPickle
from ansible.module_utils._text import to_text, to_native
from ansible.playbook.conditional import Conditional
from ansible.playbook.task import Task
from ansible.template import Templar
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.utils.unsafe_proxy import UnsafeProxy, wrap_var
from ansible.vars.clean import namespace_facts, clean_facts
from ansible.utils.vars import combine_vars

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ['TaskExecutor']


def remove_omit(task_args, omit_token):
    '''
    Remove args with a value equal to the ``omit_token`` recursively
    to align with now having suboptions in the argument_spec
    '''
    new_args = {}

    for i in iteritems(task_args):
        if i[1] == omit_token:
            continue
        elif isinstance(i[1], dict):
            new_args[i[0]] = remove_omit(i[1], omit_token)
        else:
            new_args[i[0]] = i[1]

    return new_args


class TaskExecutor:

    '''
    This is the main worker class for the executor pipeline, which
    handles loading an action plugin to actually dispatch the task to
    a given host. This class roughly corresponds to the old Runner()
    class.
    '''

    # Modules that we optimize by squashing loop items into a single call to
    # the module
    SQUASH_ACTIONS = frozenset(C.DEFAULT_SQUASH_ACTIONS)

    def __init__(self, host, task, job_vars, play_context, new_stdin, loader, shared_loader_obj, rslt_q):
        self._host = host
        self._task = task
        self._job_vars = job_vars
        self._play_context = play_context
        self._new_stdin = new_stdin
        self._loader = loader
        self._shared_loader_obj = shared_loader_obj
        self._connection = None
        self._rslt_q = rslt_q
        self._loop_eval_error = None

        self._task.squash()

    def run(self):
        '''
        The main executor entrypoint, where we determine if the specified
        task requires looping and either runs the task with self._run_loop()
        or self._execute(). After that, the returned results are parsed and
        returned as a dict.
        '''

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

                    # loop through the item results, and set the global changed/failed result flags based on any item.
                    for item in item_results:
                        if 'changed' in item and item['changed'] and not res.get('changed'):
                            res['changed'] = True
                        if 'failed' in item and item['failed']:
                            item_ignore = item.pop('_ansible_ignore_errors')
                            if not res.get('failed'):
                                res['failed'] = True
                                res['msg'] = 'One or more items failed'
                                self._task.ignore_errors = item_ignore
                            elif self._task.ignore_errors and not item_ignore:
                                self._task.ignore_errors = item_ignore

                        # ensure to accumulate these
                        for array in ['warnings', 'deprecations']:
                            if array in item and item[array]:
                                if array not in res:
                                    res[array] = []
                                if not isinstance(item[array], list):
                                    item[array] = [item[array]]
                                res[array] = res[array] + item[array]
                                del item[array]

                    if not res.get('Failed', False):
                        res['msg'] = 'All items completed'
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
                if isinstance(res, UnsafeProxy):
                    return res._obj
                elif isinstance(res, binary_type):
                    return to_text(res, errors=errors)
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
            return dict(failed=True, msg=wrap_var(to_text(e, nonstring='simplerepr')))
        except Exception as e:
            return dict(failed=True, msg='Unexpected failure during module execution.', exception=to_text(traceback.format_exc()), stdout='')
        finally:
            try:
                self._connection.close()
            except AttributeError:
                pass
            except Exception as e:
                display.debug(u"error closing connection: %s" % to_text(e))

    def _get_loop_items(self):
        '''
        Loads a lookup plugin to handle the with_* portion of a task (if specified),
        and returns the items result.
        '''

        # save the play context variables to a temporary dictionary,
        # so that we can modify the job vars without doing a full copy
        # and later restore them to avoid modifying things too early
        play_context_vars = dict()
        self._play_context.update_vars(play_context_vars)

        old_vars = dict()
        for k in play_context_vars:
            if k in self._job_vars:
                old_vars[k] = self._job_vars[k]
            self._job_vars[k] = play_context_vars[k]

        # get search path for this task to pass to lookup plugins
        self._job_vars['ansible_search_path'] = self._task.get_search_path()

        templar = Templar(loader=self._loader, shared_loader_obj=self._shared_loader_obj, variables=self._job_vars)
        items = None
        if self._task.loop_with:
            if self._task.loop_with in self._shared_loader_obj.lookup_loader:
                fail = True
                if self._task.loop_with == 'first_found':
                    # first_found loops are special. If the item is undefined then we want to fall through to the next value rather than failing.
                    fail = False

                loop_terms = listify_lookup_plugin_terms(terms=self._task.loop, templar=templar, loader=self._loader, fail_on_undefined=fail,
                                                         convert_bare=False)
                if not fail:
                    loop_terms = [t for t in loop_terms if not templar._contains_vars(t)]

                # get lookup
                mylookup = self._shared_loader_obj.lookup_loader.get(self._task.loop_with, loader=self._loader, templar=templar)

                # give lookup task 'context' for subdir (mostly needed for first_found)
                for subdir in ['template', 'var', 'file']:  # TODO: move this to constants?
                    if subdir in self._task.action:
                        break
                setattr(mylookup, '_subdir', subdir + 's')

                # run lookup
                items = mylookup.run(terms=loop_terms, variables=self._job_vars, wantlist=True)
            else:
                raise AnsibleError("Unexpected failure in finding the lookup named '%s' in the available lookup plugins" % self._task.loop_with)

        elif self._task.loop:
            items = templar.template(self._task.loop)
            if not isinstance(items, list):
                raise AnsibleError(
                    "Invalid data passed to 'loop', it requires a list, got this instead: %s."
                    " Hint: If you passed a list/dict of just one element,"
                    " try adding wantlist=True to your lookup invocation or use q/query instead of lookup." % items
                )

        # now we restore any old job variables that may have been modified,
        # and delete them if they were in the play context vars but not in
        # the old variables dictionary
        for k in play_context_vars:
            if k in old_vars:
                self._job_vars[k] = old_vars[k]
            else:
                del self._job_vars[k]

        if items:
            for idx, item in enumerate(items):
                if item is not None and not isinstance(item, UnsafeProxy):
                    items[idx] = UnsafeProxy(item)

        # ensure basedir is always in (dwim already searches here but we need to display it)
        if self._loader.get_basedir() not in self._job_vars['ansible_search_path']:
            self._job_vars['ansible_search_path'].append(self._loader.get_basedir())

        return items

    def _run_loop(self, items):
        '''
        Runs the task with the loop items specified and collates the result
        into an array named 'results' which is inserted into the final result
        along with the item for which the loop ran.
        '''

        results = []

        # make copies of the job vars and task so we can add the item to
        # the variables and re-validate the task with the item variable
        # task_vars = self._job_vars.copy()
        task_vars = self._job_vars

        loop_var = 'item'
        index_var = None
        label = None
        loop_pause = 0
        templar = Templar(loader=self._loader, shared_loader_obj=self._shared_loader_obj, variables=self._job_vars)
        if self._task.loop_control:
            # FIXME: move this to the object itself to allow post_validate to take care of templating
            loop_var = templar.template(self._task.loop_control.loop_var)
            index_var = templar.template(self._task.loop_control.index_var)
            loop_pause = templar.template(self._task.loop_control.pause)
            # the these may be 'None', so we still need to default to something useful
            # this is tempalted below after an item is assigned
            label = (self._task.loop_control.label or ('{{' + loop_var + '}}'))

        if loop_var in task_vars:
            display.warning(u"The loop variable '%s' is already in use. "
                            u"You should set the `loop_var` value in the `loop_control` option for the task"
                            u" to something else to avoid variable collisions and unexpected behavior." % loop_var)

        ran_once = False
        if self._task.loop_with:
            # Only squash with 'with_:' not with the 'loop:', 'magic' squashing can be removed once with_ loops are
            items = self._squash_items(items, loop_var, task_vars)

        for item_index, item in enumerate(items):
            task_vars[loop_var] = item
            if index_var:
                task_vars[index_var] = item_index

            # Update template vars to reflect current loop iteration
            templar.set_available_variables(task_vars)

            # pause between loop iterations
            if loop_pause and ran_once:
                try:
                    time.sleep(float(loop_pause))
                except ValueError as e:
                    raise AnsibleError('Invalid pause value: %s, produced error: %s' % (loop_pause, to_native(e)))
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
            task_fields = self._task.dump_attrs()
            (self._task, tmp_task) = (tmp_task, self._task)
            (self._play_context, tmp_play_context) = (tmp_play_context, self._play_context)

            # now update the result with the item info, and append the result
            # to the list of results
            res[loop_var] = item
            if index_var:
                res[index_var] = item_index
            res['_ansible_item_result'] = True
            res['_ansible_ignore_errors'] = task_fields.get('ignore_errors')

            if label is not None:
                res['_ansible_item_label'] = templar.template(label, cache=False)

            self._rslt_q.put(
                TaskResult(
                    self._host.name,
                    self._task._uuid,
                    res,
                    task_fields=task_fields,
                ),
                block=False,
            )
            results.append(res)
            del task_vars[loop_var]

        return results

    def _squash_items(self, items, loop_var, variables):
        '''
        Squash items down to a comma-separated list for certain modules which support it
        (typically package management modules).
        '''
        name = None
        try:
            # _task.action could contain templatable strings (via action: and
            # local_action:)  Template it before comparing.  If we don't end up
            # optimizing it here, the templatable string might use template vars
            # that aren't available until later (it could even use vars from the
            # with_items loop) so don't make the templated string permanent yet.
            templar = Templar(loader=self._loader, shared_loader_obj=self._shared_loader_obj, variables=variables)
            task_action = self._task.action
            if templar._contains_vars(task_action):
                task_action = templar.template(task_action, fail_on_undefined=False)

            if len(items) > 0 and task_action in self.SQUASH_ACTIONS:
                if all(isinstance(o, string_types) for o in items):
                    final_items = []

                    for allowed in ['name', 'pkg', 'package']:
                        name = self._task.args.pop(allowed, None)
                        if name is not None:
                            break

                    # This gets the information to check whether the name field
                    # contains a template that we can squash for
                    template_no_item = template_with_item = None
                    if name:
                        if templar._contains_vars(name):
                            variables[loop_var] = '\0$'
                            template_no_item = templar.template(name, variables, cache=False)
                            variables[loop_var] = '\0@'
                            template_with_item = templar.template(name, variables, cache=False)
                            del variables[loop_var]

                        # Check if the user is doing some operation that doesn't take
                        # name/pkg or the name/pkg field doesn't have any variables
                        # and thus the items can't be squashed
                        if template_no_item != template_with_item:
                            for item in items:
                                variables[loop_var] = item
                                if self._task.evaluate_conditional(templar, variables):
                                    new_item = templar.template(name, cache=False)
                                    final_items.append(new_item)
                            self._task.args['name'] = final_items
                            # Wrap this in a list so that the calling function loop
                            # executes exactly once
                            return [final_items]
                        else:
                            # Restore the name parameter
                            self._task.args['name'] = name
                # elif:
                    # Right now we only optimize single entries.  In the future we
                    # could optimize more types:
                    # * lists can be squashed together
                    # * dicts could squash entries that match in all cases except the
                    #   name or pkg field.
        except Exception:
            # Squashing is an optimization.  If it fails for any reason,
            # simply use the unoptimized list of items.

            # Restore the name parameter
            if name is not None:
                self._task.args['name'] = name
        return items

    def _execute(self, variables=None):
        '''
        The primary workhorse of the executor system, this runs the task
        on the specified host (which may be the delegated_to host) and handles
        the retry/until and block rescue/always execution
        '''

        if variables is None:
            variables = self._job_vars

        templar = Templar(loader=self._loader, shared_loader_obj=self._shared_loader_obj, variables=variables)

        context_validation_error = None
        try:
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
            # a certain subset of variables exist.
            self._play_context.update_vars(variables)

            # FIXME: update connection/shell plugin options
        except AnsibleError as e:
            # save the error, which we'll raise later if we don't end up
            # skipping this task during the conditional evaluation step
            context_validation_error = e

        # Evaluate the conditional (if any) for this task, which we do before running
        # the final task post-validation. We do this before the post validation due to
        # the fact that the conditional may specify that the task be skipped due to a
        # variable not being present which would otherwise cause validation to fail
        try:
            if not self._task.evaluate_conditional(templar, variables):
                display.debug("when evaluation is False, skipping this task")
                return dict(changed=False, skipped=True, skip_reason='Conditional result was False', _ansible_no_log=self._play_context.no_log)
        except AnsibleError:
            # loop error takes precedence
            if self._loop_eval_error is not None:
                raise self._loop_eval_error  # pylint: disable=raising-bad-type
            raise

        # Not skipping, if we had loop error raised earlier we need to raise it now to halt the execution of this task
        if self._loop_eval_error is not None:
            raise self._loop_eval_error  # pylint: disable=raising-bad-type

        # if we ran into an error while setting up the PlayContext, raise it now
        if context_validation_error is not None:
            raise context_validation_error  # pylint: disable=raising-bad-type

        # if this task is a TaskInclude, we just return now with a success code so the
        # main thread can expand the task list for the given host
        if self._task.action in ('include', 'include_tasks'):
            include_variables = self._task.args.copy()
            include_file = include_variables.pop('_raw_params', None)
            if not include_file:
                return dict(failed=True, msg="No include file was specified to the include")

            include_file = templar.template(include_file)
            return dict(include=include_file, include_variables=include_variables)

        # if this task is a IncludeRole, we just return now with a success code so the main thread can expand the task list for the given host
        elif self._task.action == 'include_role':
            include_variables = self._task.args.copy()
            return dict(include_variables=include_variables)

        # Now we do final validation on the task, which sets all fields to their final values.
        self._task.post_validate(templar=templar)
        if '_variable_params' in self._task.args:
            variable_params = self._task.args.pop('_variable_params')
            if isinstance(variable_params, dict):
                display.deprecated("Using variables for task params is unsafe, especially if the variables come from an external source like facts",
                                   version="2.6")
                variable_params.update(self._task.args)
                self._task.args = variable_params

        # get the connection and the handler for this execution
        if (not self._connection or
                not getattr(self._connection, 'connected', False) or
                self._play_context.remote_addr != self._connection._play_context.remote_addr):
            self._connection = self._get_connection(variables=variables, templar=templar)
        else:
            # if connection is reused, its _play_context is no longer valid and needs
            # to be replaced with the one templated above, in case other data changed
            self._connection._play_context = self._play_context

        self._set_connection_options(variables, templar)
        self._set_shell_options(variables, templar)

        # get handler
        self._handler = self._get_action_handler(connection=self._connection, templar=templar)

        # Apply default params for action/module, if present
        # These are collected as a list of dicts, so we need to merge them
        module_defaults = {}
        for default in self._task.module_defaults:
            module_defaults.update(default)
        if module_defaults:
            module_defaults = templar.template(module_defaults)
        if self._task.action in module_defaults:
            tmp_args = module_defaults[self._task.action].copy()
            tmp_args.update(self._task.args)
            self._task.args = tmp_args

        # And filter out any fields which were set to default(omit), and got the omit token value
        omit_token = variables.get('omit')
        if omit_token is not None:
            self._task.args = remove_omit(self._task.args, omit_token)

        # Read some values from the task, so that we can modify them if need be
        if self._task.until:
            retries = self._task.retries
            if retries is None:
                retries = 3
            elif retries <= 0:
                retries = 1
            else:
                retries += 1
        else:
            retries = 1

        delay = self._task.delay
        if delay < 0:
            delay = 1

        # make a copy of the job vars here, in case we need to update them
        # with the registered variable value later on when testing conditions
        vars_copy = variables.copy()

        display.debug("starting attempt loop")
        result = None
        for attempt in range(1, retries + 1):
            display.debug("running the handler")
            try:
                result = self._handler.run(task_vars=variables)
            except AnsibleActionSkip as e:
                return dict(skipped=True, msg=to_text(e))
            except AnsibleActionFail as e:
                return dict(failed=True, msg=to_text(e))
            except AnsibleConnectionFailure as e:
                return dict(unreachable=True, msg=to_text(e))
            display.debug("handler run complete")

            # preserve no log
            result["_ansible_no_log"] = self._play_context.no_log

            # update the local copy of vars with the registered value, if specified,
            # or any facts which may have been generated by the module execution
            if self._task.register:
                vars_copy[self._task.register] = wrap_var(result)

            if self._task.async_val > 0:
                if self._task.poll > 0 and not result.get('skipped') and not result.get('failed'):
                    result = self._poll_async_result(result=result, templar=templar, task_vars=vars_copy)
                    # FIXME callback 'v2_runner_on_async_poll' here

                # ensure no log is preserved
                result["_ansible_no_log"] = self._play_context.no_log

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

            if 'ansible_facts' in result:
                if self._task.action in ('set_fact', 'include_vars'):
                    vars_copy.update(result['ansible_facts'])
                else:
                    vars_copy.update(namespace_facts(result['ansible_facts']))
                    if C.INJECT_FACTS_AS_VARS:
                        vars_copy.update(clean_facts(result['ansible_facts']))

            # set the failed property if it was missing.
            if 'failed' not in result:
                # rc is here for backwards compatibility and modules that use it instead of 'failed'
                if 'rc' in result and result['rc'] not in [0, "0"]:
                    result['failed'] = True
                else:
                    result['failed'] = False

            # Make attempts and retries available early to allow their use in changed/failed_when
            if self._task.until:
                result['attempts'] = attempt

            # set the changed property if it was missing.
            if 'changed' not in result:
                result['changed'] = False

            # re-update the local copy of vars with the registered value, if specified,
            # or any facts which may have been generated by the module execution
            # This gives changed/failed_when access to additional recently modified
            # attributes of result
            if self._task.register:
                vars_copy[self._task.register] = wrap_var(result)

            # if we didn't skip this task, use the helpers to evaluate the changed/
            # failed_when properties
            if 'skipped' not in result:
                _evaluate_changed_when_result(result)
                _evaluate_failed_when_result(result)

            if retries > 1:
                cond = Conditional(loader=self._loader)
                cond.when = self._task.until
                if cond.evaluate_conditional(templar, vars_copy):
                    break
                else:
                    # no conditional check, or it failed, so sleep for the specified time
                    if attempt < retries:
                        result['_ansible_retry'] = True
                        result['retries'] = retries
                        display.debug('Retrying task, attempt %d of %d' % (attempt, retries))
                        self._rslt_q.put(TaskResult(self._host.name, self._task._uuid, result, task_fields=self._task.dump_attrs()), block=False)
                        time.sleep(delay)
        else:
            if retries > 1:
                # we ran out of attempts, so mark the result as failed
                result['attempts'] = retries - 1
                result['failed'] = True

        # do the final update of the local variables here, for both registered
        # values and any facts which may have been created
        if self._task.register:
            variables[self._task.register] = wrap_var(result)

        if 'ansible_facts' in result:
            if self._task.action in ('set_fact', 'include_vars'):
                variables.update(result['ansible_facts'])
            else:
                variables.update(namespace_facts(result['ansible_facts']))
                if C.INJECT_FACTS_AS_VARS:
                    variables.update(clean_facts(result['ansible_facts']))

        # save the notification target in the result, if it was specified, as
        # this task may be running in a loop in which case the notification
        # may be item-specific, ie. "notify: service {{item}}"
        if self._task.notify is not None:
            result['_ansible_notify'] = self._task.notify

        # add the delegated vars to the result, so we can reference them
        # on the results side without having to do any further templating
        # FIXME: we only want a limited set of variables here, so this is currently
        #        hardcoded but should be possibly fixed if we want more or if
        #        there is another source of truth we can use
        delegated_vars = variables.get('ansible_delegated_vars', dict()).get(self._task.delegate_to, dict()).copy()
        if len(delegated_vars) > 0:
            result["_ansible_delegated_vars"] = {'ansible_delegated_host': self._task.delegate_to}
            for k in ('ansible_host', ):
                result["_ansible_delegated_vars"][k] = delegated_vars.get(k)

        # and return
        display.debug("attempt loop complete, returning result")
        return result

    def _poll_async_result(self, result, templar, task_vars=None):
        '''
        Polls for the specified JID to be complete
        '''

        if task_vars is None:
            task_vars = self._job_vars

        async_jid = result.get('ansible_job_id')
        if async_jid is None:
            return dict(failed=True, msg="No job id was returned by the async task")

        # Create a new pseudo-task to run the async_status module, and run
        # that (with a sleep for "poll" seconds between each retry) until the
        # async time limit is exceeded.

        async_task = Task().load(dict(action='async_status jid=%s' % async_jid, environment=self._task.environment))

        # FIXME: this is no longer the case, normal takes care of all, see if this can just be generalized
        # Because this is an async task, the action handler is async. However,
        # we need the 'normal' action handler for the status check, so get it
        # now via the action_loader
        normal_handler = self._shared_loader_obj.action_loader.get(
            'normal',
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
                async_result = normal_handler.run(task_vars=task_vars)
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
                    normal_handler._connection._reset()
                except AttributeError:
                    pass

                # Little hack to raise the exception if we've exhausted the timeout period
                time_left -= self._task.poll
                if time_left <= 0:
                    raise
            else:
                time_left -= self._task.poll

        if int(async_result.get('finished', 0)) != 1:
            if async_result.get('_ansible_parsed'):
                return dict(failed=True, msg="async task did not complete within the requested time")
            else:
                return dict(failed=True, msg="async task produced unparseable results", async_result=async_result)
        else:
            return async_result

    def _get_connection(self, variables, templar):
        '''
        Reads the connection property for the host, and returns the
        correct connection object from the list of connection plugins
        '''

        if self._task.delegate_to is not None:
            # since we're delegating, we don't want to use interpreter values
            # which would have been set for the original target host
            for i in list(variables.keys()):
                if isinstance(i, string_types) and i.startswith('ansible_') and i.endswith('_interpreter'):
                    del variables[i]
            # now replace the interpreter values with those that may have come
            # from the delegated-to host
            delegated_vars = variables.get('ansible_delegated_vars', dict()).get(self._task.delegate_to, dict())
            if isinstance(delegated_vars, dict):
                for i in delegated_vars:
                    if isinstance(i, string_types) and i.startswith("ansible_") and i.endswith("_interpreter"):
                        variables[i] = delegated_vars[i]

        conn_type = self._play_context.connection

        connection = self._shared_loader_obj.connection_loader.get(
            conn_type,
            self._play_context,
            self._new_stdin,
            task_uuid=self._task._uuid,
            ansible_playbook_pid=to_text(os.getppid())
        )

        if not connection:
            raise AnsibleError("the connection plugin '%s' was not found" % conn_type)

        # FIXME: remove once all plugins pull all data from self._options
        self._play_context.set_options_from_plugin(connection)

        if any(((connection.supports_persistence and C.USE_PERSISTENT_CONNECTIONS), connection.force_persistence)):
            self._play_context.timeout = connection.get_option('persistent_command_timeout')
            display.vvvv('attempting to start connection', host=self._play_context.remote_addr)
            display.vvvv('using connection plugin %s' % connection.transport, host=self._play_context.remote_addr)
            # We don't need to send the entire contents of variables to ansible-connection
            filtered_vars = dict((key, value) for key, value in variables.items() if key.startswith('ansible'))
            socket_path = self._start_connection(filtered_vars)
            display.vvvv('local domain socket path is %s' % socket_path, host=self._play_context.remote_addr)
            setattr(connection, '_socket_path', socket_path)

        return connection

    def _set_connection_options(self, variables, templar):

        # Keep the pre-delegate values for these keys
        PRESERVE_ORIG = ('inventory_hostname',)

        # create copy with delegation built in
        final_vars = combine_vars(variables, variables.get('ansible_delegated_vars', dict()).get(self._task.delegate_to, dict()))

        # grab list of usable vars for this plugin
        option_vars = C.config.get_plugin_vars('connection', self._connection._load_name)

        # create dict of 'templated vars'
        options = {'_extras': {}}
        for k in option_vars:
            if k in PRESERVE_ORIG:
                options[k] = templar.template(variables[k])
            elif k in final_vars:
                options[k] = templar.template(final_vars[k])

        # add extras if plugin supports them
        if getattr(self._connection, 'allow_extras', False):
            for k in final_vars:
                if k.startswith('ansible_%s_' % self._connection._load_name) and k not in options:
                    options['_extras'][k] = templar.template(final_vars[k])

        # set options with 'templated vars' specific to this plugin
        self._connection.set_options(var_options=options)
        self._set_shell_options(final_vars, templar)

    def _set_shell_options(self, variables, templar):
        option_vars = C.config.get_plugin_vars('shell', self._connection._shell._load_name)
        options = {}
        for k in option_vars:
            if k in variables:
                options[k] = templar.template(variables[k])
        self._connection._shell.set_options(var_options=options)

    def _get_action_handler(self, connection, templar):
        '''
        Returns the correct action plugin to handle the requestion task action
        '''

        module_prefix = self._task.action.split('_')[0]

        # let action plugin override module, fallback to 'normal' action plugin otherwise
        if self._task.action in self._shared_loader_obj.action_loader:
            handler_name = self._task.action
        elif all((module_prefix in C.NETWORK_GROUP_MODULES, module_prefix in self._shared_loader_obj.action_loader)):
            handler_name = module_prefix
        else:
            handler_name = 'normal'

        handler = self._shared_loader_obj.action_loader.get(
            handler_name,
            task=self._task,
            connection=connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=templar,
            shared_loader_obj=self._shared_loader_obj,
        )

        if not handler:
            raise AnsibleError("the handler '%s' was not found" % handler_name)

        return handler

    def _start_connection(self, variables):
        '''
        Starts the persistent connection
        '''
        master, slave = pty.openpty()

        python = sys.executable

        def find_file_in_path(filename):
            # Check $PATH first, followed by same directory as sys.argv[0]
            paths = os.environ['PATH'].split(os.pathsep) + [os.path.dirname(sys.argv[0])]
            for dirname in paths:
                fullpath = os.path.join(dirname, filename)
                if os.path.isfile(fullpath):
                    return fullpath

            raise AnsibleError("Unable to find location of '%s'" % filename)

        p = subprocess.Popen(
            [python, find_file_in_path('ansible-connection'), to_text(os.getppid())],
            stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdin = os.fdopen(master, 'wb', 0)
        os.close(slave)

        # Need to force a protocol that is compatible with both py2 and py3.
        # That would be protocol=2 or less.
        # Also need to force a protocol that excludes certain control chars as
        # stdin in this case is a pty and control chars will cause problems.
        # that means only protocol=0 will work.
        src = cPickle.dumps(self._play_context.serialize(), protocol=0)
        stdin.write(src)
        stdin.write(b'\n#END_INIT#\n')

        src = cPickle.dumps(variables, protocol=0)
        stdin.write(src)
        stdin.write(b'\n#END_VARS#\n')

        stdin.flush()

        (stdout, stderr) = p.communicate()
        stdin.close()

        if p.returncode == 0:
            result = json.loads(to_text(stdout, errors='surrogate_then_replace'))
        else:
            try:
                result = json.loads(to_text(stderr, errors='surrogate_then_replace'))
            except getattr(json.decoder, 'JSONDecodeError', ValueError):
                # JSONDecodeError only available on Python 3.5+
                result = {'error': to_text(stderr, errors='surrogate_then_replace')}

        if 'messages' in result:
            for msg in result.get('messages'):
                display.vvvv('%s' % msg, host=self._play_context.remote_addr)

        if 'error' in result:
            if self._play_context.verbosity > 2:
                if result.get('exception'):
                    msg = "The full traceback is:\n" + result['exception']
                    display.display(msg, color=C.COLOR_ERROR)
            raise AnsibleError(result['error'])

        return result['socket_path']
