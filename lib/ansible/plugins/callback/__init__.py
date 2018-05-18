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

import difflib
import json
import sys
import warnings
from copy import deepcopy

from ansible import constants as C
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins import AnsiblePlugin, get_plugin_class
from ansible.module_utils._text import to_text
from ansible.utils.color import stringc
from ansible.vars.clean import strip_internal_keys

try:
    from __main__ import display as global_display
except ImportError:
    from ansible.utils.display import Display
    global_display = Display()

try:
    from __main__ import cli
except ImportError:
    # using API w/o cli
    cli = False

__all__ = ["CallbackBase"]


class CallbackBase(AnsiblePlugin):

    '''
    This is a base ansible callback class that does nothing. New callbacks should
    use this class as a base and override any callback methods they wish to execute
    custom actions.
    '''

    def __init__(self, display=None, options=None):
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
            self._display.vvvv('Loading callback plugin %s of type %s, v%s from %s' % (name, ctype, version, sys.modules[self.__module__].__file__))

        self.disabled = False

        self._plugin_options = {}
        if options is not None:
            self.set_options(options)

        self._hide_in_debug = ('changed', 'failed', 'skipped', 'invocation')

    ''' helper for callbacks, so they don't all have to include deepcopy '''
    _copy_result = deepcopy

    def set_option(self, k, v):
        self._plugin_options[k] = v

    def get_option(self, k):
        return self._plugin_options[k]

    def set_options(self, task_keys=None, var_options=None, direct=None):
        ''' This is different than the normal plugin method as callbacks get called early and really don't accept keywords.
            Also _options was already taken for CLI args and callbacks use _plugin_options instead.
        '''

        # load from config
        self._plugin_options = C.config.get_plugin_options(get_plugin_class(self), self._load_name, keys=task_keys, variables=var_options)

        # or parse specific options
        if direct:
            for k in direct:
                if k in self._plugin_options:
                    self.set_option(k, direct[k])

    def _dump_results(self, result, indent=None, sort_keys=True, keep_invocation=False):

        if not indent and (result.get('_ansible_verbose_always') or self._display.verbosity > 2):
            indent = 4

        # All result keys stating with _ansible_ are internal, so remove them from the result before we output anything.
        abridged_result = strip_internal_keys(result)

        # remove invocation unless specifically wanting it
        if not keep_invocation and self._display.verbosity < 3 and 'invocation' in result:
            del abridged_result['invocation']

        # remove diff information from screen output
        if self._display.verbosity < 3 and 'diff' in result:
            del abridged_result['diff']

        # remove exception from screen output
        if 'exception' in abridged_result:
            del abridged_result['exception']

        return json.dumps(abridged_result, cls=AnsibleJSONEncoder, indent=indent, ensure_ascii=False, sort_keys=sort_keys)

    def _handle_warnings(self, res):
        ''' display warnings, if enabled and any exist in the result '''
        if C.ACTION_WARNINGS:
            if 'warnings' in res and res['warnings']:
                for warning in res['warnings']:
                    self._display.warning(warning)
                del res['warnings']
            if 'deprecations' in res and res['deprecations']:
                for warning in res['deprecations']:
                    self._display.deprecated(**warning)
                del res['deprecations']

    def _handle_exception(self, result):

        if 'exception' in result:
            msg = "An exception occurred during task execution. "
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result['exception'].strip().split('\n')[-1]
                msg += "To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "The full traceback is:\n" + result['exception']
                del result['exception']

            self._display.display(msg, color=C.COLOR_ERROR)

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
                                diff[x] = json.dumps(diff[x], sort_keys=True, indent=4, separators=(',', ': ')) + '\n'
                        if 'before_header' in diff:
                            before_header = "before: %s" % diff['before_header']
                        else:
                            before_header = 'before'
                        if 'after_header' in diff:
                            after_header = "after: %s" % diff['after_header']
                        else:
                            after_header = 'after'
                        before_lines = to_text(diff['before']).splitlines(True)
                        after_lines = to_text(diff['after']).splitlines(True)
                        if before_lines and not before_lines[-1].endswith('\n'):
                            before_lines[-1] += '\n\\ No newline at end of file\n'
                        if after_lines and not after_lines[-1].endswith('\n'):
                            after_lines[-1] += '\n\\ No newline at end of file\n'
                        differ = difflib.unified_diff(before_lines,
                                                      after_lines,
                                                      fromfile=before_header,
                                                      tofile=after_header,
                                                      fromfiledate='',
                                                      tofiledate='',
                                                      n=C.DIFF_CONTEXT)
                        difflines = list(differ)
                        if len(difflines) >= 3 and sys.version_info[:2] == (2, 6):
                            # difflib in Python 2.6 adds trailing spaces after
                            # filenames in the -- before/++ after headers.
                            difflines[0] = difflines[0].replace(' \n', '\n')
                            difflines[1] = difflines[1].replace(' \n', '\n')
                            # it also treats empty files differently
                            difflines[2] = difflines[2].replace('-1,0', '-0,0').replace('+1,0', '+0,0')
                        has_diff = False
                        for line in difflines:
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
                        ret.append(to_text(diff['prepared']))
            except UnicodeDecodeError:
                ret.append(">> the files are different, but the diff library cannot compare unicode strings\n\n")
        return u''.join(ret)

    def _get_item(self, result):
        if result.get('_ansible_no_log', False):
            item = "(censored due to no_log)"
        elif result.get('_ansible_item_label', False):
            item = result.get('_ansible_item_label')
        else:
            item = result.get('item', None)

        return item

    def _process_items(self, result):
        # just remove them as now they get handled by individual callbacks
        del result._result['results']

    def _clean_results(self, result, task_name):
        ''' removes data from results for display '''
        if task_name in ['debug']:
            for hideme in self._hide_in_debug:
                result.pop(hideme, None)
                if 'msg' in result:
                    result.pop('item', None)

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

    # V2 METHODS, by default they call v1 counterparts if possible
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
            self.runner_on_skipped(host, self._get_item(getattr(result._result, 'results', {})))

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.runner_on_unreachable(host, result._result)

    # FIXME: not called
    def v2_runner_on_async_poll(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        # FIXME, get real clock
        clock = 0
        self.runner_on_async_poll(host, result._result, jid, clock)

    # FIXME: not called
    def v2_runner_on_async_ok(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        self.runner_on_async_ok(host, result._result, jid)

    # FIXME: not called
    def v2_runner_on_async_failed(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        self.runner_on_async_failed(host, result._result, jid)

    def v2_playbook_on_start(self, playbook):
        self.playbook_on_start()

    def v2_playbook_on_notify(self, handler, host):
        self.playbook_on_notify(host, handler)

    def v2_playbook_on_no_hosts_matched(self):
        self.playbook_on_no_hosts_matched()

    def v2_playbook_on_no_hosts_remaining(self):
        self.playbook_on_no_hosts_remaining()

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.playbook_on_task_start(task.name, is_conditional)

    # FIXME: not called
    def v2_playbook_on_cleanup_task_start(self, task):
        pass  # no v1 correspondence

    def v2_playbook_on_handler_task_start(self, task):
        pass  # no v1 correspondence

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        self.playbook_on_vars_prompt(varname, private, prompt, encrypt, confirm, salt_size, salt, default)

    # FIXME: not called
    def v2_playbook_on_import_for_host(self, result, imported_file):
        host = result._host.get_name()
        self.playbook_on_import_for_host(host, imported_file)

    # FIXME: not called
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
        pass  # no v1 correspondence

    def v2_runner_item_on_ok(self, result):
        pass

    def v2_runner_item_on_failed(self, result):
        pass

    def v2_runner_item_on_skipped(self, result):
        pass

    def v2_runner_retry(self, result):
        pass
