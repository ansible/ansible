#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
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
version_added: "2.5"
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
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
requirements:
  - f5-sdk >= 2.2.3
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
from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.f5_utils import F5_COMMON_ARGS
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from f5.bigip import ManagementRoot as BigIpMgmt
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


def hard_timeout(client, want, start):
    elapsed = datetime.datetime.utcnow() - start
    client.module.fail_json(
        want.msg or "Timeout when waiting for BIG-IP", elapsed=elapsed.seconds
    )


class AnsibleF5ClientStub(AnsibleF5Client):
    """Interim class to disconnect Params from connection

    This module is an interim class that was made to separate the Ansible Module
    Parameters from the connection to BIG-IP.

    Since this module needs to be able to control the connection process, the default
    class is not appropriate. Therefore, we overload it and re-define out the
    connection related work to a separate method.

    This class should serve as a reason to break apart this work itself into separate
    classes in module_utils. There will be on-going work to do this and, when done,
    the result will replace this work here.

    """

    def __init__(self, argument_spec=None, supports_check_mode=False,
                 mutually_exclusive=None, required_together=None,
                 required_if=None, required_one_of=None, add_file_common_args=False,
                 f5_product_name='bigip'):
        self.f5_product_name = f5_product_name

        merged_arg_spec = dict()
        merged_arg_spec.update(F5_COMMON_ARGS)
        if argument_spec:
            merged_arg_spec.update(argument_spec)
            self.arg_spec = merged_arg_spec

        mutually_exclusive_params = []
        if mutually_exclusive:
            mutually_exclusive_params += mutually_exclusive

        required_together_params = []
        if required_together:
            required_together_params += required_together

        self.module = AnsibleModule(
            argument_spec=merged_arg_spec,
            supports_check_mode=supports_check_mode,
            mutually_exclusive=mutually_exclusive_params,
            required_together=required_together_params,
            required_if=required_if,
            required_one_of=required_one_of,
            add_file_common_args=add_file_common_args
        )

        self.check_mode = self.module.check_mode
        self._connect_params = self._get_connect_params()

    def connect(self):
        try:
            if 'transport' not in self.module.params or self.module.params['transport'] != 'cli':
                self.api = self._get_mgmt_root(
                    self.f5_product_name, **self._connect_params
                )
            return True
        except Exception:
            return False

    def _get_mgmt_root(self, type, **kwargs):
        if type == 'bigip':
            result = BigIpMgmt(
                kwargs['server'],
                kwargs['user'],
                kwargs['password'],
                port=kwargs['server_port'],
                timeout=1,
                token='tmos'
            )
            return result


class Parameters(AnsibleF5Parameters):
    returnables = [
        'elapsed'
    ]

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        if params:
            self.update(params=params)
        self._values['__warnings'] = []

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

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
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
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
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def execute(self):
        signal.signal(
            signal.SIGALRM,
            lambda sig, frame: hard_timeout(self.client, self.want, start)
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
                connected = self._connect_to_device()
                if not connected:
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
            self.client.module.fail_json(
                msg=self.want.msg or "Timeout when waiting for BIG-IP", elapsed=elapsed.seconds
            )
        elapsed = datetime.datetime.utcnow() - start
        self.changes.update({'elapsed': elapsed.seconds})
        return False

    def _connect_to_device(self):
        result = self.client.connect()
        return result

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
        self.argument_spec = dict(
            timeout=dict(default=7200, type='int'),
            delay=dict(default=0, type='int'),
            sleep=dict(default=1, type='int'),
            msg=dict()
        )
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5ClientStub(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name,
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
