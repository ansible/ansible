#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Tomi Raittinen <tomi.raittinen@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: panos_facts
short_description: Collects facts from Palo Alto Networks device
description:
    - Collects fact information from Palo Alto Networks firewall running PanOS.
author:
    - Tomi Raittinen (@traittinen)
notes:
    - Tested on PanOS 8.0.5
requirements:
    - pan-python
version_added: 2.8
options:
    gather_subset:
        description:
            - Scopes what information is gathered from the device.
              Possible values for this argument include all, system, session,
              interfaces, ha, vr, vsys and config. You can specify a list of
              values to include a larger subset. Values can also be used with
              an initial ! to specify that a specific subset should not be
              collected. Certain subsets might be supported by Panorama.
        required: false
        default: ['!config']
    host:
        description:
            - IP address or hostname of PAN-OS device being configured.
        required: true
        aliases: ['ip_address']
    username:
        description:
            - Username credentials to use for authentication. If the value is
              not specified in the task, the value of environment variable
              C(ANSIBLE_NET_USERNAME) will be used instead.
    password:
        description:
            - Password credentials to use for authentication. If the value is
              not specified in the task, the value of environment variable
              C(ANSIBLE_NET_PASSWORD) will be used instead.

'''

EXAMPLES = '''

# Gather facts
- name: Get facts
  panos_facts:
    host: myfw.company.com
    username: admin
    password: mysecret
    gather_subset: config

'''

RETURN = '''
net_hostname:
    description: Hostname of the local node.
    returned: When C(system) is specified in C(gather_subset).
    type: str
net_serial:
    description: Serial number of the local node.
    returned: When C(system) is specified in C(gather_subset).
    type: str
net_model:
    description: Device model of the local node.
    returned: When C(system) is specified in C(gather_subset).
    type: str
net_version:
    description: PanOS version of the local node.
    returned: When C(system) is specified in C(gather_subset).
    type: str
net_uptime:
    description: Uptime of the local node.
    returned: When C(system) is specified in C(gather_subset).
    type: str
    sample: 469 days, 19:30:16
net_full_commit_required:
    description: Specifies whether full commit is required to apply changes.
    returned: When C(system) is specified in C(gather_subset).
    type: bool
net_uncommitted_changes:
    description: Specifies if commit is required to apply changes.
    returned: When C(system) is specified in C(gather_subset).
    type: bool
net_multivsys:
    description: Specifies whether multivsys mode is enabled on local node.
    returned: When C(system) is specified in C(gather_subset).
    type: str
    sample: on
net_session_usage:
    description: Current number of active sessions on local node
    returned: When C(session) is specified in C(gather_subset).
    type: int
net_session_max:
    description: Maximum number of sessions on local node.
    returned: When C(session) is specified in C(gather_subset).
    type: int
net_pps:
    description: Current packets/s throughput.
    returned: When C(session) is specified in C(gather_subset).
    type: int
net_kbps:
    description: Current kb/s throughput.
    returned: When C(session) is specified in C(gather_subset).
    type: int
net_ha_enabled:
    description: Specifies whether HA is enabled or not.
    returned: When C(ha) is specified in C(gather_subset).
    type: bool
net_ha_localmode:
    description: Specifies the HA mode on local node.
    returned: When C(ha) is specified in C(gather_subset).
    type: str
    sample: Active-Passive
net_ha_localstate:
    description: Specifies the HA state on local node.
    returned: When C(ha) is specified in C(gather_subset).
    type: str
    sample: active
net_config:
    description: Device confiration in XML format.
    returned: When C(config) is specified in C(gather_subset).
    type: str
net_interfaces:
    description: Network interface information.
    returned: When C(interface) is specified in C(gather_subset).
    type: complex
    contains:
        name:
            description: Interface name.
            type: str
            sample: ae1.23
        comment:
            description: Interface description/comment.
            type: str
        ip:
            description: List of interface IP addresses in CIDR format.
            type: list
            sample: 192.0.2.1/24
        ipv6:
            description: List of interface IPv6 addresses in CIDR format.
            type: list
            sample: 2001:db8::0000:1/64
        tag:
            description: VLAN tag for the subinterface.
            type: int
            sample: 23
net_virtual-routers:
    description: Virtual Router information.
    returned: When C(vr) is specified in C(gather_subset).
    type: complex
    contains:
        vr_name:
            description: Name of the virtual router.
            type: str
        vr_routerid:
            description: BGP router ID.
            type: str
            sample: 192.0.2.1
        vr_asn:
            description: BGP autonomous system number.
            type: int
            sample: 65001
        vr_iflist:
            description: List interfaces in the VR.
            type: list
            sample:
                - ae2.12
                - ae2.14
