# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Matt Martz <matt@sivel.net>
# Copyright (C) 2016 Rackspace US, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import runpy
import json
import os
import subprocess
import sys

from contextlib import contextmanager

from ansible.executor.powershell.module_manifest import PSModuleDepFinder
from ansible.module_utils.six import reraise
from ansible.module_utils._text import to_bytes, to_text

from .utils import CaptureStd, find_executable, get_module_name_from_filename


class AnsibleModuleCallError(RuntimeError):
    pass


class AnsibleModuleImportError(ImportError):
    pass


class AnsibleModuleNotInitialized(Exception):
    pass


class _FakeAnsibleModuleInit:
    def __init__(self):
        self.args = tuple()
        self.kwargs = {}
        self.called = False

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.called = True
        raise AnsibleModuleCallError('AnsibleModuleCallError')


def _fake_load_params():
    pass


@contextmanager
def setup_env(filename):
    # Used to clean up imports later
    pre_sys_modules = list(sys.modules.keys())

    fake = _FakeAnsibleModuleInit()
    module = __import__('ansible.module_utils.basic').module_utils.basic
    _original_init = module.AnsibleModule.__init__
    _original_load_params = module._load_params
    setattr(module.AnsibleModule, '__init__', fake)
    setattr(module, '_load_params', _fake_load_params)

    try:
        yield fake
    finally:
        setattr(module.AnsibleModule, '__init__', _original_init)
        setattr(module, '_load_params', _original_load_params)

        # Clean up imports to prevent issues with mutable data being used in modules
        for k in list(sys.modules.keys()):
            # It's faster if we limit to items in ansible.module_utils
            # But if this causes problems later, we should remove it
            if k not in pre_sys_modules and k.startswith('ansible.module_utils.'):
                del sys.modules[k]


def get_ps_argument_spec(filename):
    # This uses a very small skeleton of Ansible.Basic.AnsibleModule to return the argspec defined by the module. This
    # is pretty rudimentary and will probably require something better going forward.
    pwsh = find_executable('pwsh')
    if not pwsh:
        raise FileNotFoundError('Required program for PowerShell arg spec inspection "pwsh" not found.')

    module_path = os.path.join(os.getcwd(), filename)
    b_module_path = to_bytes(module_path, errors='surrogate_or_strict')
    with open(b_module_path, mode='rb') as module_fd:
        b_module_data = module_fd.read()

    ps_dep_finder = PSModuleDepFinder()
    ps_dep_finder.scan_module(b_module_data)

    util_manifest = json.dumps({
        'module_path': to_text(module_path, errors='surrogiate_or_strict'),
        'ps_utils': dict([(name, info['path']) for name, info in ps_dep_finder.ps_modules.items()])
    })

    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ps_argspec.ps1')
    proc = subprocess.Popen([script_path, util_manifest], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=False)
    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        raise AnsibleModuleImportError(stderr.decode('utf-8'))

    kwargs = json.loads(stdout)

    # the validate-modules code expects the options spec to be under the argument_spec key not options as set in PS
    kwargs['argument_spec'] = kwargs.pop('options', {})

    return kwargs['argument_spec'], (), kwargs


def get_py_argument_spec(filename, collection):
    name = get_module_name_from_filename(filename, collection)

    with setup_env(filename) as fake:
        try:
            with CaptureStd():
                runpy.run_module(name, run_name='__main__', alter_sys=True)
        except AnsibleModuleCallError:
            pass
        except BaseException as e:
            # we want to catch all exceptions here, including sys.exit
            reraise(AnsibleModuleImportError, AnsibleModuleImportError('%s' % e), sys.exc_info()[2])

        if not fake.called:
            raise AnsibleModuleNotInitialized()

    try:
        try:
            # for ping kwargs == {'argument_spec':{'data':{'type':'str','default':'pong'}}, 'supports_check_mode':True}
            return fake.kwargs['argument_spec'], fake.args, fake.kwargs
        except KeyError:
            return fake.args[0], fake.args, fake.kwargs
    except (TypeError, IndexError):
        return {}, (), {}


def get_argument_spec(filename, collection):
    if filename.endswith('.py'):
        return get_py_argument_spec(filename, collection)
    else:
        return get_ps_argument_spec(filename)
