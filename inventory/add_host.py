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
    - This module bypasses the play host loop and only runs once for all the hosts in the play, if you need it
      to iterate use a with_ directive.
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
