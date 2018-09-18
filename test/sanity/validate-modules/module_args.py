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

import imp
import sys

from contextlib import contextmanager

import mock

from ansible.module_utils.six import reraise


MODULE_CLASSES = [
    'ansible.module_utils.basic.AnsibleModule',
]


class AnsibleModuleCallError(RuntimeError):
    pass


class AnsibleModuleImportError(ImportError):
    pass


@contextmanager
def add_mocks(filename):
    # Used to clean up imports later
    pre_sys_modules = list(sys.modules.keys())

    module_mock = mock.MagicMock()
    for module_class in MODULE_CLASSES:
        p = mock.patch('%s.__init__' % module_class, new=module_mock).start()
        p.side_effect = AnsibleModuleCallError('AnsibleModuleCallError')
    mock.patch('ansible.module_utils.basic._load_params').start()

    yield module_mock

    mock.patch.stopall()

    # Clean up imports to prevent issues with mutable data being used in modules
    for k in list(sys.modules.keys()):
        # It's faster if we limit to items in ansible.module_utils
        # But if this causes problems later, we should remove it
        if k not in pre_sys_modules and k.startswith('ansible.module_utils.'):
            del sys.modules[k]


def get_argument_spec(filename):
    with add_mocks(filename) as module_mock:
        try:
            mod = imp.load_source('module', filename)
            if not module_mock.call_args:
                mod.main()
        except AnsibleModuleCallError:
            pass
        except Exception as e:
            reraise(AnsibleModuleImportError, AnsibleModuleImportError('%s' % e), sys.exc_info()[2])

    try:
        args, kwargs = module_mock.call_args
        try:
            return kwargs['argument_spec'], args, kwargs
        except KeyError:
            return args[0], args, kwargs
    except TypeError:
        return {}, (), {}
