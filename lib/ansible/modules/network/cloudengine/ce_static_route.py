#!/usr/bin/python
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
#

DOCUMENTATION = '''
---
module: ce_static_route
version_added: "2.2"
short_description: Config or delete static route.
description:
    - Manages the static routes of Huawei CloudEngine switches.
author: Yang yang (@CloudEngine-Ansible)
notes:
    - If no vrf is supplied, vrf is set to default.
      If state=absent, the route will be removed, regardless of the
      non-required parameters.
options:
    prefix:
        description:
            - Destination ip address of static route.
        required: true
    mask:
        description:
            - Destination ip mask of static route.
        required: true
    aftype:
        description:
            - Destination ip address family type of static route.
        required: true
        choices: ['v4','v6']
    next_hop:
        description:
            - Next hop address of static route.
        required: true
    nhp_interface:
        description:
            - Next hop interface full name of static route.
        required: false
    vrf:
        description:
            - VPN instance.
        required: false
        default: null
    destvrf:
        description:
            - VPN instance of next hop ip address.
        required: false
        default: null
    tag:
        description:
            - Route tag value (numeric).
        required: false
        default: null
    description:
        description:
            - Name of the route. Used with the name parameter on the CLI.
        required: false
        default: null
    pref:
        description:
            - Preference or administrative difference of route (range 1-255).
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource.
        required: false
        choices: ['present','absent']
        default: present
'''

