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

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.executor.connection_info import ConnectionInformation
from ansible.playbook.conditional import Conditional
from ansible.playbook.task import Task
from ansible.plugins import lookup_loader, connection_loader, action_loader
from ansible.utils.listify import listify_lookup_plugin_terms

from ansible.utils.debug import debug

__all__ = ['TaskExecutor']

import json
import time

class TaskExecutor:

    '''
    This is the main worker class for the executor pipeline, which
    handles loading an action plugin to actually dispatch the task to
    a given host. This class roughly corresponds to the old Runner()
    class.
    '''

    def __init__(self, host, task, job_vars, connection_info, loader, module_loader):
        self._host            = host
        self._task            = task
        self._job_vars        = job_vars
        self._connection_info = connection_info
        self._loader          = loader
        self._module_loader   = module_loader

    def run(self):
        '''
        The main executor entrypoint, where we determine if the specified
        task requires looping and either runs the task with 
        '''

        debug("in run()")

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
                    res = dict(results=item_results)
                else:
                    res = dict(changed=False, skipped=True, skipped_reason='No items in the list', results=[])
            else:
                debug("calling self._execute()")
                res = self._execute()
                debug("_execute() done")

            debug("dumping result to json")
            result = json.dumps(res)
            debug("done dumping result, returning")
            return result
        except AnsibleError, e:
            return dict(failed=True, msg=str(e))

    def _get_loop_items(self):
        '''
        Loads a lookup plugin to handle the with_* portion of a task (if specified),
        and returns the items result.
        '''

        items = None
        if self._task.loop and self._task.loop in lookup_loader:
            loop_terms = listify_lookup_plugin_terms(terms=self._task.loop_args, variables=self._job_vars, loader=self._loader)
            items = lookup_loader.get(self._task.loop, loader=self._loader).run(terms=loop_terms, variables=self._job_vars)

        return items

    def _run_loop(self, items):
        '''
        Runs the task with the loop items specified and collates the result
        into an array named 'results' which is inserted into the final result
        along with the item for which the loop ran.
        '''

        results = []

        # FIXME: squash items into a flat list here for those modules
        #        which support it (yum, apt, etc.) but make it smarter
        #        than it is today?

        for item in items:
            # make copies of the job vars and task so we can add the item to
            # the variables and re-validate the task with the item variable
            task_vars = self._job_vars.copy()
            task_vars['item'] = item

            try:
                tmp_task = self._task.copy()
            except AnsibleParserError, e:
                results.append(dict(failed=True, msg=str(e)))
                continue

            # now we swap the internal task with the copy, execute,
            # and swap them back so we can do the next iteration cleanly
            (self._task, tmp_task) = (tmp_task, self._task)
            res = self._execute(variables=task_vars)
            (self._task, tmp_task) = (tmp_task, self._task)

            # FIXME: we should be sending back a callback result for each item in the loop here

            # now update the result with the item info, and append the result
            # to the list of results
            res['item'] = item
            results.append(res)

        return results

    def _execute(self, variables=None):
        '''
        The primary workhorse of the executor system, this runs the task
        on the specified host (which may be the delegated_to host) and handles
        the retry/until and block rescue/always execution
        '''

        if variables is None:
            variables = self._job_vars

        self._connection = self._get_connection()
        self._handler    = self._get_action_handler(connection=self._connection)

        if not self._task.evaluate_conditional(variables):
            debug("when evaulation failed, skipping this task")
            return dict(skipped=True, skip_reason='Conditional check failed')

        self._task.post_validate(variables)

        retries = self._task.retries
        if retries <= 0:
            retries = 1

        delay = self._task.delay
        if delay < 0:
            delay = 1

        debug("starting attempt loop")
        result = None
        for attempt in range(retries):
            if attempt > 0:
                # FIXME: this should use the callback mechanism
                print("FAILED - RETRYING: %s (%d retries left)" % (self._task, retries-attempt))
                result['attempts'] = attempt + 1

            debug("running the handler")
            result = self._handler.run(task_vars=variables)
            debug("handler run complete")

            if self._task.async > 0:
                # the async_wrapper module returns dumped JSON via its stdout
                # response, so we parse it here and replace the result
                try:
                    result = json.loads(result.get('stdout'))
                except ValueError, e:
                    return dict(failed=True, msg="The async task did not return valid JSON: %s" % str(e))

                if self._task.poll > 0:
                    result = self._poll_async_result(result=result)

            if self._task.until:
                # make a copy of the job vars here, in case we need to update them
                vars_copy = variables.copy()
                # now update them with the registered value, if it is set
                if self._task.register:
                    vars_copy[self._task.register] = result
                # create a conditional object to evaluate the until condition
                cond = Conditional(loader=self._loader)
                cond.when = self._task.until
                if cond.evaluate_conditional(vars_copy):
                    break
            elif 'failed' not in result and result.get('rc', 0) == 0:
                # if the result is not failed, stop trying
                break

            if attempt < retries - 1:
                time.sleep(delay)

        debug("attempt loop complete, returning result")
        return result

    def _poll_async_result(self, result):
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
        normal_handler = action_loader.get(
            'normal',
            task=async_task,
            connection=self._connection,
            connection_info=self._connection_info,
            loader=self._loader,
            module_loader=self._module_loader,
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

    def _get_connection(self):
        '''
        Reads the connection property for the host, and returns the
        correct connection object from the list of connection plugins
        '''

        # FIXME: delegate_to calculation should be done here
        # FIXME: calculation of connection params/auth stuff should be done here

        # FIXME: add all port/connection type munging here (accelerated mode,
        #        fixing up options for ssh, etc.)? and 'smart' conversion
        conn_type = self._connection_info.connection
        if conn_type == 'smart':
            conn_type = 'ssh'

        connection = connection_loader.get(conn_type, self._host, self._connection_info)
        if not connection:
            raise AnsibleError("the connection plugin '%s' was not found" % conn_type)

        connection.connect()

        return connection

    def _get_action_handler(self, connection):
        '''
        Returns the correct action plugin to handle the requestion task action
        '''

        if self._task.action in action_loader:
            if self._task.async != 0:
                raise AnsibleError("async mode is not supported with the %s module" % module_name)
            handler_name = self._task.action
        elif self._task.async == 0:
            handler_name = 'normal'
        else:
            handler_name = 'async'

        handler = action_loader.get(
            handler_name,
            task=self._task,
            connection=connection,
            connection_info=self._connection_info,
            loader=self._loader,
            module_loader=self._module_loader,
        )
        if not handler:
            raise AnsibleError("the handler '%s' was not found" % handler_name)

        return handler
