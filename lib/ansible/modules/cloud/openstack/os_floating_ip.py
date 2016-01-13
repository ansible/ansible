#!/usr/bin/python
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Author: Davide Guerri <davide.guerri@hp.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

try:
    import shade
    from shade import meta

    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_floating_ip
version_added: "2.0"
short_description: Add/Remove floating IP from an instance
extends_documentation_fragment: openstack
description:
   - Add or Remove a floating IP to an instance
options:
   server:
     description:
        - The name or ID of the instance to which the IP address
          should be assigned.
     required: true
   network:
     description:
        - The name or ID of a neutron external network or a nova pool name.
     required: false
   floating_ip_address:
     description:
        - A floating IP address to attach or to detach. Required only if state
          is absent. When state is present can be used to specify a IP address
          to attach.
     required: false
   reuse:
     description:
        - When state is present, and floating_ip_address is not present,
          this parameter can be used to specify whether we should try to reuse
          a floating IP address already allocated to the project.
     required: false
     default: false
   fixed_address:
     description:
        - To which fixed IP of server the floating IP address should be
          attached to.
     required: false
   wait:
     description:
        - When attaching a floating IP address, specify whether we should
          wait for it to appear as attached.
     required: false
     default: false
   timeout:
     description:
        - Time to wait for an IP address to appear as attached. See wait.
     required: false
     default: 60
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     required: false
     default: present
requirements: ["shade"]
'''

EXAMPLES = '''
# Assign a floating IP to the fist interface of `cattle001` from an exiting
# external network or nova pool. A new floating IP from the first available
# external network is allocated to the project.
- os_floating_ip:
     cloud: dguerri
     server: cattle001

# Assign a new floating IP to the instance fixed ip `192.0.2.3` of
# `cattle001`. If a free floating IP is already allocated to the project, it is
# reused; if not, a new one is created.
- os_floating_ip:
     cloud: dguerri
     state: present
     reuse: yes
     server: cattle001
     network: ext_net
     fixed_address: 192.0.2.3
     wait: true
     timeout: 180

# Detach a floating IP address from a server
- os_floating_ip:
     cloud: dguerri
     state: absent
     floating_ip_address: 203.0.113.2
     server: cattle001
'''


def _get_floating_ip(cloud, floating_ip_address):
    f_ips = cloud.search_floating_ips(
        filters={'floating_ip_address': floating_ip_address})
    if not f_ips:
        return None

    return f_ips[0]


def main():
    argument_spec = openstack_full_argument_spec(
        server=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
        network=dict(required=False, default=None),
        floating_ip_address=dict(required=False, default=None),
        reuse=dict(required=False, type='bool', default=False),
        fixed_address=dict(required=False, default=None),
        wait=dict(required=False, type='bool', default=False),
        timeout=dict(required=False, type='int', default=60),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    server_name_or_id = module.params['server']
    state = module.params['state']
    network = module.params['network']
    floating_ip_address = module.params['floating_ip_address']
    reuse = module.params['reuse']
    fixed_address = module.params['fixed_address']
    wait = module.params['wait']
    timeout = module.params['timeout']

    cloud = shade.openstack_cloud(**module.params)

    try:
        server = cloud.get_server(server_name_or_id)
        if server is None:
            module.fail_json(
                msg="server {0} not found".format(server_name_or_id))

        if state == 'present':
            server = cloud.add_ips_to_server(
                server=server, ips=floating_ip_address, ip_pool=network,
                reuse=reuse, fixed_address=fixed_address, wait=wait,
                timeout=timeout)
            fip_address = cloud.get_server_public_ip(server)
            # Update the floating IP status
            f_ip = _get_floating_ip(cloud, fip_address)
            module.exit_json(changed=True, floating_ip=f_ip)

        elif state == 'absent':
            if floating_ip_address is None:
                module.fail_json(msg="floating_ip_address is required")

            f_ip = _get_floating_ip(cloud, floating_ip_address)

            cloud.detach_ip_from_server(
                server_id=server['id'], floating_ip_id=f_ip['id'])
            # Update the floating IP status
            f_ip = cloud.get_floating_ip(id=f_ip['id'])
            module.exit_json(changed=True, floating_ip=f_ip)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *


if __name__ == '__main__':
    main()
