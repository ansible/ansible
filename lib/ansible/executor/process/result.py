# (c) 2019, Red Hat, Inc.
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

from __future__ import (absolute_import, division, print_function)

import os
import threading

from sys import exc_info
from traceback import format_tb

from ansible import constants as C
from ansible.executor.process.base import AnsibleProcessBase
from ansible.executor.task_result import TaskResult
from ansible.inventory.host import Host
from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types
from ansible.playbook.task import Task
from ansible.plugins.callback import CallbackBase
from ansible.plugins.loader import callback_loader
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.cpu import mask_to_bytes, sched_setaffinity
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath
from ansible.utils.sentinel import Sentinel


display = Display()


class ResultProcess(AnsibleProcessBase):

    __metaclass__ = type

    def __init__(self, final_q, results_q, run_additional_callbacks=True, run_tree=True):

        super(ResultProcess, self).__init__()
        self._final_q = final_q
        self._results_q = results_q
        self._stdout_callback = None
        self._callback_plugins = []
        self._run_additional_callbacks = run_additional_callbacks
        self._run_tree = run_tree
        self._callback_lock = threading.Lock()

        self.load_callbacks()

    def _run(self):
        #s = mask_to_bytes(0x02)
        #sched_setaffinity(os.getpid(), len(s), s)

        while True:
            try:
                result = self._final_q.get()
                if result is Sentinel:
                    break
                elif isinstance(result, TaskResult):
                    display.debug("handling result")
                    self.handle_result(result)
                elif isinstance(result, tuple):
                    display.debug("handling a direct callback request")
                    self.handle_direct_callback(result)
            except Exception as e:
                # FIXME: send back a message here
                display.debug('Callback Exception: \n' + ' '.join(format_tb(exc_info()[2])))
                display.debug("RESULTS PROCESSING ERROR: %s" % str(e))

        display.debug("RESULTS PROCESS EXITING")

    def handle_result(self, task_result):
        orig_host = Host().deserialize(task_result._host)
        orig_task = Task().deserialize(task_result._task)
        task_result._host = orig_host
        task_result._task = orig_task

        # send callbacks for 'non final' results
        if '_ansible_retry' in task_result._result:
            self.send_callback('v2_runner_retry', task_result)
            return
        elif '_ansible_item_result' in task_result._result:
            if task_result.is_failed() or task_result.is_unreachable():
                self.send_callback('v2_runner_item_on_failed', task_result)
            elif task_result.is_skipped():
                self.send_callback('v2_runner_item_on_skipped', task_result)
            else:
                if 'diff' in task_result._result:
                    if self._diff or getattr(orig_task, 'diff', False):
                        self.send_callback('v2_on_file_diff', task_result)
                self.send_callback('v2_runner_item_on_ok', task_result)
            return

        # all host status messages contain 2 entries: (msg, task_result)
        role_ran = False
        changed = False
        status_type = None
        status_msg = ''
        if task_result.is_failed():
            role_ran = True
            status_type = 'failed'
            status_msg = 'failing host because task failed'
            if orig_task.ignore_errors:
                status_type = 'failed_ignored'
                status_msg = 'task failed, but ignore_error was enabled'
            elif orig_task.run_once:
                # if we're using run_once, we have to fail every host here
                status_type = 'failed_all'
                status_msg = 'failing all hosts because a run_once task failed'
            self.send_callback('v2_runner_on_failed', task_result, ignore_errors=orig_task.ignore_errors)
        elif task_result.is_unreachable():
            status_type = 'unreachable'
            status_msg = 'Host %s is unreachable' % orig_host.name
            if orig_task.ignore_unreachable:
                status_type = 'unreachable_ignored'
                status_msg = 'Host %s is unreachable, but ignore_unreachable was enabled' % orig_host.name
            self.send_callback('v2_runner_on_unreachable', task_result)
        elif task_result.is_skipped():
            status_type = 'skipped'
            status_msg = 'task was skipped'
            self.send_callback('v2_runner_on_skipped', task_result)
        else:
            # everything was ok
            role_ran = True
            changed = task_result.is_changed()
            status_type = 'ok'
            status_msg = 'task finished successfully'
            self.send_callback('v2_runner_on_ok', task_result)

        display.debug("sending task result back to main proc")
        self._results_q.put({
            'host_name': orig_host.name,
            'task_uuid': orig_task._uuid,
            'status_type': status_type,
            'status_msg': status_msg,
            'original_result': task_result._result,
            'changed': changed,
            'role_ran': role_ran,
            'needs_debug': task_result.needs_debugger(),
        }, block=True)
        display.debug("done sending task result back to main proc")

    def load_callbacks(self):
        '''
        Loads all available callbacks, with the exception of those which
        utilize the CALLBACK_TYPE option. When CALLBACK_TYPE is set to 'stdout',
        only one such callback plugin will be loaded.
        '''

        stdout_callback_loaded = False
        if self._stdout_callback is None:
            self._stdout_callback = C.DEFAULT_STDOUT_CALLBACK

        if isinstance(self._stdout_callback, CallbackBase):
            stdout_callback_loaded = True
        elif isinstance(self._stdout_callback, string_types):
            if self._stdout_callback not in callback_loader:
                raise AnsibleError("Invalid callback for stdout specified: %s" % self._stdout_callback)
            else:
                self._stdout_callback = callback_loader.get(self._stdout_callback)
                self._stdout_callback.set_options()
                stdout_callback_loaded = True
        else:
            raise AnsibleError("callback must be an instance of CallbackBase or the name of a callback plugin")

        for callback_plugin in callback_loader.all(class_only=True):
            callback_type = getattr(callback_plugin, 'CALLBACK_TYPE', '')
            callback_needs_whitelist = getattr(callback_plugin, 'CALLBACK_NEEDS_WHITELIST', False)
            (callback_name, _) = os.path.splitext(os.path.basename(callback_plugin._original_path))
            if callback_type == 'stdout':
                # we only allow one callback of type 'stdout' to be loaded,
                if callback_name != self._stdout_callback or stdout_callback_loaded:
                    continue
                stdout_callback_loaded = True
            elif callback_name == 'tree' and self._run_tree:
                # special case for ansible cli option
                pass
            elif not self._run_additional_callbacks or (callback_needs_whitelist and (
                    C.DEFAULT_CALLBACK_WHITELIST is None or callback_name not in C.DEFAULT_CALLBACK_WHITELIST)):
                # 2.x plugins shipped with ansible should require whitelisting, older or non shipped should load automatically
                continue

            callback_obj = callback_plugin()
            callback_obj.set_options()
            self._callback_plugins.append(callback_obj)

        for callback_plugin_name in (c for c in C.DEFAULT_CALLBACK_WHITELIST if AnsibleCollectionRef.is_valid_fqcr(c)):
            # TODO: need to extend/duplicate the stdout callback check here (and possible move this ahead of the old way
            callback_obj = callback_loader.get(callback_plugin_name)
            self._callback_plugins.append(callback_obj)

    def send_callback(self, *args, **kwargs):
        threading.Thread(target=self._send_callback, args=args, kwargs=kwargs).start()
        # self._send_callback(*args, **kwargs)

    def _send_callback(self, method_name, *args, **kwargs):
        try:
            # self._callback_lock.acquire()
            for callback_plugin in [self._stdout_callback] + self._callback_plugins:
                # a plugin that set self.disabled to True will not be called
                # see osx_say.py example for such a plugin
                if getattr(callback_plugin, 'disabled', False):
                    continue

                # try to find v2 method, fallback to v1 method, ignore callback if no method found
                methods = []
                for possible in [method_name, 'v2_on_any']:
                    gotit = getattr(callback_plugin, possible, None)
                    if gotit is None:
                        gotit = getattr(callback_plugin, possible.replace('v2_', ''), None)
                    if gotit is not None:
                        methods.append(gotit)

                # send clean copies
                new_args = []
                for arg in args:
                    # FIXME: add play/task cleaners
                    if isinstance(arg, TaskResult):
                        new_args.append(arg.clean_copy())
                    # elif isinstance(arg, Play):
                    # elif isinstance(arg, Task):
                    else:
                        new_args.append(arg)

                for method in methods:
                    try:
                        method(*new_args, **kwargs)
                    except Exception as e:
                        # TODO: add config toggle to make this fatal or not?
                        display.warning(u"Failure using method (%s) in callback plugin (%s): %s" % (to_text(method_name), to_text(callback_plugin), to_text(e)))
                        from traceback import format_tb
                        from sys import exc_info
                        display.vvv('Callback Exception: \n' + ' '.join(format_tb(exc_info()[2])))
        finally:
            # self._callback_lock.release()
            pass

    def handle_direct_callback(self, result):
        callback_name = result[0]
        callback_args = result[1:]
        self.send_callback(callback_name, *callback_args)
