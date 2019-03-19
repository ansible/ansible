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
module: bigip_ucs
short_description: Manage upload, installation and removal of UCS files
description:
   - Manage upload, installation and removal of UCS files.
version_added: 2.4
options:
  include_chassis_level_config:
    description:
      - During restore of the UCS file, include chassis level configuration
        that is shared among boot volume sets. For example, cluster default
        configuration.
    type: bool
  ucs:
    description:
      - The path to the UCS file to install. The parameter must be
        provided if the C(state) is either C(installed) or C(activated).
        When C(state) is C(absent), the full path for this parameter will be
        ignored and only the filename will be used to select a UCS for removal.
        Therefore you could specify C(/mickey/mouse/test.ucs) and this module
        would only look for C(test.ucs).
    type: str
  force:
    description:
      - If C(yes) will upload the file every time and replace the file on the
        device. If C(no), the file will only be uploaded if it does not already
        exist. Generally should be C(yes) only in cases where you have reason
        to believe that the image was corrupted during upload.
    type: bool
    default: no
  no_license:
    description:
      - Performs a full restore of the UCS file and all the files it contains,
        with the exception of the license file. The option must be used to
        restore a UCS on RMA devices (Returned Materials Authorization).
    type: bool
  no_platform_check:
    description:
      - Bypasses the platform check and allows a UCS that was created using a
        different platform to be installed. By default (without this option),
        a UCS created from a different platform is not allowed to be installed.
    type: bool
  passphrase:
    description:
      - Specifies the passphrase that is necessary to load the specified UCS file.
    type: bool
  reset_trust:
    description:
      - When specified, the device and trust domain certs and keys are not
        loaded from the UCS. Instead, a new set is regenerated.
    type: bool
  state:
    description:
      - When C(installed), ensures that the UCS is uploaded and installed,
        on the system. When C(present), ensures that the UCS is uploaded.
        When C(absent), the UCS will be removed from the system. When
        C(installed), the uploading of the UCS is idempotent, however the
        installation of that configuration is not idempotent.
    type: str
    choices:
      - absent
      - installed
      - present
    default: present
notes:
   - Only the most basic checks are performed by this module. Other checks and
     considerations need to be taken into account. See the following URL.
     https://support.f5.com/kb/en-us/solutions/public/11000/300/sol11318.html
   - This module does not handle devices with the FIPS 140 HSM
   - This module does not handle BIG-IPs systems on the 6400, 6800, 8400, or
     8800 hardware platform.
   - This module does not verify that the new or replaced SSH keys from the
     UCS file are synchronized between the BIG-IP system and the SCCP
   - This module does not support the 'rma' option
   - This module does not support restoring a UCS archive on a BIG-IP 1500,
     3400, 4100, 6400, 6800, or 8400 hardware platform other than the system
     from which the backup was created
   - The UCS restore operation restores the full configuration only if the
     hostname of the target system matches the hostname on which the UCS
     archive was created. If the hostname does not match, only the shared
     configuration is restored. You can ensure hostnames match by using
     the C(bigip_hostname) Ansible module in a task before using this module.
   - This module does not support re-licensing a BIG-IP restored from a UCS
   - This module does not support restoring encrypted archives on replacement
     RMA units.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Upload UCS
  bigip_ucs:
    ucs: /root/bigip.localhost.localdomain.ucs
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Install (upload, install) UCS.
  bigip_ucs:
    ucs: /root/bigip.localhost.localdomain.ucs
    state: installed
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Install (upload, install) UCS without installing the license portion
  bigip_ucs:
    ucs: /root/bigip.localhost.localdomain.ucs
    state: installed
    no_license: yes
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Install (upload, install) UCS except the license, and bypassing the platform check
  bigip_ucs:
    ucs: /root/bigip.localhost.localdomain.ucs
    state: installed
    no_license: yes
    no_platform_check: yes
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Install (upload, install) UCS using a passphrase necessary to load the UCS
  bigip_ucs:
    ucs: /root/bigip.localhost.localdomain.ucs
    state: installed
    passphrase: MyPassphrase1234
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove uploaded UCS file
  bigip_ucs:
    ucs: bigip.localhost.localdomain.ucs
    state: absent
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import os
import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
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

try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError:
        pass


