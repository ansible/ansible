#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_software_image
short_description: Manage software images on a BIG-IP
description:
  - Manages software images on a BIG-IP. These images may include both base images
    and hotfix images.
version_added: 2.7
options:
  force:
    description:
      - When C(yes), will upload the file every time and replace the file on the
        device.
      - When C(no), the file will only be uploaded if it does not already
        exist.
      - Generally should be C(yes) only in cases where you have reason
        to believe that the image was corrupted during upload.
    type: bool
    default: no
  state:
    description:
      - When C(present), ensures that the image is uploaded.
      - When C(absent), ensures that the image is removed.
    type: str
    choices:
      - absent
      - present
    default: present
  image:
    description:
      - The image to put on the remote device.
      - This may be an absolute or relative location on the Ansible controller.
      - Image names, whether they are base ISOs or hotfix ISOs, B(must) be unique.
    type: str
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Upload relative image to the BIG-IP
  bigip_software_image:
    image: BIGIP-13.0.0.0.0.1645.iso
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Upload absolute image to the BIG-IP
  bigip_software_image:
    image: /path/to/images/BIGIP-13.0.0.0.0.1645.iso
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Upload image in a role to the BIG-IP
  bigip_software_image:
    image: "{{ role_path }}/files/BIGIP-13.0.0.0.0.1645.iso"
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
image_type:
  description: Whether the image is a release or hotfix image
  returned: changed
  type: str
  sample: release
version:
  description: Version of the software contained in the image.
  returned: changed
  type: str
  sample: 13.1.0.8
build:
  description: Build version of the software contained in the image.
  returned: changed
  type: str
  sample: 0.0.3
checksum:
  description: MD5 checksum of the ISO.
  returned: changed
  type: str
  sample: 8cdbd094195fab4b2b47ff4285577b70
file_size:
  description: Size of the uploaded image in MB.
  returned: changed
  type: int
  sample: 1948
'''

import os
import time

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import upload_file
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import upload_file


class Parameters(AnsibleF5Parameters):
    api_map = {
        'fileSize': 'file_size'
    }

    api_attributes = [

    ]

    returnables = [
        'image_type',
        'version',
        'build',
        'checksum',
        'file_size',
    ]

    updatables = [

    ]


class ApiParameters(Parameters):
    @property
    def file_size(self):
        if self._values['file_size'] is None:
            return None
        tmp = self._values['file_size'].split(' ')
        return int(tmp[0])


class ModuleParameters(Parameters):
    @property
    def filename(self):
        return os.path.basename(self.image)


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


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()
        self.image_type = None

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        if self.image_exists() or self.hotfix_exists():
            return True
        return False

    def image_exists(self):
        result = False
        uri = "https://{0}:{1}/mgmt/tm/sys/software/image/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.filename
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
            if resp.status == 404 or 'code' in response and response['code'] == 404:
                result = False
            else:
                self.image_type = 'release'
                result = True
        except ValueError:
            pass
        return result

    def hotfix_exists(self):
        result = False
        uri = "https://{0}:{1}/mgmt/tm/sys/software/hotfix/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.filename
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
            if resp.status == 404 or 'code' in response and response['code'] == 404:
                result = False
            else:
                self.image_type = 'hotfix'
                result = True
        except ValueError:
            pass
        return result

    def update(self):
        if self.module.check_mode:
            return True
        if self.want.force:
            # The process of updating is a forced re-creation.
            self.remove_from_device()
            self.create_on_device()
            return True
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()

        # Deleting images involves a short period of inconsistency in the REST
        # API due to needing to remove files from disk and update MCPD.
        #
        # This should not (realistically) take more than 30 seconds.
        for x in range(0, 30):
            if not self.exists():
                return True
            time.sleep(1)
        raise F5ModuleError("Failed to delete the resource.")

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True

        self.create_on_device()

        # Creating images involves a short period of inconsistency in the REST
        # API likely due to having to move files into appropriate places on disk
        # and update MCPD with information.
        #
        # This should not (realistically) take more than 30 seconds.
        for x in range(0, 30):
            if self.exists():
                # We want to return some information about the image that was just uploaded
                #
                # This must appear after the creation process because the information
                # does not exist on the device (has been parsed by BIG-IP) until the
                # ISO is uploaded.
                self.want = self.read_current_from_device()
                self._set_changed_options()
                return True
            time.sleep(1)
        raise F5ModuleError("Failed to create the resource.")

    def create_on_device(self):
        url = 'https://{0}:{1}/mgmt/cm/autodeploy/software-image-uploads'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        try:
            upload_file(self.client, url, self.want.image)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def read_current_from_device(self):
        if self.image_exists():
            return self.read_iso_from_device('image')
        elif self.hotfix_exists():
            return self.read_iso_from_device('hotfix')

    def read_iso_from_device(self, type):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/{2}/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            type,
            self.want.filename
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = ApiParameters(params=response)
        result.update({'image_type': self.image_type})
        return result

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        if self.image_exists():
            self.remove_iso_from_device('image')
        elif self.hotfix_exists():
            self.remove_iso_from_device('hotfix')

    def remove_iso_from_device(self, type):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/{2}/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            type,
            self.want.filename
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(response.content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            force=dict(type='bool'),
            image=dict(required=True),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
