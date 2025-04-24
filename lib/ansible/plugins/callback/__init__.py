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

from __future__ import annotations

import difflib
import functools
import json
import re
import sys
import textwrap
import typing as t
import collections.abc as _c

from typing import TYPE_CHECKING

from copy import deepcopy

from ansible import constants as C
from ansible.module_utils._internal import _datatag
from ansible._internal._yaml import _dumper
from ansible.plugins import AnsiblePlugin
from ansible.utils.color import stringc
from ansible.utils.display import Display
from ansible.vars.clean import strip_internal_keys, module_response_deepcopy
from ansible.module_utils._internal._json._profiles import _fallback_to_str
from ansible._internal._templating import _engine

import yaml

if TYPE_CHECKING:
    from ansible.executor.task_result import CallbackTaskResult

global_display = Display()


__all__ = ["CallbackBase"]


_DEBUG_ALLOWED_KEYS = frozenset(('msg', 'exception', 'warnings', 'deprecations'))
# Characters that libyaml/pyyaml consider breaks
_YAML_BREAK_CHARS = '\n\x85\u2028\u2029'  # NL, NEL, LS, PS
# regex representation of libyaml/pyyaml of a space followed by a break character
_SPACE_BREAK_RE = re.compile(fr' +([{_YAML_BREAK_CHARS}])')


_T_callable = t.TypeVar("_T_callable", bound=t.Callable)


def _callback_base_impl(wrapped: _T_callable) -> _T_callable:
    """
    Decorator for the no-op methods on the `CallbackBase` base class.
    Used to avoid unnecessary dispatch overhead to no-op base callback methods.
    """
    wrapped._base_impl = True

    return wrapped


class _AnsibleCallbackDumper(_dumper.AnsibleDumper):
    def __init__(self, *args, lossy: bool = False, **kwargs):
        super().__init__(*args, **kwargs)

        self._lossy = lossy

    def _pretty_represent_str(self, data):
        """Uses block style for multi-line strings"""
        data = _datatag.AnsibleTagHelper.as_native_type(data)

        if _should_use_block(data):
            style = '|'
            if self._lossy:
                data = _munge_data_for_lossy_yaml(data)
        else:
            style = self.default_style

        node = yaml.representer.ScalarNode('tag:yaml.org,2002:str', data, style=style)

        if self.alias_key is not None:
            self.represented_objects[self.alias_key] = node

        return node

    @classmethod
    def _register_representers(cls) -> None:
        super()._register_representers()

        # exact type checks occur first against representers, then subclasses against multi-representers
        cls.add_representer(str, cls._pretty_represent_str)
        cls.add_multi_representer(str, cls._pretty_represent_str)


def _should_use_block(scalar):
    """Returns true if string should be in block format based on the existence of various newline separators"""
    # This method of searching is faster than using a regex
    for ch in _YAML_BREAK_CHARS:
        if ch in scalar:
            return True

    return False


class _SpecialCharacterTranslator:
    def __getitem__(self, ch):
        # "special character" logic from pyyaml yaml.emitter.Emitter.analyze_scalar, translated to decimal
        # for perf w/ str.translate
        if (ch == 10 or
            32 <= ch <= 126 or
            ch == 133 or
            160 <= ch <= 55295 or
            57344 <= ch <= 65533 or
            65536 <= ch < 1114111)\
                and ch != 65279:
            return ch
        return None


def _filter_yaml_special(scalar: str) -> str:
    """Filter a string removing any character that libyaml/pyyaml declare as special"""
    return scalar.translate(_SpecialCharacterTranslator())


def _munge_data_for_lossy_yaml(scalar: str) -> str:
    """Modify a string so that analyze_scalar in libyaml/pyyaml will allow block formatting"""
    # we care more about readability than accuracy, so...
    # ...libyaml/pyyaml does not permit trailing spaces for block scalars
    scalar = scalar.rstrip()
    # ...libyaml/pyyaml does not permit tabs for block scalars
    scalar = scalar.expandtabs()
    # ...libyaml/pyyaml only permits special characters for double quoted scalars
    scalar = _filter_yaml_special(scalar)
    # ...libyaml/pyyaml only permits spaces followed by breaks for double quoted scalars
    return _SPACE_BREAK_RE.sub(r'\1', scalar)


