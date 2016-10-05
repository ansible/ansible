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
module: bigip_device_dns
short_description: Manage BIG-IP device DNS settings
description:
  - Manage BIG-IP device DNS settings
version_added: "2.2"
options:
  cache:
    description:
      - Specifies whether the system caches DNS lookups or performs the
        operation each time a lookup is needed. Please note that this applies
        only to Access Policy Manager features, such as ACLs, web application
        rewrites, and authentication.
    required: false
    default: disable
    choices:
       - enable
       - disable
  name_servers:
    description:
      - A list of name serverz that the system uses to validate DNS lookups
  forwarders:
    description:
      - A list of BIND servers that the system can use to perform DNS lookups
  search:
    description:
      - A list of domains that the system searches for local domain lookups,
        to resolve local host names.
  ip_version:
    description:
      - Specifies whether the DNS specifies IP addresses using IPv4 or IPv6.
    required: false
    choices:
      - 4
      - 6
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that an existing variable is set to C(value).
    required: false
    default: present
    choices:
      - absent
      - present
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install requests
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Set the DNS settings on the BIG-IP
  bigip_device_dns:
      name_servers:
          - 208.67.222.222
          - 208.67.220.220
      search:
          - localdomain
          - lab.local
      state: present
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost
'''

RETURN = '''
cache:
    description: The new value of the DNS caching
    returned: changed
    type: string
    sample: "enabled"
name_servers:
    description: List of name servers that were added or removed
    returned: changed
    type: list
    sample: "['192.0.2.10', '172.17.12.10']"
forwarders:
    description: List of forwarders that were added or removed
    returned: changed
    type: list
    sample: "['192.0.2.10', '172.17.12.10']"
search:
    description: List of search domains that were added or removed
    returned: changed
    type: list
    sample: "['192.0.2.10', '172.17.12.10']"
ip_version:
    description: IP version that was set that DNS will specify IP addresses in
    returned: changed
    type: int
    sample: 4
