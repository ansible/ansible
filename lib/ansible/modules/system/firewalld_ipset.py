#!/usr/bin/python

# Copyright: (c) 2018, [rwaweber]
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: firewalld_ipset

short_description: A module to manage firewalld ipsets

description:
  - This module utilizes the firewalld python client to manipulate and manage
    the existence of ipsets. These can be ipv4, ipv6, and mac addresses. It is
    particularly useful if you take advantage of the firewalld zone model.

version_added: "2.8"

author: Will Weber (@rwaweber)

options:
  name:
    description: A name for the given ipset
    required: True
    type: str
  settype:
    description:
      - A type declaration for the given set of addresses. Supported types can
        be found in the firewalld code
        https://github.com/firewalld/firewalld/blob/master/src/firewall/core/ipset.py#L36.
        Typical usage with ips or mac addresses will use either a "hash:ip"
        or "hash:mac" option.
    required: True
    choices:
      - "hash:ip"
      - "hash:ip,port"
      - "hash:ip,port,ip"
      - "hash:ip,port,net"
      - "hash:ip,mark"
      - "hash:net"
      - "hash:net,net"
      - "hash:net,port"
      - "hash:net,port,net"
      - "hash:net,iface"
      - "hash:mac"
  state:
    description: The desired state of the ipset
    required: True
    choices: [ "present", "absent" ]
  permanent:
    description: Should the changes be applied permanently
    required: False
    default: False
    type: bool
  immediate:
    description: Should the changes be applied immediately
    required: False
    default: False
    type: bool
  addresses:
    description: The list of addresses to be added or removed from the ipset. This can be ipv4, ipv6, and mac addresses.
    required: False
    type: list

requirements:
  - Firewalld python client library on the remote.

notes:
  - Not tested on any Debian based system.
  - Requires the python2 bindings of firewalld, which may not be installed by default.
  - For distributions where the python2 firewalld bindings are unavailable (e.g Fedora 28 and later) you will have to set the
    ansible_python_interpreter for these hosts to the python3 interpreter path and install the python3 bindings.
'''

EXAMPLES = '''
# this could be useful to pair with an ASN lookup somewhere else
- name: Create an ipset for blocked addresses
  firewalld_ipset:
    name: blocklist
    state: present
    settype: "hash:ip"
    permanent: true
    immediate: true
    addresses:
      - 192.168.10.1
      - 192.168.10.5
      - 192.168.128.1/17

# known bad mac addresses
- name: Create an ipset for blocked mac addresses
  firewalld_ipset:
    name: blocklist-mac
    state: absent
    settype: "hash:mac"
    permanent: true
    immediate: true
    addresses:
      - f0:50:80:90:00:ab
      - f0:50:80:90:00:ac
      - f0:50:80:90:00:ad
      - f0:50:80:90:00:ae
      - f0:50:80:90:00:af

# Known safe client ranges
- name: Create an ipset for allowed addresses
  firewalld_ipset:
    name: allowlist
    state: absent
    settype: "hash:ip"
    permanent: true
    immediate: true
    addresses:
      - 10.0.0.1/16

# block the bad sets
- name: Block inbound traffic from the ipsets we wish to block
  firewalld:
    source: "{{ item }}"
    zone: block
    state: enabled
    immediate: true
    permanent: true
  with_items:
    - 'ipset:blocklist'
    - 'ipset:blocklist-mac'

# Allow from clients we have authorized to the internal zone
- name: Allow traffic from the allowlist to the internal zone
  firewalld:
    source: 'ipset:allowlist'
    zone: internal
    state: enabled
    immediate: true
    permanent: true

# expose a sensitive service to the authorized clients
- name: expose port 3000 on internal zone, now authorized clients can reach
  firewalld:
    port: 3000/tcp
    zone: internal
    state: enabled
    immediate: true
    permanent: true
'''

RETURN = '''
changed:
  description: was the state modified after execution
  returned: always
  type: bool
  sample: true
firewalld_ipset_name:
  description: The name of the specified ipset
  returned: always
  type: str
  sample: the-authorized-clients
firewalld_ipset_addresses:
  description: the list of addresses we are looking to manipulate for an ipset
  returned: always
  type: list
  sample: [ "8.8.8.8", "1.1.1.1", "8.8.7.7" ]
'''


from ansible.module_utils.basic import AnsibleModule

try:
    from firewall.client import FirewallClient
    from firewall.client import FirewallClientIPSetSettings
except ImportError:
    # not sure of the best way to handle these imports -- maybe importing
    # FirewallTransaction?
    pass


def firewalld_state(client, indata):
    if indata['immediate']:
        client.reload()
    if indata['permanent']:
        client.runtimeToPermanent()


def run():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(choices=['present', 'absent'], required=True),
        settype=dict(choices=[
            "hash:ip", "hash:ip,port", "hash:ip,port,ip",
            "hash:ip,port,net", "hash:ip,mark",
            "hash:net", "hash:net,net",
            "hash:net,port", "hash:net,port,net", "hash:net,iface",
            "hash:mac"
        ], required=True),
        permanent=dict(type='bool', required=False, default=False),
        immediate=dict(type='bool', required=False, default=False),
        addresses=dict(type='list', required=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # setup the FirewallDClient
    client = FirewallClient()
    sets = client.getIPSets()
    settings = FirewallClientIPSetSettings()
    settings.setType(module.params['settype'])
    config = client.config()

    # construct return data
    result = {
        "changed": False,
        "firewalld_ipset_name": module.params['name'],
        "firewalld_ipset_addresses": module.params['addresses']
    }

    if module.check_mode:
        return result

    # Modifying a preexisting ipset
    if module.params['name'] in sets and module.params['state'] == 'present':
        client_ipset_config = config.getIPSetByName(module.params['name'])
        original_entries = client_ipset_config.getEntries()
        client_ipset_config.setEntries(module.params['addresses'])
        firewalld_state(client, module.params)
        new_entries = client_ipset_config.getEntries()
        result['changed'] = (new_entries != original_entries)
        result['firewalld_ipset_addresses'] = new_entries

    # Creating a new ipset because the one proposed in the module declaration
    # does not exist already.
    elif module.params['name'] not in sets and module.params['state'] == 'present':
        client_ipset_config = config.addIPSet(module.params['name'], settings)
        original_entries = client_ipset_config.getEntries()
        client_ipset_config.setEntries(module.params['addresses'])
        firewalld_state(client, module.params)
        new_entries = client_ipset_config.getEntries()
        result['changed'] = (new_entries != original_entries)
        result['firewalld_ipset_addresses'] = new_entries

    # Removing an ipset that exists right now. If an ipset is asked to be
    # removed when it doesn't exist, we should just return an "unchanged"
    # state.
    elif module.params['name'] in sets and module.params['state'] == 'absent':
        client_ipset_config = config.getIPSetByName(module.params['name'])
        original_entries = client_ipset_config.remove()
        firewalld_state(client, module.params)
        result['changed'] = True

    module.exit_json(**result)


def main():
    run()


if __name__ == '__main__':
    main()
