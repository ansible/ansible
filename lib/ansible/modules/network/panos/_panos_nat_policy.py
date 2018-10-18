#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: panos_nat_policy
short_description: create a policy NAT rule
description:
    - Create a policy nat rule. Keep in mind that we can either end up configuring source NAT, destination NAT, or both. Instead of splitting it
      into two we will make a fair attempt to determine which one the user wants.
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
deprecated:
    alternative: Use M(panos_nat_rule) instead.
    removed_in: '2.9'
    why: This module depended on outdated and old SDK, use M(panos_nat_rule) instead.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
    password:
        description:
            - password for authentication
        required: true
    username:
        description:
            - username for authentication
        default: "admin"
    rule_name:
        description:
            - name of the SNAT rule
        required: true
    from_zone:
        description:
            - list of source zones
        required: true
    to_zone:
        description:
            - destination zone
        required: true
    source:
        description:
            - list of source addresses
        default: ["any"]
    destination:
        description:
            - list of destination addresses
        default: ["any"]
    service:
        description:
            - service
        default: "any"
    snat_type:
        description:
            - type of source translation
    snat_address:
        description:
            - snat translated address
    snat_interface:
        description:
            - snat interface
    snat_interface_address:
        description:
            - snat interface address
    snat_bidirectional:
        description:
            - bidirectional flag
        type: bool
        default: 'no'
    dnat_address:
        description:
            - dnat translated address
    dnat_port:
        description:
            - dnat translated port
    override:
        description:
            - attempt to override rule if one with the same name already exists
        type: bool
        default: 'no'
    commit:
        description:
            - commit if changed
        type: bool
        default: 'yes'
'''

EXAMPLES = '''
# Create a source and destination nat rule
  - name: create nat SSH221 rule for 10.0.1.101
    panos_nat:
      ip_address: "192.168.1.1"
      password: "admin"
      rule_name: "Web SSH"
      from_zone: ["external"]
      to_zone: "external"
      source: ["any"]
      destination: ["10.0.0.100"]
      service: "service-tcp-221"
      snat_type: "dynamic-ip-and-port"
      snat_interface: "ethernet1/2"
      dnat_address: "10.0.1.101"
      dnat_port: "22"
      commit: False
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    import pan.xapi
    from pan.xapi import PanXapiError

    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_NAT_XPATH = "/config/devices/entry[@name='localhost.localdomain']" + \
             "/vsys/entry[@name='vsys1']" + \
             "/rulebase/nat/rules/entry[@name='%s']"


def nat_rule_exists(xapi, rule_name):
    xapi.get(_NAT_XPATH % rule_name)
    e = xapi.element_root.find('.//entry')
    if e is None:
        return False
    return True


def dnat_xml(m, dnat_address, dnat_port):
    if dnat_address is None and dnat_port is None:
        return None

    exml = ["<destination-translation>"]
    if dnat_address is not None:
        exml.append("<translated-address>%s</translated-address>" %
                    dnat_address)
    if dnat_port is not None:
        exml.append("<translated-port>%s</translated-port>" %
                    dnat_port)
    exml.append('</destination-translation>')

    return ''.join(exml)


def snat_xml(m, snat_type, snat_address, snat_interface,
             snat_interface_address, snat_bidirectional):
    if snat_type == 'static-ip':
        if snat_address is None:
            m.fail_json(msg="snat_address should be speicified "
                            "for snat_type static-ip")

        exml = ["<source-translation>", "<static-ip>"]
        if snat_bidirectional:
            exml.append('<bi-directional>%s</bi-directional>' % 'yes')
        else:
            exml.append('<bi-directional>%s</bi-directional>' % 'no')
        exml.append('<translated-address>%s</translated-address>' %
                    snat_address)
        exml.append('</static-ip>')
        exml.append('</source-translation>')
    elif snat_type == 'dynamic-ip-and-port':
        exml = ["<source-translation>",
                "<dynamic-ip-and-port>"]
        if snat_interface is not None:
            exml = exml + [
                "<interface-address>",
                "<interface>%s</interface>" % snat_interface]
            if snat_interface_address is not None:
                exml.append("<ip>%s</ip>" % snat_interface_address)
            exml.append("</interface-address>")
        elif snat_address is not None:
            exml.append("<translated-address>")
            for t in snat_address:
                exml.append("<member>%s</member>" % t)
            exml.append("</translated-address>")
        else:
            m.fail_json(msg="no snat_interface or snat_address "
                            "specified for snat_type dynamic-ip-and-port")
        exml.append('</dynamic-ip-and-port>')
        exml.append('</source-translation>')
    else:
        m.fail_json(msg="unknown snat_type %s" % snat_type)

    return ''.join(exml)


def add_nat(xapi, module, rule_name, from_zone, to_zone,
            source, destination, service, dnatxml=None, snatxml=None):
    exml = []
    if dnatxml:
        exml.append(dnatxml)
    if snatxml:
        exml.append(snatxml)

    exml.append("<to><member>%s</member></to>" % to_zone)

    exml.append("<from>")
    exml = exml + ["<member>%s</member>" % e for e in from_zone]
    exml.append("</from>")

    exml.append("<source>")
    exml = exml + ["<member>%s</member>" % e for e in source]
    exml.append("</source>")

    exml.append("<destination>")
    exml = exml + ["<member>%s</member>" % e for e in destination]
    exml.append("</destination>")

    exml.append("<service>%s</service>" % service)

    exml.append("<nat-type>ipv4</nat-type>")

    exml = ''.join(exml)

    xapi.set(xpath=_NAT_XPATH % rule_name, element=exml)

    return True


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        rule_name=dict(required=True),
        from_zone=dict(type='list', required=True),
        to_zone=dict(required=True),
        source=dict(type='list', default=["any"]),
        destination=dict(type='list', default=["any"]),
        service=dict(default="any"),
        snat_type=dict(),
        snat_address=dict(),
        snat_interface=dict(),
        snat_interface_address=dict(),
        snat_bidirectional=dict(default=False),
        dnat_address=dict(),
        dnat_port=dict(),
        override=dict(type='bool', default=False),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if module._name == 'panos_nat_policy':
        module.deprecate("The 'panos_nat_policy' module is being renamed 'panos_nat_rule'", version=2.9)

    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    rule_name = module.params['rule_name']
    from_zone = module.params['from_zone']
    to_zone = module.params['to_zone']
    source = module.params['source']
    destination = module.params['destination']
    service = module.params['service']

    snat_type = module.params['snat_type']
    snat_address = module.params['snat_address']
    snat_interface = module.params['snat_interface']
    snat_interface_address = module.params['snat_interface_address']
    snat_bidirectional = module.params['snat_bidirectional']

    dnat_address = module.params['dnat_address']
    dnat_port = module.params['dnat_port']
    commit = module.params['commit']

    override = module.params["override"]
    if not override and nat_rule_exists(xapi, rule_name):
        module.exit_json(changed=False, msg="rule exists")

    try:
        changed = add_nat(
            xapi,
            module,
            rule_name,
            from_zone,
            to_zone,
            source,
            destination,
            service,
            dnatxml=dnat_xml(module, dnat_address, dnat_port),
            snatxml=snat_xml(module, snat_type, snat_address,
                             snat_interface, snat_interface_address,
                             snat_bidirectional)
        )

        if changed and commit:
            xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

        module.exit_json(changed=changed, msg="okey dokey")

    except PanXapiError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == '__main__':
    main()