net_virtual-systems:
    description: Virtual System information.
    returned: When C(vsys) is specified in C(gather_subset).
    type: complex
    contains:
        vsys_description:
            description: VSYS description/name.
            type: str
        vsys_id:
            description: VSYS ID.
            type: int
        vsys_name:
            description: VSYS name.
            type: int
            sample: vsys1
        vsys_currentsessions:
            description: Number of active sessions on VSYS.
            type: int
        vsys_vsys_maxsessions:
            description: Number of configured maximum sessions on VSYS. 0 for unlimited.
            type: int
        vsys_vrlist:
            description: List of virtual routers attached to the VSYS.
            type: list
        vsys_iflist:
            description: List of interfaces attached to the VSYS.
            type: list
        vsys_zonelist:
            description: List of security zones attached to the VSYS.
            type: list
'''

import re
import xml.etree.ElementTree as etree
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.six import iteritems

try:
    import pan.xapi
    HAS_LIB = True
except ImportError:
    HAS_LIB = False


class Factbase(object):

    def __init__(self, module):
        # FW hostname/IP and credentials
        self.__fw_address = module.params['host']
        self.__fw_username = module.params['username']
        self.__fw_password = module.params['password']

        self.facts = dict()
        self.xapi = pan.xapi.PanXapi(
            hostname=self.__fw_address,
            api_username=self.__fw_username,
            api_password=self.__fw_password
        )


class System(Factbase):

    def populate_facts(self):
        xapi = self.xapi
        xapi.op("<show><system><info></info></system></show>")
        result = xapi.xml_result().encode('utf-8')
        root = etree.fromstring(result)

        self.facts.update({
            'hostname': root.findtext('hostname'),
            'model': root.findtext('model'),
            'serial': root.findtext('serial'),
            'version': root.findtext('sw-version'),
            'uptime': root.findtext('uptime'),
            'multivsys': root.findtext('multi-vsys')
        })

        # Check uncommitted changes
        xapi.op("<check><pending-changes></pending-changes></check>")
        result = xapi.xml_result().encode('utf-8')

        if result == "yes":
            uncommitted_changes = True
        else:
            uncommitted_changes = False

        # Check if full commit is required
        if uncommitted_changes:
            xapi.op("<check><full-commit-required></full-commit-required></check>")
            result = xapi.xml_result().encode('utf-8')

            if result == "yes":
                full_commit_required = True
            else:
                full_commit_required = False
        else:
            full_commit_required = False

        self.facts.update({
            'uncommitted_changes': uncommitted_changes,
            'full_commit_required': full_commit_required
        })


class Session(Factbase):

    def populate_facts(self):
        xapi = self.xapi
        xapi.op("<show><session><info></info></session></show>")
        result = xapi.xml_root().encode('utf-8')
        root = etree.fromstring(result)

        self.facts.update({
            'session_usage': root.find('./result/num-active').text,
            'session_max': root.find('./result/num-max').text,
            'pps': root.find('./result/pps').text,
            'kbps': root.find('./result/kbps').text
        })


class Interfaces(Factbase):

    def populate_facts(self):

        xapi = self.xapi
        if_xpath = "/config/devices/entry[@name='localhost.localdomain']/network/interface"
        xapi.get(xpath=if_xpath)

        interfaces = []

        # Parse XML interface config
        config = xapi.xml_result().encode('utf-8')
        root = etree.fromstring(config)

        # Loop through physical interfaces
        if_xml = root.findall("./*/entry")
        for phy_if in if_xml:

            name = phy_if.get('name')
            comment = phy_if.findtext('comment')

            ip = []
            for i in phy_if.findall('ip/entry'):
                ip.append(i.get('name'))

            ipv6 = []
            for i in phy_if.findall('ipv6/address/entry'):
                ipv6.append(i.get('name'))

            interface = dict(
                name=name,
                comment=comment,
                ip=ip,
                ipv6=ipv6
            )
            interfaces.append(interface)

        # Loop through subinterfaces
        sub_if_xml = root.findall('.//units/entry')
        for sub_if in sub_if_xml:
            name = sub_if.get('name')
            comment = sub_if.findtext('comment')
            tag = sub_if.findtext('tag')

            if tag:
                try:
                    tag = int(tag)
                except ValueError:
                    pass

            ip = []
            for i in sub_if.findall('ip/entry'):
                ip.append(i.get('name'))

            ipv6 = []
            for i in sub_if.findall('ipv6/address/entry'):
                ipv6.append(i.get('name'))

            subinterface = dict(
                name=name,
                comment=comment,
                tag=tag,
                ip=ip,
                ipv6=ipv6
            )
            interfaces.append(subinterface)

        newlist = sorted(interfaces, key=lambda k: k['name'])
        self.facts.update({
            'interfaces': newlist
        })


class Ha(Factbase):

    def populate_facts(self):

        xapi = self.xapi
        xapi.op("<show><high-availability><all></all></high-availability></show>")
        result = xapi.xml_root().encode('utf-8')
        root = etree.fromstring(result)

        if root.find('./result/enabled').text == 'yes':
            ha_enabled = True
            ha_localmode = root.find('./result/group/local-info/mode').text
            ha_localstate = root.find('./result/group/local-info/state').text
        else:
            ha_enabled = False
            ha_localmode = "standalone"
            ha_localstate = "active"

        self.facts.update({
            'ha_enabled': ha_enabled,
            'ha_localmode': ha_localmode,
            'ha_localstate': ha_localstate
        })


class Vr(Factbase):

    def populate_facts(self):

        xapi = self.xapi
        vr_xpath = "/config/devices/entry[@name='localhost.localdomain']/network/virtual-router"
        xapi.get(xpath=vr_xpath)

        # Parse XML VR config
        config = xapi.xml_result().encode('utf-8')
        vr_root = etree.fromstring(config)

        # Loop through all VRs
        vr_xml = vr_root.findall("./entry")
        virtual_routers = []

        for vr_config in vr_xml:

            vr_name = vr_config.get('name')

            try:
                vr_asn = vr_config.find('./protocol/bgp/local-as').text
            except AttributeError:
                vr_asn = None

            try:
                vr_routerid = vr_config.find('./protocol/bgp/router-id').text
            except AttributeError:
                vr_routerid = None

            vr_iflist = []
            for i in vr_config.findall('./interface/member'):
                vr_iflist.append(i.text)

            vr = dict(
                vr_name=vr_name,
                vr_asn=vr_asn,
                vr_routerid=vr_routerid,
                vr_iflist=vr_iflist
            )
            virtual_routers.append(vr)

        self.facts.update({
            'virtual-routers': virtual_routers
        })


class Vsys(Factbase):

    def populate_facts(self):

        xapi = self.xapi
        vsys_xpath = "/config/devices/entry[@name='localhost.localdomain']/vsys"
        xapi.get(xpath=vsys_xpath)

        # Parse XML interface config
        config = xapi.xml_result().encode('utf-8')
        vsys_root = etree.fromstring(config)

        # Get session usage XML
        xapi.op("<show><session><meter></meter></session></show>")
        result = xapi.xml_root().encode('utf-8')
        session_root = etree.fromstring(result)

        # Loop through all VSYS
        vsys_xml = vsys_root.findall("./entry")
        virtual_systems = []

        for vsys_config in vsys_xml:

            vsys_name = vsys_config.get('name')
            vsys_id = re.search(r'vsys(\d+)', vsys_name).group(1)
            vsys_description = vsys_config.find('./display-name').text

            vsys_iflist = []
            for i in vsys_config.findall('./import/network/interface/member'):
                vsys_iflist.append(i.text)

            vsys_vrlist = []
            for i in vsys_config.findall('./import/network/virtual-router/member'):
                vsys_vrlist.append(i.text)

            vsys_zonelist = []
            for i in vsys_config.findall('./zone/entry'):
                vsys_zonelist.append(i.get('name'))

            vsys_sessions = session_root.find(".//entry/[vsys='" + vsys_id + "']")
            vsys_currentsessions = vsys_sessions.find('.//current').text
            vsys_maxsessions = vsys_sessions.find('.//maximum').text

            vsys = dict(
                vsys_maxsessions=vsys_maxsessions,
                vsys_currentsessions=vsys_currentsessions,
                vsys_name=vsys_name,
                vsys_id=vsys_id,
                vsys_description=vsys_description,
                vsys_iflist=vsys_iflist,
                vsys_vrlist=vsys_vrlist,
                vsys_zonelist=vsys_zonelist
            )

            virtual_systems.append(vsys)

        self.facts.update({
            'virtual-systems': virtual_systems
        })


class Config(Factbase):

    def populate_facts(self):
        xapi = self.xapi
        xapi.show()
        config = xapi.xml_result().encode('utf-8')

        self.facts.update({
            'config': config
        })


FACT_SUBSETS = dict(
    system=System,
    session=Session,
    interfaces=Interfaces,
    ha=Ha,
    vr=Vr,
    vsys=Vsys,
    config=Config
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():

    argument_spec = dict(
        host=dict(required=True, type='str', aliases=['ip_address']),
        username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
        password=dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
        gather_subset=dict(default=['!config'], type='list')
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    gather_subset = module.params['gather_subset']

    runable_subsets = set()
    exclude_subsets = set()

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue

        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Subset must be one of [%s], got %s' %
                             (', '.join(VALID_SUBSETS), subset))

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('system')

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    # Create instance classes, e.g. System, Session etc.
    instances = list()

    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    # Populate facts for instances
    for inst in instances:
        inst.populate_facts()
        facts.update(inst.facts)

    ansible_facts = dict()

    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == '__main__':
    main()
