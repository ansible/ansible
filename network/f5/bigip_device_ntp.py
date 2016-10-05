#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016 F5 Networks Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: bigip_device_ntp
short_description: Manage NTP servers on a BIG-IP
description:
  - Manage NTP servers on a BIG-IP
version_added: "2.2"
options:
  ntp_servers:
    description:
      - A list of NTP servers to set on the device. At least one of C(ntp_servers)
        or C(timezone) is required.
    required: false
    default: []
  state:
    description:
      - The state of the NTP servers on the system. When C(present), guarantees
        that the NTP servers are set on the system. When C(absent), removes the
        specified NTP servers from the device configuration.
    required: false
    default: present
    choices:
      - absent
      - present
  timezone:
    description:
      - The timezone to set for NTP lookups. At least one of C(ntp_servers) or
        C(timezone) is required.
    default: UTC
    required: false
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Set NTP server
  bigip_device_ntp:
      ntp_servers:
          - "192.0.2.23"
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Set timezone
  bigip_device_ntp:
      password: "secret"
      server: "lb.mydomain.com"
      timezone: "America/Los_Angeles"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost
'''

RETURN = '''
ntp_servers:
    description: The NTP servers that were set on the device
    returned: changed
    type: list
    sample: ["192.0.2.23", "192.0.2.42"]
timezone:
    description: The timezone that was set on the device
    returned: changed
    type: string
    sample: "true"
'''

try:
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


class BigIpDeviceNtp(object):
    def __init__(self, *args, **kwargs):
        if not HAS_F5SDK:
            raise F5ModuleError("The python f5-sdk module is required")

        # The params that change in the module
        self.cparams = dict()

        # Stores the params that are sent to the module
        self.params = kwargs
        self.api = ManagementRoot(kwargs['server'],
                                  kwargs['user'],
                                  kwargs['password'],
                                  port=kwargs['server_port'])

    def flush(self):
        result = dict()
        changed = False
        state = self.params['state']

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        if 'servers' in self.cparams:
            self.cparams['ntp_servers'] = self.cparams.pop('servers')

        result.update(**self.cparams)
        result.update(dict(changed=changed))
        return result

    def read(self):
        """Read information and transform it

        The values that are returned by BIG-IP in the f5-sdk can have encoding
        attached to them as well as be completely missing in some cases.

        Therefore, this method will transform the data from the BIG-IP into a
        format that is more easily consumable by the rest of the class and the
        parameters that are supported by the module.
        """
        p = dict()
        r = self.api.tm.sys.ntp.load()

        if hasattr(r, 'servers'):
            # Deliberately using sets to supress duplicates
            p['servers'] = set([str(x) for x in r.servers])
        if hasattr(r, 'timezone'):
            p['timezone'] = str(r.timezone)
        return p

    def present(self):
        changed = False
        params = dict()
        current = self.read()

        check_mode = self.params['check_mode']
        ntp_servers = self.params['ntp_servers']
        timezone = self.params['timezone']

        # NTP servers can be set independently
        if ntp_servers is not None:
            if 'servers' in current:
                items = set(ntp_servers)
                if items != current['servers']:
                    params['servers'] = list(ntp_servers)
            else:
                params['servers'] = ntp_servers

        # Timezone can be set independently
        if timezone is not None:
            if 'timezone' in current and current['timezone'] != timezone:
                params['timezone'] = timezone

        if params:
            changed = True
            self.cparams = camel_dict_to_snake_dict(params)
            if check_mode:
                return changed
        else:
            return changed

        r = self.api.tm.sys.ntp.load()
        r.update(**params)
        r.refresh()

        return changed

    def absent(self):
        changed = False
        params = dict()
        current = self.read()

        check_mode = self.params['check_mode']
        ntp_servers = self.params['ntp_servers']

        if not ntp_servers:
            raise F5ModuleError(
                "Absent can only be used when removing NTP servers"
            )

        if ntp_servers and 'servers' in current:
            servers = current['servers']
            new_servers = [x for x in servers if x not in ntp_servers]

            if servers != new_servers:
                params['servers'] = new_servers

        if params:
            changed = True
            self.cparams = camel_dict_to_snake_dict(params)
            if check_mode:
                return changed
        else:
            return changed

        r = self.api.tm.sys.ntp.load()
        r.update(**params)
        r.refresh()
        return changed


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        ntp_servers=dict(required=False, type='list', default=None),
        timezone=dict(default=None, required=False)
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['ntp_servers', 'timezone']
        ],
        supports_check_mode=True
    )

    try:
        obj = BigIpDeviceNtp(check_mode=module.check_mode, **module.params)
        result = obj.flush()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
