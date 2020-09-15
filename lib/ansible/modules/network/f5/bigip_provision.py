#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_provision
short_description: Manage BIG-IP module provisioning
description:
  - Manage BIG-IP module provisioning. This module will only provision at the
    standard levels of Dedicated, Nominal, and Minimum.
version_added: 2.4
options:
  module:
    description:
      - The module to provision in BIG-IP.
    type: str
    required: True
    choices:
      - am
      - afm
      - apm
      - asm
      - avr
      - cgnat
      - fps
      - gtm
      - ilx
      - lc
      - ltm
      - mgmt
      - pem
      - sam
      - sslo
      - swg
      - urldb
      - vcmp
    aliases:
      - name
  level:
    description:
      - Sets the provisioning level for the requested modules. Changing the
        level for one module may require modifying the level of another module.
        For example, changing one module to C(dedicated) requires setting all
        others to C(none). Setting the level of a module to C(none) means that
        the module is not activated.
      - Use C(state) absent to set c(level) to none and de-provision module.
      - This parameter is not relevant to C(cgnat - pre tmos 15.0) or C(mgmt) and will not be
        applied to the C(cgnat - pre tmos 15.0) or C(mgmt) module.
    type: str
    choices:
      - dedicated
      - nominal
      - minimum
    default: nominal
  memory:
    description:
      - Sets additional memory for management module. This is in addition to
        minimum allocated RAM of 1264MB.
      - The accepted value range is C(0 - 8192). Maximum value is restricted by
        systems available RAM.
      - Specifying C(large) reserves an additional 500MB for mgmt module.
      - Specifying C(medium) reserves an additional 200MB for mgmt module.
      - Specifying C(small) reserves no additional RAM for mgmt module.
      - Use C(large) for configurations containing more than 2000 objects, or
        more specifically, for any configuration that exceeds 1000 objects
        per 2 GB of installed memory. Changing the Management C(mgmt) size
        after initial provisioning causes a reprovision operation
    type: str
    version_added: 2.9
  state:
    description:
      - The state of the provisioned module on the system. When C(present),
        guarantees that the specified module is provisioned at the requested
        level provided that there are sufficient resources on the device (such
        as physical RAM) to support the provisioned module.
      - When C(absent), de-provision the module.
      - C(absent), is not a relevant option to C(mgmt) module as module can not be de-provisioned.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Greg Crosby (@crosbygw)
'''

EXAMPLES = r'''
- name: Provision PEM at "nominal" level
  bigip_provision:
    module: pem
    level: nominal
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  delegate_to: localhost

- name: Provision a dedicated SWG. This will unprovision every other module
  bigip_provision:
    module: swg
    level: dedicated
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  delegate_to: localhost

- name: Provision mgmt with medium amount of memory.
  bigip_provision:
    module: mgmt
    memory: medium
    provider:
      server: lb.mydomain.com
      password: secret
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
level:
  description: The new provisioning level of the module.
  returned: changed
  type: str
  sample: minimum
memory:
  description: The new provisioned amount of memory for mgmt module.
  returned: changed
  type: str
  sample: large
