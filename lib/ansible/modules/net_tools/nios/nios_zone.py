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
from ansible.module_utils.net_tools.nios.api import get_provider_spec, Wapi

def main():
    """main entry point for module execution
    """
    grid_spec = dict(
        name=dict(required=True),
    )

    ib_spec = dict(
        fqdn=dict(required=True, aliases=['name'], ib_req=True),
        view=dict(default='default', aliases=['dns_view'], ib_req=True),

        grid_primary=dict(type='list', elements='dict', options=grid_spec),
        grid_secondaries=dict(type='list', elements='dict', options=grid_spec),

        extattrs=dict(type='dict'),
        comment=dict()
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
    result = wapi.run('zone_auth', ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
