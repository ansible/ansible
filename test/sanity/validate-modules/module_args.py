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
import traceback

from contextlib import contextmanager

import mock


MODULE_CLASSES = [
    'ansible.module_utils.basic.AnsibleModule',
]


# This can be removed once we replace ``raise Exception`` with ``module.fail_json``
HAS_HACKS = [
    'ansible.module_utils.k8s.common.HAS_K8S_MODULE_HELPER',
    'ansible.module_utils.k8s.common.HAS_STRING_UTILS',
]

# Some of these can be removed once we replace ``raise Exception`` with ``module.fail_json``
# Others are related to using info from imports before ``AnsibleModule`` is executed
IMPORT_MODULE_HACKS = [
    # f5
    'netaddr.IPAddress',
    'netaddr.AddrFormatError',
    'objectpath.Tree',
    'f5.utils.iapp_parser.NonextantTemplateNameException',
    'f5.sdk_exception.LazyAttributesRequired',
    'f5.utils.responses.handlers.Stats'
    'f5.bigip.ManagementRoot',
    'f5.bigip.contexts.TransactionContextManager',
    'f5.bigiq.ManagementRoot',
    'f5.iworkflow.ManagementRoot',
    'icontrol.exceptions.iControlUnexpectedHTTPError',
    # radware
    'vdirect_client.rest_client',
    # webfaction
    'xmlrpclib',
    # azure
    'msrestazure.azure_exceptions.CloudError',
    'azure.storage.cloudstorageaccount.CloudStorageAccount',
    'azure.common.AzureMissingResourceHttpError',
    'azure.mgmt.storage.models.ProvisioningState',
    'azure.mgmt.storage.models.SkuName',
    'azure.mgmt.dns.models.ARecord',
    # google
    'libcloud',
    'libcloud.common.google',
    'libcloud.dns.types.Provider',
    # dimensiondata
    'libcloud.common.dimensiondata',
]


class AnsibleModuleCallError(RuntimeError):
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

    for has in HAS_HACKS:
        mock.patch(has, True).start()

    sys_mock = mock.MagicMock()
    sys_mock.__version__ = '0.0.0'
    sys_mocks = []
    for module in IMPORT_MODULE_HACKS:
        if module in sys.modules:
            continue
        parts = module.split('.')
        for i in range(len(parts)):
            dotted = '.'.join(parts[:i + 1])
            # Never mock out ansible or ansible.module_utils
            # we may get here if a specific module_utils file needed mocked
            if dotted in ('ansible', 'ansible.module_utils',):
                continue
            sys.modules[dotted] = sys_mock
            sys_mocks.append(dotted)

    yield module_mock

    for m in mocks:
        m.stop()

    for m in sys_mocks:
        try:
            del sys.modules[m]
        except KeyError:
            pass


def get_argument_spec(filename):
    with add_mocks(filename) as module_mock:
        try:
            mod = imp.load_source('module', filename)
            if not module_mock.call_args:
                mod.main()
        except AnsibleModuleCallError:
            pass
        except Exception:
            sys.stderr.write('%s\n' % traceback.format_exc())

    try:
        args, kwargs = module_mock.call_args
        try:
            return kwargs['argument_spec']
        except KeyError:
            return args[0]
    except TypeError:
        return {}
