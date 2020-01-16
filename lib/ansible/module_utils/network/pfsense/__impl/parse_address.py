# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Orion Poplawski <orion@nwra.com>
# Copyright: (c) 2019, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


def parse_address(self, param, allow_self=True):
    """ validate param address field and returns it as a dict """
    addr = param.split(':')
    if len(addr) > 3:
        self.module.fail_json(msg='Cannot parse address %s' % (param))

    address = addr[0]

    ret = dict()
    # Check if the first character is "!"
    if address[0] == '!':
        # Invert the rule
        ret['not'] = None
        address = address[1:]

    if address == 'NET' or address == 'IP':
        interface = addr[1] if len(addr) > 1 else None
        ports = addr[2] if len(addr) > 2 else None
        if interface is None or interface == '':
            self.module.fail_json(msg='Cannot parse address %s' % (param))

        ret['network'] = self.parse_interface(interface)
        if address == 'IP':
            ret['network'] += 'ip'
    else:
        ports = addr[1] if len(addr) > 1 else None
        if address == 'any':
            ret['any'] = None
        # rule with this firewall
        elif allow_self and address == '(self)':
            ret['network'] = '(self)'
        # rule with interface name (LAN, WAN...)
        elif self.is_interface_name(address):
            ret['network'] = self.get_interface_pfsense_by_name(address)
        else:
            if not self.is_ip_or_alias(address):
                self.module.fail_json(msg='Cannot parse address %s, not IP or alias' % (address))
            ret['address'] = address

    if ports is not None:
        ports = ports.split('-')
        if len(ports) > 2 or ports[0] is None or ports[0] == '' or len(ports) == 2 and (ports[1] is None or ports[1] == ''):
            self.module.fail_json(msg='Cannot parse address %s' % (param))

        if not self.is_port_or_alias(ports[0]):
            self.module.fail_json(msg='Cannot parse port %s, not port number or alias' % (ports[0]))
        ret['port'] = ports[0]

        if len(ports) > 1:
            if not self.is_port_or_alias(ports[1]):
                self.module.fail_json(msg='Cannot parse port %s, not port number or alias' % (ports[1]))
            ret['port'] += '-' + ports[1]

    return ret
