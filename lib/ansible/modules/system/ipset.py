#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Susant Sahani <susant@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipset
short_description: Automates ipset
description:
    - Allows you to setup rules to quickly and easily block sets of ip addresses.
version_added: "2.8"
options:
    ipset_name:
        description:
            - creating a new "set" of network addresses.
    hash_type:
       description: What kind of set
       choices: [ "hash:net", "hash:ip", "hash:mac", "hash:ip,mac", "hash:net,net", "hash:ip,port",
                  "hash:net,port", "hash:ip,port,ip", "hash:ip,port,net", "hash:ip,mark", "hash:net,port,net",
                  "hash:net,iface" ]
    keys:
        description:
            - Space separated list of keys according to the hash type.
    state:
        description:
            - Whether set or address/network creates or added.
        choices: [ "add", "delete", "destroy", "create" ]
author: "Susant Sahani (@ssahani) <susant@redhat.com>"
'''

EXAMPLES = '''
# Create hashset
- ipset:
       ipset_name: test3
       hash_type:  hash:ip
       state: create

# Add ip address to hashset
- ipset:
       ipset_name: test3
       keys: "10.65.208.22 10.65.208.26 10.65.208.28"
       state: add

# Delete ip address from hashset
- ipset:
        ipset_name: test3
        keys: "10.65.208.22"
        state: delete

# Delete hashset
- ipset:
       ipset_name: test3
       state: destroy
'''

RETURN = r'''
'''

from ansible.module_utils.basic import get_platform, AnsibleModule


class IpsetModule(object):

    def __init__(self, module):
        self.module = module
        self.args = self.module.params
        self.ipset_cmd = self.module.get_bin_path('ipset', required=True)
        self.ipset_name = module.params['ipset_name']
        self.hash_type = module.params['hash_type']
        self.keys = module.params['keys']
        self.state = module.params['state']
        self.changed = False

    def ipset_add_address(self):
        rc = ''

        list_keys = self.keys.split(' ')
        for key in list_keys:
            cmd = "%s add %s %s" % (self.ipset_cmd, self.ipset_name, key)
            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to add %s to hash %s: %s' % (key, self.ipset_name, out + err))

        return rc

    def ipset_delete_address(self):
        rc = ''

        list_keys = self.keys.split(' ')
        for key in list_keys:
            cmd = "%s del %s %s" % (self.ipset_cmd, self.ipset_name, key)

            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to delete %s to hash %s: %s' % (key, self.ipset_name, out + err))

        return rc

    def ipset_create_hashset(self):
        cmd = "%s create %s %s" % (self.ipset_cmd, self.ipset_name, self.hash_type)

        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Failed to create ipset %s: %s' % (self.ipset_name, out + err))
        else:
            return rc

    def ipset_destroy_hashset(self):
        cmd = "%s destroy %s" % (self.ipset_cmd, self.ipset_name)

        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Failed to destroy ipset %s: %s' % (self.ipset_name, out + err))
        else:
            return rc

    def configure_ipset(self):
        rc = False

        if self.state == 'create':
            rc = self.ipset_create_hashset()
        elif self.state == 'destroy':
            rc = self.ipset_destroy_hashset()
        elif self.state == 'add':
            rc = self.ipset_add_address()
        elif self.state == 'delete':
            rc = self.ipset_delete_address()

        return rc


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ipset_name=dict(required=True, type='str'),
            hash_type=dict(choices=['hash:net', 'hash:ip', 'hash:mac', 'hash:ip,mac', 'hash:net,net',
                                    'hash:ip,port', 'hash:net,port', 'hash:ip,port,ip', 'hash:ip,port,net',
                                    'hash:ip,mark', 'hash:net,port,net', 'hash:net,iface'],
                           required=False, default=None, type='str'),
            keys=dict(required=False, default=None, type='str'),
            state=dict(choices=['add', 'delete', 'destroy', 'create'], required=True),
        ),
        supports_check_mode=False
    )

    ipset_name = module.params['ipset_name']
    hash_type = module.params['hash_type']
    keys = module.params['keys']
    state = module.params['state']

    if ipset_name is None:
        module.fail_json(msg='ipset_name cannot be None')

    if state == 'create' and hash_type is None:
        module.fail_json(msg='hash_type cannot be None when state is create')

    if keys is None:
        if state == 'add' or state == 'delete':
            module.fail_json(msg='Keys cannot None when state is add or delete')

    ipset = IpsetModule(module)
    result = ipset.configure_ipset()

    module.exit_json(changed=result)


if __name__ == '__main__':
    main()
