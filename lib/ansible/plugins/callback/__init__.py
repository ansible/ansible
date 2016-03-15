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
import difflib
import warnings
from copy import deepcopy

from ansible.compat.six import string_types

from ansible import constants as C
from ansible.vars import strip_internal_keys
from ansible.utils.color import stringc
from ansible.utils.unicode import to_unicode

try:
    from __main__ import display as global_display
except ImportError:
    from ansible.utils.display import Display
    global_display = Display()

__all__ = ["CallbackBase"]

try:
    from __main__ import cli
except ImportError:
    # using API w/o cli 
    cli = False

class CallbackBase:

    '''
    This is a base ansible callback class that does nothing. New callbacks should
    use this class as a base and override any callback methods they wish to execute
    custom actions.
    '''

    def __init__(self, display=None):
        if display:
            self._display = display
        else:
            self._display = global_display

        if cli:
            self._options = cli.options
        else:
            self._options = None

        if self._display.verbosity >= 4:
            name = getattr(self, 'CALLBACK_NAME', 'unnamed')
            ctype = getattr(self, 'CALLBACK_TYPE', 'old')
            version = getattr(self, 'CALLBACK_VERSION', '1.0')
            self._display.vvvv('Loaded callback %s of type %s, v%s' % (name, ctype, version))

    ''' helper for callbacks, so they don't all have to include deepcopy '''
    _copy_result = deepcopy

    def _copy_result_exclude(self, result, exclude):
        values = []
        for e in exclude:
            values.append(getattr(result, e))
            setattr(result, e, None)

        result_copy = deepcopy(result)
        for i,e in enumerate(exclude):
            setattr(result, e, values[i])

        return result_copy

    def _dump_results(self, result, indent=None, sort_keys=True, keep_invocation=False):
        if result.get('_ansible_no_log', False):
            return json.dumps(dict(censored="the output has been hidden due to the fact that 'no_log: true' was specified for this result"))

        if not indent and '_ansible_verbose_always' in result and result['_ansible_verbose_always']:
            indent = 4

        # All result keys stating with _ansible_ are internal, so remove them from the result before we output anything.
        abridged_result = strip_internal_keys(result)

        # remove invocation unless specifically wanting it
        if not keep_invocation and self._display.verbosity < 3 and 'invocation' in result:
            del abridged_result['invocation']

        return json.dumps(abridged_result, indent=indent, ensure_ascii=False, sort_keys=sort_keys)

    def _handle_warnings(self, res):
        ''' display warnings, if enabled and any exist in the result '''
        if C.COMMAND_WARNINGS and 'warnings' in res and res['warnings']:
            for warning in res['warnings']:
                self._display.warning(warning)

    def _get_diff(self, difflist):

        if not isinstance(difflist, list):
            difflist = [difflist]

        ret = []
        for diff in difflist:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    if 'dst_binary' in diff:
                        ret.append("diff skipped: destination file appears to be binary\n")
                    if 'src_binary' in diff:
                        ret.append("diff skipped: source file appears to be binary\n")
                    if 'dst_larger' in diff:
                        ret.append("diff skipped: destination file size is greater than %d\n" % diff['dst_larger'])
                    if 'src_larger' in diff:
                        ret.append("diff skipped: source file size is greater than %d\n" % diff['src_larger'])
                    if 'before' in diff and 'after' in diff:
                        # format complex structures into 'files'
                        for x in ['before', 'after']:
                            if isinstance(diff[x], dict):
                                diff[x] = json.dumps(diff[x], sort_keys=True, indent=4)
                        if 'before_header' in diff:
                            before_header = "before: %s" % diff['before_header']
                        else:
                            before_header = 'before'
                        if 'after_header' in diff:
                            after_header = "after: %s" % diff['after_header']
                        else:
                            after_header = 'after'
                        differ = difflib.unified_diff(to_unicode(diff['before']).splitlines(True),
                                                      to_unicode(diff['after']).splitlines(True),
                                                      fromfile=before_header,
                                                      tofile=after_header,
                                                      fromfiledate='',
                                                      tofiledate='',
                                                      n=C.DIFF_CONTEXT)
                        has_diff = False
                        for line in differ:
                            has_diff = True
                            if line.startswith('+'):
                                line = stringc(line, C.COLOR_DIFF_ADD)
                            elif line.startswith('-'):
                                line = stringc(line, C.COLOR_DIFF_REMOVE)
                            elif line.startswith('@@'):
                                line = stringc(line, C.COLOR_DIFF_LINES)
                            ret.append(line)
                        if has_diff:
                            ret.append('\n')
                    if 'prepared' in diff:
                        ret.append(to_unicode(diff['prepared']))
            except UnicodeDecodeError:
                ret.append(">> the files are different, but the diff library cannot compare unicode strings\n\n")
        return u''.join(ret)

    def _get_item(self, result):
        if result.get('_ansible_no_log', False):
            item = "(censored due to no_log)"
        else:
            item = result.get('item', None)

        return item

    def _process_items(self, result):
        # just remove them as now they get handled by individual callbacks
        del result._result['results']

    def _clean_results(self, result, task_name):
        if 'changed' in result and task_name in ['debug']:
            del result['changed']
        if 'invocation' in result and task_name in ['debug']:
            del result['invocation']

    def set_play_context(self, play_context):
        pass

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        pass

    def runner_on_ok(self, host, res):
        pass

    def runner_on_skipped(self, host, item=None):
        pass

    def runner_on_unreachable(self, host, res):
        pass

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        pass

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, name):
        pass

    def playbook_on_stats(self, stats):
        pass

    def on_file_diff(self, host, diff):
        pass

    ####### V2 METHODS, by default they call v1 counterparts if possible ######
    def v2_on_any(self, *args, **kwargs):
        self.on_any(args, kwargs)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self.runner_on_failed(host, result._result, ignore_errors)

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self.runner_on_ok(host, result._result)

    def v2_runner_on_skipped(self, result):
        if C.DISPLAY_SKIPPED_HOSTS:
            host = result._host.get_name()
            self.runner_on_skipped(host, self._get_item(getattr(result._result,'results',{})))

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.runner_on_unreachable(host, result._result)

    def v2_runner_on_no_hosts(self, task):
        self.runner_on_no_hosts()

    def v2_runner_on_async_poll(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        #FIXME, get real clock
        clock = 0
        self.runner_on_async_poll(host, result._result, jid, clock)

    def v2_runner_on_async_ok(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        self.runner_on_async_ok(host, result._result, jid)

    def v2_runner_on_async_failed(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        self.runner_on_async_failed(host, result._result, jid)

    def v2_runner_on_file_diff(self, result, diff):
        pass #no v1 correspondance

    def v2_playbook_on_start(self, playbook):
        self.playbook_on_start()

    def v2_playbook_on_notify(self, result, handler):
        host = result._host.get_name()
        self.playbook_on_notify(host, handler)

    def v2_playbook_on_no_hosts_matched(self):
        self.playbook_on_no_hosts_matched()

    def v2_playbook_on_no_hosts_remaining(self):
        self.playbook_on_no_hosts_remaining()

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.playbook_on_task_start(task, is_conditional)

    def v2_playbook_on_cleanup_task_start(self, task):
        pass #no v1 correspondance

    def v2_playbook_on_handler_task_start(self, task):
        pass #no v1 correspondance

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        self.playbook_on_vars_prompt(varname, private, prompt, encrypt, confirm, salt_size, salt, default)

    def v2_playbook_on_setup(self):
        self.playbook_on_setup()

    def v2_playbook_on_import_for_host(self, result, imported_file):
        host = result._host.get_name()
        self.playbook_on_import_for_host(host, imported_file)

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        host = result._host.get_name()
        self.playbook_on_not_import_for_host(host, missing_file)

    def v2_playbook_on_play_start(self, play):
        self.playbook_on_play_start(play.name)

    def v2_playbook_on_stats(self, stats):
        self.playbook_on_stats(stats)

    def v2_on_file_diff(self, result):
        if 'diff' in result._result:
            host = result._host.get_name()
            self.on_file_diff(host, result._result['diff'])

    def v2_playbook_on_include(self, included_file):
        pass #no v1 correspondance

    def v2_playbook_item_on_ok(self, result):
        pass

    def v2_playbook_item_on_failed(self, result):
        pass

    def v2_playbook_item_on_skipped(self, result):
        pass

    def v2_playbook_retry(self, result):
        pass

