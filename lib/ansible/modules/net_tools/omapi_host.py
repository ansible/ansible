#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Loic Blot <loic.blot@unix-experience.fr>
# Sponsored by Infopro Digital. http://www.infopro-digital.com/
# Sponsored by E.T.A.I. http://www.etai.fr/
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: omapi_host

short_description: Setup OMAPI hosts.
description:
    - Create, update and remove OMAPI hosts into compatible DHCPd servers.
version_added: "2.3"
requirements:
  - pypureomapi
author: "Loic Blot (@nerzhul)"
options:
    state:
        description:
            - Create or remove OMAPI host.
        required: true
        choices: ['present', 'absent']
    name:
        description:
            - Sets the host lease hostname (mandatory if state=present).
        default: None
    host:
        description:
            - Sets OMAPI server host to interact with.
        default: localhost
    port:
        description:
            - Sets the OMAPI server port to interact with.
        default: 7911
    key_name:
        description:
            - Sets the TSIG key name for authenticating against OMAPI server.
        required: true
    key:
        description:
            - Sets the TSIG key content for authenticating against OMAPI server.
        required: true
    macaddr:
        description:
            - Sets the lease host MAC address.
        required: true
    ip:
        description:
            - Sets the lease host IP address.
        required: false
        default: None
    statements:
        description:
            - Attach a list of OMAPI DHCP statements with host lease (without ending semicolon).
        required: false
        default: []
    ddns:
        description:
            - Enable dynamic DNS updates for this host.
        required: false
        default: false

'''
EXAMPLES = '''
- name: Remove a host using OMAPI
  omapi_host:
    key_name: "defomapi"
    key: "+bFQtBCta6j2vWkjPkNFtgA=="
    host: "10.1.1.1"
    macaddr: "00:66:ab:dd:11:44"
    state: absent

- name: Add a host using OMAPI
  omapi_host:
    key_name: "defomapi"
    key: "+bFQtBCta6j2vWkjPkNFtgA=="
    host: "10.98.4.55"
    macaddr: "44:dd:ab:dd:11:44"
    name: "server01"
    ip: "192.168.88.99"
    ddns: yes
    statements:
      - 'filename "pxelinux.0"'
      - 'next-server 1.1.1.1'
    state: present
'''

RETURN = '''
changed:
    description: If module has modified a host
    returned: success
    type: string
lease:
    description: dictionary containing host information
    returned: success
    type: complex
    contains:
        ip-address:
            description: IP address, if there is.
            returned: success
            type: string
            sample: '192.168.1.5'
        hardware-address:
            description: MAC address
            returned: success
            type: string
            sample: '00:11:22:33:44:55'
        hardware-type:
            description: hardware type, generally '1'
            returned: success
            type: int
            sample: 1
        name:
            description: hostname
            returned: success
            type: string
            sample: 'mydesktop'
