# -*- coding: utf-8 -*-

# Copyright (C) 2016 Matt Martz <matt@sivel.net>
# Copyright (C) 2016 Rackspace US, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import reraise

import imp
import mock
import sys
from contextlib import contextmanager


class AnsibleModuleCallError(RuntimeError):
    pass


class AnsibleModuleImportError(ImportError):
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


def get_argument_spec(filename):
    with setup_env(filename) as fake:
        try:
            # We use ``module`` here instead of ``__main__``
            # which helps with some import issues in this tool
            # where modules may import things that conflict
            mod = imp.load_source('module', filename)
            if not fake.called:
                mod.main()
        except AnsibleModuleCallError:
            pass
        except Exception as e:
            reraise(AnsibleModuleImportError, AnsibleModuleImportError('%s' % e), sys.exc_info()[2])

    try:
        try:
            return fake.kwargs['argument_spec'], fake.args, fake.kwargs
        except KeyError:
            return fake.args[0], fake.args, fake.kwargs
    except TypeError:
        return {}, (), {}
