"""Ansible-specific pylint plugin for checking deprecation comments."""

# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import shlex
import tokenize

import pylint.checkers
import pylint.lint

import ansible.release

from ansible.module_utils.compat.version import LooseVersion


class AnsibleDeprecatedCommentChecker(pylint.checkers.BaseTokenChecker):
    """Checks for ``# deprecated:`` comments to ensure that the ``version`` has not passed or met the time for removal."""

    name = 'deprecated-comment'
    msgs = {
        'E9601': (
            "Deprecated core version (%r) found: %s",
            "ansible-deprecated-version-comment",
            None,
        ),
        'E9602': (
            "Deprecated comment contains invalid keys %r",
            "ansible-deprecated-version-comment-invalid-key",
            None,
        ),
        'E9603': (
            "Deprecated comment missing version",
            "ansible-deprecated-version-comment-missing-version",
            None,
        ),
        'E9604': (
            "Deprecated python version (%r) found: %s",
            "ansible-deprecated-python-version-comment",
            None,
        ),
        'E9605': (
            "Deprecated comment contains invalid version %r: %s",
            "ansible-deprecated-version-comment-invalid-version",
            None,
        ),
    }

    ANSIBLE_VERSION = LooseVersion('.'.join(ansible.release.__version__.split('.')[:3]))
    """The current ansible-core X.Y.Z version."""

    def process_tokens(self, tokens: list[tokenize.TokenInfo]) -> None:
        for token in tokens:
            if token.type == tokenize.COMMENT:
                self._process_comment(token)

    def _deprecated_string_to_dict(self, token: tokenize.TokenInfo, string: str) -> dict[str, str]:
        valid_keys = {'description', 'core_version', 'python_version'}
        data = dict.fromkeys(valid_keys)
        for opt in shlex.split(string):
            if '=' not in opt:
                data[opt] = None
                continue
            key, _sep, value = opt.partition('=')
            data[key] = value
        if not any((data['core_version'], data['python_version'])):
            self.add_message(
                'ansible-deprecated-version-comment-missing-version',
                line=token.start[0],
                col_offset=token.start[1],
            )
        bad = set(data).difference(valid_keys)
        if bad:
            self.add_message(
                'ansible-deprecated-version-comment-invalid-key',
                line=token.start[0],
                col_offset=token.start[1],
                args=(','.join(bad),),
            )
        return data

    def _process_python_version(self, token: tokenize.TokenInfo, data: dict[str, str]) -> None:
        check_version = '.'.join(map(str, self.linter.config.py_version))  # minimum supported Python version provided by ansible-test

        try:
            if LooseVersion(check_version) > LooseVersion(data['python_version']):
                self.add_message(
                    'ansible-deprecated-python-version-comment',
                    line=token.start[0],
                    col_offset=token.start[1],
                    args=(
                        data['python_version'],
                        data['description'] or 'description not provided',
                    ),
                )
        except (ValueError, TypeError) as exc:
            self.add_message(
                'ansible-deprecated-version-comment-invalid-version',
                line=token.start[0],
                col_offset=token.start[1],
                args=(data['python_version'], exc),
            )

    def _process_core_version(self, token: tokenize.TokenInfo, data: dict[str, str]) -> None:
        try:
            if self.ANSIBLE_VERSION >= LooseVersion(data['core_version']):
                self.add_message(
                    'ansible-deprecated-version-comment',
                    line=token.start[0],
                    col_offset=token.start[1],
                    args=(
                        data['core_version'],
                        data['description'] or 'description not provided',
                    ),
                )
        except (ValueError, TypeError) as exc:
            self.add_message(
                'ansible-deprecated-version-comment-invalid-version',
                line=token.start[0],
                col_offset=token.start[1],
                args=(data['core_version'], exc),
            )

    def _process_comment(self, token: tokenize.TokenInfo) -> None:
        if token.string.startswith('# deprecated:'):
            data = self._deprecated_string_to_dict(token, token.string[13:].strip())
            if data['core_version']:
                self._process_core_version(token, data)
            if data['python_version']:
                self._process_python_version(token, data)


def register(linter: pylint.lint.PyLinter) -> None:
    """Required method to auto-register this checker."""
    linter.register_checker(AnsibleDeprecatedCommentChecker(linter))
