# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
    name: snmp
    plugin_type: inventory
    version_added: "2.7"
    short_description: Uses snmpv2 query to find devices.
    description:
        - Use sysDescr to find hosts and group them by platform.
        - Platforms: asa, ios, iosxr, nxos, dellos, junos, aruba and eos.
    extends_documentation_fragment:
      - constructed
      - inventory_cache
    requirements:
      - pysnmp library
      - netaddr library
    options:
        network:
            description: CIDRs to scan, separated by comma.
            type: string
            default: 192.168.0.0/24
        port:
            description: SNMP Port
            type: integer
            default: 161
        exclude:
            description: CIDRs to exclude from the scan, separated by comma.
            type: list
        community:
            description: The SNMP communities to query, separated by comma.
            type: string
            default: public
    notes:
        - TODO:
            - async
            - snmpv3
            - cache
            - Additional platforms
'''
EXAMPLES = '''
    # snmp.config file in YAML format
    plugin: snmp
    version: 2c
    community: mycommunity, public, idontknow
    networks: 192.168.99.99/27, 192.168.100.0/23
    exclude: 192.168.100.1/32, 192.168.100.2/32
    port: 161
'''

import re, time
from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_native
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

try:
    import netaddr as pynetaddr
except:
    raise AnsibleError('snmp inventory plugin requires the netapp library. Try: pip install netaddr')

try:
    import pysnmp.hlapi as pysnmpClient
except:
    raise AnsibleError('snmp inventory plugin requires the pysnmp library. Try: pip install pysnmp')

class Factory(object):
    InventoryModule = None
    BatchBank = None
    SysDescrParser = None
    SnmpClient = None
    NetAddr = None

#TODO: Async with control of batch Size
class BatchBank(object):

    BALANCE = 0

    def __init__(self, balance=128):
        BALANCE = balance

    @staticmethod
    def balance():
        Factory.InventoryModule.display.vvvv(
            (
                "BatchBank.balance: {balance}"
            ).format(
                balance=BatchBank.BALANCE
            )
        )

        return BatchBank.BALANCE

    @staticmethod
    def debit(amount=1):
        BatchBank.BALANCE = BatchBank.BALANCE - amount
        Factory.InventoryModule.display.vvvv(
            (
                "BatchBank.debit: {amount}"
            ).format(
                amount=amount
            )
        )

        return BatchBank.BALANCE

    @staticmethod
    def credit(amount=1):
        BatchBank.BALANCE = BatchBank.BALANCE + amount
        Factory.InventoryModule.display.vvvv(
            (
                "BatchBank.credit: {amount}"
            ).format(
                amount=amount
            )
        )

        return BatchBank.BALANCE

# TODO: Add additional platforms
class SysDescrParser(object):
    @staticmethod
    def platforms():
        ''' New devices/platform must be populated HERE
        '''
        return {
                    'asa'    : re.compile('^Cisco\sAdaptive\sSecurity\sAppliance'),
                    'ios'    : re.compile('^Cisco\sIOS\sSoftware'),
                    'iosxr'  : re.compile('^Cisco\sIOS\sXR\sSoftware'),
                    'nxos'   : re.compile('^Cisco\sNexus\sOperating\sSystem'),
                    'dellos' : re.compile('^Dell\sApplication\sSoftware'),
                    'junos'  : re.compile('^JUNOS'),
                    'aruba'  : re.compile('^Aruba\sOperating\sSystem\sSoftware'),
                    'eos'    : re.compile('^Arista')
                }

    @staticmethod
    def get_platform(text):
        Factory.InventoryModule.display.vvvv(
            (
                "sysDescrParser.get_platform: {text}"
            ).format(
                text=text
            )
        )

        platforms = SysDescrParser.platforms()
        for platform, rule in platforms.items():
            if rule.match(text):
                Factory.InventoryModule.display.vvvv(
                    (
                        "sysDescrParser.get_platform: "
                        "match {platform}"
                    ).format(
                        platform=platform
                    )
                )

                return platform

        platform = 'unknown'
        Factory.InventoryModule.display.vvvv(
            (
                "SysDescrParser.get_platform: "
                "match {platform}"
            ).format(
                platform=platform
            )
        )

        return platform

#TODO: snmpv3
class SnmpClient(object):
    def __init__(   self, target='localhost', port=161,
                    community='public', mib='SNMPv2-MIB', oid='sysDescr' ):
        self._target = target
        self._port = port
        self._community = community
        self._mib = mib
        self._oid = oid
        self._snmpEngine = pysnmpClient.SnmpEngine()

    def _objectIdentity(self):
        return pysnmpClient.ObjectIdentity(self._mib, self._oid, 0)

    def _communityData(self):
        return pysnmpClient.CommunityData(self._community)

    def _udpTransportTarget(self):
        return pysnmpClient.UdpTransportTarget( (self._target, self._port),
                                                timeout=2.0,
                                                retries=2 )

    def _contextData(self):
        return pysnmpClient.ContextData()

    def _objectType(self):
        return pysnmpClient.ObjectType( self._objectIdentity() )

    # TODO: Make it async
    def run(self):
        return next(    pysnmpClient.getCmd(
                                self._snmpEngine,
                                self._communityData(),
                                self._udpTransportTarget(),
                                self._contextData(),
                                self._objectType()
                        )
                    )

class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'snmp'

    def __init__(self):
        super(InventoryModule, self).__init__()

    def _discovery(self):
        network_whitelist = self._options.get('network', '192.168.0.0/24')
        network_whitelist = network_whitelist.strip().split(',')
        ip_whitelist = Factory.NetAddr.IPSet(network_whitelist)

        network_blacklist = self._options.get('exclude', '127.0.0.1')
        network_blacklist = network_blacklist.strip().split(',')
        ip_blacklist = Factory.NetAddr.IPSet(network_blacklist)

        snmp_communities = self._options.get('community', 'public')
        snmp_communities = snmp_communities.strip().split(',')

        # Loop over ips in the network range
        for ip in ip_whitelist:
            Factory.SnmpClient._target = to_native(ip)
            Factory.SnmpClient._port = self._options.get('port', 161)
            Factory.SnmpClient._port = to_native(Factory.SnmpClient._port)

            if Factory.SnmpClient._target in ip_blacklist:
                Factory.InventoryModule.display.vvv(
                    (
                        "InventoryModule._discovery: "
                        "ignoring {host} in exclude list"
                    ).format(
                        host=Factory.SnmpClient._target
                    )
                )

                continue

            # Loop over communities
            for snmp_community in snmp_communities:
                snmp_community = snmp_community.strip()
                Factory.SnmpClient._community = to_native(snmp_community)

                try:
                    Factory.InventoryModule.display.vvvv(
                        (
                            "InventoryModule._discovery: "
                            "processing {host} ({community})"
                        ).format(
                            host=Factory.SnmpClient._target,
                            community=Factory.SnmpClient._community
                        )
                    )

                    (   errorIndication,
                        errorStatus,
                        errorIndex, varBinds ) = Factory.SnmpClient.run()

                except Exception as e:
                    Factory.InventoryModule.display.vvvv(
                        (
                            "InventoryModule._discovery: "
                            "bypassing {host}"
                        ).format(
                            host=Factory.SnmpClient._target
                        )
                    )

                    continue

                if errorIndication:
                    errorIndication = to_native(errorIndication)
                    Factory.InventoryModule.display.vvvv(
                        (
                            "InventoryModule._discovery errorIndication: "
                            "{error}"
                        ).format(
                            error=errorIndication
                        )
                    )

                    continue

                elif errorStatus:
                    errorStatus = to_native(errorStatus)
                    Factory.InventoryModule.display.vvvv(
                        (
                            "InventoryModule._discovery errorStatus: "
                            "{error}"
                        ).format(
                            error=errorStatus
                        )
                    )

                    continue

                else:
                    for snmp_oid, snmp_text in varBinds:
                        snmp_text = to_native(snmp_text)
                        group_name = Factory.SysDescrParser.get_platform(snmp_text)

                        Factory.InventoryModule.inventory.add_group(group_name)
                        Factory.InventoryModule.display.vv(
                            (
                                "InventoryModule._discovery: "
                                "add_group({group})"
                            ).format(
                                group=group_name
                            )
                        )

                        Factory.InventoryModule.inventory.set_variable(
                            group_name,
                            'ansible_network_os',
                            group_name
                        )

                        Factory.InventoryModule.display.vv(
                            (
                                "InventoryModule._discovery: "
                                "set_variable({group}, 'ansible_network_os', {group})"
                            ).format(
                                group=group_name
                            )
                        )


                        Factory.InventoryModule.inventory.add_host(
                            Factory.SnmpClient._target,
                            group=group_name
                        )

                        Factory.InventoryModule.display.vv(
                            (
                                "InventoryModule._discovery: "
                                "add_host({host}, {group})"
                            ).format(
                                host=Factory.SnmpClient._target,
                                group=group_name
                            )
                        )


    # TODO: CACHE
    def parse(self, inventory, loader, path, cache=False):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._options = self._read_config_data(path)
        Factory.InventoryModule = self
        Factory.SysDescrParser = SysDescrParser()
        Factory.BatchBank = BatchBank()
        Factory.SnmpClient = SnmpClient()
        Factory.NetAddr = pynetaddr
        self._discovery()