'''

import time

from ansible.module_utils.basic import AnsibleModule
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import TransactionContextManager
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import TransactionContextManager
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'value': 'memory',
    }

    api_attributes = [
        'level',
        'value',
    ]

    returnables = [
        'level',
        'memory',
    ]

    updatables = [
        'level',
        'cgnat',
        'memory',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):

    def _validate_memory_limit(self, limit):
        if self._values['memory'] == 'small':
            return '0'
        if self._values['memory'] == 'medium':
            return '200'
        if self._values['memory'] == 'large':
            return '500'
        if 0 <= int(limit) <= 8192:
            return str(limit)
        raise F5ModuleError(
            "Valid 'memory' must be in range 0 - 8192, 'small', 'medium', or 'large'."
        )

    @property
    def level(self):
        if self._values['level'] is None:
            return None
        if self._values['module'] == 'mgmt':
            return None
        if self.state == 'absent':
            return 'none'
        return str(self._values['level'])

    @property
    def memory(self):
        if self._values['memory'] is None:
            return None
        if self._values['module'] != 'mgmt':
            return None
        return int(self._validate_memory_limit(self._values['memory']))


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
            return result
        except Exception:
            return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    @property
    def memory(self):
        if self._values['memory'] is None:
            return None
        if self._values['memory'] == '0':
            return 'small'
        if self._values['memory'] == '200':
            return 'medium'
        if self._values['memory'] == '500':
            return 'large'
        return str(self._values['memory'])


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            result = self.__default(param)
            return result

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def cgnat(self):
        if self.want.module == 'cgnat':
            if self.want.state == 'absent' and self.have.enabled is True:
                return True
            if self.want.state == 'present' and self.have.disabled is True:
                return True


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.have = None
        self.want = ModuleParameters(params=self.module.params)
        self.changes = UsableChanges()

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
        return result

    def version_is_greater_or_equal_15(self):
        version = tmos_version(self.client)
        if LooseVersion(version) >= LooseVersion('15.0.0'):
            return True
        else:
            return False

    def present(self):
        if self.exists():
            return False
        return self.update()

    def exists(self):
        if self.want.module == 'cgnat' and not self.version_is_greater_or_equal_15():
            uri = "https://{0}:{1}/mgmt/tm/sys/feature-module/cgnat/".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
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
            if 'disabled' in response and response['disabled'] is True:
                return False
            elif 'enabled' in response and response['enabled'] is True:
                return True
        elif self.want.module == 'mgmt':
            uri = "https://{0}:{1}/mgmt/tm/sys/db/provision.extramb/".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
            )
            resp = self.client.api.get(uri)
            try:
                response = resp.json()
            except ValueError:
                return False
            if resp.status == 404 or 'code' in response and response['code'] == 404:
                return False
            if str(response['value']) != 0 and self.want.memory == 0:
                return False
            if str(response['value']) == 0 and self.want.memory == 0:
                return True
            if str(response['value']) == self.want.memory:
                return True
            return False
        try:
            for x in range(0, 5):
                uri = "https://{0}:{1}/mgmt/tm/sys/provision/{2}".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                    self.want.module
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

                if str(response['level']) != 'none' and self.want.level == 'none':
                    return True
                if str(response['level']) == 'none' and self.want.level == 'none':
                    return False
                if str(response['level']) == self.want.level:
                    return True
                return False
        except Exception as ex:
            if 'not registered' in str(ex):
                return False
            time.sleep(1)

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        result = self.update_on_device()
        if self.want.module == 'cgnat' and not self.version_is_greater_or_equal_15():
            return result
        self._wait_for_module_provisioning()

        if self.want.module == 'vcmp':
            self._wait_for_reboot()
            self._wait_for_module_provisioning()

        if self.want.module == 'asm':
            self._wait_for_asm_ready()
        if self.want.module == 'afm':
            self._wait_for_afm_ready()
        if self.want.module == 'cgnat':
            self._wait_for_cgnat_ready()
        if self.want.module == 'mgmt':
            self._wait_for_mgmt_ready()
        return True

    def should_reboot(self):
        for x in range(0, 24):
            try:
                uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                    'provision.action'
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

                if response['value'] == 'reboot':
                    return True
                elif response['value'] == 'none':
                    time.sleep(5)
            except Exception:
                time.sleep(5)
        return False

    def reboot_device(self):
        nops = 0
        last_reboot = self._get_last_reboot()

        try:
            params = dict(
                command="run",
                utilCmdArgs='-c "/sbin/reboot"'
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
            if 'commandResult' in response:
                return str(response['commandResult'])
        except Exception:
            pass

        # Sleep a little to let rebooting take effect
        time.sleep(20)

        while nops < 3:
            try:
                self.client.reconnect()
                next_reboot = self._get_last_reboot()
                if next_reboot is None:
                    nops = 0
                if next_reboot == last_reboot:
                    nops = 0
                else:
                    nops += 1
            except Exception as ex:
                # This can be caused by restjavad restarting.
                pass
            time.sleep(10)
        return None

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update_on_device(self):
        if self.want.module == 'cgnat' and not self.version_is_greater_or_equal_15():
            if self.changes.cgnat:
                return self.provision_cgnat_on_device()
            return False
        elif self.want.level == 'dedicated' and self.want.module != 'mgmt':
            self.provision_dedicated_on_device()
        else:
            self.provision_non_dedicated_on_device()

    def provision_cgnat_on_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/feature-module/cgnat/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        params = dict(enabled=True)
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def provision_dedicated_on_device(self):
        params = self.want.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/provision/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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

        resources = [x['name'] for x in response['items'] if x['name'] != self.want.module]

        with TransactionContextManager(self.client) as transact:
            for resource in resources:
                target = uri + resource
                resp = transact.api.patch(target, json=dict(level='none'))
                try:
                    response = resp.json()
                except ValueError as ex:
                    raise F5ModuleError(str(ex))

                if 'code' in response and response['code'] in [400, 404]:
                    if 'message' in response:
                        raise F5ModuleError(response['message'])
                    else:
                        raise F5ModuleError(resp.content)

            target = uri + self.want.module
            resp = transact.api.patch(target, json=params)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] in [400, 404]:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)

    def provision_non_dedicated_on_device(self):
        params = self.want.api_params()
        if self.want.module == 'mgmt':
            uri = "https://{0}:{1}/mgmt/tm/sys/db/provision.extramb/".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
            )
        else:
            uri = "https://{0}:{1}/mgmt/tm/sys/provision/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                self.want.module
            )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def read_current_from_device(self):
        if self.want.module == 'cgnat' and not self.version_is_greater_or_equal_15():
            uri = "https://{0}:{1}/mgmt/tm/sys/feature-module/cgnat/".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
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
        elif self.want.module == 'mgmt':
            uri = "https://{0}:{1}/mgmt/tm/sys/db/provision.extramb/".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
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
        else:
            uri = "https://{0}:{1}/mgmt/tm/sys/provision/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                self.want.module
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
        return ApiParameters(params=response)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        if self.want.module == 'cgnat' and not self.version_is_greater_or_equal_15():
            return self.deprovision_cgnat_on_device()

        self.remove_from_device()
        self._wait_for_module_provisioning()
        # For vCMP, because it has to reboot, we also wait for mcpd to become available
        # before "moving on", or else the REST API would not be available and subsequent
        # Tasks would fail.
        if self.want.module == 'vcmp':
            self._wait_for_reboot()
            self._wait_for_module_provisioning()

        if self.should_reboot():
            self.save_on_device()
            self.reboot_device()
            self._wait_for_module_provisioning()

        if self.exists():
            raise F5ModuleError("Failed to de-provision the module")
        return True

    def save_on_device(self):
        command = 'tmsh save sys config'
        params = dict(
            command="run",
            utilCmdArgs='-c "{0}"'.format(command)
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/provision/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.module
        )
        resp = self.client.api.patch(uri, json=dict(level='none'))
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def deprovision_cgnat_on_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/feature-module/cgnat/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        params = dict(disabled=True)
        resp = self.client.api.patch(uri, json=params)
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

    def _wait_for_module_provisioning(self):
        # To prevent things from running forever, the hack is to check
        # for mprov's status twice. If mprov is finished, then in most
        # cases (not ASM) the provisioning is probably ready.
        nops = 0

        # Sleep a little to let provisioning settle and begin properly
        time.sleep(5)

        while nops < 3:
            try:
                if not self._is_mprov_running_on_device():
                    nops += 1
                else:
                    nops = 0
            except Exception:
                # This can be caused by restjavad restarting.
                try:
                    self.client.reconnect()
                except Exception:
                    pass
            time.sleep(5)

    def _is_mprov_running_on_device(self):
        # /usr/libexec/qemu-kvm is added here to prevent vcmp provisioning
        # from never allowing the mprov provisioning to succeed.
        #
        # It turns out that the 'mprov' string is found when enabling vcmp. The
        # qemu-kvm command that is run includes it.
        #
        # For example,
        #   /usr/libexec/qemu-kvm -rt-usecs 880 ... -mem-path /dev/mprov/vcmp -f5-tracing ...
        #
        try:
            command = "ps aux | grep \'[m]prov\' | grep -v /usr/libexec/qemu-kvm"
            params = dict(
                command="run",
                utilCmdArgs='-c "{0}"'.format(command)
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

            if 'commandResult' in response:
                return True
        except Exception:
            pass
        return False

    def _wait_for_asm_ready(self):
        """Waits specifically for ASM

        On older versions, ASM can take longer to actually start up than
        all the previous checks take. This check here is specifically waiting for
        the Policies API to stop raising errors
        :return:
        """
        nops = 0
        restarted_asm = False
        while nops < 3:
            try:
                uri = "https://{0}:{1}/mgmt/tm/asm/policies/".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                )
                resp = self.client.api.get(uri)

                try:
                    response = resp.json()
                except ValueError as ex:
                    raise F5ModuleError(str(ex))

                if 'code' in response and response['code'] in [400, 403]:
                    if 'message' in response:
                        raise F5ModuleError(response['message'])
                    else:
                        raise F5ModuleError(resp.content)

                if len(response['items']) >= 0:
                    nops += 1
                else:
                    nops = 0
            except Exception as ex:
                if not restarted_asm:
                    self._restart_asm()
                    restarted_asm = True
            time.sleep(5)

    def _wait_for_afm_ready(self):
        """Waits specifically for AFM

        AFM can take longer to actually start up than all the previous checks take.
        This check here is specifically waiting for the Security API to stop raising
        errors.
        :return:
        """
        nops = 0
        while nops < 3:
            try:
                uri = "https://{0}:{1}/mgmt/tm/security/".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                )
                resp = self.client.api.get(uri)

                try:
                    response = resp.json()
                except ValueError as ex:
                    raise F5ModuleError(str(ex))

                if 'code' in response and response['code'] in [400, 403]:
                    if 'message' in response:
                        raise F5ModuleError(response['message'])
                    else:
                        raise F5ModuleError(resp.content)

                if len(response['items']) >= 0:
                    nops += 1
                else:
                    nops = 0
            except Exception as ex:
                pass
            time.sleep(5)

    def _wait_for_cgnat_ready(self):
        """Waits specifically for CGNAT

        Starting in TMOS 15.0 cgnat can take longer to actually start up than all the previous checks take.
        This check here is specifically waiting for a cgnat API to stop raising
        errors.
        :return:
        """
        nops = 0
        while nops < 3:
            try:
                uri = "https://{0}:{1}/mgmt/tm/ltm/lsn-pool".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                )
                resp = self.client.api.get(uri)

                try:
                    response = resp.json()
                except ValueError as ex:
                    raise F5ModuleError(str(ex))

                if 'code' in response and response['code'] in [400, 403]:
                    if 'message' in response:
                        raise F5ModuleError(response['message'])
                    else:
                        raise F5ModuleError(resp.content)

                if len(response['items']) >= 0:
                    nops += 1
                else:
                    nops = 0
            except Exception as ex:
                pass
            time.sleep(5)

    def _wait_for_mgmt_ready(self):
        """Waits specifically for MGMT

        Modifying memory reserve for mgmt can take longer to actually start up than all the previous checks take.
        This check here is specifically waiting for a MGMT API to stop raising
        errors.
        :return:
        """
        nops = 0
        while nops < 3:
            try:
                uri = "https://{0}:{1}/mgmt/tm".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                )
                resp = self.client.api.get(uri)

                try:
                    response = resp.json()
                except ValueError as ex:
                    raise F5ModuleError(str(ex))

                if 'code' in response and response['code'] in [400, 403]:
                    if 'message' in response:
                        raise F5ModuleError(response['message'])
                    else:
                        raise F5ModuleError(resp.content)

                if len(response['items']) >= 0:
                    nops += 1
                else:
                    nops = 0
            except Exception as ex:
                pass
            time.sleep(5)

    def _restart_asm(self):
        try:
            params = dict(
                command="run",
                utilCmdArgs='-c "bigstart restart asm"'
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
            time.sleep(60)
            return True
        except Exception:
            pass
        return None

    def _get_last_reboot(self):
        try:
            params = dict(
                command="run",
                utilCmdArgs='-c "/usr/bin/last reboot | head -1"'
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

            if 'commandResult' in response:
                return str(response['commandResult'])
        except Exception:
            pass
        return None

    def _wait_for_reboot(self):
        nops = 0

        last_reboot = self._get_last_reboot()

        # Sleep a little to let provisioning settle and begin properly
        time.sleep(5)

        while nops < 6:
            try:
                self.client.reconnect()
                next_reboot = self._get_last_reboot()
                if next_reboot is None:
                    nops = 0
                if next_reboot == last_reboot:
                    nops = 0
                else:
                    nops += 1
            except Exception as ex:
                # This can be caused by restjavad restarting.
                pass
            time.sleep(10)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            module=dict(
                required=True,
                choices=[
                    'afm', 'am', 'apm', 'asm', 'avr', 'cgnat',
                    'fps', 'gtm', 'ilx', 'lc', 'ltm', 'mgmt',
                    'pem', 'sam', 'sslo', 'swg', 'urldb', 'vcmp'
                ],
                aliases=['name']
            ),
            level=dict(
                default='nominal',
                choices=['nominal', 'dedicated', 'minimum']
            ),
            memory=dict(),
            state=dict(
                default='present',
                choices=['present', 'absent']
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['parameters', 'parameters_src']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
