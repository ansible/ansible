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
module: lldpad
short_description: Automates lldpad
description:
    - Allows you to configure lldpad for various configurations.
version_added: "2.8"
options:
    name:
        description:
            - Specifies the name of the interface.
    lldp:
       description: Specifies the admin status tp be applied.
       choices: [ "tx", "rx", "rxtx", "disabled" ]
    tlv_identifier:
        description:
            - Specifies the type of the TLV which should be configured. Please see 'lldptool --help'
    tlv_value:
        description:
            - Specifies the value what should be applied to the tlv_identifier.
    tx:
        description:
            - A boolean. Controls the transmission of specific TLV ideantifier.

author: "Susant Sahani (@ssahani) <susant@redhat.com>"
'''

EXAMPLES = '''
# Configure LLDP adminStatus to Receive and Transmit for interface eth0
- lldpad:
    name=eth0
    lldp=rxtx

# Set a Management Address TLV on eth0 to carry IPv4 address 192.168.10.10
- lldpad:
    name=eth0
    tlv_identifier=mngAddr
    tlv_value=ipv4=192.168.10.10

# Enable transmit of MTU for interface eth0
- lldpad:
    name=eth0
    tx=yes
    tlv_identifier=MTU

# Enable transmit of mngAddr for interface eth0
- lldpad:
    name=eth0
    tx=yes
    tlv_identifier=mngAddr

# Enable transmit of macPhyCfg for interface eth0
- lldpad:
    name=eth0
    tx=yes
    tlv_identifier=macPhyCfg
'''

RETURN = r'''
'''

from ansible.module_utils.basic import get_platform, AnsibleModule


class LldpadModule(object):

    def __init__(self, module):
        self.module = module
        self.args = self.module.params
        self.lldptool = self.module.get_bin_path('lldptool', required=True)
        self.name = module.params['name']
        self.lldp = module.params['lldp']
        self.tlv_identifier = module.params['tlv_identifier']
        self.tlv_value = module.params['tlv_value']
        self.tx = module.params['tx']
        self.changed = False

    def bool_to_str(self, v):
        if v:
            return "yes"
        else:
            return "no"

    def lldpad_configure_lldp(self):
        list_names = self.name.split(' ')

        for interface in list_names:
            cmd = "%s set-lldp -i %s adminStatus=%s" % (self.lldptool, interface, self.lldp)

            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='lldptool failed to apply set-lldp on lldpad %s: %s' % (interface, out + err))
                return err

            return True

    def lldpad_configure_tlv(self):
        list_names = self.name.split(' ')

        for interface in list_names:
            cmd = "%s -T -i %s -V %s %s" % (self.lldptool, interface, self.tlv_identifier, self.tlv_value)

            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='lldptool failed to apply set-tlv on lldpad set-tlv %s: %s %s' % (interface, out + err, cmd))
                return err

            return True

    def lldpad_configure_tlv_tx(self):
        list_names = self.name.split(' ')

        for interface in list_names:
            cmd = "%s set-tlv -i %s -V %s enableTx=%s" % (self.lldptool, interface, self.tlv_identifier, self.bool_to_str(self.tx))
            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='lldptool failed to configure lldpad set-tlv type %s: %s %s' % (interface, out + err, cmd))
                return err

            return True

    def configure_lldpad(self):
        rc = ''

        if self.lldp:
            rc = self.lldpad_configure_lldp()

        if self.tlv_identifier and self.tlv_value:
            rc = self.lldpad_configure_tlv()

        if self.tx and self.tlv_identifier:
            rc = self.lldpad_configure_tlv_tx()

        if rc is True:
            self.changed = True

        return rc


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type=str,),
            lldp=dict(type=str, choices=['tx', 'rx', 'rxtx', 'disabled']),
            tlv_identifier=dict(required=False, default=None, type='str'),
            tlv_value=dict(required=False, default=None, type='str'),
            tx=dict(type=bool),
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    tlv_identifier = module.params['tlv_identifier']
    tlv_value = module.params['tlv_value']
    tx = module.params['tx']

    if name is None:
        module.fail_json(msg='Interace name can not be None')
    if tlv_identifier:
        if tlv_value is None and tx is None:
            module.fail_json(msg='tlv_value is required for tlv_indentifier or tx')

    lldpad = LldpadModule(module)
    rc = lldpad.configure_lldpad()

    result = {}
    if rc is False:
        result['changed'] = False
    else:
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
