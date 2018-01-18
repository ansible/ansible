#!/usr/bin/python
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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
"""

EXAMPLES = """
"""

RETURN = """
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.net_tools.nios.api import get_provider_spec, Wapi


def ipaddr(module, key, filtered_keys=None):
    ''' Transforms the input value into a struct supported by WAPI

    This function will transform the input from the playbook into a struct
    that is valid for WAPI in the form of:

        {
            ipv4addr: <value>,
            mac: <value>
        }

    This function does not validate the values are properly formatted or in
    the acceptable range, that is left to WAPI.
    '''
    filtered_keys = filtered_keys or list()
    objects = list()
    for item in module.params[key]:
        objects.append(dict([(k, v) for k, v in iteritems(item) if v is not None and k not in filtered_keys]))
    import q; q(objects)
    return objects

def ipv4addrs(module):
    return ipaddr(module, 'ipv4addrs', filtered_keys=['address'])

def ipv6addrs(module):
    return ipaddr(module, 'ipv6addrs', filtered_keys=['address'])


def main():
    """main entry point for module execution
    """
    ipv4addr_spec = dict(
        ipv4addr=dict(required=True, aliases=['address'], ib_req=True),
        mac=dict()
    )

    ipv6addr_spec = dict(
        ipv6addr=dict(required=True, aliases=['address'], ib_req=True)
    )

    ib_spec = dict(
        name=dict(required=True, ib_req=True),
        view=dict(default='default', aliases=['dns_view'], ib_req=True),

        ipv4addrs=dict(type='list', aliases=['ipv4'], elements='dict', options=ipv4addr_spec, transform=ipv4addrs),
        ipv6addrs=dict(type='list', aliases=['ipv6'], elements='dict', options=ipv6addr_spec, transform=ipv6addrs),

        ttl=dict(type='int'),

        extattrs=dict(type='dict'),
        comment=dict(),
    )

    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)
    argument_spec.update(get_provider_spec())

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    wapi = Wapi(module)
    result = wapi.run('record:host', ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
