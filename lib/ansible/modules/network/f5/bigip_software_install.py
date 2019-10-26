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
module: bigip_software_install
short_description: Install software images on a BIG-IP
description:
  - Install new images on a BIG-IP.
version_added: 2.7
options:
  image:
    description:
      - Image to install on the remote device.
    type: str
  volume:
    description:
      - The volume to install the software image to.
    type: str
  state:
    description:
      - When C(installed), ensures that the software is installed on the volume
        and the volume is set to be booted from. The device is B(not) rebooted
        into the new software.
      - When C(activated), performs the same operation as C(installed), but
        the system is rebooted to the new software.
    type: str
    choices:
      - activated
      - installed
    default: activated
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''
EXAMPLES = r'''
- name: Ensure an existing image is installed in specified volume
  bigip_software_install:
    image: BIGIP-13.0.0.0.0.1645.iso
    volume: HD1.2
    state: installed
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Ensure an existing image is activated in specified volume
  bigip_software_install:
    image: BIGIP-13.0.0.0.0.1645.iso
    state: activated
    volume: HD1.2
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import time
import ssl

from ansible.module_utils.six.moves.urllib.error import URLError
from ansible.module_utils.urls import urlparse
from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec


class Parameters(AnsibleF5Parameters):
    api_map = {

    }

    api_attributes = [
        'options',
        'volume',
    ]

    returnables = [

    ]

    updatables = [

    ]


class ApiParameters(Parameters):
    @property
    def image_names(self):
        result = []
        result += self.read_image_from_device('image')
        result += self.read_image_from_device('hotfix')
        return result

    def read_image_from_device(self, t):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            t,
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return []

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                return []
            else:
                return []
        if 'items' not in response:
            return []
        return [x['name'].split('/')[0] for x in response['items']]


class ModuleParameters(Parameters):
    @property
    def version(self):
        if self._values['version']:
            return self._values['version']

        self._values['version'] = self.image_info['version']
        return self._values['version']

    @property
    def build(self):
        # Return cached copy if we have it
        if self._values['build']:
            return self._values['build']

        # Otherwise, get copy from image info cache
        self._values['build'] = self.image_info['build']
        return self._values['build']

    @property
    def image_info(self):
        if self._values['image_info']:
            image = self._values['image_info']
        else:
            # Otherwise, get a new copy and store in cache
            image = self.read_image()
            self._values['image_info'] = image
        return image

    @property
    def image_type(self):
        if self._values['image_type']:
            return self._values['image_type']
        if 'software:image' in self.image_info['kind']:
            self._values['image_type'] = 'image'
        else:
            self._values['image_type'] = 'hotfix'
        return self._values['image_type']

    def read_image(self):
        image = self.read_image_from_device(type='image')
        if image:
            return image
        image = self.read_image_from_device(type='hotfix')
        if image:
            return image
        return None

    def read_image_from_device(self, type):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/{2}/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            type,
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'items' in response:
            for item in response['items']:
                if item['name'].startswith(self.image):
                    return item


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
        self.want = ModuleParameters(params=self.module.params, client=self.client)
        self.have = ApiParameters(client=self.client)
        self.changes = UsableChanges()
        self.volume_url = None

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
        result = dict()

        changed = self.present()

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
            return False
        else:
            return self.update()

    def _set_volume_url(self, item):
        path = urlparse(item['selfLink']).path
        self.volume_url = "https://{0}:{1}{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            path
        )

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/volume/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.get(uri)

        try:
            collection = resp.json()
        except ValueError:
            return False

        for item in collection['items']:
            if item['name'].startswith(self.want.volume):
                self._set_volume_url(item)
                break

        if not self.volume_url:
            self.volume_url = uri + self.want.volume

        resp = self.client.api.get(self.volume_url)

        try:
            response = resp.json()
        except ValueError:
            return False

        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False

        # version key can be missing in the event that an existing volume has
        # no installed software in it.
        if self.want.version != response.get('version', None):
            return False
        if self.want.build != response.get('build', None):
            return False

        if self.want.state == 'installed':
            return True
        if self.want.state == 'activated':
            if 'defaultBootLocation' in response['media'][0]:
                return True
        return False

    def volume_exists(self):
        resp = self.client.api.get(self.volume_url)

        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def update(self):
        if self.module.check_mode:
            return True

        if self.want.image and self.want.image not in self.have.image_names:
            raise F5ModuleError(
                "The specified image was not found on the device."
            )

        options = list()
        if not self.volume_exists():
            options.append({'create-volume': True})
        if self.want.state == 'activated':
            options.append({'reboot': True})
        self.want.update({'options': options})

        self.update_on_device()
        self.wait_for_software_install_on_device()
        if self.want.state == 'activated':
            self.wait_for_device_reboot()
        return True

    def update_on_device(self):
        params = {
            "command": "install",
            "name": self.want.image,
        }
        params.update(self.want.api_params())

        uri = "https://{0}:{1}/mgmt/tm/sys/software/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.image_type
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
            if 'commandResult' in response and len(response['commandResult'].strip()) > 0:
                raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def wait_for_device_reboot(self):
        while True:
            time.sleep(5)
            try:
                self.client.reconnect()
                volume = self.read_volume_from_device()
                if volume is None:
                    continue
                if 'active' in volume and volume['active'] is True:
                    break
            except F5ModuleError:
                # Handle all exceptions because if the system is offline (for a
                # reboot) the REST client will raise exceptions about
                # connections
                pass

    def wait_for_software_install_on_device(self):
        # We need to delay this slightly in case the the volume needs to be
        # created first
        for dummy in range(10):
            try:
                if self.volume_exists():
                    break
            except F5ModuleError:
                pass
            time.sleep(5)
        while True:
            time.sleep(10)
            volume = self.read_volume_from_device()
            if volume is None or 'status' not in volume:
                self.client.reconnect()
                continue
            if volume['status'] == 'complete':
                break
            elif volume['status'] == 'failed':
                raise F5ModuleError

    def read_volume_from_device(self):
        try:
            resp = self.client.api.get(self.volume_url)
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        except ssl.SSLError:
            # Suggests BIG-IP is still in the middle of restarting itself or
            # restjavad is restarting.
            return None
        except URLError:
            # At times during reboot BIG-IP will reset or timeout connections so we catch and pass this here.
            return None

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            image=dict(),
            volume=dict(),
            state=dict(
                default='activated',
                choices=['activated', 'installed']
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