class Parameters(AnsibleF5Parameters):
    api_map = {}
    updatables = []
    returnables = []
    api_attributes = []


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    def _check_required_if(self, parameter):
        if self._values[parameter] is not True:
            return self._values[parameter]
        if self.state != 'installed':
            raise F5ModuleError(
                '"{0}" parameters requires "installed" state'.format(parameter)
            )

    @property
    def basename(self):
        return os.path.basename(self.ucs)

    @property
    def options(self):
        return {
            'include-chassis-level-config': self.include_chassis_level_config,
            'no-license': self.no_license,
            'no-platform-check': self.no_platform_check,
            'passphrase': self.passphrase,
            'reset-trust': self.reset_trust
        }

    @property
    def reset_trust(self):
        self._check_required_if('reset_trust')
        return self._values['reset_trust']

    @property
    def passphrase(self):
        self._check_required_if('passphrase')
        return self._values['passphrase']

    @property
    def no_platform_check(self):
        self._check_required_if('no_platform_check')
        return self._values['no_platform_check']

    @property
    def no_license(self):
        self._check_required_if('no_license')
        return self._values['no_license']

    @property
    def include_chassis_level_config(self):
        self._check_required_if('include_chassis_level_config')
        return self._values['include_chassis_level_config']

    @property
    def install_command(self):
        cmd = 'tmsh load sys ucs /var/local/ucs/{0}'.format(self.basename)
        # Append any options that might be specified
        options = OrderedDict(sorted(self.options.items(), key=lambda t: t[0]))
        for k, v in iteritems(options):
            if v is False or v is None:
                continue
            elif k == 'passphrase':
                cmd += ' %s %s' % (k, v)
            else:
                cmd += ' %s' % (k)
        return cmd


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


class ReportableChanges(Changes):
    pass


class UsableChanges(Changes):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)

    def exec_module(self):
        if self.is_version_v1():
            manager = V1Manager(**self.kwargs)
        else:
            manager = V2Manager(**self.kwargs)

        return manager.exec_module()

    def is_version_v1(self):
        """Checks to see if the TMOS version is less than 12.1.0

        Versions prior to 12.1.0 have a bug which prevents the REST
        API from properly listing any UCS files when you query the
        /mgmt/tm/sys/ucs endpoint. Therefore you need to do everything
        through tmsh over REST.

        :return: Bool
        """
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('12.1.0'):
            return True
        else:
            return False


class Difference(object):
    pass


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.changes = UsableChanges()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state in ['present', 'installed']:
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def update(self):
        if self.module.check_mode:
            if self.want.force:
                return True
            return False
        elif self.want.force:
            self.remove()
            return self.create()
        elif self.want.state == 'installed':
            return self.install_on_device()
        else:
            return False

    def create(self):
        if self.module.check_mode:
            return True
        self.create_on_device()
        if not self.exists():
            raise F5ModuleError("Failed to upload the UCS file")
        if self.want.state == 'installed':
            self.install_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the UCS file")
        return True

    def wait_for_rest_api_restart(self):
        time.sleep(5)
        for x in range(0, 60):
            try:
                self.client.reconnect()
                break
            except Exception:
                time.sleep(3)

    def wait_for_configuration_reload(self):
        noops = 0
        while noops < 4:
            time.sleep(3)
            try:
                params = dict(command="run",
                              utilCmdArgs='-c "tmsh show sys mcp-state"'
                              )
                uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
                    self.client.provider['server'],
                    self.client.provider['server_port']
                )
                resp = self.client.api.post(uri, json=params)
                try:
                    output = resp.json()
                except ValueError as ex:
                    raise F5ModuleError(str(ex))
                if 'code' in output and output['code'] in [400, 403]:
                    if 'message' in output:
                        raise F5ModuleError(output['message'])
                    else:
                        raise F5ModuleError(resp.content)
            except Exception as ex:
                # This can be caused by restjavad restarting.
                continue

            if 'commandResult' not in output:
                continue

            # Need to re-connect here because the REST framework will be restarting
            # and thus be clearing its authorization cache
            result = output['commandResult']
            if self._is_config_reloading_failed_on_device(result):
                raise F5ModuleError(
                    "Failed to reload the configuration. This may be due "
                    "to a cross-version incompatibility. {0}".format(result)
                )
            if self._is_config_reloading_success_on_device(result):
                if self._is_config_reloading_running_on_device(result):
                    noops += 1
                    continue
            noops = 0

    def _is_config_reloading_success_on_device(self, output):
        succeed = r'Last Configuration Load Status\s+full-config-load-succeed'
        matches = re.search(succeed, output)
        if matches:
            return True
        return False

    def _is_config_reloading_running_on_device(self, output):
        running = r'Running Phase\s+running'
        matches = re.search(running, output)
        if matches:
            return True
        return False

    def _is_config_reloading_failed_on_device(self, output):
        failed = r'Last Configuration Load Status\s+base-config-load-failed'
        matches = re.search(failed, output)
        if matches:
            return True
        return False


