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
from ansible.errors import AnsibleError
from ansible.executor.connection_info import ConnectionInformation
from ansible.playbook.task import Task
from ansible.plugins import lookup_loader, connection_loader, action_loader

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

    def __init__(self, host, task, job_vars, connection_info, loader):
        self._host            = host
        self._task            = task
        self._job_vars        = job_vars
        self._connection_info = connection_info
        self._loader          = loader

    def run(self):
        '''
        The main executor entrypoint, where we determine if the specified
        task requires looping and either runs the task with 
        '''

        debug("in run()")
        items = self._get_loop_items()
        if items:
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

    def _get_loop_items(self):
        '''
        Loads a lookup plugin to handle the with_* portion of a task (if specified),
        and returns the items result.
        '''

        items = None
        if self._task.loop and self._task.loop in lookup_loader:
            items = lookup_loader.get(self._task.loop).run(self._task.loop_args)

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
            res = self._execute()
            res['item'] = item
            results.append(res)

        return results

    def _execute(self):
        '''
        The primary workhorse of the executor system, this runs the task
        on the specified host (which may be the delegated_to host) and handles
        the retry/until and block rescue/always execution
        '''

        self._connection = self._get_connection()
        self._handler    = self._get_action_handler(connection=self._connection)

        # check to see if this task should be skipped, due to it being a member of a
        # role which has already run (and whether that role allows duplicate execution)
        if self._task._role and self._task._role.has_run():
            # If there is no metadata, the default behavior is to not allow duplicates,
            # if there is metadata, check to see if the allow_duplicates flag was set to true
            if self._task._role._metadata is None or self._task._role._metadata and not self._task._role._metadata.allow_duplicates:
                debug("task belongs to a role which has already run, but does not allow duplicate execution")
                return dict(skipped=True, skip_reason='This role has already been run, but does not allow duplicates')

        if not self._task.evaluate_conditional(self._job_vars):
            debug("when evaulation failed, skipping this task")
            return dict(skipped=True, skip_reason='Conditional check failed')

        if not self._task.evaluate_tags(self._connection_info.only_tags, self._connection_info.skip_tags):
            debug("Tags don't match, skipping this task")
            return dict(skipped=True, skip_reason='Skipped due to specified tags')

        retries = self._task.retries
        if retries <= 0:
            retries = 1

        delay = self._task.delay
        if delay < 0:
            delay = 0

        debug("starting attempt loop")
        result = None
        for attempt in range(retries):
            if attempt > 0:
                # FIXME: this should use the callback mechanism
                print("FAILED - RETRYING: %s (%d retries left)" % (self._task, retries-attempt))
                result['attempts'] = attempt + 1

            debug("running the handler")
            result = self._handler.run(task_vars=self._job_vars)
            debug("handler run complete")

            if self._task.async > 0 and self._task.poll > 0:
                result = self._poll_async_result(result=result)

            if self._task.until:
                # TODO: implement until logic (pseudo logic follows...)
                # if VariableManager.check_conditional(cond, extra_vars=(dict(result=result))):
                #     break
                pass
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

        # the async_wrapper module returns dumped JSON via its stdout
        # response, so we parse it here
        try:
            async_data = json.loads(result.get('stdout'))
        except ValueError, e:
            return dict(failed=True, msg="The async task did not return valid JSON: %s" % str(e))

        async_jid = async_data.get('ansible_job_id')
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
            loader=self._loader
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
            loader=self._loader
        )
        if not handler:
            raise AnsibleError("the handler '%s' was not found" % handler_name)

        return handler