EXAMPLES = '''
# Config a ipv4 static route, next hop is an address and that it has the proper description
- ce_static_route: prefix=2.1.1.2 mask = 24 next_hop=3.1.1.2 description='Configured by Ansible' aftype=v4
# Config a ipv4 static route ,next hop is an interface and that it has the proper description
- ce_static_route: prefix=2.1.1.2 mask = 24 next_hop=10GE1/0/1 description='Configured by Ansible' aftype=v4
# Config a ipv6 static route, next hop is an address and that it has the proper description
- ce_static_route: prefix=fc00:0:0:2001::  mask = 64 next_hop=fc00:0:0:2004::1 description='Configured by Ansible' aftype=v6
# Config a ipv4 static route, next hop is an interface and that it has the proper description
- ce_static_route: prefix=fc00:0:0:2001:: mask = 64 next_hop=10GE1/0/1 description='Configured by Ansible' aftype=v6
# Config a VRF and set ipv4 static route, next hop is an address and that it has the proper description
- ce_static_route: vrf=vpna prefix=2.1.1.2 mask = 24 next_hop=3.1.1.2 description='Configured by Ansible' aftype=v4
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"next_hop": "3.3.3.3", "pref": "100",
            "prefix": "192.168.20.642", "mask": "24", "description": "testing",
            "vrf": "_public_"}
existing:
    description: k/v pairs of existing switchport
    type: dict
    sample:  {null}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict or null
    sample:  {"next_hop": "3.3.3.3", "pref": "100",
            "prefix": "192.168.20.0", "mask": "24", "description": "testing",
            "tag" : "null"}
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: ["ip route-static 2.2.2.0 255.255.255.0 3.3.3.1"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


import re
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


CE_NC_GET_STATIC_ROUTE = """
<filter type="subtree">
      <staticrt xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <staticrtbase>
          <srRoutes>
            <srRoute>
              <vrfName></vrfName>
              <afType></afType>
              <topologyName></topologyName>
              <prefix></prefix>
              <maskLength></maskLength>
              <ifName></ifName>
              <destVrfName></destVrfName>
              <nexthop></nexthop>
              <description></description>
              <preference></preference>
              <tag></tag>
            </srRoute>
          </srRoutes>
        </staticrtbase>
      </staticrt>
    </filter>
"""

CE_NC_GET_STATIC_ROUTE_ABSENT = """
<filter type="subtree">
      <staticrt xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <staticrtbase>
          <srRoutes>
            <srRoute>
              <vrfName></vrfName>
              <afType></afType>
              <topologyName></topologyName>
              <prefix></prefix>
              <maskLength></maskLength>
              <ifName></ifName>
              <destVrfName></destVrfName>
              <nexthop></nexthop>
            </srRoute>
          </srRoutes>
        </staticrtbase>
      </staticrt>
    </filter>
"""

CE_NC_SET_STATIC_ROUTE = """
<staticrt xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <staticrtbase>
          <srRoutes>
            <srRoute operation="merge">
              <vrfName>%s</vrfName>
              <afType>%s</afType>
              <topologyName>base</topologyName>
              <prefix>%s</prefix>
              <maskLength>%s</maskLength>
              <ifName>%s</ifName>
              <destVrfName>%s</destVrfName>
              <nexthop>%s</nexthop>%s%s%s
            </srRoute>
          </srRoutes>
        </staticrtbase>
      </staticrt>
"""
CE_NC_SET_DESCRIPTION = """
<description>%s</description>
"""

CE_NC_SET_PREFERENCE = """
<preference>%s</preference>
"""

CE_NC_SET_TAG = """
<tag>%s</tag>
"""

CE_NC_DELETE_STATIC_ROUTE = """
<staticrt xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <staticrtbase>
          <srRoutes>
            <srRoute operation="delete">
              <vrfName>%s</vrfName>
              <afType>%s</afType>
              <topologyName>base</topologyName>
              <prefix>%s</prefix>
              <maskLength>%s</maskLength>
              <ifName>%s</ifName>
              <destVrfName>%s</destVrfName>
              <nexthop>%s</nexthop>
            </srRoute>
          </srRoutes>
        </staticrtbase>
      </staticrt>
"""


state_type = ('present', 'absent')

valid_version = ('v4', 'v6')


class CE_StaticRoute(object):
    """CE_StaticRoute"""

    def __init__(self, argument_spec, ):
        self.spec = argument_spec
        self.module = None
        self.netconf = None
        self.init_module()

        # static route info
        self.prefix = self.module.params['prefix']
        self.mask = self.module.params['mask']
        self.aftype = self.module.params['aftype']
        self.next_hop = self.module.params['next_hop']
        self.nhp_interface = self.module.params['nhp_interface']
        self.tag = self.module.params['tag']
        self.description = self.module.params['description']
        self.state = self.module.params['state']
        self.pref = self.module.params['pref']

        # vpn instance info
        self.vrf = self.module.params['vrf']
        self.destvrf = self.module.params['destvrf']

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.password = self.module.params['password']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

        # init netconf connect
        self.init_netconf()

    def init_module(self):
        """init_module"""

        self.module = NetworkModule(
            argument_spec=self.spec, supports_check_mode=True)

    def init_netconf(self):
        """init_netconf"""

        if not HAS_NCCLIENT:
            raise Exception("the ncclient library is required")

        self.netconf = get_netconf(host=self.host,
                                   port=self.port,
                                   username=self.username,
                                   password=self.module.params['password'])
        if not self.netconf:
            self.module.fail_json(msg='Error: netconf init failed')

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def build_config_xml(self, xmlstr):
        """build_config_xml"""

        return '<config> ' + xmlstr + ' </config>'

    def convert_len_to_mask(self, masklen):
        """convert mask length to ip address mask, i.e. 24 to 255.255.255.0"""

        mask_int = ["0"] * 4
        length = int(masklen)

        if length > 32:
            self.module.fail_json(msg='IPv4 ipaddress mask length is invalid')
        if length < 8:
            mask_int[0] = str(int((0xFF << (8 - length % 8)) & 0xFF))
        if length >= 8:
            mask_int[0] = '255'
            mask_int[1] = str(int((0xFF << (16 - (length % 16))) & 0xFF))
        if length >= 16:
            mask_int[1] = '255'
            mask_int[2] = str(int((0xFF << (24 - (length % 24))) & 0xFF))
        if length >= 24:
            mask_int[2] = '255'
            mask_int[3] = str(int((0xFF << (32 - (length % 32))) & 0xFF))
        if length == 32:
            mask_int[3] = '255'

        return '.'.join(mask_int)

    def is_valid_v4addr(self, addr):
        """check is ipv4 addr is valid"""
        if addr.find('.') != -1:
            addr_list = addr.split('.')
            if len(addr_list) != 4:
                return False
            for each_num in addr_list:
                if not each_num.isdigit():
                    return False
                if int(each_num) > 255:
                    return False
            return True
        return False

    def is_valid_v6addr(self, addr):
        """check is ipv6 addr is valid"""
        if addr.find(':') != -1:
            addr_list = addr.split(':')
            if len(addr_list) > 6:
                return False
            if addr_list[1] != "":
                return False
            return True
        return False

    def is_valid_version(self, version):
        """is_valid_version"""
        return version in valid_version

    def is_valid_tag(self, tag):
        """is_valid_tag"""

        if not tag.isdigit():
            return False

        if int(tag) < 1 or int(tag) > 4294967295:
            return False

        return True

    def is_valid_preference(self, pref):
        """is_valid_preference"""
        if pref.isdigit():
            return int(pref) > 0 and int(pref) < 256
        else:
            return False

    def is_valid_description(self, description):
        """is_valid_description"""
        if description.find('?') != -1:
            return False
        if len(description) < 1 or len(description) > 255:
            return False
        return True

    def convert_ip_prefix(self):
        """convert prefix to real value i.e. 2.2.2.2/24 to 2.2.2.0/24"""
        if self.aftype == "v4":
            if self.prefix.find('.') == -1:
                return False
            if self.mask == '32':
                self.prefix = self.prefix
                return True
            if self.mask == '0':
                self.prefix = '0.0.0.0'
                return True
            addr_list = self.prefix.split('.')
            length = len(addr_list)
            if length > 4:
                return False
            for each_num in addr_list:
                if not each_num.isdigit():
                    return False
                if int(each_num) > 255:
                    return False
            byte_len = 8
            ip_len = int(self.mask) / byte_len
            ip_bit = int(self.mask) % byte_len
        else:
            if self.prefix.find(':') == -1:
                return False
            if self.mask == '128':
                self.prefix = self.prefix
                return True
            if self.mask == '0':
                self.prefix = '::'
                return True
            addr_list = self.prefix.split(':')
            length = len(addr_list)
            if length > 6:
                return False
            byte_len = 16
            ip_len = int(self.mask) / byte_len
            ip_bit = int(self.mask) % byte_len

        if self.aftype == "v4":
            for i in range(ip_len + 1, length):
                addr_list[i] = 0
        else:
            for i in range(length - ip_len, length):
                addr_list[i] = 0
        for j in range(0, byte_len - ip_bit):
            if self.aftype == "v4":
                addr_list[ip_len] = int(addr_list[ip_len]) & (0 << j)
            else:
                if addr_list[length - ip_len - 1] == "":
                    continue
                addr_list[length - ip_len -
                          1] = '0x%s' % addr_list[length - ip_len - 1]
                addr_list[length - ip_len -
                          1] = int(addr_list[length - ip_len - 1], 16) & (0 << j)

        if self.aftype == "v4":
            self.prefix = '%s.%s.%s.%s' % (addr_list[0], addr_list[
                                           1], addr_list[2], addr_list[3])
            return True
        else:
            ipv6_addr_str = ""
            for num in range(0, length - ip_len):
                ipv6_addr_str += '%s:' % addr_list[num]
            self.prefix = ipv6_addr_str
            return True

    def set_update_cmd(self):
        """ set update command"""
        if not self.changed:
            return
        if self.aftype == "v4":
            maskstr = self.convert_len_to_mask(self.mask)
        else:
            maskstr = self.mask
        if self.state == "present":
            if self.vrf:
                if self.destvrf:
                    self.updates_cmd.append('ip route-static vpn-instance %s %s vpn-instance %s %s %s'
                                            % (self.vrf, self.prefix, maskstr, self.destvrf, self.next_hop))
                else:
                    if self.nhp_interface:
                        self.updates_cmd.append('ip route-static vpn-instance %s %s %s %s %s'
                                                % (self.vrf, self.prefix, maskstr, self.nhp_interface, self.next_hop))
                    else:
                        self.updates_cmd.append('ip route-static vpn-instance %s %s %s %s'
                                                % (self.vrf, self.prefix, maskstr, self.next_hop))
            elif self.destvrf:
                self.updates_cmd.append('ip route-static %s vpn-instance %s %s %s'
                                        % (self.prefix, maskstr, self.destvrf, self.next_hop))
            else:
                if self.nhp_interface:
                    self.updates_cmd.append('ip route-static %s %s %s %s'
                                            % (self.prefix, maskstr, self.nhp_interface, self.next_hop))
                else:
                    self.updates_cmd.append('ip route-static %s %s %s'
                                            % (self.prefix, maskstr, self.next_hop))

            if self.pref:
                self.updates_cmd.append(' preference %s' % (self.prefix))
            if self.tag:
                self.updates_cmd.append(' tag %s' % (self.prefix))
            if self.description:
                self.updates_cmd.append(' description %s' % (self.prefix))

        if self.state == "absent":
            if self.vrf:
                if self.destvrf:
                    self.updates_cmd.append('undo ip route-static vpn-instance %s %s vpn-instance %s %s %s'
                                            % (self.vrf, self.prefix, maskstr, self.destvrf, self.next_hop))
                else:
                    self.updates_cmd.append('undo ip route-static vpn-instance %s %s %s %s'
                                            % (self.vrf, self.prefix, maskstr, self.next_hop))
            elif self.destvrf:
                self.updates_cmd.append('undo ip route-static %s vpn-instance %s %s %s'
                                        % (self.prefix, maskstr, self.destvrf, self.next_hop))
            else:
                self.updates_cmd.append('undo ip route-static %s %s %s'
                                        % (self.prefix, maskstr, self.next_hop))

    def operate_static_route(self, version, prefix, mask, nhp_interface, next_hop, vrf, destvrf, state):
        """ operate ipv4 static route"""

        description_xml = """\n"""
        preference_xml = """\n"""
        tag_xml = """\n"""
        if nhp_interface is None:
            nhp_interface = "Invalid0"

        if vrf is None:
            vpn_instance = "_public_"
        else:
            vpn_instance = vrf

        if destvrf is None:
            dest_vpn_instance = "_public_"
        else:
            dest_vpn_instance = destvrf
        if self.description:
            description_xml = CE_NC_SET_DESCRIPTION % self.description
        if self.pref:
            preference_xml = CE_NC_SET_PREFERENCE % self.pref
        if self.tag:
            tag_xml = CE_NC_SET_TAG % self.tag

        if state == "present":
            configxmlstr = CE_NC_SET_STATIC_ROUTE % (
                vpn_instance, version, prefix, mask, nhp_interface, dest_vpn_instance, next_hop, description_xml, preference_xml, tag_xml)
        else:
            configxmlstr = CE_NC_DELETE_STATIC_ROUTE % (
                vpn_instance, version, prefix, mask, nhp_interface, dest_vpn_instance, next_hop)

        conf_str = self.build_config_xml(configxmlstr)

        try:
            con_obj = self.netconf.set_config(config=conf_str)
            self.check_response(con_obj, "OPERATE_STATIC_ROUTE")
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def get_static_route(self, version, prefix, mask, nhp_interface, next_hop, vrf, destvrf, state):
        """ operate ipv4 static route"""

        if nhp_interface is None:
            nhp_interface = "Invalid0"

        if vrf is None:
            vpn_instance = "_public_"
        else:
            vpn_instance = vrf

        if destvrf is None:
            dest_vpn_instance = "_public_"
        else:
            dest_vpn_instance = destvrf

        if state == 'absent':
            getxmlstr = CE_NC_GET_STATIC_ROUTE_ABSENT
            xmlstr_new_1 = (vpn_instance.lower(), version, 'base', prefix,
                            mask, dest_vpn_instance.lower(), next_hop, nhp_interface.lower())
        else:
            getxmlstr = CE_NC_GET_STATIC_ROUTE
            xmlstr_new_1 = (vpn_instance.lower(), version, 'base', prefix,
                            mask, dest_vpn_instance.lower(), next_hop, self.pref, self.tag, self.description, nhp_interface.lower())

        try:
            get_obj = self.netconf.get_config(filter=getxmlstr)
        except RPCError as err:
            self.module.fail_json(msg='Error: %s' % err.message)

        if state == 'absent':
            re_find_1 = re.findall(
                r'.*<vrfname>(.*)</vrfname>.*\s.*<aftype>(.*)</aftype>.*\s'
                r'.*<topologyname>(.*)</topologyname>.*\s.*<prefix>(.*)</prefix>.*\s'
                r'.*<masklength>(.*)</masklength>.*\s.*<destvrfname>(.*)</destvrfname>.*\s'
                r'.*<nexthop>(.*)</nexthop>.*\s.*<ifname>(.*)</ifname>.*', get_obj.xml.lower())
        else:
            re_find_1 = re.findall(
                r'.*<vrfname>(.*)</vrfname>.*\s.*<aftype>(.*)</aftype>.*\s'
                r'.*<topologyname>(.*)</topologyname>.*\s.*<prefix>(.*)</prefix>.*\s'
                r'.*<masklength>(.*)</masklength>.*\s.*<destvrfname>(.*)</destvrfname>.*\s'
                r'.*<nexthop>(.*)</nexthop>.*\s.*<preference>(.*)</preference>.*\s'
                r'.*<tag>(.*)</tag>.*\s.*<description>(.*)</description>.*\s'
                r'.*<ifname>(.*)</ifname>.*', get_obj.xml.lower())

        if re_find_1 is None:
            return state == "present"

        if xmlstr_new_1 in re_find_1:
            if state == "present":
                return False
            else:
                return True
        else:
            return state == "present"

    def check_params(self):
        """Check all input params"""
        # prefix, mask, aftype, next_hop, state, check
        if not self.prefix or not self.mask or not self.aftype or not self.next_hop or not self.state:
            self.module.fail_json(
                msg='Error: Prefix or mask or address family type or next_hop or state must be set.')
        # ipv4 prefix and mask check
        if not self.mask.isdigit():
            self.module.fail_json(msg='Error: mask is invalid.')
        if self.aftype == "v4":
            if int(self.mask) > 32 or int(self.mask) < 0:
                self.module.fail_json(
                    msg='Error: ipv4 mask must be an integer between 1 and 32.')
            # next_hop check
            if self.next_hop:
                if not self.is_valid_v4addr(self.next_hop):
                    self.module.fail_json(
                        msg='Error: The %s is not a valid address' % self.next_hop)
        # ipv6 mask check
        if self.aftype == "v6":
            if int(self.mask) > 128 or int(self.mask) < 0:
                self.module.fail_json(
                    msg='Error: ipv6 mask must be an integer between 1 and 128.')
            if self.next_hop:
                if not self.is_valid_v6addr(self.next_hop):
                    self.module.fail_json(
                        msg='Error: The %s is not a valid address' % self.next_hop)
        # address family check
        if not self.is_valid_version(self.aftype):
            self.module.fail_json(
                msg='Error: The %s  can should be present or absent' % self.state)
        # description check
        if self.description:
            if not self.is_valid_description(self.description):
                self.module.fail_json(
                    msg='Error: Dsecription length should be 1 ~ 35,and can not contain "?".')
        # tag check
        if self.tag:
            if not self.is_valid_tag(self.tag):
                self.module.fail_json(
                    msg='Error: Tag should be integer 1 ~ 4294967295.')
        # preference check
        if self.pref:
            if not self.is_valid_preference(self.pref):
                self.module.fail_json(
                    msg='Error: Preference should be integer 1 ~ 255.')
        if self.nhp_interface:
            if self.destvrf:
                self.module.fail_json(
                    msg='Error: Dest vrf dose no support next hop is interface.')
        # convert prefix
        if not self.convert_ip_prefix():
            self.module.fail_json(
                msg='Error: The %s is not a valid address' % self.prefix)

    def set_ip_static_route(self):
        """set ip static route"""
        if not self.changed:
            return
        version = None
        if self.aftype == "v4":
            version = "ipv4unicast"
        else:
            version = "ipv6unicast"
        self.operate_static_route(version, self.prefix, self.mask, self.nhp_interface,
                                  self.next_hop, self.vrf, self.destvrf, self.state)

    def get_ip_static_route(self):
        """get ip static route"""

        if self.aftype == "v4":
            version = "ipv4unicast"
        else:
            version = "ipv6unicast"
        change = self.get_static_route(version, self.prefix, self.mask, self.nhp_interface,
                                       self.next_hop, self.vrf, self.destvrf, self.state)
        return change

    def get_proposed(self):
        """get_proposed"""

        self.proposed['prefix'] = self.prefix
        self.proposed['mask'] = self.mask
        self.proposed['aftype'] = self.aftype
        self.proposed['next_hop'] = self.next_hop
        if self.nhp_interface:
            self.proposed['nhp_interface'] = self.nhp_interface
        else:
            self.proposed['nhp_interface'] = "Invalid0"
        if self.vrf:
            self.proposed['vrf'] = self.vrf
        if self.destvrf:
            self.proposed['destvrf'] = self.destvrf
        if self.tag:
            self.proposed['tag'] = self.tag
        if self.description:
            self.proposed['description'] = self.description
        if self.pref:
            self.proposed['pref'] = self.pref
        self.proposed['state'] = self.state

    def get_existing(self):
        """get_existing"""

        change = None
        change = self.get_ip_static_route()
        if change:
            self.existing['prefix'] = self.prefix
            self.existing['mask'] = self.mask
            self.existing['aftype'] = self.aftype
            self.existing['next_hop'] = self.next_hop
            if self.nhp_interface:
                self.proposed['nhp_interface'] = self.nhp_interface
            else:
                self.proposed['nhp_interface'] = "Invalid0"
            if self.vrf:
                self.existing['vrf'] = self.vrf
            if self.destvrf:
                self.existing['destvrf'] = self.destvrf
            if self.tag:
                self.existing['tag'] = self.tag
            if self.description:
                self.existing['description'] = self.description
            if self.pref:
                self.existing['pref'] = self.pref
            self.changed = True
        else:
            self.existing = dict()
            self.changed = False

    def get_end_state(self):
        """get_end_state"""

        if self.aftype == "v4":
            version = "ipv4unicast"
        else:
            version = "ipv6unicast"
        change_ok = self.get_static_route(version, self.prefix, self.mask, self.nhp_interface,
                                          self.next_hop, self.vrf, self.destvrf, self.state)
        if self.state == "present" and not change_ok:
            self.end_state["prefix"] = self.prefix
            self.end_state["mask"] = self.mask
            self.end_state["aftype"] = self.aftype
            self.end_state["next_hop"] = self.next_hop
            if self.nhp_interface:
                self.proposed['nhp_interface'] = self.nhp_interface
            else:
                self.proposed['nhp_interface'] = "Invalid0"
            if self.vrf:
                self.end_state["vrf"] = self.vrf
            if self.destvrf:
                self.end_state["destvrf"] = self.destvrf
            if self.tag:
                self.end_state["tag"] = self.tag
            if self.description:
                self.end_state["description"] = self.description
            if self.pref:
                self.end_state["pref"] = self.pref
        if self.state == "absent" and not change_ok:
            self.end_state = dict()

    def work(self):
        """worker"""

        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.set_ip_static_route()
        self.set_update_cmd()
        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """main"""

    argument_spec = dict(
        prefix=dict(required=True, type='str'),
        mask=dict(required=True, type='str'),
        aftype=dict(choices=['v4', 'v6'], required=True),
        next_hop=dict(required=True, type='str'),
        nhp_interface=dict(required=False, type='str'),
        vrf=dict(required=False, type='str'),
        destvrf=dict(required=False, type='str'),
        tag=dict(required=False, type='str'),
        description=dict(required=False, type='str'),
        pref=dict(required=False, type='str'),
        state=dict(choices=['absent', 'present'],
                   default='present', required=False),
    )

    interface = CE_StaticRoute(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
