"""Testing callback to record callback events and generalize the results for easier diffs."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'test_callback'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.path = os.environ.get('TEST_CALLBACK_PATH', os.path.abspath('test_callback.log'))
        self.ignore = set(os.environ.get('TEST_CALLBACK_IGNORE', 'v2_on_any').split(','))
        self.fd = open(self.path, 'w')

    def v2_on_any(self, *args, **kwargs):
        self.log('v2_on_any', kwargs, args)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.log('v2_runner_on_failed', locals())

    def v2_runner_on_ok(self, result):
        self.log('v2_runner_on_ok', locals())

    def v2_runner_on_skipped(self, result):
        self.log('v2_runner_on_skipped', locals())

    def v2_runner_on_unreachable(self, result):
        self.log('v2_runner_on_unreachable', locals())

    def v2_runner_on_async_poll(self, result):
        self.log('v2_runner_on_async_poll', locals())

    def v2_runner_on_async_ok(self, result):
        self.log('v2_runner_on_async_ok', locals())

    def v2_runner_on_async_failed(self, result):
        self.log('v2_runner_on_async_failed', locals())

    def v2_playbook_on_start(self, playbook):
        self.log('v2_playbook_on_start', locals())

    def v2_playbook_on_notify(self, handler, host):
        self.log('v2_playbook_on_notify', locals())

    def v2_playbook_on_no_hosts_matched(self):
        self.log('v2_playbook_on_no_hosts_matched', locals())

    def v2_playbook_on_no_hosts_remaining(self):
        self.log('v2_playbook_on_no_hosts_remaining', locals())

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.log('v2_playbook_on_task_start', locals())

    def v2_playbook_on_cleanup_task_start(self, task):
        self.log('v2_playbook_on_cleanup_task_start', locals())

    def v2_playbook_on_handler_task_start(self, task):
        self.log('v2_playbook_on_handler_task_start', locals())

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        self.log('v2_playbook_on_vars_prompt', locals())

    def v2_playbook_on_import_for_host(self, result, imported_file):
        self.log('v2_playbook_on_import_for_host', locals())

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        self.log('v2_playbook_on_not_import_for_host', locals())

    def v2_playbook_on_play_start(self, play):
        self.log('v2_playbook_on_play_start', locals())

    def v2_playbook_on_stats(self, stats):
        self.log('v2_playbook_on_stats', locals())

    def v2_on_file_diff(self, result):
        self.log('v2_on_file_diff', locals())

    def v2_playbook_on_include(self, included_file):
        self.log('v2_playbook_on_include', locals())

    def v2_runner_item_on_ok(self, result):
        self.log('v2_runner_item_on_ok', locals())

    def v2_runner_item_on_failed(self, result):
        self.log('v2_runner_item_on_failed', locals())

    def v2_runner_item_on_skipped(self, result):
        self.log('v2_runner_item_on_skipped', locals())

    def v2_runner_retry(self, result):
        self.log('v2_runner_retry', locals())

    def log(self, name, kwargs, args=None):
        if name in self.ignore:
            return

        kwargs = kwargs or {}

        kwargs.pop('self', None)
        result = kwargs.pop('result', None)

        message = name

        try:
            if result and hasattr(result, '_task'):
                task = result._task
            else:
                task = kwargs.pop('task', None)

            if task and hasattr(task, '_uuid'):
                task_uuid = task._uuid

                if task_uuid:
                    message += ' task_uuid=%s' % remap_uuid(task_uuid)

            if task and hasattr(task, 'get_name'):
                message += ' task_name="%s"' % task.get_name()

            if result and hasattr(result, '_host'):
                host = result._host

                if host and hasattr(host, '_uuid'):
                    message += ' host_uuid=%s' % remap_uuid(host._uuid)

                if host and hasattr(host, 'name'):
                    message += ' host_name=%s' % host.name

            playbook = kwargs.pop('playbook', None)

            if playbook and hasattr(playbook, '_file_name'):
                message += ' filename="%s"' % relative_path(playbook._file_name)

            play = kwargs.pop('play', None)

            if play and hasattr(play, 'get_name'):
                message += ' play_name="%s"' % play.get_name()

            included_file = kwargs.pop('included_file', None)

            if included_file and hasattr(included_file, '_filename'):
                message += ' filename="%s"' % relative_path(included_file._filename)

            stats = kwargs.pop('stats', None)

            if stats and hasattr(stats, 'processed'):
                message += ' hosts=%d' % len(stats.processed)

            if kwargs:
                message += ' %s' % ' '.join(['%s=%s' % (k, kwargs[k]) for k in sorted(kwargs)])

            if args:
                message += ' args=%s' % list(args)
        except:
            message += ' EXCEPTION'

        self.write_log(message)

    def write_log(self, message):
        self.fd.write('%s\n' % message)


REMAPPED_UUIDS = {}
UUID_COUNTER = 0
BASE_DIR = None

base_dir = os.getcwd()

while len(base_dir) >= 1:
    if os.path.isfile(os.path.join(base_dir, 'shippable.yml')):
        BASE_DIR = os.path.realpath(base_dir) + '/'
        break

    base_dir = os.path.dirname(base_dir)

if not BASE_DIR:
    raise Exception('unable to determine base_dir')


def relative_path(path):
    path = os.path.realpath(path)

    if path.startswith(BASE_DIR):
        path = path[len(BASE_DIR):]

    return path


def remap_uuid(uuid):
    global UUID_COUNTER

    if uuid not in REMAPPED_UUIDS:
        UUID_COUNTER += 1
        REMAPPED_UUIDS[uuid] = UUID_COUNTER

    return REMAPPED_UUIDS[uuid]
