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

import base64
import json
import subprocess
import sys
import time

from ansible.compat.six import iteritems

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleConnectionFailure
from ansible.playbook.conditional import Conditional
from ansible.playbook.task import Task
from ansible.template import Templar
from ansible.utils.encrypt import key_for_hostname
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.utils.unicode import to_unicode
from ansible.vars.unsafe_proxy import UnsafeProxy

__all__ = ['TaskExecutor']

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

    def __init__(self, host, task, job_vars, play_context, new_stdin, loader, shared_loader_obj):
        self._host              = host
        self._task              = task
        self._job_vars          = job_vars
        self._play_context      = play_context
        self._new_stdin         = new_stdin
        self._loader            = loader
        self._shared_loader_obj = shared_loader_obj

        try:
            from __main__ import display
            self._display = display
        except ImportError:
            from ansible.utils.display import Display
            self._display = Display()

    def run(self):
        '''
        The main executor entrypoint, where we determine if the specified
        task requires looping and either runs the task with 
        '''

        self._display.debug("in run()")

        try:
            # lookup plugins need to know if this task is executing from
            # a role, so that it can properly find files/templates/etc.
            roledir = None
            if self._task._role:
                roledir = self._task._role._role_path
            self._job_vars['roledir'] = roledir

            items = self._get_loop_items()
            if items is not None:
                if len(items) > 0:
                    item_results = self._run_loop(items)

                    # loop through the item results, and remember the changed/failed
                    # result flags based on any item there.
                    changed = False
                    failed  = False
                    for item in item_results:
                        if 'changed' in item and item['changed']:
                           changed = True
                        if 'failed' in item and item['failed']:
                           failed = True

                    # create the overall result item, and set the changed/failed
                    # flags there to reflect the overall result of the loop
                    res = dict(results=item_results)

                    if changed:
                        res['changed'] = True

                    if failed:
                        res['failed'] = True
                        res['msg'] = 'One or more items failed'
                    else:
                        res['msg'] = 'All items completed'
                else:
                    res = dict(changed=False, skipped=True, skipped_reason='No items in the list', results=[])
            else:
                self._display.debug("calling self._execute()")
                res = self._execute()
                self._display.debug("_execute() done")

            # make sure changed is set in the result, if it's not present
            if 'changed' not in res:
                res['changed'] = False

            def _clean_res(res):
                if isinstance(res, dict):
                    for k in res.keys():
                        res[k] = _clean_res(res[k])
                elif isinstance(res, list):
                    for idx,item in enumerate(res):
                        res[idx] = _clean_res(item)
                elif isinstance(res, UnsafeProxy):
                    return res._obj
                return res

            self._display.debug("dumping result to json")
            res = _clean_res(res)
            self._display.debug("done dumping result, returning")
            return res
        except AnsibleError as e:
            return dict(failed=True, msg=to_unicode(e, nonstring='simplerepr'))
        finally:
            try:
                self._connection.close()
            except AttributeError:
                pass
            except Exception as e:
                self._display.debug("error closing connection: %s" % to_unicode(e))

    def _get_loop_items(self):
        '''
        Loads a lookup plugin to handle the with_* portion of a task (if specified),
        and returns the items result.
        '''

        # create a copy of the job vars here so that we can modify
        # them temporarily without changing them too early for other
        # parts of the code that might still need a pristine version
        vars_copy = self._job_vars.copy()

        # now we update them with the play context vars
        self._play_context.update_vars(vars_copy)

        templar = Templar(loader=self._loader, shared_loader_obj=self._shared_loader_obj, variables=vars_copy)
        items = None
        if self._task.loop:
            if self._task.loop in self._shared_loader_obj.lookup_loader:
                #TODO: remove convert_bare true and deprecate this in with_ 
                try:
                    loop_terms = listify_lookup_plugin_terms(terms=self._task.loop_args, templar=templar, loader=self._loader, fail_on_undefined=True, convert_bare=True)
                except AnsibleUndefinedVariable as e:
                    if 'has no attribute' in str(e):
                        loop_terms = []
                        self._display.deprecated("Skipping task due to undefined attribute, in the future this will be a fatal error.")
                    else:
                        raise
                items = self._shared_loader_obj.lookup_loader.get(self._task.loop, loader=self._loader, templar=templar).run(terms=loop_terms, variables=vars_copy)
            else:
                raise AnsibleError("Unexpected failure in finding the lookup named '%s' in the available lookup plugins" % self._task.loop)

        if items:
            from ansible.vars.unsafe_proxy import UnsafeProxy
            for idx, item in enumerate(items):
                if item is not None and not isinstance(item, UnsafeProxy):
                    items[idx] = UnsafeProxy(item)
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
        task_vars = self._job_vars.copy()

        items = self._squash_items(items, task_vars)
        for item in items:
            task_vars['item'] = item

            try:
                tmp_task = self._task.copy()
                tmp_play_context = self._play_context.copy()
            except AnsibleParserError as e:
                results.append(dict(failed=True, msg=str(e)))
                continue

            # now we swap the internal task and play context with their copies,
            # execute, and swap them back so we can do the next iteration cleanly
            (self._task, tmp_task) = (tmp_task, self._task)
            (self._play_context, tmp_play_context) = (tmp_play_context, self._play_context)
            res = self._execute(variables=task_vars)
            (self._task, tmp_task) = (tmp_task, self._task)
            (self._play_context, tmp_play_context) = (tmp_play_context, self._play_context)

            # now update the result with the item info, and append the result
            # to the list of results
            res['item'] = item
            results.append(res)

        return results

    def _squash_items(self, items, variables):
        '''
        Squash items down to a comma-separated list for certain modules which support it
        (typically package management modules).
        '''
        if len(items) > 0 and self._task.action in self.SQUASH_ACTIONS:
            final_items = []
            name = self._task.args.pop('name', None) or self._task.args.pop('pkg', None)
            for item in items:
                variables['item'] = item
                templar = Templar(loader=self._loader, shared_loader_obj=self._shared_loader_obj, variables=variables)
                if self._task.evaluate_conditional(templar, variables):
                    if templar._contains_vars(name):
                        new_item = templar.template(name)
                        final_items.append(new_item)
                    else:
                        final_items.append(item)
            joined_items = ",".join(final_items)
            self._task.args['name'] = joined_items
            return [joined_items]
        else:
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

        # apply the given task's information to the connection info,
        # which may override some fields already set by the play or
        # the options specified on the command line
        self._play_context = self._play_context.set_task_and_variable_override(task=self._task, variables=variables, templar=templar)

        # fields set from the play/task may be based on variables, so we have to
        # do the same kind of post validation step on it here before we use it.
        # We also add "magic" variables back into the variables dict to make sure
        # a certain subset of variables exist.
        self._play_context.update_vars(variables)
        self._play_context.post_validate(templar=templar)

        # Evaluate the conditional (if any) for this task, which we do before running
        # the final task post-validation. We do this before the post validation due to
        # the fact that the conditional may specify that the task be skipped due to a
        # variable not being present which would otherwise cause validation to fail
        if not self._task.evaluate_conditional(templar, variables):
            self._display.debug("when evaulation failed, skipping this task")
            return dict(changed=False, skipped=True, skip_reason='Conditional check failed', _ansible_no_log=self._play_context.no_log)

        # Now we do final validation on the task, which sets all fields to their final values.
        # In the case of debug tasks, we save any 'var' params and restore them after validating
        # so that variables are not replaced too early.
        prev_var = None
        if self._task.action == 'debug' and 'var' in self._task.args:
            prev_var = self._task.args.pop('var')

        original_args = self._task.args.copy()
        self._task.post_validate(templar=templar)
        if '_variable_params' in self._task.args:
            variable_params = self._task.args.pop('_variable_params')
            if isinstance(variable_params, dict):
                self._display.deprecated("Using variables for task params is unsafe, especially if the variables come from an external source like facts")
                variable_params.update(self._task.args)
                self._task.args = variable_params

        if prev_var is not None:
            self._task.args['var'] = prev_var

        # if this task is a TaskInclude, we just return now with a success code so the
        # main thread can expand the task list for the given host
        if self._task.action == 'include':
            include_variables = original_args
            include_file = include_variables.get('_raw_params')
            del include_variables['_raw_params']
            return dict(include=include_file, include_variables=include_variables)

        # get the connection and the handler for this execution
        self._connection = self._get_connection(variables=variables, templar=templar)
        self._connection.set_host_overrides(host=self._host)

        self._handler = self._get_action_handler(connection=self._connection, templar=templar)

        # And filter out any fields which were set to default(omit), and got the omit token value
        omit_token = variables.get('omit')
        if omit_token is not None:
            self._task.args = dict((i[0], i[1]) for i in iteritems(self._task.args) if i[1] != omit_token)

        # Read some values from the task, so that we can modify them if need be
        retries = self._task.retries
        if retries <= 0:
            retries = 1

        delay = self._task.delay
        if delay < 0:
            delay = 1

        # make a copy of the job vars here, in case we need to update them
        # with the registered variable value later on when testing conditions
        vars_copy = variables.copy()

        self._display.debug("starting attempt loop")
        result = None
        for attempt in range(retries):
            if attempt > 0:
                # FIXME: this should use the self._display.callback/message passing mechanism
                self._display.display("FAILED - RETRYING: %s (%d retries left). Result was: %s" % (self._task, retries-attempt, result), color="red")
                result['attempts'] = attempt + 1

            self._display.debug("running the handler")
            try:
                result = self._handler.run(task_vars=variables)
            except AnsibleConnectionFailure as e:
                return dict(unreachable=True, msg=str(e))
            self._display.debug("handler run complete")

            if self._task.async > 0:
                # the async_wrapper module returns dumped JSON via its stdout
                # response, so we parse it here and replace the result
                try:
                    result = json.loads(result.get('stdout'))
                except (TypeError, ValueError) as e:
                    return dict(failed=True, msg="The async task did not return valid JSON: %s" % str(e))

                if self._task.poll > 0:
                    result = self._poll_async_result(result=result, templar=templar)

            # update the local copy of vars with the registered value, if specified,
            # or any facts which may have been generated by the module execution
            if self._task.register:
                vars_copy[self._task.register] = result 

            if 'ansible_facts' in result:
                vars_copy.update(result['ansible_facts'])

            # create a conditional object to evaluate task conditions
            cond = Conditional(loader=self._loader)

            def _evaluate_changed_when_result(result):
                if self._task.changed_when is not None:
                    cond.when = [ self._task.changed_when ]
                    result['changed'] = cond.evaluate_conditional(templar, vars_copy)

            def _evaluate_failed_when_result(result):
                if self._task.failed_when is not None:
                    cond.when = [ self._task.failed_when ]
                    failed_when_result = cond.evaluate_conditional(templar, vars_copy)
                    result['failed_when_result'] = result['failed'] = failed_when_result
                    return failed_when_result
                return False

            if self._task.until:
                cond.when = self._task.until
                if cond.evaluate_conditional(templar, vars_copy):
                    _evaluate_changed_when_result(result)
                    _evaluate_failed_when_result(result)
                    break
            elif (self._task.changed_when is not None or self._task.failed_when is not None) and 'skipped' not in result:
                    _evaluate_changed_when_result(result)
                    if _evaluate_failed_when_result(result):
                        break
            elif 'failed' not in result:
                if result.get('rc', 0) != 0:
                    result['failed'] = True
                else:
                    # if the result is not failed, stop trying
                    break

            if attempt < retries - 1:
                time.sleep(delay)
            else:
                _evaluate_changed_when_result(result)
                _evaluate_failed_when_result(result)

        # do the final update of the local variables here, for both registered
        # values and any facts which may have been created
        if self._task.register:
            variables[self._task.register] = result

        if 'ansible_facts' in result:
            variables.update(result['ansible_facts'])

        # save the notification target in the result, if it was specified, as
        # this task may be running in a loop in which case the notification
        # may be item-specific, ie. "notify: service {{item}}"
        if self._task.notify is not None:
            result['_ansible_notify'] = self._task.notify

        # preserve no_log setting
        result["_ansible_no_log"] = self._play_context.no_log

        # and return
        self._display.debug("attempt loop complete, returning result")
        return result

    def _poll_async_result(self, result, templar):
        '''
        Polls for the specified JID to be complete
        '''

        async_jid = result.get('ansible_job_id')
        if async_jid is None:
            return dict(failed=True, msg="No job id was returned by the async task")

        # Create a new psuedo-task to run the async_status module, and run
        # that (with a sleep for "poll" seconds between each retry) until the
        # async time limit is exceeded.

        async_task = Task().load(dict(action='async_status jid=%s' % async_jid))

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

        time_left = self._task.async
        while time_left > 0:
            time.sleep(self._task.poll)

            async_result = normal_handler.run()
            if int(async_result.get('finished', 0)) == 1 or 'failed' in async_result or 'skipped' in async_result:
                break

            time_left -= self._task.poll

        if int(async_result.get('finished', 0)) != 1:
            return dict(failed=True, msg="async task did not complete within the requested time")
        else:
            return async_result

    def _get_connection(self, variables, templar):
        '''
        Reads the connection property for the host, and returns the
        correct connection object from the list of connection plugins
        '''

        # FIXME: calculation of connection params/auth stuff should be done here

        if not self._play_context.remote_addr:
            self._play_context.remote_addr = self._host.address

        if self._task.delegate_to is not None:
            # since we're delegating, we don't want to use interpreter values
            # which would have been set for the original target host
            for i in variables.keys():
                if i.startswith('ansible_') and i.endswith('_interpreter'):
                    del variables[i]
            # now replace the interpreter values with those that may have come
            # from the delegated-to host
            delegated_vars = variables.get('ansible_delegated_vars', dict()).get(self._host.name, dict())
            if isinstance(delegated_vars, dict):
                for i in delegated_vars:
                    if i.startswith("ansible_") and i.endswith("_interpreter"):
                        variables[i] = delegated_vars[i]

        conn_type = self._play_context.connection
        if conn_type == 'smart':
            conn_type = 'ssh'
            if sys.platform.startswith('darwin') and self._play_context.password:
                # due to a current bug in sshpass on OSX, which can trigger
                # a kernel panic even for non-privileged users, we revert to
                # paramiko on that OS when a SSH password is specified
                conn_type = "paramiko"
            else:
                # see if SSH can support ControlPersist if not use paramiko
                try:
                    cmd = subprocess.Popen(['ssh','-o','ControlPersist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    (out, err) = cmd.communicate()
                    if "Bad configuration option" in err or "Usage:" in err:
                        conn_type = "paramiko"
                except OSError:
                    conn_type = "paramiko"

        connection = self._shared_loader_obj.connection_loader.get(conn_type, self._play_context, self._new_stdin)
        if not connection:
            raise AnsibleError("the connection plugin '%s' was not found" % conn_type)

        if self._play_context.accelerate:
            # launch the accelerated daemon here
            ssh_connection = connection
            handler = self._shared_loader_obj.action_loader.get(
                'normal',
                task=self._task,
                connection=ssh_connection,
                play_context=self._play_context,
                loader=self._loader,
                templar=templar,
                shared_loader_obj=self._shared_loader_obj,
            )

            key = key_for_hostname(self._play_context.remote_addr)
            accelerate_args = dict(
                password=base64.b64encode(key.__str__()),
                port=self._play_context.accelerate_port,
                minutes=C.ACCELERATE_DAEMON_TIMEOUT,
                ipv6=self._play_context.accelerate_ipv6,
                debug=self._play_context.verbosity,
            )

            connection = self._shared_loader_obj.connection_loader.get('accelerate', self._play_context, self._new_stdin)
            if not connection:
                raise AnsibleError("the connection plugin '%s' was not found" % conn_type)

            try:
                connection._connect()
            except AnsibleConnectionFailure:
                res = handler._execute_module(module_name='accelerate', module_args=accelerate_args, task_vars=variables, delete_remote_tmp=False)
                connection._connect()

        return connection

    def _get_action_handler(self, connection, templar):
        '''
        Returns the correct action plugin to handle the requestion task action
        '''

        if self._task.action in self._shared_loader_obj.action_loader:
            if self._task.async != 0:
                raise AnsibleError("async mode is not supported with the %s module" % self._task.action)
            handler_name = self._task.action
        elif self._task.async == 0:
            handler_name = 'normal'
        else:
            handler_name = 'async'

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

