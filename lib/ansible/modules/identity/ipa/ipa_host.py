#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_host
author: Thomas Krahn (@Nosmoht)
short_description: Manage FreeIPA host
description:
- Add, modify and delete an IPA host using IPA API
options:
  fqdn:
    description:
    - Full qualified domain name.
    - Can not be changed as it is the unique identifier.
    required: true
    aliases: ["name"]
  description:
    description:
    - A description of this host.
  force:
    description:
    - Force host name even if not in DNS.
    required: false
    type: bool
  ip_address:
    description:
    - Add the host to DNS with this IP address.
  mac_address:
    description:
    - List of Hardware MAC address(es) off this host.
    - If option is omitted MAC addresses will not be checked or changed.
    - If an empty list is passed all assigned MAC addresses will be removed.
    - MAC addresses that are already assigned but not passed will be removed.
    aliases: ["macaddress"]
  ns_host_location:
    description:
    - Host location (e.g. "Lab 2")
    aliases: ["nshostlocation"]
  ns_hardware_platform:
    description:
    - Host hardware platform (e.g. "Lenovo T61")
    aliases: ["nshardwareplatform"]
  ns_os_version:
    description:
    - Host operating system and version (e.g. "Fedora 9")
    aliases: ["nsosversion"]
  user_certificate:
    description:
    - List of Base-64 encoded server certificates.
    - If option is omitted certificates will not be checked or changed.
    - If an empty list is passed all assigned certificates will be removed.
    - Certificates already assigned but not passed will be removed.
    aliases: ["usercertificate"]
  state:
    description: State to ensure
    default: present
    choices: ["present", "absent", "enabled", "disabled"]
  update_dns:
    description:
    - If set C("True") with state as C("absent"), then removes DNS records of the host managed by FreeIPA DNS.
    - This option has no effect for states other than "absent".
    default: false
    type: bool
    version_added: "2.5"
  random_password:
    description: Generate a random password to be used in bulk enrollment
    default: False
    type: bool
    version_added: '2.5'
extends_documentation_fragment: ipa.documentation
version_added: "2.3"
'''

EXAMPLES = '''
# Ensure host is present
- ipa_host:
    name: host01.example.com
    description: Example host
    ip_address: 192.168.0.123
    ns_host_location: Lab
    ns_os_version: CentOS 7
    ns_hardware_platform: Lenovo T61
    mac_address:
    - "08:00:27:E3:B1:2D"
    - "52:54:00:BD:97:1E"
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Generate a random password for bulk enrolment
- ipa_host:
    name: host01.example.com
    description: Example host
    ip_address: 192.168.0.123
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    validate_certs: False
    random_password: True

# Ensure host is disabled
- ipa_host:
    name: host01.example.com
    state: disabled
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure that all user certificates are removed
- ipa_host:
    name: host01.example.com
    user_certificate: []
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure host is absent
- ipa_host:
    name: host01.example.com
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure host and its DNS record is absent
- ipa_host:
    name: host01.example.com
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
    update_dns: True
'''

RETURN = '''
host:
  description: Host as returned by IPA API.
  returned: always
  type: dict
host_diff:
  description: List of options that differ and would be changed
  returned: if check mode and a difference is found
  type: list
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class HostIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(HostIPAClient, self).__init__(module, host, port, protocol)

    def host_show(self, name):
        return self._post_json(method='host_show', name=name)

    def host_find(self, name):
        return self._post_json(method='host_find', name=None, item={'all': True, 'fqdn': name})

    def host_add(self, name, host):
        return self._post_json(method='host_add', name=name, item=host)

    def host_mod(self, name, host):
        return self._post_json(method='host_mod', name=name, item=host)

    def host_del(self, name, update_dns):
        return self._post_json(method='host_del', name=name, item={'updatedns': update_dns})

    def host_disable(self, name):
        return self._post_json(method='host_disable', name=name)


def get_host_dict(description=None, force=None, ip_address=None, ns_host_location=None, ns_hardware_platform=None,
                  ns_os_version=None, user_certificate=None, mac_address=None, random_password=None):
    data = {}
    if description is not None:
        data['description'] = description
    if force is not None:
        data['force'] = force
    if ip_address is not None:
        data['ip_address'] = ip_address
    if ns_host_location is not None:
        data['nshostlocation'] = ns_host_location
    if ns_hardware_platform is not None:
        data['nshardwareplatform'] = ns_hardware_platform
    if ns_os_version is not None:
        data['nsosversion'] = ns_os_version
    if user_certificate is not None:
        data['usercertificate'] = [{"__base64__": item} for item in user_certificate]
    if mac_address is not None:
        data['macaddress'] = mac_address
    if random_password is not None:
        data['random'] = random_password
    return data


def get_host_diff(client, ipa_host, module_host):
    non_updateable_keys = ['force', 'ip_address']
    if not module_host.get('random'):
        non_updateable_keys.append('random')
    for key in non_updateable_keys:
        if key in module_host:
            del module_host[key]

    return client.get_diff(ipa_data=ipa_host, module_data=module_host)


def ensure(module, client):
    name = module.params['fqdn']
    state = module.params['state']

    ipa_host = client.host_find(name=name)
    module_host = get_host_dict(description=module.params['description'],
                                force=module.params['force'], ip_address=module.params['ip_address'],
                                ns_host_location=module.params['ns_host_location'],
                                ns_hardware_platform=module.params['ns_hardware_platform'],
                                ns_os_version=module.params['ns_os_version'],
                                user_certificate=module.params['user_certificate'],
                                mac_address=module.params['mac_address'],
                                random_password=module.params.get('random_password'),
                                )
    changed = False
    if state in ['present', 'enabled', 'disabled']:
        if not ipa_host:
            changed = True
            if not module.check_mode:
                # OTP password generated by FreeIPA is visible only for host_add command
                # so, return directly from here.
                return changed, client.host_add(name=name, host=module_host)
        else:
            diff = get_host_diff(client, ipa_host, module_host)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_host.get(key)
                    ipa_host_show = client.host_show(name=name)
                    if ipa_host_show.get('has_keytab', False) and module.params.get('random_password'):
                        client.host_disable(name=name)
                    return changed, client.host_mod(name=name, host=data)

    else:
        if ipa_host:
            changed = True
            update_dns = module.params.get('update_dns', False)
            if not module.check_mode:
                client.host_del(name=name, update_dns=update_dns)

    return changed, client.host_find(name=name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(description=dict(type='str'),
                         fqdn=dict(type='str', required=True, aliases=['name']),
                         force=dict(type='bool'),
                         ip_address=dict(type='str'),
                         ns_host_location=dict(type='str', aliases=['nshostlocation']),
                         ns_hardware_platform=dict(type='str', aliases=['nshardwareplatform']),
                         ns_os_version=dict(type='str', aliases=['nsosversion']),
                         user_certificate=dict(type='list', aliases=['usercertificate']),
                         mac_address=dict(type='list', aliases=['macaddress']),
                         update_dns=dict(type='bool'),
                         state=dict(type='str', default='present', choices=['present', 'absent', 'enabled', 'disabled']),
                         random_password=dict(type='bool'),)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    client = HostIPAClient(module=module,
                           host=module.params['ipa_host'],
                           port=module.params['ipa_port'],
                           protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, host = ensure(module, client)
        module.exit_json(changed=changed, host=host)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
