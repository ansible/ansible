#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
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
module: vmware_dns_config
short_description: Manage VMware ESXi DNS Configuration
description:
    - Manage VMware ESXi DNS Configuration
version_added: 2.0
author: "Joseph Callen (@jcpowermac)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    change_hostname_to:
        description:
            - The hostname that an ESXi host should be changed to.
        required: True
    domainname:
        description:
            - The domain the ESXi host should be apart of.
        required: True
    dns_servers:
        description:
            - The DNS servers that the host should be configured to use.
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Example vmware_dns_config command from Ansible Playbooks
- name: Configure ESXi hostname and DNS servers
  local_action:
    module: vmware_dns_config
    hostname: esxi_hostname
    username: root
    password: your_password
    change_hostname_to: esx01
    domainname: foo.org
    dns_servers:
        - 8.8.8.8
        - 8.8.4.4
'''
try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def configure_dns(host_system, hostname, domainname, dns_servers):

    changed = False
    host_config_manager = host_system.configManager
    host_network_system = host_config_manager.networkSystem
    config = host_network_system.dnsConfig

    config.dhcp = False

    if config.address != dns_servers:
        config.address = dns_servers
        changed = True
    if config.domainName != domainname:
        config.domainName = domainname
        changed = True
    if config.hostName != hostname:
        config.hostName = hostname
        changed = True
    if changed:
        host_network_system.UpdateDnsConfig(config)

    return changed


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(change_hostname_to=dict(required=True, type='str'),
                         domainname=dict(required=True, type='str'),
                         dns_servers=dict(required=True, type='list')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    change_hostname_to = module.params['change_hostname_to']
    domainname = module.params['domainname']
    dns_servers = module.params['dns_servers']
    try:
        content = connect_to_api(module)
        host = get_all_objs(content, [vim.HostSystem])
        if not host:
            module.fail_json(msg="Unable to locate Physical Host.")
        host_system = host.keys()[0]
        changed = configure_dns(host_system, change_hostname_to, domainname, dns_servers)
        module.exit_json(changed=changed)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
