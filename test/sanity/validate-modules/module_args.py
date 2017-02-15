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

from modulefinder import ModuleFinder

import mock


MODULE_CLASSES = [
    'ansible.module_utils.basic.AnsibleModule',
    'ansible.module_utils.vca.VcaAnsibleModule',
    'ansible.module_utils.nxos.NetworkModule',
    'ansible.module_utils.eos.NetworkModule',
    'ansible.module_utils.ios.NetworkModule',
    'ansible.module_utils.iosxr.NetworkModule',
    'ansible.module_utils.junos.NetworkModule',
    'ansible.module_utils.openswitch.NetworkModule',
]


class AnsibleModuleCallError(RuntimeError):
    pass


def add_mocks(filename):
    gp = mock.patch('ansible.module_utils.basic.get_platform').start()
    gp.return_value = 'linux'

    module_mock = mock.MagicMock()
    mocks = []
    for module_class in MODULE_CLASSES:
        mocks.append(
            mock.patch('ansible.module_utils.basic.AnsibleModule',
                       new=module_mock)
        )
    for m in mocks:
        p = m.start()
        p.side_effect = AnsibleModuleCallError()

    finder = ModuleFinder()
    try:
        finder.run_script(filename)
    except:
        pass

    sys_mock = mock.MagicMock()
    sys_mock.__version__ = '0.0.0'
    sys_mocks = []
    for module, sources in finder.badmodules.items():
        if module in sys.modules:
            continue
        if [s for s in sources if s[:7] in ['ansible', '__main_']]:
            parts = module.split('.')
            for i in range(len(parts)):
                dotted = '.'.join(parts[:i+1])
                # Never mock out ansible or ansible.module_utils
                # we may get here if a specific module_utils file needed mocked
                if dotted in ('ansible', 'ansible.module_utils',):
                    continue
                sys.modules[dotted] = sys_mock
                sys_mocks.append(dotted)

    return module_mock, mocks, sys_mocks


def remove_mocks(mocks, sys_mocks):
    for m in mocks:
        m.stop()

    for m in sys_mocks:
        try:
            del sys.modules[m]
        except KeyError:
            pass


def get_argument_spec(filename):
    module_mock, mocks, sys_mocks = add_mocks(filename)

    try:
        mod = imp.load_source('module', filename)
        if not module_mock.call_args:
            mod.main()
    except AnsibleModuleCallError:
        pass
    except Exception:
        # We can probably remove this branch, it is here for use while testing
        pass

    remove_mocks(mocks, sys_mocks)

    try:
        args, kwargs = module_mock.call_args
        try:
            return kwargs['argument_spec']
        except KeyError:
            return args[0]
    except TypeError:
        return {}
