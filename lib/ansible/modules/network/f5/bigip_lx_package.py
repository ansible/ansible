#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_lx_package
short_description: Manages Javascript LX packages on a BIG-IP
description:
  - Manages Javascript LX packages on a BIG-IP. This module will allow
    you to deploy LX packages to the BIG-IP and manage their lifecycle.
version_added: 2.5
options:
  package:
    description:
      - The LX package that you want to upload or remove. When C(state) is C(present),
        and you intend to use this module in a C(role), it is recommended that you use
        the C({{ role_path }}) variable. An example is provided in the C(EXAMPLES) section.
      - When C(state) is C(absent), it is not necessary for the package to exist on the
        Ansible controller. If the full path to the package is provided, the fileame will
        specifically be cherry picked from it to properly remove the package.
    type: path
  state:
    description:
      - Whether the LX package should exist or not.
    type: str
    default: present
    choices:
      - present
      - absent
notes:
  - Requires the rpm tool be installed on the host. This can be accomplished through
    different ways on each platform. On Debian based systems with C(apt);
    C(apt-get install rpm). On Mac with C(brew); C(brew install rpm).
    This command is already present on RedHat based systems.
  - Requires BIG-IP >= 12.1.0 because the required functionality is missing
    on versions earlier than that.
  - The module name C(bigip_iapplx_package) has been deprecated in favor of C(bigip_lx_package).
requirements:
  - Requires BIG-IP >= 12.1.0
  - The 'rpm' tool installed on the Ansible controller
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Install AS3
  bigip_lx_package:
    package: f5-appsvcs-3.5.0-3.noarch.rpm
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Add an LX package stored in a role
  bigip_lx_package:
    package: "{{ roles_path }}/files/MyApp-0.1.0-0001.noarch.rpm'"
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove an LX package
  bigip_lx_package:
    package: MyApp-0.1.0-0001.noarch.rpm
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import os
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import urlparse
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.icontrol import upload_file
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.icontrol import upload_file


class Parameters(AnsibleF5Parameters):
    api_attributes = []
    returnables = []

    @property
    def package(self):
        if self._values['package'] is None:
            return None
        return self._values['package']

    @property
    def package_file(self):
        if self._values['package'] is None:
            return None
        return os.path.basename(self._values['package'])

    @property
    def package_name(self):
        """Return a valid name for the package

        BIG-IP determines the package name by the content of the RPM info.
        It does not use the filename. Therefore, we do the same. This method
        is only used though when the file actually exists on your Ansible
        controller.

        If the package does not exist, then we instead use the filename
        portion of the 'package' argument that is provided.

        Non-existence typically occurs when using 'state' = 'absent'

        :return:
        """
        cmd = ['rpm', '-qp', '--queryformat', '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}', self.package]
        rc, out, err = self._module.run_command(cmd)
        if not out:
            return str(self.package_file)
        return out

    @property
    def package_root(self):
        if self._values['package'] is None:
            return None
        base = os.path.basename(self._values['package'])
        result = os.path.splitext(base)
        return result[0]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    pass


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(module=self.module, params=self.module.params)
        self.changes = UsableChanges()

    def exec_module(self):
        result = dict()
        changed = False
        state = self.want.state

        version = tmos_version(self.client)
        if LooseVersion(version) <= LooseVersion('12.0.0'):
            raise F5ModuleError(
                "This version of BIG-IP is not supported."
            )

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def present(self):
        if self.exists():
            return False
        else:
            return self.create()

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the LX package.")
        return True

    def create(self):
        if self.module.check_mode:
            return True
        if not os.path.exists(self.want.package):
            if self.want.package.startswith('/'):
                raise F5ModuleError(
                    "The specified LX package was not found at {0}.".format(self.want.package)
                )
            else:
                raise F5ModuleError(
                    "The specified LX package was not found in {0}.".format(os.getcwd())
                )
        self.upload_to_device()
        self.create_on_device()
        self.enable_iapplx_on_device()
        self.remove_package_file_from_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to install LX package.")

    def exists(self):
        exists = False
        packages = self.get_installed_packages_on_device()
        if os.path.exists(self.want.package):
            exists = True
        for package in packages:
            if exists:
                if self.want.package_name == package['packageName']:
                    return True
            else:
                if self.want.package_root == package['packageName']:
                    return True
        return False

    def get_installed_packages_on_device(self):
        uri = "https://{0}:{1}/mgmt/shared/iapp/package-management-tasks".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        params = dict(operation='QUERY')
        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        path = urlparse(response["selfLink"]).path
        task = self._wait_for_task(path)

        if task['status'] == 'FINISHED':
            return task['queryResponse']
        raise F5ModuleError(
            "Failed to find the installed packages on the device."
        )

    def _wait_for_task(self, path):
        task = None
        for x in range(0, 60):
            task = self.check_task_on_device(path)
            if task['status'] in ['FINISHED', 'FAILED']:
                return task
            time.sleep(1)
        return task

    def check_task_on_device(self, path):
        uri = "https://{0}:{1}{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            path
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response

    def upload_to_device(self):
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/uploads'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        try:
            upload_file(self.client, url, self.want.package)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def remove_package_file_from_device(self):
        params = dict(
            command="run",
            utilCmdArgs="/var/config/rest/downloads/{0}".format(self.want.package_file)
        )
        uri = "https://{0}:{1}/mgmt/tm/util/unix-rm".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def create_on_device(self):
        remote_path = "/var/config/rest/downloads/{0}".format(self.want.package_file)
        params = dict(
            operation='INSTALL', packageFilePath=remote_path
        )
        uri = "https://{0}:{1}/mgmt/shared/iapp/package-management-tasks".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        path = urlparse(response["selfLink"]).path
        task = self._wait_for_task(path)

        if task['status'] == 'FINISHED':
            return True
        else:
            raise F5ModuleError(task['errorMessage'])

    def remove_from_device(self):
        params = dict(
            operation='UNINSTALL',
            packageName=self.want.package_root
        )
        uri = "https://{0}:{1}/mgmt/shared/iapp/package-management-tasks".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        path = urlparse(response["selfLink"]).path
        task = self._wait_for_task(path)

        if task['status'] == 'FINISHED':
            return True
        return False

    def enable_iapplx_on_device(self):
        params = dict(
            command="run",
            utilCmdArgs='-c "touch /var/config/rest/iapps/enable"'
        )
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            package=dict(type='path')
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['state', 'present', ['package']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
