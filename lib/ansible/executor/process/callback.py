# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import multiprocessing
import os
import sys
import traceback

from jinja2.exceptions import TemplateNotFound

import ansible.constants as C

from ansible.executor.task_result import TaskResult
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.six.moves import queue as Queue

__all__ = ['CallbackProcess', 'CallbackSentinel']


class CallbackSentinel:
    pass


class CallbackProcess(multiprocessing.Process):
    def __init__(self, queue, callback_plugins, display):

        super(CallbackProcess, self).__init__()

        self._queue = queue
        self._callback_plugins = callback_plugins
        self._display = display

    def _send(self, method_name, *args, **kwargs):
        for callback_plugin in self._callback_plugins:
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
                    self._display.warning(
                        u"Failure using method (%s) in callback plugin (%s): %s" % (to_text(method_name),
                                                                                    to_text(callback_plugin),
                                                                                    to_text(e))
                    )
                    self._display.vvv('Callback Exception: \n%s' % traceback.format_exc())

    def run(self):
        while True:
            try:
                method_name, args, kwargs = self._queue.get()
                if isinstance(method_name, CallbackSentinel):
                    break
                self._send(method_name, *args, **kwargs)
            except (IOError, EOFError, KeyboardInterrupt):
                break
            except Queue.Empty:
                pass
        try:
            self._queue.close()
            self.terminate()
        except AttributeError:
            pass
