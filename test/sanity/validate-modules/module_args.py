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
    gp = mock.patch('ansible.module_utils.basic.get_platform').start()
    gp.return_value = 'linux'

    module_mock = mock.MagicMock()
    mocks = []
    for module_class in MODULE_CLASSES:
        mocks.append(
            mock.patch('%s.__init__' % module_class, new=module_mock)
        )
    for m in mocks:
        p = m.start()
        p.side_effect = AnsibleModuleCallError('AnsibleModuleCallError')
    mocks.append(
        mock.patch('ansible.module_utils.basic._load_params').start()
    )

    yield module_mock

    for m in mocks:
        m.stop()


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
            return kwargs['argument_spec']
        except KeyError:
            return args[0]
    except TypeError:
        return {}
