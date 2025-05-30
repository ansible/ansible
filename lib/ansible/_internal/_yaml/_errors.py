from __future__ import annotations

import re

import typing as t

from yaml import MarkedYAMLError
from yaml.constructor import ConstructorError

from ansible._internal._errors import _error_utils
from ansible.errors import AnsibleParserError
from ansible._internal._datatag._tags import Origin


class AnsibleConstructorError(ConstructorError):
    """Ansible-specific ConstructorError used to bypass exception analysis during wrapping in AnsibleYAMLParserError."""


class AnsibleYAMLParserError(AnsibleParserError):
    """YAML-specific parsing failure wrapping an exception raised by the YAML parser."""

    _default_message = 'YAML parsing failed.'

    _include_cause_message = False  # hide the underlying cause message, it's included by `handle_exception` as needed

    _formatted_source_context_value: str | None = None

    @property
    def _formatted_source_context(self) -> str | None:
        return self._formatted_source_context_value

    @classmethod
    def handle_exception(cls, exception: Exception, origin: Origin) -> t.NoReturn:
        if isinstance(exception, MarkedYAMLError):
            origin = origin.replace(line_num=exception.problem_mark.line + 1, col_num=exception.problem_mark.column + 1)

        source_context = _error_utils.SourceContext.from_origin(origin)

        target_line = source_context.target_line or ''  # for these cases, we don't need to distinguish between None and empty string

        message: str | None = None
        help_text = None

        # FIXME: Do all this by walking the parsed YAML doc stream. Using regexes is a dead-end; YAML's just too flexible to not have a
        #  raft of false-positives and corner cases. If we directly consume either the YAML parse stream or override the YAML composer, we can
        #  better catch these things without worrying about duplicating YAML's scalar parsing logic around quoting/escaping. At first, we can
        #  replace the regex logic below with tiny special-purpose parse consumers to catch specific issues, but ideally, we could do a lot of this
        #  inline with the actual doc parse, since our rules are a lot more strict than YAML's (eg, no support for non-scalar keys), and a lot of the
        #  problem cases where that comes into play are around expression quoting and Jinja {{ syntax looking like weird YAML values we don't support.
        #  Some common examples, where -> is "what YAML actually sees":
        #  foo: {{ bar }} -> {"foo": {{"bar": None}: None}} - a mapping with a mapping as its key (legal YAML, but not legal Python/Ansible)
        #
        #  - copy: src=foo.txt  # kv syntax (kv could be on following line(s), too- implicit multi-line block scalar)
        #      dest: bar.txt  # orphaned mapping, since the value of `copy` is the scalar "src=foo.txt"
        #
        #  - msg == "Error: 'dude' was not found"  # unquoted scalar has a : in it -> {'msg == "Error"': 'dude'} [ was not found" ] is garbage orphan scalar

        # noinspection PyUnboundLocalVariable
        if not isinstance(exception, MarkedYAMLError):
            pass  # unexpected exception, don't use special analysis of exception

        elif isinstance(exception, AnsibleConstructorError):
            pass  # raised internally by ansible code, don't use special analysis of exception

        # Check for tabs.
        # There may be cases where there is a valid tab in a line that has other errors.
        # That's OK, users should "fix" their tab usage anyway -- at which point later error handling logic will hopefully find the real issue.
        elif (tab_idx := target_line.find('\t')) >= 0:
            source_context = _error_utils.SourceContext.from_origin(origin.replace(col_num=tab_idx + 1))
            message = "Tabs are usually invalid in YAML."

        # Check for unquoted templates.
        elif match := re.search(r'^\s*(?:-\s+)*(?:[\w\s]+:\s+)?(?P<value>\{\{.*}})', target_line):
            source_context = _error_utils.SourceContext.from_origin(origin.replace(col_num=match.start('value') + 1))
            message = 'This may be an issue with missing quotes around a template block.'
            # FIXME: Use the captured value to show the actual fix required.
            help_text = """
For example:

    raw: {{ some_var }}

Should be:

    raw: "{{ some_var }}"
"""

        # Check for common unquoted colon mistakes.
        elif (
            # ignore lines starting with only whitespace and a colon
            not target_line.lstrip().startswith(':')
            # find the value after list/dict preamble
            and (value_match := re.search(r'^\s*(?:-\s+)*(?:[\w\s\[\]{}]+:\s+)?(?P<value>.*)$', target_line))
            # ignore properly quoted values
            and (target_fragment := _replace_quoted_value(value_match.group('value')))
            # look for an unquoted colon in the value
            and (colon_match := re.search(r':($| )', target_fragment))
        ):
            source_context = _error_utils.SourceContext.from_origin(origin.replace(col_num=value_match.start('value') + colon_match.start() + 1))
            message = 'Colons in unquoted values must be followed by a non-space character.'
            # FIXME: Use the captured value to show the actual fix required.
            help_text = """
For example:

    raw: echo 'name: ansible'

Should be:

    raw: "echo 'name: ansible'"
"""

        # Check for common quoting mistakes.
        elif match := re.search(r'^\s*(?:-\s+)*(?:[\w\s]+:\s+)?(?P<value>[\"\'].*?\s*)$', target_line):
            suspected_value = match.group('value')
            first, last = suspected_value[0], suspected_value[-1]

            if first != last:  # "foo" in bar
                source_context = _error_utils.SourceContext.from_origin(origin.replace(col_num=match.start('value') + 1))
                message = 'Values starting with a quote must end with the same quote.'
                # FIXME: Use the captured value to show the actual fix required, and use that same logic to improve the origin further.
                help_text = """
For example:

    raw: "foo" in bar

Should be:

    raw: '"foo" in bar'
"""
            elif first == last and target_line.count(first) > 2:  # "foo" and "bar"
                source_context = _error_utils.SourceContext.from_origin(origin.replace(col_num=match.start('value') + 1))
                message = 'Values starting with a quote must end with the same quote, and not contain that quote.'
                # FIXME: Use the captured value to show the actual fix required, and use that same logic to improve the origin further.
                help_text = """
For example:

    raw: "foo" in "bar"

Should be:

    raw: '"foo" in "bar"'
"""

        if not message:
            if isinstance(exception, MarkedYAMLError):
                # marked YAML error, pull out the useful messages while omitting the noise
                message = ' '.join(filter(None, (exception.context, exception.problem, exception.note)))
                message = message.strip()
                message = f'{message[0].upper()}{message[1:]}'

                if not message.endswith('.'):
                    message += '.'
            else:
                # unexpected error, use the exception message (normally hidden by overriding include_cause_message)
                message = str(exception)

            message = re.sub(r'\s+', ' ', message).strip()

        error = cls(message, obj=source_context.origin)
        error._formatted_source_context_value = str(source_context)
        error._help_text = help_text

        raise error from exception


def _replace_quoted_value(value: str, replacement='.') -> str:
    return re.sub(r"""^\s*('[^']*'|"[^"]*")\s*$""", lambda match: replacement * len(match.group(0)), value)
