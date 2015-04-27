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

import json
import pipes
import subprocess
import sys
import time

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.executor.connection_info import ConnectionInformation
from ansible.playbook.conditional import Conditional
from ansible.playbook.task import Task
from ansible.plugins import lookup_loader, connection_loader, action_loader
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.utils.unicode import to_unicode

from ansible.utils.debug import debug

__all__ = ['TaskExecutor']

class TaskExecutor:

    '''
    This is the main worker class for the executor pipeline, which
    handles loading an action plugin to actually dispatch the task to
    a given host. This class roughly corresponds to the old Runner()
    class.
    '''

    def __init__(self, host, task, job_vars, connection_info, new_stdin, loader, module_loader):
        self._host            = host
        self._task            = task
        self._job_vars        = job_vars
        self._connection_info = connection_info
        self._new_stdin       = new_stdin
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

                    # loop through the item results, and remember the changed/failed
                    # result flags based on any item there.
                    changed = False
                    failed  = False
                    for item in item_results:
                        if 'changed' in item:
                           changed = True
                        if 'failed' in item:
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
                debug("calling self._execute()")
                res = self._execute()
                debug("_execute() done")

            # make sure changed is set in the result, if it's not present
            if 'changed' not in res:
                res['changed'] = False

            debug("dumping result to json")
            result = json.dumps(res)
            debug("done dumping result, returning")
            return result
        except AnsibleError, e:
            return dict(failed=True, msg=to_unicode(e, nonstring='simplerepr'))

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

        # make copies of the job vars and task so we can add the item to
        # the variables and re-validate the task with the item variable
        task_vars = self._job_vars.copy()

        items = self._squash_items(items, task_vars)
        for item in items:
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

            # now update the result with the item info, and append the result
            # to the list of results
            res['item'] = item
            results.append(res)

            # FIXME: we should be sending back a callback result for each item in the loop here
            print(res)

        return results

    def _squash_items(self, items, variables):
        '''
        Squash items down to a comma-separated list for certain modules which support it
        (typically package management modules).
        '''

        if len(items) > 0 and self._task.action in ('apt', 'yum', 'pkgng', 'zypper'):
            final_items = []
            for item in items:
                variables['item'] = item
                if self._task.evaluate_conditional(variables):
                    final_items.append(item)
            return [",".join(final_items)]
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

        # fields set from the play/task may be based on variables, so we have to
        # do the same kind of post validation step on it here before we use it.
        self._connection_info.post_validate(variables=variables, loader=self._loader)

        # now that the connection information is finalized, we can add 'magic'
        # variables to the variable dictionary
        self._connection_info.update_vars(variables)

        # get the connection and the handler for this execution
        self._connection = self._get_connection(variables)
        self._handler    = self._get_action_handler(connection=self._connection)

        # Evaluate the conditional (if any) for this task, which we do before running
        # the final task post-validation. We do this before the post validation due to
        # the fact that the conditional may specify that the task be skipped due to a
        # variable not being present which would otherwise cause validation to fail
        if not self._task.evaluate_conditional(variables):
            debug("when evaulation failed, skipping this task")
            return dict(changed=False, skipped=True, skip_reason='Conditional check failed')

        # Now we do final validation on the task, which sets all fields to their final values
        self._task.post_validate(variables)

        # if this task is a TaskInclude, we just return now with a success code so the
        # main thread can expand the task list for the given host
        if self._task.action == 'include':
            include_variables = self._task.args.copy()
            include_file = include_variables.get('_raw_params')
            del include_variables['_raw_params']
            return dict(changed=True, include=include_file, include_variables=include_variables)

        # And filter out any fields which were set to default(omit), and got the omit token value
        omit_token = variables.get('omit')
        if omit_token is not None:
            self._task.args = dict(filter(lambda x: x[1] != omit_token, self._task.args.iteritems()))

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

        debug("starting attempt loop")
        result = None
        for attempt in range(retries):
            if attempt > 0:
                # FIXME: this should use the callback/message passing mechanism
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

            # update the local copy of vars with the registered value, if specified,
            # or any facts which may have been generated by the module execution
            if self._task.register:
                vars_copy[self._task.register] = result 

            if 'ansible_facts' in result:
                vars_copy.update(result['ansible_facts'])

            # create a conditional object to evaluate task conditions
            cond = Conditional(loader=self._loader)

            # FIXME: make sure until is mutually exclusive with changed_when/failed_when
            if self._task.until:
                cond.when = self._task.until
                if cond.evaluate_conditional(vars_copy):
                    break
            elif (self._task.changed_when or self._task.failed_when) and 'skipped' not in result:
                if self._task.changed_when:
                    cond.when = [ self._task.changed_when ]
                    result['changed'] = cond.evaluate_conditional(vars_copy)
                if self._task.failed_when:
                    cond.when = [ self._task.failed_when ]
                    failed_when_result = cond.evaluate_conditional(vars_copy)
                    result['failed_when_result'] = result['failed'] = failed_when_result
                    if failed_when_result:
                        break
            elif 'failed' not in result and result.get('rc', 0) == 0:
                # if the result is not failed, stop trying
                break

            if attempt < retries - 1:
                time.sleep(delay)

        # do the final update of the local variables here, for both registered
        # values and any facts which may have been created
        if self._task.register:
            variables[self._task.register] = result 

        if 'ansible_facts' in result:
            variables.update(result['ansible_facts'])

        # and return
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

    def _get_connection(self, variables):
        '''
        Reads the connection property for the host, and returns the
        correct connection object from the list of connection plugins
        '''

        # FIXME: delegate_to calculation should be done here
        # FIXME: calculation of connection params/auth stuff should be done here

        self._connection_info.remote_addr = self._host.ipv4_address
        if self._task.delegate_to is not None:
            self._compute_delegate(variables)

        conn_type = self._connection_info.connection
        if conn_type == 'smart':
            conn_type = 'ssh'
            if sys.platform.startswith('darwin') and self._connection_info.remote_pass:
                # due to a current bug in sshpass on OSX, which can trigger
                # a kernel panic even for non-privileged users, we revert to
                # paramiko on that OS when a SSH password is specified
                conn_type = "paramiko"
            else:
                # see if SSH can support ControlPersist if not use paramiko
                cmd = subprocess.Popen(['ssh','-o','ControlPersist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (out, err) = cmd.communicate()
                if "Bad configuration option" in err:
                    conn_type = "paramiko"

        connection = connection_loader.get(conn_type, self._connection_info, self._new_stdin)
        if not connection:
            raise AnsibleError("the connection plugin '%s' was not found" % conn_type)

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

    def _compute_delegate(self, variables):

        # get the vars for the delegate by its name
        try:
            this_info = variables['hostvars'][self._task.delegate_to]
        except:
            # make sure the inject is empty for non-inventory hosts
            this_info = {}

        # get the real ssh_address for the delegate and allow ansible_ssh_host to be templated
        #self._connection_info.remote_user      = self._compute_delegate_user(self.delegate_to, delegate['inject'])
        self._connection_info.remote_addr      = this_info.get('ansible_ssh_host', self._task.delegate_to)
        self._connection_info.port             = this_info.get('ansible_ssh_port', self._connection_info.port)
        self._connection_info.password         = this_info.get('ansible_ssh_pass', self._connection_info.password)
        self._connection_info.private_key_file = this_info.get('ansible_ssh_private_key_file', self._connection_info.private_key_file)
        self._connection_info.connection       = this_info.get('ansible_connection', self._connection_info.connection)
        self._connection_info.become_pass      = this_info.get('ansible_sudo_pass', self._connection_info.become_pass)

        if self._connection_info.remote_addr in ('127.0.0.1', 'localhost'):
             self._connection_info.connection = 'local'

        # Last chance to get private_key_file from global variables.
        # this is useful if delegated host is not defined in the inventory
        #if delegate['private_key_file'] is None:
        #    delegate['private_key_file'] = remote_inject.get('ansible_ssh_private_key_file', None)

        #if delegate['private_key_file'] is not None:
        #    delegate['private_key_file'] = os.path.expanduser(delegate['private_key_file'])

        for i in this_info:
            if i.startswith("ansible_") and i.endswith("_interpreter"):
                variables[i] = this_info[i]

