# (C) 2012, Michael DeHaan, <michael.dehaan@gmail.com>

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

import logging
import logging.handlers
import os
import pprint
import re

# from ansible.utils.unicode import to_bytes
from ansible.plugins.callback import CallbackBase

# import logging_tree


# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.

DEBUG_LOG_FORMAT = "%(asctime)s [%(name)s %(levelname)s %(hostname)s %(playbook)s] pid=%(process)d %(funcName)s:%(lineno)d - %(message)s"
CONTEXT_DEBUG_LOG_FORMAT = "%(asctime)s [%(name)s %(levelname)s %(hostname)s] [playbook=%(playbook)s:%(playbook_uuid)s play=%(play)s:%(play_uuid)s task=%(task)s:%(task_uuid)s] (%(process)d):%(funcName)s:%(lineno)d - %(message)s"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(process)d @%(filename)s:%(lineno)d - %(message)s"
MIN_LOG_FORMAT = "%(asctime)s %(funcName)s:%(lineno)d - %(message)s"


def sluggify(value):
    return '%s' % (re.sub(r'[^\w-]', '_', value).lower().lstrip('_'))


class PlaybookContextLoggingFilter(object):
    def __init__(self, name, playbook_context=None):
        self.name = name
        self.playbook_context = playbook_context

    def filter(self, record):
        if not self.playbook_context:
            return True

        # TODO: squash this with properties

        record.playbook = None
        record.playbook_uuid = None
        record.play = None
        record.play_uuid = None
        record.task = None
        record.task_uuid = None
        record.hostname = getattr(record, 'hostname', '')
        record.task_log = getattr(record, 'task_log', '')

        if self.playbook_context.playbook:
            record.playbook = os.path.basename(self.playbook_context.playbook._file_name)
        if self.playbook_context.playbook_uuid:
            record.playbook_uuid = self.playbook_context.playbook_uuid

        if self.playbook_context.play:
            record.play = sluggify(self.playbook_context.play.get_name())
        if self.playbook_context.play_uuid:
            record.play_uuid = self.playbook_context.play_uuid

        if self.playbook_context.task:
            record.task = sluggify(self.playbook_context.task.name)
        if self.playbook_context.task_uuid:
            record.task_uuid = self.playbook_context.task_uuid

        if self.playbook_context.hostname:
            record.hostname = self.playbook_context.hostname

        return True


class StdlogFileHandler(logging.handlers.WatchedFileHandler, object):
    def __init__(self, *args, **kwargs):
        playbook_context = kwargs.pop('playbook_context', None)
        super(StdlogFileHandler, self).__init__(*args, **kwargs)

        self.addFilter(PlaybookContextLoggingFilter(name="",
                                                    playbook_context=playbook_context))


class StdlogStreamHandler(logging.StreamHandler, object):
    def __init__(self, *args, **kwargs):
        playbook_context = kwargs.pop('playbook_context', None)
        super(StdlogStreamHandler, self).__init__(*args, **kwargs)

        self.addFilter(PlaybookContextLoggingFilter(name="",
                                                    playbook_context=playbook_context))


class TaskResultRepr(object):
    def __init__(self, result):
        self.result = result
        self.host = self.result._host
        self.task = self.result._task
        self.verbose = True

    def __repr__(self):
        # return "TaskResult(host=%s, task=%s, return_data=%s)" % (self._host, self._task, self._result)
        return "TaskResult(host=%s, uuid=%s)" % (self.host, self.task._uuid)

    def str_impl(self):
        parts = []
        parts.append("TaskResult:")
        parts.append("    host: %s" % self.host)
        parts.append("    task: %s" % self.task)
        parts.append("    task._uuid: %s" % self.task._uuid)
        parts.append("    return_data: %s" % pprint.pformat(self.result))
        for key, value in self.result._result.items():
            parts.append(' key: %s=%s' % (key, value))
        return '\n'.join(parts)

    # enable for way more verbose logs
    # __str__ = str_impl


