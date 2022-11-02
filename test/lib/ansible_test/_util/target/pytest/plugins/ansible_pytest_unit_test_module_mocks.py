# -*- coding: utf-8 -*-

# Copyright (c) 2017–2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Pytest fixtures for mocking Ansible modules."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import partial
from io import BufferedReader, BytesIO, TextIOWrapper
from textwrap import dedent
import json
import runpy
import subprocess
import sys

import pytest
import yaml

import ansible.module_utils.basic
from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils.six import PY2, raise_from, string_types
from ansible.module_utils.six.moves.collections_abc import MutableMapping


@pytest.fixture
def ansible_module_name(request):
    """Return a module name shared across fixtures.

    Its value is expected to be either set via ``@pytest.mark.parametrize``
    or this fixture is to be redefined on the test module level.
    """
    if isinstance(getattr(request, 'param', None), str):
        return request.param

    try:
        return request.getfixturevalue('ansible_global_module_name')
    except pytest.FixtureLookupError as fixture_lookup_err:
        raise raise_from(  # `raise` is a hack for pylint
            NotImplementedError(
                'Please, define "ansible_global_module_name" fixture '
                'returning a string on the test module level or pass '
                'the module name using the indirect params feature '
                'of `@pytest.mark.parametrize`:\n\n{err!s}'.
                format(err=fixture_lookup_err.formatrepr()),
            ),
            fixture_lookup_err,
        )


@pytest.fixture
def run_ansible_module(
        ansible_module_name,  # pylint: disable=redefined-outer-name
        make_ansible_module_caller,  # pylint: disable=redefined-outer-name
):
    """Construct a callable for invoking a module in-process."""
    return make_ansible_module_caller(ansible_module_name)


@pytest.fixture
def run_ansible_module_in_subprocess(
        ansible_module_name,  # pylint: disable=redefined-outer-name
        make_ansible_module_subprocess_caller,  # pylint: disable=redefined-outer-name
):
    """Construct a callable for invoking a module in a subprocess."""
    return make_ansible_module_subprocess_caller(ansible_module_name)


@pytest.fixture
def run_ansible_task_yaml(
        make_ansible_module_caller,  # pylint: disable=redefined-outer-name
):
    """Construct a callable for invoking modules via YAML interface."""
    def run_from_yaml(yaml_input, ansible_module_class=None):
        dict_input = yaml.safe_load(dedent(yaml_input))

        if not dict_input:
            raise ValueError('The input must not be empty')

        if len(dict_input) != 1:
            raise ValueError('The input must look like one task')

        if isinstance(dict_input, list):
            dict_input = dict_input[0]

        module_name, module_args = tuple(*dict_input.items())
        return make_ansible_module_caller(
            module_name,
            ansible_module_class=ansible_module_class,
        )(**module_args)

    return run_from_yaml


class _SyntheticSystemExit(SystemExit):
    """Synthetic version of :py:class:`SystemExit`.

    To be used as a module execution termination.
    """

    def __init__(self, return_value, status):
        """Initialize a synthetic version of :py:class:`SystemExit`.

        :param return_value: a chunk of data attached to the exception
        object.
        :type return_value: dict

        :param status: is an optional argument that can be an integer return
        code or a string. In case, it's a string, the return code is set
        to ``1``.
        :type status: int or str

        Refs:
        * https://github.com/python/cpython/blob/bceb1979/Objects/exceptions.c#L615-L638
        * https://docs.python.org/3/library/exceptions.html#SystemExit
        * https://docs.python.org/3/library/sys.html#sys.exit
        """
        self._return_value = return_value
        super(_SyntheticSystemExit, self).__init__(status)

    @property
    def return_value(self):
        """A chunk of context the exception carries."""
        return self._return_value