class CallbackBase(AnsiblePlugin):
    """
    This is a base ansible callback class that does nothing. New callbacks should
    use this class as a base and override any callback methods they wish to execute
    custom actions.
    """

    def __init__(self, display: Display | None = None, options: dict[str, t.Any] | None = None) -> None:
        super().__init__()

        if display:
            self._display = display
        else:
            self._display = global_display

        # FUTURE: fix double-loading of non-collection stdout callback plugins that don't set CALLBACK_NEEDS_ENABLED

        # FUTURE: this code is jacked for 2.x- it should just use the type names and always assume 2.0+ for normal cases
        if self._display.verbosity >= 4:
            name = getattr(self, 'CALLBACK_NAME', 'unnamed')
            ctype = getattr(self, 'CALLBACK_TYPE', 'old')
            version = getattr(self, 'CALLBACK_VERSION', '1.0')
            self._display.vvvv('Loading callback plugin %s of type %s, v%s from %s' % (name, ctype, version, sys.modules[self.__module__].__file__))

        self.disabled = False
        self.wants_implicit_tasks = False

        self._plugin_options: dict[str, t.Any] = {}

        if options is not None:
            self.set_options(options)

        self._hide_in_debug = (
            'changed', 'failed', 'skipped', 'invocation', 'skip_reason',
            'ansible_loop_var', 'ansible_index_var', 'ansible_loop',
        )

        self._current_task_result: CallbackTaskResult | None = None

    # helper for callbacks, so they don't all have to include deepcopy
    _copy_result = deepcopy

    def set_option(self, k, v):
        self._plugin_options[k] = C.config.get_config_value(k, plugin_type=self.plugin_type, plugin_name=self._load_name, direct={k: v})

    def get_option(self, k, hostvars=None):
        return self._plugin_options[k]

    def has_option(self, option):
        return (option in self._plugin_options)

    def set_options(self, task_keys=None, var_options=None, direct=None):
        """ This is different than the normal plugin method as callbacks get called early and really don't accept keywords.
            Also _options was already taken for CLI args and callbacks use _plugin_options instead.
        """

        # load from config
        self._plugin_options = C.config.get_plugin_options(self.plugin_type, self._load_name, keys=task_keys, variables=var_options, direct=direct)

    @staticmethod
    def host_label(result: CallbackTaskResult) -> str:
        """Return label for the hostname (& delegated hostname) of a task result."""
        label = result.host.get_name()
        if result.task.delegate_to and result.task.delegate_to != result.host.get_name():
            # show delegated host
            label += " -> %s" % result.task.delegate_to
            # in case we have 'extra resolution'
            ahost = result.result.get('_ansible_delegated_vars', {}).get('ansible_host', result.task.delegate_to)
            if result.task.delegate_to != ahost:
                label += "(%s)" % ahost
        return label

    def _run_is_verbose(self, result: CallbackTaskResult, verbosity: int = 0) -> bool:
        return ((self._display.verbosity > verbosity or result.result.get('_ansible_verbose_always', False) is True)
                and result.result.get('_ansible_verbose_override', False) is False)

    def _dump_results(
        self,
        result: _c.Mapping[str, t.Any],
        indent: int | None = None,
        sort_keys: bool = True,
        keep_invocation: bool = False,
        serialize: bool = True,
    ) -> str:
        try:
            result_format = self.get_option('result_format')
        except KeyError:
            # Callback does not declare result_format nor extend result_format_callback
            result_format = 'json'

        try:
            pretty_results = self.get_option('pretty_results')
        except KeyError:
            # Callback does not declare pretty_results nor extend result_format_callback
            pretty_results = None

        indent_conditions = (
            result.get('_ansible_verbose_always'),
            pretty_results is None and result_format != 'json',
            pretty_results is True,
            self._display.verbosity > 2,
        )

        if not indent and any(indent_conditions):
            indent = 4
        if pretty_results is False:
            # pretty_results=False overrides any specified indentation
            indent = None

        # All result keys stating with _ansible_ are internal, so remove them from the result before we output anything.
        abridged_result = strip_internal_keys(module_response_deepcopy(result))

        # remove invocation unless specifically wanting it
        if not keep_invocation and self._display.verbosity < 3 and 'invocation' in result:
            del abridged_result['invocation']

        # remove diff information from screen output
        if self._display.verbosity < 3 and 'diff' in result:
            del abridged_result['diff']

        # remove error/warning values; the stdout callback should have already handled them
        abridged_result.pop('exception', None)
        abridged_result.pop('warnings', None)
        abridged_result.pop('deprecations', None)

        abridged_result = _engine.TemplateEngine().transform(abridged_result)  # ensure the dumped view matches the transformed view a playbook sees

        if not serialize:
            # Just return ``abridged_result`` without going through serialization
            # to permit callbacks to take advantage of ``_dump_results``
            # that want to further modify the result, or use custom serialization
            return abridged_result

        # DTFIX-RELEASE: Switch to stock json/yaml serializers here? We should always have a transformed plain-types result.

        if result_format == 'json':
            return json.dumps(abridged_result, cls=_fallback_to_str.Encoder, indent=indent, ensure_ascii=False, sort_keys=sort_keys)

        if result_format == 'yaml':
            # None is a sentinel in this case that indicates default behavior
            # default behavior for yaml is to prettify results
            lossy = pretty_results in (None, True)
            if lossy:
                # if we already have stdout, we don't need stdout_lines
                if 'stdout' in abridged_result and 'stdout_lines' in abridged_result:
                    abridged_result['stdout_lines'] = '<omitted>'

                # if we already have stderr, we don't need stderr_lines
                if 'stderr' in abridged_result and 'stderr_lines' in abridged_result:
                    abridged_result['stderr_lines'] = '<omitted>'

            return '\n%s' % textwrap.indent(
                yaml.dump(
                    abridged_result,
                    allow_unicode=True,
                    Dumper=functools.partial(_AnsibleCallbackDumper, lossy=lossy),
                    default_flow_style=False,
                    indent=indent,
                    # sort_keys=sort_keys  # This requires PyYAML>=5.1
                ),
                ' ' * (indent or 4)
            )

        # DTFIX-RELEASE: add test to exercise this case
        raise ValueError(f'Unsupported result_format {result_format!r}.')

    def _handle_warnings(self, res: _c.MutableMapping[str, t.Any]) -> None:
        """Display warnings and deprecation warnings sourced by task execution."""
        if res.pop('warnings', None) and self._current_task_result and (warnings := self._current_task_result.warnings):
            # display warnings from the current task result if `warnings` was not removed from `result` (or made falsey)
            for warning in warnings:
                # DTFIX-RELEASE: what to do about propagating wrap_text from the original display.warning call?
                self._display._warning(warning, wrap_text=False)

        if res.pop('deprecations', None) and self._current_task_result and (deprecations := self._current_task_result.deprecations):
            # display deprecations from the current task result if `deprecations` was not removed from `result` (or made falsey)
            for deprecation in deprecations:
                self._display._deprecated(deprecation)

    def _handle_exception(self, result: _c.MutableMapping[str, t.Any], use_stderr: bool = False) -> None:
        if result.pop('exception', None) and self._current_task_result and (exception := self._current_task_result.exception):
            # display exception from the current task result if `exception` was not removed from `result` (or made falsey)
            self._display._error(exception, wrap_text=False, stderr=use_stderr)

    def _handle_warnings_and_exception(self, result: CallbackTaskResult) -> None:
        """Standardized handling of warnings/deprecations and exceptions from a task/item result."""
        # DTFIX-RELEASE: make/doc/porting-guide a public version of this method?
        try:
            use_stderr = self.get_option('display_failed_stderr')
        except KeyError:
            use_stderr = False

        self._handle_warnings(result.result)
        self._handle_exception(result.result, use_stderr=use_stderr)

    def _serialize_diff(self, diff):
        try:
            result_format = self.get_option('result_format')
        except KeyError:
            # Callback does not declare result_format nor extend result_format_callback
            result_format = 'json'

        try:
            pretty_results = self.get_option('pretty_results')
        except KeyError:
            # Callback does not declare pretty_results nor extend result_format_callback
            pretty_results = None

        if result_format == 'json':
            return json.dumps(diff, sort_keys=True, indent=4, separators=(u',', u': ')) + u'\n'

        if result_format == 'yaml':
            # None is a sentinel in this case that indicates default behavior
            # default behavior for yaml is to prettify results
            lossy = pretty_results in (None, True)
            return '%s\n' % textwrap.indent(
                yaml.dump(
                    diff,
                    allow_unicode=True,
                    Dumper=functools.partial(_AnsibleCallbackDumper, lossy=lossy),
                    default_flow_style=False,
                    indent=4,
                    # sort_keys=sort_keys  # This requires PyYAML>=5.1
                ),
                '    '
            )

        # DTFIX-RELEASE: add test to exercise this case
        raise ValueError(f'Unsupported result_format {result_format!r}.')

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
                    if isinstance(diff[x], _c.Mapping):
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

    def _get_item_label(self, result: _c.Mapping[str, t.Any]) -> t.Any:
        """ retrieves the value to be displayed as a label for an item entry from a result object"""
        if result.get('_ansible_no_log', False):
            item = "(censored due to no_log)"
        else:
            item = result.get('_ansible_item_label', result.get('item'))
        return item

    def _process_items(self, result: CallbackTaskResult) -> None:
        # just remove them as now they get handled by individual callbacks
        del result.result['results']

    def _clean_results(self, result, task_name):
        """ removes data from results for display """

        # mostly controls that debug only outputs what it was meant to
        # FIXME: this is a terrible heuristic to format debug's output- it masks exception detail
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

    @_callback_base_impl
    def on_any(self, *args, **kwargs):
        pass

    @_callback_base_impl
    def runner_on_failed(self, host, res, ignore_errors=False):
        pass

    @_callback_base_impl
    def runner_on_ok(self, host, res):
        pass

    @_callback_base_impl
    def runner_on_skipped(self, host, item=None):
        pass

    @_callback_base_impl
    def runner_on_unreachable(self, host, res):
        pass

    @_callback_base_impl
    def runner_on_no_hosts(self):
        pass

    @_callback_base_impl
    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    @_callback_base_impl
    def runner_on_async_ok(self, host, res, jid):
        pass

    @_callback_base_impl
    def runner_on_async_failed(self, host, res, jid):
        pass

    @_callback_base_impl
    def playbook_on_start(self):
        pass

    @_callback_base_impl
    def playbook_on_notify(self, host, handler):
        pass

    @_callback_base_impl
    def playbook_on_no_hosts_matched(self):
        pass

    @_callback_base_impl
    def playbook_on_no_hosts_remaining(self):
        pass

    @_callback_base_impl
    def playbook_on_task_start(self, name, is_conditional):
        pass

    @_callback_base_impl
    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None, unsafe=None):
        pass

    @_callback_base_impl
    def playbook_on_setup(self):
        pass

    @_callback_base_impl
    def playbook_on_import_for_host(self, host, imported_file):
        pass

    @_callback_base_impl
    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    @_callback_base_impl
    def playbook_on_play_start(self, name):
        pass

    @_callback_base_impl
    def playbook_on_stats(self, stats):
        pass

    @_callback_base_impl
    def on_file_diff(self, host, diff):
        pass

    # V2 METHODS, by default they call v1 counterparts if possible
    @_callback_base_impl
    def v2_on_any(self, *args, **kwargs):
        self.on_any(args, kwargs)

    @_callback_base_impl
    def v2_runner_on_failed(self, result: CallbackTaskResult, ignore_errors: bool = False) -> None:
        """Process results of a failed task.

        Note: The value of 'ignore_errors' tells Ansible whether to
        continue running tasks on the host where this task failed.
        But the 'ignore_errors' directive only works when the task can
        run and returns a value of 'failed'. It does not make Ansible
        ignore undefined variable errors, connection failures, execution
        issues (for example, missing packages), or syntax errors.

        :param result: The parameters of the task and its results.
        :type result: CallbackTaskResult
        :param ignore_errors: Whether Ansible should continue \
            running tasks on the host where the task failed.
        :type ignore_errors: bool

        :return: None
        :rtype: None
        """
        host = result.host.get_name()
        self.runner_on_failed(host, result.result, ignore_errors)

    @_callback_base_impl
    def v2_runner_on_ok(self, result: CallbackTaskResult) -> None:
        """Process results of a successful task.

        :param result: The parameters of the task and its results.
        :type result: CallbackTaskResult

        :return: None
        :rtype: None
        """
        host = result.host.get_name()
        self.runner_on_ok(host, result.result)

    @_callback_base_impl
    def v2_runner_on_skipped(self, result: CallbackTaskResult) -> None:
        """Process results of a skipped task.

        :param result: The parameters of the task and its results.
        :type result: CallbackTaskResult

        :return: None
        :rtype: None
        """
        if C.DISPLAY_SKIPPED_HOSTS:
            host = result.host.get_name()
            self.runner_on_skipped(host, self._get_item_label(getattr(result.result, 'results', {})))

    @_callback_base_impl
    def v2_runner_on_unreachable(self, result: CallbackTaskResult) -> None:
        """Process results of a task if a target node is unreachable.

        :param result: The parameters of the task and its results.
        :type result: CallbackTaskResult

        :return: None
        :rtype: None
        """
        host = result.host.get_name()
        self.runner_on_unreachable(host, result.result)

    @_callback_base_impl
    def v2_runner_on_async_poll(self, result: CallbackTaskResult) -> None:
        """Get details about an unfinished task running in async mode.

        Note: The value of the `poll` keyword in the task determines
        the interval at which polling occurs and this method is run.

        :param result: The parameters of the task and its status.
        :type result: CallbackTaskResult

        :rtype: None
        :rtype: None
        """
        host = result.host.get_name()
        jid = result.result.get('ansible_job_id')
        # FIXME, get real clock
        clock = 0
        self.runner_on_async_poll(host, result.result, jid, clock)

    @_callback_base_impl
    def v2_runner_on_async_ok(self, result: CallbackTaskResult) -> None:
        """Process results of a successful task that ran in async mode.

        :param result: The parameters of the task and its results.
        :type result: CallbackTaskResult

        :return: None
        :rtype: None
        """
        host = result.host.get_name()
        jid = result.result.get('ansible_job_id')
        self.runner_on_async_ok(host, result.result, jid)

    @_callback_base_impl
    def v2_runner_on_async_failed(self, result: CallbackTaskResult) -> None:
        host = result.host.get_name()
        # Attempt to get the async job ID. If the job does not finish before the
        # async timeout value, the ID may be within the unparsed 'async_result' dict.
        jid = result.result.get('ansible_job_id')
        if not jid and 'async_result' in result.result:
            jid = result.result['async_result'].get('ansible_job_id')
        self.runner_on_async_failed(host, result.result, jid)

    @_callback_base_impl
    def v2_playbook_on_start(self, playbook):
        self.playbook_on_start()

    @_callback_base_impl
    def v2_playbook_on_notify(self, handler, host):
        self.playbook_on_notify(host, handler)

    @_callback_base_impl
    def v2_playbook_on_no_hosts_matched(self):
        self.playbook_on_no_hosts_matched()

    @_callback_base_impl
    def v2_playbook_on_no_hosts_remaining(self):
        self.playbook_on_no_hosts_remaining()

    @_callback_base_impl
    def v2_playbook_on_task_start(self, task, is_conditional):
        self.playbook_on_task_start(task.name, is_conditional)

    # FIXME: not called
    @_callback_base_impl
    def v2_playbook_on_cleanup_task_start(self, task):
        pass  # no v1 correspondence

    @_callback_base_impl
    def v2_playbook_on_handler_task_start(self, task):
        pass  # no v1 correspondence

    @_callback_base_impl
    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None, unsafe=None):
        self.playbook_on_vars_prompt(varname, private, prompt, encrypt, confirm, salt_size, salt, default, unsafe)

    # FIXME: not called
    @_callback_base_impl
    def v2_playbook_on_import_for_host(self, result: CallbackTaskResult, imported_file) -> None:
        host = result.host.get_name()
        self.playbook_on_import_for_host(host, imported_file)

    # FIXME: not called
    @_callback_base_impl
    def v2_playbook_on_not_import_for_host(self, result: CallbackTaskResult, missing_file) -> None:
        host = result.host.get_name()
        self.playbook_on_not_import_for_host(host, missing_file)

    @_callback_base_impl
    def v2_playbook_on_play_start(self, play):
        self.playbook_on_play_start(play.name)

    @_callback_base_impl
    def v2_playbook_on_stats(self, stats):
        self.playbook_on_stats(stats)

    @_callback_base_impl
    def v2_on_file_diff(self, result: CallbackTaskResult) -> None:
        if 'diff' in result.result:
            host = result.host.get_name()
            self.on_file_diff(host, result.result['diff'])

    @_callback_base_impl
    def v2_playbook_on_include(self, included_file):
        pass  # no v1 correspondence

    @_callback_base_impl
    def v2_runner_item_on_ok(self, result: CallbackTaskResult) -> None:
        pass

    @_callback_base_impl
    def v2_runner_item_on_failed(self, result: CallbackTaskResult) -> None:
        pass

    @_callback_base_impl
    def v2_runner_item_on_skipped(self, result: CallbackTaskResult) -> None:
        pass

    @_callback_base_impl
    def v2_runner_retry(self, result: CallbackTaskResult) -> None:
        pass

    @_callback_base_impl
    def v2_runner_on_start(self, host, task):
        """Event used when host begins execution of a task

        .. versionadded:: 2.8
        """
        pass