class PlaybookContext(object):
    def __init__(self, playbook=None, play=None, task=None):
        # TODO: use something like chainmap for nested context?
        self.playbook = playbook
        self.playbook_uuid = None

        self.play = play
        self.play_uuid = None

        self.task = task
        self.task_uuid = None

        self.hostname = None

    def update(self, result=None):
        """On a task result, if for the current task, that task is done."""
        if not result:
            return

        if self.task_uuid == result._task._uuid:
            self.task = None
            self.task_uuid = None

        self.hostname = result._host.get_name()

    # NOTE: not used currently
    def logger_name(self, base_logger_name=None):
        logger_name = base_logger_name or ""
        if self.playbook:
            logger_name += '.%s' % self.playbook._name
        if self.play:
            play_name = sluggify(self.play.get_name())
            logger_name += '.%s' % play_name
        if self.task:
            if self.task.name:
                task_name = sluggify(self.task.name)
                logger_name += '.%s' % task_name
        return logger_name


class CallbackModule(CallbackBase):
    """
    Logging callbacks using python stdlin logging
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    # CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = 'stdlog'
    # CALLBACK_NEEDS_WHITELIST = True

    log_level = logging.DEBUG
    log_name = 'ansible_stdlog'
    #log_format = CONTEXT_DEBUG_LOG_FORMAT
    # log_format = LOG_FORMAT
    # log_format = MIN_LOG_FORMAT
    log_format = DEBUG_LOG_FORMAT

    def __init__(self):
        super(CallbackModule, self).__init__()

        # TODO: replace with a stack
        self.host = None

        self.context = PlaybookContext()

        # Note.. reference to the class to be used as a callable not an instance
        self.rr = TaskResultRepr
        self.formatter = logging.Formatter(fmt=self.log_format)

        self.stream_handler = StdlogStreamHandler(playbook_context=self.context)
        self.stream_handler.setFormatter(self.formatter)

        self.file_handler = StdlogFileHandler('/tmp/ansible_stdlog.log',
                                              playbook_context=self.context)
        self.file_handler.setFormatter(self.formatter)

        self.logger = logging.getLogger(self.log_name)
        self.logger.addHandler(self.stream_handler)
        self.logger.addHandler(self.file_handler)

        self.logger.setLevel(self.log_level)

    # Note: it would be useful to have a 'always called'
    # callback, and a 'only called if not handled' callback
    def _handle_v2_on_any(self, *args, **kwargs):
        for arg in args:
            self.logger.debug(arg)

        for k, v in kwargs.items():
            self.logger.debug('kw_k=%s', k)
            self.logger.debug('kw_v=%s', v)

    # TODO: remove, not used at,
    def context_logger(self, host=None):
        # 'ansible_stdlog.host.playbook.play.task'
        # 'ansible_stdlog.host.playbook.'
        # ansible_stdlog.play.task? ansible_stdlog.play.task.host?
        # playbook.play.task.
        # playbook filename sans ext?
        # TODO: figure out a reasonable label style name for a playbook

        logger = logging.getLogger(self.context.logger_name(self.log_name))
        logger.setLevel(self.log_level)
        return logger

    def result_update(self, result):

        for log_record_dict in result._result.get('log_records', []):
            log_record_dict['hostname'] = result._host
            log_record_dict['task_log'] = 'task_log'
            # log_record_dict['args'] = tuple(log_record_dict['arg_reprs']) or None

            log_record = logging.makeLogRecord(log_record_dict)
            self.logger.handle(log_record)
        self.context.update(result)
        self.logger.debug('result=%s', self.rr(result))

    # Add host info to context and remove this method
    def not_result_logger(self, result):
        """Grab a logging.Logger with the host and category in the logger name.

        Why not log the result here? Because we get the
        calling method name logged for free if we do it in
        the entry point, where we'd get 'result_update' here."""

        return self.context_logger(host=result.host.get_name())

    def v2_runner_on_failed(self, result, ignore_errors=None):
        self.result_update(result)
        self.logger.debug('result=%s', self.rr(result))
        self.logger.debug('ignore_errors=%s', ignore_errors or False)

    def v2_runner_on_ok(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', self.rr(result))

    def v2_runner_on_skipped(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', self.rr(result))

    def v2_runner_on_unreachable(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', self.rr(result))

    def v2_runner_on_no_hosts(self, task):
        self.logger.debug('no hosts on task=%s', task)

    def v2_runner_on_async_pool(self, result):
        # need a async_result_logger?
        self.result_update(result)
        self.logger.debug('result=%s', result)

    def v2_runner_on_async_ok(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', result)

    def v2_runner_on_async_failed(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', result)

    def v2_runner_on_file_diff(self, result, diff):
        self.result_update(result)
        self.logger.debug('diff=%s', diff)

    def v2_playbook_on_start(self, playbook):
        # self.playbook = playbook
        self.context.playbook = playbook
        self.logger.debug('playbook=%s', playbook)

    def v2_playbook_on_notify(self, result, handler):
        self.result_update(result)
        self.logger.debug('result=%s', result)
        self.logger.debug('handler=%s', handler)

    def v2_playbook_on_play_start(self, play):
        # self.play = play
        self.context.play = play
        self.context.play_uuid = play._uuid

        self.logger.debug('play=%s', play)

    def v2_playbook_on_no_hosts_matched(self):
        self.logger.debug('playbook=%s, no hosts matches' % self.context.playbook)

    def v2_playbook_on_hosts_remaining(self):
        self.logger.debug('playbook=%s, no hosts remaining' % self.context.playbook)

    def v2_playbook_on_task_start(self, task, is_conditional):
        # TODO self.context.update(task=, task_uuid=) ?
        self.context.task = task
        self.context.task_uuid = task._uuid

        self.logger.debug('playbook=%s', self.context.playbook)
        self.logger.debug('task=%s', task)
        self.logger.debug('is_conditional=%s', is_conditional)

    def v2_playbook_on_cleanup_task_start(self, task):
        self.logger.debug('playbook=%s, cleanup on task=%s', self.context.playbook, task)

        # NOTE: needed?
        # self.context.playbook = None

    def v2_playbook_on_handler_task_start(self, task):
        self.logger.debug('playbook=%s, handler start for task=%s',
                          self.context.playbook, task)

    def v2_playbook_on_vars_prompt(self, varname, private=None,
                                   prompt=None, encrypt=None, confirm=None,
                                   salt_size=None, salt=None, default=None):
        self.logger.debug('playbook=%s vars_prompt=%s',
                          self.context.playbook, locals())

    def v2_playbook_on_setup(self):
        self.logger.debug('playbook=%s, setup', self.context.playbook)

    def v2_playbook_on_import_for_host(self, result, imported_file):
        self.result_update(result)
        self.logger.debug('playbook=%s', self.context.playbook)
        self.logger.debug('imported_file=%s', imported_file)
        self.logger.debug('result=%s', result)

    def v2_playbook_on_not_import_for_host(self, result, imported_file):
        self.result_update(result)
        self.logger.debug('playbook=%s', self.context.playbook)
        self.logger.debug('(not) imported_file=%s', imported_file)
        self.logger.debug('result=%s', result)

    def v2_playbook_on_stats(self, stats):
        # self.stats_update ?
        self.logger.debug('playbook=%s', self.context.playbook)
        self.logger.debug('stats=%s', stats)
        self.context.playbook = None

    def v2_on_file_diff(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', result)

    def v2_runner_item_on_ok(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', result)

    def v2_playbook_on_include(self, included_file):
        self.logger.debug('playbook=%s', self.context.playbook)
        self.logger.debug('included_file=%s', included_file)

    def v2_runner_item_on_failed(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', result)

    def v2_runner_item_on_skipped(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', result)

    def v2_runner_retry(self, result):
        self.result_update(result)
        self.logger.debug('result=%s', result)