'''

import binascii
import socket
import struct
import traceback

try:
    from pypureomapi import Omapi, OmapiMessage, OmapiError, OmapiErrorNotFound
    from pypureomapi import pack_ip, unpack_ip, pack_mac, unpack_mac
    from pypureomapi import OMAPI_OP_STATUS, OMAPI_OP_UPDATE
    pureomapi_found = True
except ImportError:
    pureomapi_found = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native


class OmapiHostManager:
    def __init__(self, module):
        self.module = module
        self.omapi = None
        self.connect()

    def connect(self):
        try:
            self.omapi = Omapi(self.module.params['host'], self.module.params['port'], self.module.params['key_name'],
                               self.module.params['key'])
        except binascii.Error:
            self.module.fail_json(msg="Unable to open OMAPI connection. 'key' is not a valid base64 key.")
        except OmapiError as e:
            self.module.fail_json(msg="Unable to open OMAPI connection. Ensure 'host', 'port', 'key' and 'key_name' "
                                      "are valid. Exception was: %s" % to_native(e))
        except socket.error as e:
            self.module.fail_json(msg="Unable to connect to OMAPI server: %s" % to_native(e))

    def get_host(self, macaddr):
        msg = OmapiMessage.open(to_bytes("host", errors='surrogate_or_strict'))
        msg.obj.append((to_bytes("hardware-address", errors='surrogate_or_strict'), pack_mac(macaddr)))
        msg.obj.append((to_bytes("hardware-type", errors='surrogate_or_strict'), struct.pack("!I", 1)))
        response = self.omapi.query_server(msg)
        if response.opcode != OMAPI_OP_UPDATE:
            return None
        return response

    @staticmethod
    def unpack_facts(obj):
        result = dict(obj)
        if 'hardware-address' in result:
            result['hardware-address'] = unpack_mac(result['hardware-address'])

        if 'ip-address' in result:
            result['ip-address'] = unpack_ip(result['ip-address'])

        if 'hardware-type' in result:
            result['hardware-type'] = struct.unpack("!I", result['hardware-type'])

        return result

    def setup_host(self):
        if self.module.params['hostname'] is None or len(self.module.params['hostname']) == 0:
            self.module.fail_json(msg="name attribute could not be empty when adding or modifying host.")

        msg = None
        host_response = self.get_host(self.module.params['macaddr'])
        # If host was not found using macaddr, add create message
        if host_response is None:
            msg = OmapiMessage.open(to_bytes('host', errors='surrogate_or_strict'))
            msg.message.append(('create', struct.pack('!I', 1)))
            msg.message.append(('exclusive', struct.pack('!I', 1)))
            msg.obj.append(('hardware-address', pack_mac(self.module.params['macaddr'])))
            msg.obj.append(('hardware-type', struct.pack('!I', 1)))
            msg.obj.append(('name', self.module.params['hostname']))
            if self.module.params['ip'] is not None:
                msg.obj.append((to_bytes("ip-address", errors='surrogate_or_strict'), pack_ip(self.module.params['ip'])))

            stmt_join = ""
            if self.module.params['ddns']:
                stmt_join += 'ddns-hostname "{0}"; '.format(self.module.params['hostname'])

            try:
                if len(self.module.params['statements']) > 0:
                    stmt_join += "; ".join(self.module.params['statements'])
                    stmt_join += "; "
            except TypeError as e:
                self.module.fail_json(msg="Invalid statements found: %s" % to_native(e),
                                      exception=traceback.format_exc())

            if len(stmt_join) > 0:
                msg.obj.append(('statements', stmt_join))

            try:
                response = self.omapi.query_server(msg)
                if response.opcode != OMAPI_OP_UPDATE:
                    self.module.fail_json(msg="Failed to add host, ensure authentication and host parameters "
                                              "are valid.")
                self.module.exit_json(changed=True, lease=self.unpack_facts(response.obj))
            except OmapiError as e:
                self.module.fail_json(msg="OMAPI error: %s" % to_native(e), exception=traceback.format_exc())
        # Forge update message
        else:
            response_obj = self.unpack_facts(host_response.obj)
            fields_to_update = {}

            if to_bytes('ip-address', errors='surrogate_or_strict') not in response_obj or \
                            unpack_ip(response_obj[to_bytes('ip-address', errors='surrogate_or_strict')]) != self.module.params['ip']:
                fields_to_update['ip-address'] = pack_ip(self.module.params['ip'])

            # Name cannot be changed
            if 'name' not in response_obj or response_obj['name'] != self.module.params['hostname']:
                self.module.fail_json(msg="Changing hostname is not supported. Old was %s, new is %s. "
                                          "Please delete host and add new." %
                                          (response_obj['name'], self.module.params['hostname']))

            """
            # It seems statements are not returned by OMAPI, then we cannot modify them at this moment.
            if 'statements' not in response_obj and len(self.module.params['statements']) > 0 or \
                response_obj['statements'] != self.module.params['statements']:
                with open('/tmp/omapi', 'w') as fb:
                    for (k,v) in iteritems(response_obj):
                        fb.writelines('statements: %s %s\n' % (k, v))
            """
            if len(fields_to_update) == 0:
                self.module.exit_json(changed=False, lease=response_obj)
            else:
                msg = OmapiMessage.update(host_response.handle)
                msg.update_object(fields_to_update)

            try:
                response = self.omapi.query_server(msg)
                if response.opcode != OMAPI_OP_STATUS:
                    self.module.fail_json(msg="Failed to modify host, ensure authentication and host parameters "
                                              "are valid.")
                self.module.exit_json(changed=True)
            except OmapiError as e:
                self.module.fail_json(msg="OMAPI error: %s" % to_native(e), exception=traceback.format_exc())

    def remove_host(self):
        try:
            self.omapi.del_host(self.module.params['macaddr'])
            self.module.exit_json(changed=True)
        except OmapiErrorNotFound:
            self.module.exit_json()
        except OmapiError as e:
            self.module.fail_json(msg="OMAPI error: %s" % to_native(e), exception=traceback.format_exc())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, type='str', choices=['present', 'absent']),
            host=dict(type='str', default="localhost"),
            port=dict(type='int', default=7911),
            key_name=dict(required=True, type='str', default=None),
            key=dict(required=True, type='str', default=None, no_log=True),
            macaddr=dict(required=True, type='str', default=None),
            hostname=dict(type='str', default=None, aliases=['name']),
            ip=dict(type='str', default=None),
            ddns=dict(type='bool', default=False),
            statements=dict(type='list', default=[])
        ),
        supports_check_mode=False
    )

    if not pureomapi_found:
        module.fail_json(msg="pypureomapi library is required by this module.")

    if module.params['key'] is None or len(module.params["key"]) == 0:
        module.fail_json(msg="'key' parameter cannot be empty.")

    if module.params['key_name'] is None or len(module.params["key_name"]) == 0:
        module.fail_json(msg="'key_name' parameter cannot be empty.")

    host_manager = OmapiHostManager(module)
    try:
        if module.params['state'] == 'present':
            host_manager.setup_host()
        elif module.params['state'] == 'absent':
            host_manager.remove_host()
    except ValueError as e:
        module.fail_json(msg="OMAPI input value error: %s" % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