'''

try:
    from f5.bigip.contexts import TransactionContextManager
    from f5.bigip import ManagementRoot
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


REQUIRED = ['name_servers', 'search', 'forwarders', 'ip_version', 'cache']
CACHE = ['disable', 'enable']
IP = [4, 6]


class BigIpDeviceDns(object):
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

        if self.dhcp_enabled():
            raise F5ModuleError(
                "DHCP on the mgmt interface must be disabled to make use of " +
                "this module"
            )

        if state == 'absent':
            changed = self.absent()
        else:
            changed = self.present()

        result.update(**self.cparams)
        result.update(dict(changed=changed))
        return result

    def dhcp_enabled(self):
        r = self.api.tm.sys.dbs.db.load(name='dhclient.mgmt')
        if r.value == 'enable':
            return True
        else:
            return False

    def read(self):
        result = dict()

        cache = self.api.tm.sys.dbs.db.load(name='dns.cache')
        proxy = self.api.tm.sys.dbs.db.load(name='dns.proxy.__iter__')
        dns = self.api.tm.sys.dns.load()

        result['cache'] = str(cache.value)
        result['forwarders'] = str(proxy.value).split(' ')

        if hasattr(dns, 'nameServers'):
            result['name_servers'] = dns.nameServers
        if hasattr(dns, 'search'):
            result['search'] = dns.search
        if hasattr(dns, 'include') and 'options inet6' in dns.include:
            result['ip_version'] = 6
        else:
            result['ip_version'] = 4
        return result

    def present(self):
        params = dict()
        current = self.read()

        # Temporary locations to hold the changed params
        update = dict(
            dns=None,
            forwarders=None,
            cache=None
        )

        nameservers = self.params['name_servers']
        search_domains = self.params['search']
        ip_version = self.params['ip_version']
        forwarders = self.params['forwarders']
        cache = self.params['cache']
        check_mode = self.params['check_mode']

        if nameservers:
            if 'name_servers' in current:
                if nameservers != current['name_servers']:
                    params['nameServers'] = nameservers
            else:
                params['nameServers'] = nameservers

        if search_domains:
            if 'search' in current:
                if search_domains != current['search']:
                    params['search'] = search_domains
            else:
                params['search'] = search_domains

        if ip_version:
            if 'ip_version' in current:
                if ip_version != int(current['ip_version']):
                    if ip_version == 6:
                        params['include'] = 'options inet6'
                    elif ip_version == 4:
                        params['include'] = ''
            else:
                if ip_version == 6:
                    params['include'] = 'options inet6'
                elif ip_version == 4:
                    params['include'] = ''

        if params:
            self.cparams.update(camel_dict_to_snake_dict(params))

            if 'include' in params:
                del self.cparams['include']
                if params['include'] == '':
                    self.cparams['ip_version'] = 4
                else:
                    self.cparams['ip_version'] = 6

            update['dns'] = params.copy()
            params = dict()

        if forwarders:
            if 'forwarders' in current:
                if forwarders != current['forwarders']:
                    params['forwarders'] = forwarders
            else:
                params['forwarders'] = forwarders

        if params:
            self.cparams.update(camel_dict_to_snake_dict(params))
            update['forwarders'] = ' '.join(params['forwarders'])
            params = dict()

        if cache:
            if 'cache' in current:
                if cache != current['cache']:
                    params['cache'] = cache

        if params:
            self.cparams.update(camel_dict_to_snake_dict(params))
            update['cache'] = params['cache']
            params = dict()

        if self.cparams:
            changed = True
            if check_mode:
                return changed
        else:
            return False

        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            cache = api.tm.sys.dbs.db.load(name='dns.cache')
            proxy = api.tm.sys.dbs.db.load(name='dns.proxy.__iter__')
            dns = api.tm.sys.dns.load()

            # Empty values can be supplied, but you cannot supply the
            # None value, so we check for that specifically
            if update['cache'] is not None:
                cache.update(value=update['cache'])
            if update['forwarders'] is not None:
                proxy.update(value=update['forwarders'])
            if update['dns'] is not None:
                dns.update(**update['dns'])
        return changed

    def absent(self):
        params = dict()
        current = self.read()

        # Temporary locations to hold the changed params
        update = dict(
            dns=None,
            forwarders=None
        )

        nameservers = self.params['name_servers']
        search_domains = self.params['search']
        forwarders = self.params['forwarders']
        check_mode = self.params['check_mode']

        if forwarders and 'forwarders' in current:
            set_current = set(current['forwarders'])
            set_new = set(forwarders)

            forwarders = set_current - set_new
            if forwarders != set_current:
                forwarders = list(forwarders)
                params['forwarders'] = ' '.join(forwarders)

        if params:
            changed = True
            self.cparams.update(camel_dict_to_snake_dict(params))
            update['forwarders'] = params['forwarders']
            params = dict()

        if nameservers and 'name_servers' in current:
            set_current = set(current['name_servers'])
            set_new = set(nameservers)

            nameservers = set_current - set_new
            if nameservers != set_current:
                params['nameServers'] = list(nameservers)

        if search_domains and 'search' in current:
            set_current = set(current['search'])
            set_new = set(search_domains)

            search_domains = set_current - set_new
            if search_domains != set_current:
                params['search'] = list(search_domains)

        if params:
            changed = True
            self.cparams.update(camel_dict_to_snake_dict(params))
            update['dns'] = params.copy()
            params = dict()

        if not self.cparams:
            return False

        if check_mode:
            return changed

        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            proxy = api.tm.sys.dbs.db.load(name='dns.proxy.__iter__')
            dns = api.tm.sys.dns.load()

            if update['forwarders'] is not None:
                proxy.update(value=update['forwarders'])
            if update['dns'] is not None:
                dns.update(**update['dns'])
        return changed


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        cache=dict(required=False, choices=CACHE, default=None),
        name_servers=dict(required=False, default=None, type='list'),
        forwarders=dict(required=False, default=None, type='list'),
        search=dict(required=False, default=None, type='list'),
        ip_version=dict(required=False, default=None, choices=IP, type='int')
    )
    argument_spec.update(meta_args)
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[REQUIRED],
        supports_check_mode=True
    )

    try:
        obj = BigIpDeviceDns(check_mode=module.check_mode, **module.params)
        result = obj.flush()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