@pytest.fixture
def _patched_ansible_module_base_class(monkeypatch):
    """Construct a no-sideeffect ``AnsibleModule`` substitution class.

    This fixture is a private API. Do not redefine it!
    """
    class PatchedAnsibleModule(ansible.module_utils.basic.AnsibleModule):
        """A return-value tracking version of the ``AnsibleModule``."""

        def exit_json(self, **kwargs):
            return_code = None

            fake_stdout_buffer = BytesIO()
            if not PY2:
                fake_stdout_buffer = TextIOWrapper(fake_stdout_buffer)

            with monkeypatch.context() as mp_ctx:
                mp_ctx.setattr(sys, 'stdout', fake_stdout_buffer)
                try:
                    super(PatchedAnsibleModule, self).exit_json(**kwargs)
                except SystemExit as sys_exit_exc:
                    return_code = sys_exit_exc.code
                else:
                    raise RuntimeError(
                        'Calling `AnsibleModule.exit_json()` must have '
                        'triggered a `SystemExit` to be raised but '
                        'mysteriously it did not. Check your '
                        'mocking/patching helpers for the '
                        'implementation mistakes.'
                    )

            fake_stdout_buffer.flush()
            if not PY2:
                fake_stdout_buffer.buffer.flush()

            fake_stdout_buffer.seek(0)

            return_value = json.loads(fake_stdout_buffer.read())

            raise _SyntheticSystemExit(return_value, return_code)

        def fail_json(self, msg, **kwargs):
            return_code = None

            fake_stdout_buffer = BytesIO()
            if not PY2:
                fake_stdout_buffer = TextIOWrapper(fake_stdout_buffer)

            with monkeypatch.context() as mp_ctx:
                mp_ctx.setattr(sys, 'stdout', fake_stdout_buffer)
                try:
                    super(PatchedAnsibleModule, self).fail_json(msg, **kwargs)
                except SystemExit as sys_exit_exc:
                    return_code = sys_exit_exc.code
                else:
                    raise RuntimeError(
                        'Calling `AnsibleModule.fail_json()` must have '
                        'triggered a `SystemExit` to be raised but '
                        'mysteriously it did not. Check your '
                        'mocking/patching helpers for the '
                        'implementation mistakes.'
                    )

            fake_stdout_buffer.flush()
            if not PY2:
                fake_stdout_buffer.buffer.flush()

            fake_stdout_buffer.seek(0)

            return_value = json.loads(fake_stdout_buffer.read())

            raise _SyntheticSystemExit(return_value, return_code)

    return PatchedAnsibleModule


@pytest.fixture
def patched_ansible_module_class(_patched_ansible_module_base_class):
    """Produce a patched AnsibleModule for to be used in tests."""
    return _patched_ansible_module_base_class


@pytest.fixture
def make_ansible_module_caller(
        monkeypatch,
        patched_ansible_module_class,  # pylint: disable=redefined-outer-name
):
    """Create an import-based module callable maker."""
    def make_module_wrapper(name_or_fqcn, ansible_module_class=None):
        # These cannot be used because `ansible-test` only symlinks
        # `ansible.modules` and `ansible.module_utils` into the test env
        # ansible.plugins.loader.module_loader.find_plugin_with_context()
        # ansible.plugins.loader.module_loader.find_plugin()
        # find_plugin(self, name, mod_type='', ignore_deprecated=False, check_aliases=False, collection_list=None)
        run_module = partial(
            runpy.run_module,
            mod_name=name_or_fqcn, run_name='__main__',
            alter_sys=True,
        )

        def run_module_with(**module_kwargs):
            with monkeypatch.context() as mp_ctx:
                mp_ctx.setattr(ansible.module_utils.basic, '_ANSIBLE_ARGS', None)
                mp_ctx.setattr(sys, 'argv', ['ansible_unittest'])

                module_args_defaults = {
                    '_ansible_keep_remote_files': False,
                    '_ansible_remote_tmp': '/tmp',
                }

                mod_args = module_kwargs.get('ANSIBLE_MODULE_ARGS', module_kwargs)
                mod_args = dict(module_args_defaults, **mod_args)
                args = json.dumps({'ANSIBLE_MODULE_ARGS': mod_args})

                args = to_bytes(args, errors='surrogate_or_strict')

                fake_stdin_buffer = BytesIO(args)
                if not PY2:
                    fake_stdin_buffer = BufferedReader(fake_stdin_buffer)

                fake_stdin = fake_stdin_buffer
                if not PY2:
                    fake_stdin = TextIOWrapper(
                        fake_stdin_buffer,
                        line_buffering=True,
                        encoding='UTF-8',
                    )

                mp_ctx.setattr(
                    ansible.module_utils.basic.sys, 'stdin', fake_stdin,
                )
                mp_ctx.setattr(
                    ansible.module_utils.basic, 'AnsibleModule',
                    ansible_module_class or patched_ansible_module_class,
                )
                try:
                    run_module()
                except _SyntheticSystemExit as sys_exit_exc:
                    return sys_exit_exc.return_value
                # pylint: disable-next=broad-except
                except BaseException as base_exc:
                    extra_advice = ''
                    if isinstance(base_exc, ImportError):
                        extra_advice = (
                            '\n\n'
                            'This may be caused by an incorrect '
                            'importable path specification in the test.'
                        )

                    return pytest.fail(  # `return` is a hack for pylint
                        'Invoking `{fqcn!s}` caused an unhandled '
                        'error {exc!r}.{extra_advice!s}'.
                        format(
                            fqcn=name_or_fqcn, exc=base_exc,
                            extra_advice=extra_advice,
                        ),
                    )
                else:
                    return pytest.fail(  # `return` is a hack for pylint
                        'The module has not communicated '
                        'a successful exit or a failure',
                    )
        return run_module_with
    return make_module_wrapper


