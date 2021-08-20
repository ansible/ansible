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
from collections import OrderedDict
from copy import deepcopy

from ansible import constants as C
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.module_utils._text import to_text
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins import AnsiblePlugin, get_plugin_class
from ansible.utils.color import stringc
from ansible.utils.display import Display
from ansible.vars.clean import strip_internal_keys, module_response_deepcopy

global_display = Display()


__all__ = ["CallbackBase"]


_DEBUG_ALLOWED_KEYS = frozenset(('msg', 'exception', 'warnings', 'deprecations'))


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

        if self._display.verbosity >= 4:
            name = getattr(self, 'CALLBACK_NAME', 'unnamed')
            ctype = getattr(self, 'CALLBACK_TYPE', 'old')
            version = getattr(self, 'CALLBACK_VERSION', '1.0')
            self._display.vvvv('Loading callback plugin %s of type %s, v%s from %s' % (name, ctype, version, sys.modules[self.__module__].__file__))

        self.disabled = False
        self.wants_implicit_tasks = False

        self._plugin_options = {}
        if options is not None:
            self.set_options(options)

        self._hide_in_debug = ('changed', 'failed', 'skipped', 'invocation', 'skip_reason')

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
        self._plugin_options = C.config.get_plugin_options(get_plugin_class(self), self._load_name, keys=task_keys, variables=var_options, direct=direct)

    @staticmethod
    def host_label(result):
        """Return label for the hostname (& delegated hostname) of a task
        result.
        """
        label = "%s" % result._host.get_name()
        if result._task.delegate_to and result._task.delegate_to != result._host.get_name():
            # show delegated host
            label += " -> %s" % result._task.delegate_to
            # in case we have 'extra resolution'
            ahost = result._result.get('_ansible_delegated_vars', {}).get('ansible_host', result._task.delegate_to)
            if result._task.delegate_to != ahost:
                label += "(%s)" % ahost
        return label

    def _run_is_verbose(self, result, verbosity=0):
        return ((self._display.verbosity > verbosity or result._result.get('_ansible_verbose_always', False) is True)
                and result._result.get('_ansible_verbose_override', False) is False)

    def _dump_results(self, result, indent=None, sort_keys=True, keep_invocation=False):

        if not indent and (result.get('_ansible_verbose_always') or self._display.verbosity > 2):
            indent = 4

        # All result keys stating with _ansible_ are internal, so remove them from the result before we output anything.
        abridged_result = strip_internal_keys(module_response_deepcopy(result))

        # remove invocation unless specifically wanting it
        if not keep_invocation and self._display.verbosity < 3 and 'invocation' in result:
            del abridged_result['invocation']

        # remove diff information from screen output
        if self._display.verbosity < 3 and 'diff' in result:
            del abridged_result['diff']

        # remove exception from screen output
        if 'exception' in abridged_result:
            del abridged_result['exception']

        try:
            jsonified_results = json.dumps(abridged_result, cls=AnsibleJSONEncoder, indent=indent, ensure_ascii=False, sort_keys=sort_keys)
        except TypeError:
            # Python3 bug: throws an exception when keys are non-homogenous types:
            # https://bugs.python.org/issue25457
            # sort into an OrderedDict and then json.dumps() that instead
            if not OrderedDict:
                raise
            jsonified_results = json.dumps(OrderedDict(sorted(abridged_result.items(), key=to_text)),
                                           cls=AnsibleJSONEncoder, indent=indent,
                                           ensure_ascii=False, sort_keys=False)
        return jsonified_results

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

    def _handle_exception(self, result, use_stderr=False):

        if 'exception' in result:
            msg = "An exception occurred during task execution. "
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result['exception'].strip().split('\n')[-1]
                msg += "To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "The full traceback is:\n" + result['exception']
                del result['exception']

            self._display.display(msg, color=C.COLOR_ERROR, stderr=use_stderr)

    def _serialize_diff(self, diff):
        return json.dumps(diff, sort_keys=True, indent=4, separators=(u',', u': ')) + u'\n'

    def _get_diff(self, difflist):

        if not isinstance(difflist, list):
            difflist = [difflist]

        ret = []
        for diff in difflist:
            if 'dst_binary' in diff:
                ret.append(u"diff skipped: destination file appears to be binary\n")
            if 'src_binary' in diff:
                ret.append(u"diff skipped: source file appears to be binary\n")
            if 'dst_larger' in diff:
                ret.append(u"diff skipped: destination file size is greater than %d\n" % diff['dst_larger'])
            if 'src_larger' in diff:
                ret.append(u"diff skipped: source file size is greater than %d\n" % diff['src_larger'])
            if 'before' in diff and 'after' in diff:
                # format complex structures into 'files'
                for x in ['before', 'after']:
                    if isinstance(diff[x], MutableMapping):
                        diff[x] = self._serialize_diff(diff[x])
                    elif diff[x] is None:
                        diff[x] = ''
                if 'before_header' in diff:
                    before_header = u"before: %s" % diff['before_header']
                else:
                    before_header = u'before'
                if 'after_header' in diff:
                    after_header = u"after: %s" % diff['after_header']
                else:
                    after_header = u'after'
                before_lines = diff['before'].splitlines(True)
                after_lines = diff['after'].splitlines(True)
                if before_lines and not before_lines[-1].endswith(u'\n'):
                    before_lines[-1] += u'\n\\ No newline at end of file\n'
                if after_lines and not after_lines[-1].endswith('\n'):
                    after_lines[-1] += u'\n\\ No newline at end of file\n'
                differ = difflib.unified_diff(before_lines,
                                              after_lines,
                                              fromfile=before_header,
                                              tofile=after_header,
                                              fromfiledate=u'',
                                              tofiledate=u'',
                                              n=C.DIFF_CONTEXT)
                difflines = list(differ)
                if len(difflines) >= 3 and sys.version_info[:2] == (2, 6):
                    # difflib in Python 2.6 adds trailing spaces after
                    # filenames in the -- before/++ after headers.
                    difflines[0] = difflines[0].replace(u' \n', u'\n')
                    difflines[1] = difflines[1].replace(u' \n', u'\n')
                    # it also treats empty files differently
                    difflines[2] = difflines[2].replace(u'-1,0', u'-0,0').replace(u'+1,0', u'+0,0')
                has_diff = False
                for line in difflines:
                    has_diff = True
                    if line.startswith(u'+'):
                        line = stringc(line, C.COLOR_DIFF_ADD)
                    elif line.startswith(u'-'):
                        line = stringc(line, C.COLOR_DIFF_REMOVE)
                    elif line.startswith(u'@@'):
                        line = stringc(line, C.COLOR_DIFF_LINES)
                    ret.append(line)
                if has_diff:
                    ret.append('\n')
            if 'prepared' in diff:
                ret.append(diff['prepared'])
        return u''.join(ret)

    def _get_item_label(self, result):
        ''' retrieves the value to be displayed as a label for an item entry from a result object'''
        if result.get('_ansible_no_log', False):
            item = "(censored due to no_log)"
        else:
            item = result.get('_ansible_item_label', result.get('item'))
        return item

    def _process_items(self, result):
        # just remove them as now they get handled by individual callbacks
        del result._result['results']

    def _clean_results(self, result, task_name):
        ''' removes data from results for display '''

        # mostly controls that debug only outputs what it was meant to
        if task_name in C._ACTION_DEBUG:
            if 'msg' in result:
                # msg should be alone
                for key in list(result.keys()):
                    if key not in _DEBUG_ALLOWED_KEYS and not key.startswith('_'):
                        result.pop(key)
            else:
                # 'var' value as field, so eliminate others and what is left should be varname
                for hidme in self._hide_in_debug:
                    result.pop(hidme, None)

    def _print_task_path(self, task, color=C.COLOR_DEBUG):
        path = task.get_path()
        if path:
            self._display.display(u"task path: %s" % path, color=color)

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

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None, unsafe=None):
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
            self.runner_on_skipped(host, self._get_item_label(getattr(result._result, 'results', {})))

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.runner_on_unreachable(host, result._result)

    def v2_runner_on_async_poll(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        # FIXME, get real clock
        clock = 0
        self.runner_on_async_poll(host, result._result, jid, clock)

    def v2_runner_on_async_ok(self, result):
        host = result._host.get_name()
        jid = result._result.get('ansible_job_id')
        self.runner_on_async_ok(host, result._result, jid)

    def v2_runner_on_async_failed(self, result):
        host = result._host.get_name()
        # Attempt to get the async job ID. If the job does not finish before the
        # async timeout value, the ID may be within the unparsed 'async_result' dict.
        jid = result._result.get('ansible_job_id')
        if not jid and 'async_result' in result._result:
            jid = result._result['async_result'].get('ansible_job_id')
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

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None, unsafe=None):
        self.playbook_on_vars_prompt(varname, private, prompt, encrypt, confirm, salt_size, salt, default, unsafe)

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

    def v2_runner_on_start(self, host, task):
        """Event used when host begins execution of a task

        .. versionadded:: 2.8
        """
        pass
