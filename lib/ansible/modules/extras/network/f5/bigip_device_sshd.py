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
module: bigip_device_sshd
short_description: Manage the SSHD settings of a BIG-IP
description:
  - Manage the SSHD settings of a BIG-IP
version_added: "2.2"
options:
  allow:
    description:
      - Specifies, if you have enabled SSH access, the IP address or address
        range for other systems that can use SSH to communicate with this
        system.
    choices:
      - all
      - IP address, such as 172.27.1.10
      - IP range, such as 172.27.*.* or 172.27.0.0/255.255.0.0
  banner:
    description:
      - Whether to enable the banner or not.
    required: false
    choices:
      - enabled
      - disabled
  banner_text:
    description:
      - Specifies the text to include on the pre-login banner that displays
        when a user attempts to login to the system using SSH.
    required: false
  inactivity_timeout:
    description:
      - Specifies the number of seconds before inactivity causes an SSH
        session to log out.
    required: false
  log_level:
    description:
      - Specifies the minimum SSHD message level to include in the system log.
    choices:
      - debug
      - debug1
      - debug2
      - debug3
      - error
      - fatal
      - info
      - quiet
      - verbose
  login:
    description:
      - Specifies, when checked C(enabled), that the system accepts SSH
        communications.
    choices:
      - enabled
      - disabled
    required: false
  port:
    description:
      - Port that you want the SSH daemon to run on.
    required: false
notes:
  - Requires the f5-sdk Python package on the host This is as easy as pip
    install f5-sdk.
  - Requires BIG-IP version 12.0.0 or greater
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Set the banner for the SSHD service from a string
  bigip_device_sshd:
      banner: "enabled"
      banner_text: "banner text goes here"
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
  delegate_to: localhost

- name: Set the banner for the SSHD service from a file
  bigip_device_sshd:
      banner: "enabled"
      banner_text: "{{ lookup('file', '/path/to/file') }}"
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
  delegate_to: localhost

- name: Set the SSHD service to run on port 2222
  bigip_device_sshd:
      password: "secret"
      port: 2222
      server: "lb.mydomain.com"
      user: "admin"
  delegate_to: localhost
'''

RETURN = '''
allow:
    description: >
        Specifies, if you have enabled SSH access, the IP address or address
        range for other systems that can use SSH to communicate with this
        system.
    returned: changed
    type: string
    sample: "192.0.2.*"
banner:
    description: Whether the banner is enabled or not.
    returned: changed
    type: string
    sample: "true"
banner_text:
    description: >
        Specifies the text included on the pre-login banner that
        displays when a user attempts to login to the system using SSH.
    returned: changed and success
    type: string
    sample: "This is a corporate device. Connecting to it without..."
inactivity_timeout:
    description: >
        The number of seconds before inactivity causes an SSH.
        session to log out
    returned: changed
    type: int
    sample: "10"
log_level:
    description: The minimum SSHD message level to include in the system log.
    returned: changed
    type: string
    sample: "debug"
login:
    description: Specifies that the system accepts SSH communications or not.
    return: changed
    type: bool
    sample: true
port:
    description: Port that you want the SSH daemon to run on.
    return: changed
    type: int
    sample: 22
'''

try:
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

CHOICES = ['enabled', 'disabled']
LEVELS = ['debug', 'debug1', 'debug2', 'debug3', 'error', 'fatal', 'info',
          'quiet', 'verbose']


class BigIpDeviceSshd(object):
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

    def update(self):
        changed = False
        current = self.read()
        params = dict()

        allow = self.params['allow']
        banner = self.params['banner']
        banner_text = self.params['banner_text']
        timeout = self.params['inactivity_timeout']
        log_level = self.params['log_level']
        login = self.params['login']
        port = self.params['port']
        check_mode = self.params['check_mode']

        if allow:
            if 'allow' in current:
                items = set(allow)
                if items != current['allow']:
                    params['allow'] = list(items)
            else:
                params['allow'] = allow

        if banner:
            if 'banner' in current:
                if banner != current['banner']:
                    params['banner'] = banner
            else:
                params['banner'] = banner

        if banner_text:
            if 'banner_text' in current:
                if banner_text != current['banner_text']:
                    params['bannerText'] = banner_text
            else:
                params['bannerText'] = banner_text

        if timeout:
            if 'inactivity_timeout' in current:
                if timeout != current['inactivity_timeout']:
                    params['inactivityTimeout'] = timeout
            else:
                params['inactivityTimeout'] = timeout

        if log_level:
            if 'log_level' in current:
                if log_level != current['log_level']:
                    params['logLevel'] = log_level
            else:
                params['logLevel'] = log_level

        if login:
            if 'login' in current:
                if login != current['login']:
                    params['login'] = login
            else:
                params['login'] = login

        if port:
            if 'port' in current:
                if port != current['port']:
                    params['port'] = port
            else:
                params['port'] = port

        if params:
            changed = True
            if check_mode:
                return changed
            self.cparams = camel_dict_to_snake_dict(params)
        else:
            return changed

        r = self.api.tm.sys.sshd.load()
        r.update(**params)
        r.refresh()

        return changed

    def read(self):
        """Read information and transform it

        The values that are returned by BIG-IP in the f5-sdk can have encoding
        attached to them as well as be completely missing in some cases.

        Therefore, this method will transform the data from the BIG-IP into a
        format that is more easily consumable by the rest of the class and the
        parameters that are supported by the module.
        """
        p = dict()
        r = self.api.tm.sys.sshd.load()

        if hasattr(r, 'allow'):
            # Deliberately using sets to supress duplicates
            p['allow'] = set([str(x) for x in r.allow])
        if hasattr(r, 'banner'):
            p['banner'] = str(r.banner)
        if hasattr(r, 'bannerText'):
            p['banner_text'] = str(r.bannerText)
        if hasattr(r, 'inactivityTimeout'):
            p['inactivity_timeout'] = str(r.inactivityTimeout)
        if hasattr(r, 'logLevel'):
            p['log_level'] = str(r.logLevel)
        if hasattr(r, 'login'):
            p['login'] = str(r.login)
        if hasattr(r, 'port'):
            p['port'] = int(r.port)
        return p

    def flush(self):
        result = dict()
        changed = False

        try:
            changed = self.update()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.cparams)
        result.update(dict(changed=changed))
        return result


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        allow=dict(required=False, default=None, type='list'),
        banner=dict(required=False, default=None, choices=CHOICES),
        banner_text=dict(required=False, default=None),
        inactivity_timeout=dict(required=False, default=None, type='int'),
        log_level=dict(required=False, default=None, choices=LEVELS),
        login=dict(required=False, default=None, choices=CHOICES),
        port=dict(required=False, default=None, type='int'),
        state=dict(default='present', choices=['present'])
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    try:
        obj = BigIpDeviceSshd(check_mode=module.check_mode, **module.params)
        result = obj.flush()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