@pytest.fixture
def make_ansible_module_subprocess_caller():
    """Create a subprocess-based module callable maker."""
    def make_module_wrapper(name_or_fqcn):
        def run_module_with(**module_kwargs):
            module_args_defaults = {
                '_ansible_keep_remote_files': False,
                '_ansible_remote_tmp': '/tmp',
            }

            mod_args = module_kwargs.get('ANSIBLE_MODULE_ARGS', module_kwargs)
            mod_args = dict(module_args_defaults, **mod_args)

            args = json.dumps({'ANSIBLE_MODULE_ARGS': mod_args})
            args = to_bytes(args, errors='surrogate_or_strict')

            process = subprocess.Popen(  # pylint: disable=consider-using-with  # no CM @ py2
                (sys.executable, '-m', name_or_fqcn),
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )

            try:
                stdoutdata, _stderrdata = process.communicate(input=args)
            finally:
                process.stdout.close()
                process.stderr.close()
                process.stdin.close()
                wait_kwargs = {} if PY2 else {'timeout': 5}
                process.wait(**wait_kwargs)

            module_return_json_string = stdoutdata.decode()
            return json.loads(module_return_json_string)
        return run_module_with
    return make_module_wrapper


@pytest.fixture
def ansible_module_args(mocker, monkeypatch, request):
    """Patch and return stdin buffer with module args."""
    monkeypatch.setattr(ansible.module_utils.basic, '_ANSIBLE_ARGS', None)
    monkeypatch.setattr(sys, 'argv', ['ansible_unittest'])

    inp_args = request.param

    module_args_defaults = {
        '_ansible_keep_remote_files': False,
        '_ansible_remote_tmp': '/tmp',
    }

    if isinstance(inp_args, string_types):
        args = inp_args
    elif isinstance(inp_args, MutableMapping):
        mod_args = inp_args.get('ANSIBLE_MODULE_ARGS', inp_args)
        mod_args = dict(module_args_defaults, **mod_args)
        args = json.dumps({'ANSIBLE_MODULE_ARGS': mod_args})
    else:
        raise TypeError('Malformed data to the `stdin` pytest fixture')

    args = to_bytes(args, errors='surrogate_or_strict')

    fake_stdin_buffer = BytesIO(args)

    fake_stdin = mocker.MagicMock() if not PY2 else fake_stdin_buffer
    if not PY2:
        fake_stdin.buffer = fake_stdin_buffer

    monkeypatch.setattr(ansible.module_utils.basic.sys, 'stdin', fake_stdin)

    return fake_stdin_buffer


@pytest.fixture
@pytest.mark.usefixtures('ansible_module_args')
def ansible_module(
        ansible_module_args,  # pylint: disable=redefined-outer-name,unused-argument
        request,
):
    """Return a patched Ansible module instance."""
    argspec = {}
    if isinstance(getattr(request, 'param', None), dict):
        argspec = request.param

    ans_mod = ansible.module_utils.basic.AnsibleModule(
        argument_spec=argspec,
    )
    ans_mod._name = 'ansible_unittest'  # pylint: disable=protected-access

    return ans_mod
