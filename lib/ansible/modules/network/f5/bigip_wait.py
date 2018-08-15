#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_wait
short_description: Wait for a BIG-IP condition before continuing
description:
  - You can wait for BIG-IP to be "ready". By "ready", we mean that BIG-IP is ready
    to accept configuration.
  - This module can take into account situations where the device is in the middle
    of rebooting due to a configuration change.
version_added: 2.5
options:
  timeout:
    description:
      - Maximum number of seconds to wait for.
      - When used without other conditions it is equivalent of just sleeping.
      - The default timeout is deliberately set to 2 hours because no individual
        REST API.
    default: 7200
  delay:
    description:
      - Number of seconds to wait before starting to poll.
    default: 0
  sleep:
    default: 1
    description:
      - Number of seconds to sleep between checks, before 2.3 this was hardcoded to 1 second.
  msg:
    description:
      - This overrides the normal error message from a failure to meet the required conditions.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Wait for BIG-IP to be ready to take configuration
  bigip_wait:
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Wait a maximum of 300 seconds for BIG-IP to be ready to take configuration
  bigip_wait:
    timeout: 300
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Wait for BIG-IP to be ready, don't start checking for 10 seconds
  bigip_wait:
    delay: 10
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import datetime
import signal
import time

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


def hard_timeout(module, want, start):
    elapsed = datetime.datetime.utcnow() - start
    module.fail_json(
        msg=want.msg or "Timeout when waiting for BIG-IP", elapsed=elapsed.seconds
    )


class Parameters(AnsibleF5Parameters):
    returnables = [
        'elapsed'
    ]

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

    @property
    def delay(self):
        if self._values['delay'] is None:
            return None
        return int(self._values['delay'])

    @property
    def timeout(self):
        if self._values['timeout'] is None:
            return None
        return int(self._values['timeout'])

    @property
    def sleep(self):
        if self._values['sleep'] is None:
            return None
        return int(self._values['sleep'])


class Changes(Parameters):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Parameters()

    def exec_module(self):
        result = dict()

        try:
            changed = self.execute()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _get_client_connection(self):
        return F5Client(**self.module.params)

    def execute(self):
        signal.signal(
            signal.SIGALRM,
            lambda sig, frame: hard_timeout(self.module, self.want, start)
        )

        # setup handler before scheduling signal, to eliminate a race
        signal.alarm(int(self.want.timeout))

        start = datetime.datetime.utcnow()
        if self.want.delay:
            time.sleep(float(self.want.delay))
        end = start + datetime.timedelta(seconds=int(self.want.timeout))
        while datetime.datetime.utcnow() < end:
            time.sleep(int(self.want.sleep))
            try:
                # The first test verifies that the REST API is available; this is done
                # by repeatedly trying to login to it.
                self.client = self._get_client_connection()
                if not self.client:
                    continue

                if self._device_is_rebooting():
                    # Wait for the reboot to happen and then start from the beginning
                    # of the waiting.
                    continue

                if self._is_mprov_running_on_device():
                    self._wait_for_module_provisioning()
                break
            except Exception:
                # The types of exception's we're handling here are "REST API is not
                # ready" exceptions.
                #
                # For example,
                #
                # Typically caused by device starting up:
                #
                #   icontrol.exceptions.iControlUnexpectedHTTPError: 404 Unexpected Error:
                #       Not Found for uri: https://localhost:10443/mgmt/tm/sys/
                #   icontrol.exceptions.iControlUnexpectedHTTPError: 503 Unexpected Error:
                #       Service Temporarily Unavailable for uri: https://localhost:10443/mgmt/tm/sys/
                #
                #
                # Typically caused by a device being down
                #
                #   requests.exceptions.SSLError: HTTPSConnectionPool(host='localhost', port=10443):
                #       Max retries exceeded with url: /mgmt/tm/sys/ (Caused by SSLError(
                #       SSLError("bad handshake: SysCallError(-1, 'Unexpected EOF')",),))
                #
                #
                # Typically caused by device still booting
                #
                #   raise SSLError(e, request=request)\nrequests.exceptions.SSLError:
                #   HTTPSConnectionPool(host='localhost', port=10443): Max retries
                #   exceeded with url: /mgmt/shared/authn/login (Caused by
                #   SSLError(SSLError(\"bad handshake: SysCallError(-1, 'Unexpected EOF')\",),)),
                continue
        else:
            elapsed = datetime.datetime.utcnow() - start
            self.module.fail_json(
                msg=self.want.msg or "Timeout when waiting for BIG-IP", elapsed=elapsed.seconds
            )
        elapsed = datetime.datetime.utcnow() - start
        self.changes.update({'elapsed': elapsed.seconds})
        return False

    def _device_is_rebooting(self):
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "runlevel"'
        )
        try:
            if '6' in output.commandResult:
                return True
        except AttributeError:
            return False

    def _wait_for_module_provisioning(self):
        # To prevent things from running forever, the hack is to check
        # for mprov's status twice. If mprov is finished, then in most
        # cases (not ASM) the provisioning is probably ready.
        nops = 0
        # Sleep a little to let provisioning settle and begin properly
        time.sleep(5)
        while nops < 4:
            try:
                if not self._is_mprov_running_on_device():
                    nops += 1
                else:
                    nops = 0
            except Exception:
                # This can be caused by restjavad restarting.
                pass
            time.sleep(10)

    def _is_mprov_running_on_device(self):
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "ps aux | grep \'[m]prov\'"'
        )
        if hasattr(output, 'commandResult'):
            return True
        return False


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            timeout=dict(default=7200, type='int'),
            delay=dict(default=0, type='int'),
            sleep=dict(default=1, type='int'),
            msg=dict()
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
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
