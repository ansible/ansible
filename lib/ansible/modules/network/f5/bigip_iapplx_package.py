#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_iapplx_package
short_description: Manages Javascript iApp packages on a BIG-IP
description:
  - Manages Javascript iApp packages on a BIG-IP. This module will allow
    you to deploy iAppLX packages to the BIG-IP and manage their lifecycle.
version_added: "2.5"
options:
  package:
    description:
      - The iAppLX package that you want to upload or remove. When C(state) is C(present),
        and you intend to use this module in a C(role), it is recommended that you use
        the C({{ role_path }}) variable. An example is provided in the C(EXAMPLES) section.
      - When C(state) is C(absent), it is not necessary for the package to exist on the
        Ansible controller. If the full path to the package is provided, the fileame will
        specifically be cherry picked from it to properly remove the package.
  state:
    description:
      - Whether the iAppLX package should exist or not.
    default: present
    choices:
      - present
      - absent
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires the rpm tool be installed on the host. This can be accomplished through
    different ways on each platform. On Debian based systems with C(apt);
    C(apt-get install rpm). On Mac with C(brew); C(brew install rpm).
    This command is already present on RedHat based systems.
  - Requires BIG-IP < 12.1.0 because the required functionality is missing
    on versions  earlier than that.
requirements:
  - f5-sdk >= 2.2.3
  - Requires BIG-IP >= 12.1.0
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Add an iAppLX package
  bigip_iapplx_package:
    package: MyApp-0.1.0-0001.noarch.rpm
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Add an iAppLX package stored in a role
  bigip_iapplx_package:
    package: "{{ roles_path }}/files/MyApp-0.1.0-0001.noarch.rpm'"
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Remove an iAppLX package
  bigip_iapplx_package:
    package: MyApp-0.1.0-0001.noarch.rpm
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import os
import subprocess
import time

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from distutils.version import LooseVersion

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


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
        p = subprocess.Popen(
            ['rpm', '-qp', '--queryformat', '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}', self.package],
            stdout=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        if not stdout:
            return self.package_file
        return stdout

    @property
    def package_root(self):
        if self._values['package'] is None:
            return None
        base = os.path.basename(self._values['package'])
        result = os.path.splitext(base)
        return result[0]

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

    def exec_module(self):
        result = dict()
        changed = False
        state = self.want.state

        version = self.client.api.tmos_version
        if LooseVersion(version) <= LooseVersion('12.0.0'):
            raise F5ModuleError(
                "This version of BIG-IP is not supported."
            )

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

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
        collection = self.client.api.shared.iapp.package_management_tasks_s
        task = collection.package_management_task.create(
            operation='QUERY'
        )
        status = self._wait_for_task(task)
        if status == 'FINISHED':
            return task.queryResponse
        raise F5ModuleError(
            "Failed to find the installed packages on the device"
        )

    def create(self):
        if self.client.check_mode:
            return True
        if not os.path.exists(self.want.package):
            raise F5ModuleError(
                "The specified iAppLX package was not found."
            )
        self.upload_to_device()
        self.create_on_device()
        self.enable_iapplx_on_device()
        self.remove_package_file_from_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the iApp template")

    def upload_to_device(self):
        upload = self.client.api.shared.file_transfer.uploads
        upload.upload_file(
            self.want.package
        )

    def remove_package_file_from_device(self):
        self.client.api.tm.util.unix_rm.exec_cmd(
            'run',
            utilCmdArgs="/var/config/rest/downloads/{0}".format(self.want.package_file)
        )

    def create_on_device(self):
        remote_path = "/var/config/rest/downloads/{0}".format(self.want.package_file)
        collection = self.client.api.shared.iapp.package_management_tasks_s
        task = collection.package_management_task.create(
            operation='INSTALL',
            packageFilePath=remote_path
        )
        status = self._wait_for_task(task)
        if status == 'FINISHED':
            return True
        else:
            raise F5ModuleError(task.errorMessage)

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the iAppLX package")
        return True

    def remove_from_device(self):
        collection = self.client.api.shared.iapp.package_management_tasks_s
        task = collection.package_management_task.create(
            operation='UNINSTALL',
            packageName=self.want.package_root
        )
        status = self._wait_for_task(task)
        if status == 'FINISHED':
            return True
        return False

    def _wait_for_task(self, task):
        for x in range(0, 60):
            task.refresh()
            if task.status in ['FINISHED', 'FAILED']:
                return task.status
            time.sleep(1)
        return task.status

    def enable_iapplx_on_device(self):
        self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "touch /var/config/rest/iapps/enable"'
        )


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            package=dict()
        )
        self.f5_product_name = 'bigip'
        self.required_if = [
            ['state', 'present', ['package']]
        ]


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name,
        required_if=spec.required_if
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
