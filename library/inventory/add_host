# -*- mode: python -*-

DOCUMENTATION = '''
---
module: add_host
short_description: add a host (and alternatively a group) to the ansible-playbook in-memory inventory
description:
  - Use variables to create new hosts and groups in inventory for use in later plays of the same playbook. 
    Takes variables so you can define the new hosts more fully.
version_added: "0.9"
options:
  name:
    aliases: [ 'hostname', 'host' ]
    description:
    - The hostname/ip of the host to add to the inventory, can include a colon and a port number.
    required: true     
  groups:
    aliases: [ 'groupname', 'group' ]
    description:
    - The groups to add the hostname to, comma separated.
    required: false
notes:
  - This module is most commonly used in conjunction with a C(with_) style loop
  - This module is commonly referred to as a host list bypass plugin. This
    means that add_host will not execute for every host targeted by a playbook.
    Instead add_host will only execute on the first host in the hosts
    list as defined by inventory.
  - For instances where you need to dynamically add all hosts targeted by a
    playbook to a group for later use, the C(group_by) module is
    potentially the better choice.
author: Seth Vidal
'''

EXAMPLES = '''
# add host to group 'just_created' with variable foo=42
- add_host: name={{ ip_from_ec2 }} groups=just_created foo=42

# add a host with a non-standard port local to your machines
- add_host: name={{ new_ip }}:{{ new_port }}

# add a host alias that we reach through a tunnel
- add_host: hostname={{ new_ip }}
            ansible_ssh_host={{ inventory_hostname }}
            ansible_ssh_port={{ new_port }}
'''