class V1Manager(BaseManager):
    """Manager class for V1 product

    V1 products include versions of BIG-IP < 12.1.0, but >= 12.0.0.

    These versions had a number of API deficiencies. These include, but
    are not limited to,

      * UCS collection endpoint listed no items
      * No API to upload UCS files

    """
    def upload_file_to_device(self, content, name):
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/uploads'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        try:
            upload_file(self.client, url, content, name)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def create_on_device(self):
        remote_path = "/var/local/ucs"
        tpath_name = '/var/config/rest/downloads'

        self.upload_file_to_device(self.want.ucs, self.want.basename)

        uri = "https://{0}:{1}/mgmt/tm/util/unix-mv/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs='{0}/{2} {1}/{2}'.format(
                tpath_name, remote_path, self.want.basename
            )
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def read_current_from_device(self):
        result = []
        params = dict(command="run",
                      utilCmdArgs='-c "tmsh list sys ucs"'
                      )
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            output = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in output and output['code'] in [400, 403]:
            if 'message' in output:
                raise F5ModuleError(output['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'commandResult' in output:
            lines = output['commandResult'].split("\n")
            result = [x.strip() for x in lines]
            result = list(set(result))
        return result

    def exists(self):
        collection = self.read_current_from_device()
        if self.want.basename in collection:
            return True
        return False

    def remove_from_device(self):
        params = dict(command="run",
                      utilCmdArgs='-c "tmsh delete sys ucs {0}"'.format(self.want.basename)
                      )
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            output = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in output and output['code'] in [400, 403]:
            if 'message' in output:
                raise F5ModuleError(output['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'commandResult' in output:
            if '{0} is deleted'.format(self.want.basename) in output['commandResult']:
                return True
        return False

    def install_on_device(self):
        try:
            params = dict(command="run",
                          utilCmdArgs='-c "{0}"'.format(self.want.install_command)
                          )
            uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
                self.client.provider['server'],
                self.client.provider['server_port']
            )
            resp = self.client.api.post(uri, json=params)
            try:
                output = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))
            if 'code' in output and output['code'] in [400, 403]:
                if 'message' in output:
                    raise F5ModuleError(output['message'])
                else:
                    raise F5ModuleError(resp.content)
        except Exception as ex:
            # Reloading a UCS configuration will cause restjavad to restart,
            # aborting the connection.
            if 'Connection aborted' in str(ex):
                pass
            elif 'TimeoutException' in str(ex):
                # Timeouts appear to be able to happen in 12.1.2
                pass
            else:
                raise F5ModuleError(str(ex))
        self.wait_for_rest_api_restart()
        self.wait_for_configuration_reload()
        return True


class V2Manager(V1Manager):
    """Manager class for V2 product

    V2 products include versions of BIG-IP >= 12.1.0 but < 13.0.0.

    These versions fixed the collection bug in V1, but had yet to add the
    ability to upload files using a dedicated UCS upload API.

    """

    def read_current_from_device(self):
        result = []
        uri = "https://{0}:{1}/mgmt/tm/sys/ucs/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        items = response.get('items', [])
        for item in items:
            result.append(os.path.basename(item['apiRawValues']['filename']))
        return result

    def exists(self):
        collection = self.read_current_from_device()
        if self.want.basename in collection:
            return True
        return False


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            force=dict(
                type='bool',
                default='no'
            ),
            include_chassis_level_config=dict(
                type='bool'
            ),
            no_license=dict(
                type='bool'
            ),
            no_platform_check=dict(
                type='bool'
            ),
            passphrase=dict(no_log=True),
            reset_trust=dict(type='bool'),
            state=dict(
                default='present',
                choices=['absent', 'installed', 'present']
            ),
            ucs=dict(required=True)
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
