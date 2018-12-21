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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_ospf_vrf
version_added: "2.4"
short_description: Manages configuration of an OSPF VPN instance on HUAWEI CloudEngine switches.
description:
    - Manages configuration of an OSPF VPN instance on HUAWEI CloudEngine switches.
author: Yang yang (@QijunPan)
options:
    ospf:
        description:
            - The ID of the ospf process.
              Valid values are an integer, 1 - 4294967295, the default value is 1.
        required: true
    route_id:
        description:
            - Specifies the ospf private route id,.
              Valid values are a string, formatted as an IP address
              (i.e. "10.1.1.1") the length is 0 - 20.
    vrf:
        description:
            - Specifies the vpn instance which use ospf,length is 1 - 31.
              Valid values are a string.
        default: _public_
    description:
        description:
            - Specifies the description information of ospf process.
    bandwidth:
        description:
            - Specifies the reference bandwidth used to assign ospf cost.
              Valid values are an integer, in Mbps, 1 - 2147483648, the default value is 100.
    lsaalflag:
        description:
            - Specifies the mode of timer to calculate interval of arrive LSA.
              If set the parameter but not specifies value, the default will be used.
              If true use general timer.
              If false use intelligent timer.
        type: bool
        default: 'no'
    lsaainterval:
        description:
            - Specifies the interval of arrive LSA when use the general timer.
              Valid value is an integer, in millisecond, from 0 to 10000.
    lsaamaxinterval:
        description:
            - Specifies the max interval of arrive LSA when use the intelligent timer.
              Valid value is an integer, in millisecond, from 0 to 10000, the default value is 1000.
    lsaastartinterval:
        description:
            - Specifies the start interval of arrive LSA when use the intelligent timer.
              Valid value is an integer, in millisecond, from 0 to 10000, the default value is 500.
    lsaaholdinterval:
        description:
            - Specifies the hold interval of arrive LSA when use the intelligent timer.
              Valid value is an integer, in millisecond, from 0 to 10000, the default value is 500.
    lsaointervalflag:
        description:
            - Specifies whether cancel the interval of LSA originate or not.
              If set the parameter but noe specifies value, the default will be used.
              true:cancel the interval of LSA originate, the interval is 0.
              false:do not cancel the interval of LSA originate.
        type: bool
        default: 'no'
    lsaointerval:
        description:
            - Specifies the interval of originate LSA .
              Valid value is an integer, in second, from 0 to 10, the default value is 5.
    lsaomaxinterval:
        description:
            - Specifies the max interval of originate LSA .
              Valid value is an integer, in millisecond, from 1 to 10000, the default value is 5000.
    lsaostartinterval:
        description:
            - Specifies the start interval of originate LSA .
              Valid value is an integer, in millisecond, from 0 to 1000, the default value is 500.
    lsaoholdinterval:
        description:
            - Specifies the hold interval of originate LSA .
              Valid value is an integer, in millisecond, from 0 to 5000, the default value is 1000.
    spfintervaltype:
        description:
            - Specifies the mode of timer which used to calculate SPF.
              If set the parameter but noe specifies value, the default will be used.
              If is intelligent-timer, then use intelligent timer.
              If is timer, then use second level timer.
              If is millisecond, then use millisecond level timer.
        choices: ['intelligent-timer','timer','millisecond']
        default: intelligent-timer
    spfinterval:
        description:
            - Specifies the interval to calculate SPF when use second level  timer.
              Valid value is an integer, in second, from 1 to 10.
    spfintervalmi:
        description:
            - Specifies the interval to calculate SPF when use millisecond level  timer.
              Valid value is an integer, in millisecond, from 1 to 10000.
    spfmaxinterval:
        description:
            - Specifies the max interval to calculate SPF when use intelligent timer.
              Valid value is an integer, in millisecond, from 1 to 20000, the default value is 5000.
    spfstartinterval:
        description:
            - Specifies the start interval to calculate SPF when use intelligent timer.
              Valid value is an integer, in millisecond, from 1 to 1000, the default value is 50.
    spfholdinterval:
        description:
            - Specifies the hold interval to calculate SPF when use intelligent timer.
              Valid value is an integer, in millisecond, from 1 to 5000, the default value is 200.
    state:
        description:
            - Specify desired state of the resource.
        choices: ['present', 'absent']
        default: present
'''

EXAMPLES = '''
- name: ospf vrf module test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: Configure ospf route id
    ce_ospf_vrf:
      ospf: 2
      route_id: 2.2.2.2
      lsaointervalflag: False
      lsaointerval: 2
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {
        "bandwidth": "100",
        "description": null,
        "lsaaholdinterval": "500",
        "lsaainterval": null,
        "lsaamaxinterval": "1000",
        "lsaastartinterval": "500",
        "lsaalflag": "False",
        "lsaoholdinterval": "1000",
        "lsaointerval": "2",
        "lsaointervalflag": "False",
        "lsaomaxinterval": "5000",
        "lsaostartinterval": "500",
        "process_id": "2",
        "route_id": "2.2.2.2",
        "spfholdinterval": "1000",
        "spfinterval": null,
        "spfintervalmi": null,
        "spfintervaltype": "intelligent-timer",
        "spfmaxinterval": "10000",
        "spfstartinterval": "500",
        "vrf": "_public_"
    }
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {
                "bandwidthReference": "100",
                "description": null,
                "lsaArrivalFlag": "false",
                "lsaArrivalHoldInterval": "500",
                "lsaArrivalInterval": null,
                "lsaArrivalMaxInterval": "1000",
                "lsaArrivalStartInterval": "500",
                "lsaOriginateHoldInterval": "1000",
                "lsaOriginateInterval": "2",
                "lsaOriginateIntervalFlag": "false",
                "lsaOriginateMaxInterval": "5000",
                "lsaOriginateStartInterval": "500",
                "processId": "2",
                "routerId": "2.2.2.2",
                "spfScheduleHoldInterval": "1000",
                "spfScheduleInterval": null,
                "spfScheduleIntervalMillisecond": null,
                "spfScheduleIntervalType": "intelligent-timer",
                "spfScheduleMaxInterval": "10000",
                "spfScheduleStartInterval": "500",
                "vrfName": "_public_"
            }
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {
                "bandwidthReference": "100",
                "description": null,
                "lsaArrivalFlag": "false",
                "lsaArrivalHoldInterval": "500",
                "lsaArrivalInterval": null,
                "lsaArrivalMaxInterval": "1000",
                "lsaArrivalStartInterval": "500",
                "lsaOriginateHoldInterval": "1000",
                "lsaOriginateInterval": "2",
                "lsaOriginateIntervalFlag": "false",
                "lsaOriginateMaxInterval": "5000",
                "lsaOriginateStartInterval": "500",
                "processId": "2",
                "routerId": "2.2.2.2",
                "spfScheduleHoldInterval": "1000",
                "spfScheduleInterval": null,
                "spfScheduleIntervalMillisecond": null,
                "spfScheduleIntervalType": "intelligent-timer",
                "spfScheduleMaxInterval": "10000",
                "spfScheduleStartInterval": "500",
                "vrfName": "_public_"
            }
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["ospf 2"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: False
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec

CE_NC_GET_OSPF_VRF = """
    <filter type="subtree">
      <ospfv2 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <ospfv2comm>
          <ospfSites>
            <ospfSite>
              <processId></processId>
              <routerId></routerId>
              <vrfName></vrfName>
              <description></description>
              <bandwidthReference></bandwidthReference>
              <lsaArrivalFlag></lsaArrivalFlag>
              <lsaArrivalInterval></lsaArrivalInterval>
              <lsaArrivalMaxInterval></lsaArrivalMaxInterval>
              <lsaArrivalStartInterval></lsaArrivalStartInterval>
              <lsaArrivalHoldInterval></lsaArrivalHoldInterval>
              <lsaOriginateIntervalFlag></lsaOriginateIntervalFlag>
              <lsaOriginateInterval></lsaOriginateInterval>
              <lsaOriginateMaxInterval></lsaOriginateMaxInterval>
              <lsaOriginateStartInterval></lsaOriginateStartInterval>
              <lsaOriginateHoldInterval></lsaOriginateHoldInterval>
              <spfScheduleIntervalType></spfScheduleIntervalType>
              <spfScheduleInterval></spfScheduleInterval>
              <spfScheduleIntervalMillisecond></spfScheduleIntervalMillisecond>
              <spfScheduleMaxInterval></spfScheduleMaxInterval>
              <spfScheduleStartInterval></spfScheduleStartInterval>
              <spfScheduleHoldInterval></spfScheduleHoldInterval>
            </ospfSite>
          </ospfSites>
        </ospfv2comm>
      </ospfv2>
    </filter>
"""

CE_NC_CREATE_OSPF_VRF = """
      <ospfv2 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <ospfv2comm>
          <ospfSites>
            <ospfSite operation="merge">
              <processId>%s</processId>
%s
              <vrfName>%s</vrfName>
              <description>%s</description>
              <bandwidthReference>%s</bandwidthReference>
              <lsaArrivalFlag>%s</lsaArrivalFlag>
              <lsaArrivalInterval>%s</lsaArrivalInterval>
              <lsaArrivalMaxInterval>%s</lsaArrivalMaxInterval>
              <lsaArrivalStartInterval>%s</lsaArrivalStartInterval>
              <lsaArrivalHoldInterval>%s</lsaArrivalHoldInterval>
              <lsaOriginateIntervalFlag>%s</lsaOriginateIntervalFlag>
              <lsaOriginateInterval>%s</lsaOriginateInterval>
              <lsaOriginateMaxInterval>%s</lsaOriginateMaxInterval>
              <lsaOriginateStartInterval>%s</lsaOriginateStartInterval>
              <lsaOriginateHoldInterval>%s</lsaOriginateHoldInterval>
              <spfScheduleIntervalType>%s</spfScheduleIntervalType>
              <spfScheduleInterval>%s</spfScheduleInterval>
              <spfScheduleIntervalMillisecond>%s</spfScheduleIntervalMillisecond>
              <spfScheduleMaxInterval>%s</spfScheduleMaxInterval>
              <spfScheduleStartInterval>%s</spfScheduleStartInterval>
              <spfScheduleHoldInterval>%s</spfScheduleHoldInterval>
            </ospfSite>
          </ospfSites>
        </ospfv2comm>
      </ospfv2>
"""
CE_NC_CREATE_ROUTE_ID = """
              <routerId>%s</routerId>
"""

CE_NC_DELETE_OSPF = """
      <ospfv2 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <ospfv2comm>
          <ospfSites>
            <ospfSite operation="delete">
              <processId>%s</processId>
              <routerId>%s</routerId>
              <vrfName>%s</vrfName>
            </ospfSite>
          </ospfSites>
        </ospfv2comm>
      </ospfv2>
"""


def build_config_xml(xmlstr):
    """build_config_xml"""

    return '<config> ' + xmlstr + ' </config>'


class OspfVrf(object):
    """
    Manages configuration of an ospf instance.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.ospf = self.module.params['ospf']
        self.route_id = self.module.params['route_id']
        self.vrf = self.module.params['vrf']
        self.description = self.module.params['description']
        self.bandwidth = self.module.params['bandwidth']
        self.lsaalflag = self.module.params['lsaalflag']
        self.lsaainterval = self.module.params['lsaainterval']
        self.lsaamaxinterval = self.module.params['lsaamaxinterval']
        self.lsaastartinterval = self.module.params['lsaastartinterval']
        self.lsaaholdinterval = self.module.params['lsaaholdinterval']
        self.lsaointervalflag = self.module.params['lsaointervalflag']
        self.lsaointerval = self.module.params['lsaointerval']
        self.lsaomaxinterval = self.module.params['lsaomaxinterval']
        self.lsaostartinterval = self.module.params['lsaostartinterval']
        self.lsaoholdinterval = self.module.params['lsaoholdinterval']
        self.spfintervaltype = self.module.params['spfintervaltype']
        self.spfinterval = self.module.params['spfinterval']
        self.spfintervalmi = self.module.params['spfintervalmi']
        self.spfmaxinterval = self.module.params['spfmaxinterval']
        self.spfstartinterval = self.module.params['spfstartinterval']
        self.spfholdinterval = self.module.params['spfholdinterval']
        self.state = self.module.params['state']

        # ospf info
        self.ospf_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()
        self.lsa_arrival_changed = False
        self.lsa_originate_changed = False
        self.spf_changed = False
        self.route_id_changed = False
        self.bandwidth_changed = False
        self.description_changed = False
        self.vrf_changed = False

    def init_module(self):
        """" init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def is_valid_ospf_process_id(self):
        """check whether the input ospf process id is valid"""

        if not self.ospf.isdigit():
            return False
        if int(self.ospf) > 4294967295 or int(self.ospf) < 1:
            return False
        return True

    def is_valid_ospf_route_id(self):
        """check is ipv4 addr is valid"""

        if self.route_id.find('.') != -1:
            addr_list = self.route_id.split('.')
            if len(addr_list) != 4:
                return False
            for each_num in addr_list:
                if not each_num.isdigit():
                    return False
                if int(each_num) > 255:
                    return False
            return True
        return False

    def is_valid_vrf_name(self):
        """check whether the input ospf vrf name is valid"""

        if len(self.vrf) > 31 or len(self.vrf) < 1:
            return False
        if self.vrf.find('?') != -1:
            return False
        if self.vrf.find(' ') != -1:
            return False
        return True

    def is_valid_description(self):
        """check whether the input ospf description is valid"""

        if len(self.description) > 80 or len(self.description) < 1:
            return False
        if self.description.find('?') != -1:
            return False
        return True

    def is_valid_bandwidth(self):
        """check whether the input ospf bandwidth reference is valid"""

        if not self.bandwidth.isdigit():
            return False
        if int(self.bandwidth) > 2147483648 or int(self.bandwidth) < 1:
            return False
        return True

    def is_valid_lsa_arrival_interval(self):
        """check whether the input ospf lsa arrival interval is valid"""

        if self.lsaainterval is None:
            return False
        if not self.lsaainterval.isdigit():
            return False
        if int(self.lsaainterval) > 10000 or int(self.lsaainterval) < 0:
            return False
        return True

    def isvalidlsamaxarrivalinterval(self):
        """check whether the input ospf lsa max arrival interval is valid"""

        if not self.lsaamaxinterval.isdigit():
            return False
        if int(self.lsaamaxinterval) > 10000 or int(self.lsaamaxinterval) < 1:
            return False
        return True

    def isvalidlsastartarrivalinterval(self):
        """check whether the input ospf lsa start arrival interval is valid"""

        if not self.lsaastartinterval.isdigit():
            return False
        if int(self.lsaastartinterval) > 1000 or int(self.lsaastartinterval) < 0:
            return False
        return True

    def isvalidlsaholdarrivalinterval(self):
        """check whether the input ospf lsa hold arrival interval is valid"""

        if not self.lsaaholdinterval.isdigit():
            return False
        if int(self.lsaaholdinterval) > 5000 or int(self.lsaaholdinterval) < 0:
            return False
        return True

    def is_valid_lsa_originate_interval(self):
        """check whether the input ospf lsa originate interval is valid"""

        if not self.lsaointerval.isdigit():
            return False
        if int(self.lsaointerval) > 10 or int(self.lsaointerval) < 0:
            return False
        return True

    def isvalidlsaoriginatemaxinterval(self):
        """check whether the input ospf lsa originate max interval is valid"""

        if not self.lsaomaxinterval.isdigit():
            return False
        if int(self.lsaomaxinterval) > 10000 or int(self.lsaomaxinterval) < 1:
            return False
        return True

    def isvalidlsaostartinterval(self):
        """check whether the input ospf lsa originate start interval is valid"""

        if not self.lsaostartinterval.isdigit():
            return False
        if int(self.lsaostartinterval) > 1000 or int(self.lsaostartinterval) < 0:
            return False
        return True

    def isvalidlsaoholdinterval(self):
        """check whether the input ospf lsa originate hold interval is valid"""

        if not self.lsaoholdinterval.isdigit():
            return False
        if int(self.lsaoholdinterval) > 5000 or int(self.lsaoholdinterval) < 1:
            return False
        return True

    def is_valid_spf_interval(self):
        """check whether the input ospf spf interval is valid"""

        if not self.spfinterval.isdigit():
            return False
        if int(self.spfinterval) > 10 or int(self.spfinterval) < 1:
            return False
        return True

    def is_valid_spf_milli_interval(self):
        """check whether the input ospf spf millisecond level interval is valid"""

        if not self.spfintervalmi.isdigit():
            return False
        if int(self.spfintervalmi) > 10000 or int(self.spfintervalmi) < 1:
            return False
        return True

    def is_valid_spf_max_interval(self):
        """check whether the input ospf spf intelligent timer max interval is valid"""

        if not self.spfmaxinterval.isdigit():
            return False
        if int(self.spfmaxinterval) > 20000 or int(self.spfmaxinterval) < 1:
            return False
        return True

    def is_valid_spf_start_interval(self):
        """check whether the input ospf spf intelligent timer start interval is valid"""

        if not self.spfstartinterval.isdigit():
            return False
        if int(self.spfstartinterval) > 1000 or int(self.spfstartinterval) < 1:
            return False
        return True

    def is_valid_spf_hold_interval(self):
        """check whether the input ospf spf intelligent timer hold interval is valid"""

        if not self.spfholdinterval.isdigit():
            return False
        if int(self.spfholdinterval) > 5000 or int(self.spfholdinterval) < 1:
            return False
        return True

    def is_route_id_exist(self):
        """is route id exist"""

        if not self.ospf_info:
            return False

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] != self.ospf:
                continue
            if ospf_site["routerId"] == self.route_id:
                return True
            else:
                continue
        return False

    def get_exist_ospf_id(self):
        """get exist ospf process id"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["processId"]
            else:
                continue
        return None

    def get_exist_route(self):
        """get exist route id"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["routerId"]
            else:
                continue
        return None

    def get_exist_vrf(self):
        """get exist vrf"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["vrfName"]
            else:
                continue
        return None

    def get_exist_bandwidth(self):
        """get exist bandwidth"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["bandwidthReference"]
            else:
                continue
        return None

    def get_exist_lsa_a_interval(self):
        """get exist lsa arrival interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaArrivalInterval"]
            else:
                continue
        return None

    def get_exist_lsa_a_interval_flag(self):
        """get exist lsa arrival interval flag"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaArrivalFlag"]
            else:
                continue
        return None

    def get_exist_lsa_a_max_interval(self):
        """get exist lsa arrival max interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaArrivalMaxInterval"]
            else:
                continue
        return None

    def get_exist_lsa_a_start_interval(self):
        """get exist lsa arrival start interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaArrivalStartInterval"]
            else:
                continue
        return None

    def get_exist_lsa_a_hold_interval(self):
        """get exist lsa arrival hold interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaArrivalHoldInterval"]
            else:
                continue
        return None

    def getexistlsaointerval(self):
        """get exist lsa originate interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaOriginateInterval"]
            else:
                continue
        return None

    def getexistlsaointerval_flag(self):
        """get exist lsa originate interval flag"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaOriginateIntervalFlag"]
            else:
                continue
        return None

    def getexistlsaomaxinterval(self):
        """get exist lsa originate max interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaOriginateMaxInterval"]
            else:
                continue
        return None

    def getexistlsaostartinterval(self):
        """get exist lsa originate start interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaOriginateStartInterval"]
            else:
                continue
        return None

    def getexistlsaoholdinterval(self):
        """get exist lsa originate hold interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["lsaOriginateHoldInterval"]
            else:
                continue
        return None

    def get_exist_spf_interval(self):
        """get exist spf second level timer interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["spfScheduleInterval"]
            else:
                continue
        return None

    def get_exist_spf_milli_interval(self):
        """get exist spf millisecond level timer interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["spfScheduleIntervalMillisecond"]
            else:
                continue
        return None

    def get_exist_spf_max_interval(self):
        """get exist spf max interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["spfScheduleMaxInterval"]
            else:
                continue
        return None

    def get_exist_spf_start_interval(self):
        """get exist spf start interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["spfScheduleStartInterval"]
            else:
                continue
        return None

    def get_exist_spf_hold_interval(self):
        """get exist spf hold interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["spfScheduleHoldInterval"]
            else:
                continue
        return None

    def get_exist_spf_interval_type(self):
        """get exist spf hold interval"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["spfScheduleIntervalType"]
            else:
                continue
        return None

    def is_ospf_exist(self):
        """is ospf exist"""

        if not self.ospf_info:
            return False

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return True
            else:
                continue
        return False

    def get_exist_description(self):
        """is description exist"""

        if not self.ospf_info:
            return None

        for ospf_site in self.ospf_info["ospfsite"]:
            if ospf_site["processId"] == self.ospf:
                return ospf_site["description"]
            else:
                continue
        return None

    def check_params(self):
        """Check all input params"""

        if self.ospf == '':
            self.module.fail_json(
                msg='Error: The ospf process id should not be null.')
        if self.ospf:
            if not self.is_valid_ospf_process_id():
                self.module.fail_json(
                    msg='Error: The ospf process id should between 1 - 4294967295.')
        if self.route_id == '':
            self.module.fail_json(
                msg='Error: The ospf route id length should not be null.')
        if self.route_id:
            if not self.is_valid_ospf_route_id():
                self.module.fail_json(
                    msg='Error: The ospf route id length should between 0 - 20,i.e.10.1.1.1.')
        if self.vrf == '':
            self.module.fail_json(
                msg='Error: The ospf vpn instance length should not be null.')
        if self.vrf:
            if not self.is_valid_vrf_name():
                self.module.fail_json(
                    msg='Error: The ospf vpn instance length should between 0 - 31,but can not contain " " or "?".')
        if self.description == '':
            self.module.fail_json(
                msg='Error: The ospf description should not be null.')
        if self.description:
            if not self.is_valid_description():
                self.module.fail_json(
                    msg='Error: The ospf description length should between 1 - 80,but can not contain "?".')
        if self.bandwidth == '':
            self.module.fail_json(
                msg='Error: The ospf bandwidth reference should not be null.')
        if self.bandwidth:
            if not self.is_valid_bandwidth():
                self.module.fail_json(
                    msg='Error: The ospf bandwidth reference should between 1 - 2147483648.')
        if self.lsaalflag is True:
            if not self.is_valid_lsa_arrival_interval():
                self.module.fail_json(
                    msg='Error: The ospf lsa arrival interval should between 0 - 10000.')
            if self.lsaamaxinterval or self.lsaastartinterval or self.lsaaholdinterval:
                self.module.fail_json(
                    msg='Error: Non-Intelligent Timer and Intelligent Timer Interval of '
                        'lsa-arrival-interval can not configured at the same time.')
        if self.lsaalflag is False:
            if self.lsaainterval:
                self.module.fail_json(
                    msg='Error: The parameter of lsa arrival interval command is invalid, '
                    'because LSA arrival interval can not be config when the LSA arrival flag is not set.')
            if self.lsaamaxinterval == '' or self.lsaastartinterval == '' or self.lsaaholdinterval == '':
                self.module.fail_json(
                    msg='Error: The ospf lsa arrival intervals should not be null.')
            if self.lsaamaxinterval:
                if not self.isvalidlsamaxarrivalinterval():
                    self.module.fail_json(
                        msg='Error: The ospf lsa arrival max interval should between 1 - 10000.')
            if self.lsaastartinterval:
                if not self.isvalidlsastartarrivalinterval():
                    self.module.fail_json(
                        msg='Error: The ospf lsa arrival start interval should between 1 - 1000.')
            if self.lsaaholdinterval:
                if not self.isvalidlsaholdarrivalinterval():
                    self.module.fail_json(
                        msg='Error: The ospf lsa arrival hold interval should between 1 - 5000.')
        if self.lsaointervalflag is True:
            if self.lsaointerval or self.lsaomaxinterval \
                    or self.lsaostartinterval or self.lsaoholdinterval:
                self.module.fail_json(
                    msg='Error: Interval for other-type and Instantly Flag '
                        'of lsa-originate-interval can not configured at the same time.')
        if self.lsaointerval == '':
            self.module.fail_json(
                msg='Error: The ospf lsa originate interval should should not be null.')
        if self.lsaointerval:
            if not self.is_valid_lsa_originate_interval():
                self.module.fail_json(
                    msg='Error: The ospf lsa originate interval should between 0 - 10 s.')
        if self.lsaomaxinterval == '' or self.lsaostartinterval == '' or self.lsaoholdinterval == '':
            self.module.fail_json(
                msg='Error: The ospf lsa originate intelligent intervals should should not be null.')
        if self.lsaomaxinterval:
            if not self.isvalidlsaoriginatemaxinterval():
                self.module.fail_json(
                    msg='Error: The ospf lsa originate max interval should between 1 - 10000 ms.')
        if self.lsaostartinterval:
            if not self.isvalidlsaostartinterval():
                self.module.fail_json(
                    msg='Error: The ospf lsa originate start interval should between 0 - 1000 ms.')
        if self.lsaoholdinterval:
            if not self.isvalidlsaoholdinterval():
                self.module.fail_json(
                    msg='Error: The ospf lsa originate hold interval should between 1 - 5000 ms.')
        if self.spfintervaltype == '':
            self.module.fail_json(
                msg='Error: The ospf spf interval type should should not be null.')
        if self.spfintervaltype == 'intelligent-timer':
            if self.spfinterval is not None or self.spfintervalmi is not None:
                self.module.fail_json(
                    msg='Error: Interval second and interval millisecond '
                        'of spf-schedule-interval can not configured if use intelligent timer.')
            if self.spfmaxinterval == '' or self.spfstartinterval == '' or self.spfholdinterval == '':
                self.module.fail_json(
                    msg='Error: The ospf spf intelligent timer intervals should should not be null.')
            if self.spfmaxinterval and not self.is_valid_spf_max_interval():
                self.module.fail_json(
                    msg='Error: The ospf spf max interval of intelligent timer should between 1 - 20000 ms.')
            if self.spfstartinterval and not self.is_valid_spf_start_interval():
                self.module.fail_json(
                    msg='Error: The ospf spf start interval of intelligent timer should between 1 - 1000 ms.')
            if self.spfholdinterval and not self.is_valid_spf_hold_interval():
                self.module.fail_json(
                    msg='Error: The ospf spf hold interval of intelligent timer should between 1 - 5000 ms.')
        if self.spfintervaltype == 'timer':
            if self.spfintervalmi is not None:
                self.module.fail_json(
                    msg='Error: Interval second and interval millisecond '
                        'of spf-schedule-interval can not configured at the same time.')
            if self.spfmaxinterval or self.spfstartinterval or self.spfholdinterval:
                self.module.fail_json(
                    msg='Error: Interval second and interval intelligent '
                        'of spf-schedule-interval can not configured at the same time.')
            if self.spfinterval == '' or self.spfinterval is None:
                self.module.fail_json(
                    msg='Error: The ospf spf timer intervals should should not be null.')
            if not self.is_valid_spf_interval():
                self.module.fail_json(
                    msg='Error: Interval second should between 1 - 10 s.')
        if self.spfintervaltype == 'millisecond':
            if self.spfinterval is not None:
                self.module.fail_json(
                    msg='Error: Interval millisecond and interval second '
                        'of spf-schedule-interval can not configured at the same time.')
            if self.spfmaxinterval or self.spfstartinterval or self.spfholdinterval:
                self.module.fail_json(
                    msg='Error: Interval millisecond and interval intelligent '
                        'of spf-schedule-interval can not configured at the same time.')
            if self.spfintervalmi == '' or self.spfintervalmi is None:
                self.module.fail_json(
                    msg='Error: The ospf spf millisecond intervals should should not be null.')
            if not self.is_valid_spf_milli_interval():
                self.module.fail_json(
                    msg='Error: Interval millisecond should between 1 - 10000 ms.')

    def get_ospf_info(self):
        """ get the detail information of ospf """

        self.ospf_info["ospfsite"] = list()

        getxmlstr = CE_NC_GET_OSPF_VRF
        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        root = ElementTree.fromstring(xml_str)

        # get the vpn address family and RD text
        ospf_sites = root.findall(
            "data/ospfv2/ospfv2comm/ospfSites/ospfSite")
        if ospf_sites:
            for ospf_site in ospf_sites:
                ospf_ele_info = dict()
                for ospf_site_ele in ospf_site:
                    if ospf_site_ele.tag in ["processId", "routerId", "vrfName", "bandwidthReference",
                                             "description", "lsaArrivalInterval", "lsaArrivalMaxInterval",
                                             "lsaArrivalStartInterval", "lsaArrivalHoldInterval", "lsaArrivalFlag",
                                             "lsaOriginateInterval", "lsaOriginateMaxInterval",
                                             "lsaOriginateStartInterval", "lsaOriginateHoldInterval",
                                             "lsaOriginateIntervalFlag", "spfScheduleInterval",
                                             "spfScheduleIntervalMillisecond", "spfScheduleMaxInterval",
                                             "spfScheduleStartInterval", "spfScheduleHoldInterval",
                                             "spfScheduleIntervalType"]:
                        ospf_ele_info[
                            ospf_site_ele.tag] = ospf_site_ele.text
                self.ospf_info["ospfsite"].append(ospf_ele_info)

    def get_proposed(self):
        """get proposed info"""

        self.proposed["process_id"] = self.ospf
        self.proposed["route_id"] = self.route_id
        self.proposed["vrf"] = self.vrf
        self.proposed["description"] = self.description
        self.proposed["bandwidth"] = self.bandwidth
        self.proposed["lsaalflag"] = self.lsaalflag
        self.proposed["lsaainterval"] = self.lsaainterval
        self.proposed["lsaamaxinterval"] = self.lsaamaxinterval
        self.proposed["lsaastartinterval"] = self.lsaastartinterval
        self.proposed["lsaaholdinterval"] = self.lsaaholdinterval
        self.proposed["lsaointervalflag"] = self.lsaointervalflag
        self.proposed["lsaointerval"] = self.lsaointerval
        self.proposed["lsaomaxinterval"] = self.lsaomaxinterval
        self.proposed["lsaostartinterval"] = self.lsaostartinterval
        self.proposed["lsaoholdinterval"] = self.lsaoholdinterval
        self.proposed["spfintervaltype"] = self.spfintervaltype
        self.proposed["spfinterval"] = self.spfinterval
        self.proposed["spfintervalmi"] = self.spfintervalmi
        self.proposed["spfmaxinterval"] = self.spfmaxinterval
        self.proposed["spfstartinterval"] = self.spfstartinterval
        self.proposed["spfholdinterval"] = self.spfholdinterval

    def operate_ospf_info(self):
        """operate ospf info"""

        config_route_id_xml = ''
        vrf = self.get_exist_vrf()
        if vrf is None:
            vrf = '_public_'
        description = self.get_exist_description()
        if description is None:
            description = ''
        bandwidth_reference = self.get_exist_bandwidth()
        if bandwidth_reference is None:
            bandwidth_reference = '100'
        lsa_in_interval = self.get_exist_lsa_a_interval()
        if lsa_in_interval is None:
            lsa_in_interval = ''
        lsa_arrival_max_interval = self.get_exist_lsa_a_max_interval()
        if lsa_arrival_max_interval is None:
            lsa_arrival_max_interval = '1000'
        lsa_arrival_start_interval = self.get_exist_lsa_a_start_interval()
        if lsa_arrival_start_interval is None:
            lsa_arrival_start_interval = '500'
        lsa_arrival_hold_interval = self.get_exist_lsa_a_hold_interval()
        if lsa_arrival_hold_interval is None:
            lsa_arrival_hold_interval = '500'
        lsa_originate_interval = self.getexistlsaointerval()
        if lsa_originate_interval is None:
            lsa_originate_interval = '5'
        lsa_originate_max_interval = self.getexistlsaomaxinterval()
        if lsa_originate_max_interval is None:
            lsa_originate_max_interval = '5000'
        lsa_originate_start_interval = self.getexistlsaostartinterval()
        if lsa_originate_start_interval is None:
            lsa_originate_start_interval = '500'
        lsa_originate_hold_interval = self.getexistlsaoholdinterval()
        if lsa_originate_hold_interval is None:
            lsa_originate_hold_interval = '1000'
        spf_interval = self.get_exist_spf_interval()
        if spf_interval is None:
            spf_interval = ''
        spf_interval_milli = self.get_exist_spf_milli_interval()
        if spf_interval_milli is None:
            spf_interval_milli = ''
        spf_max_interval = self.get_exist_spf_max_interval()
        if spf_max_interval is None:
            spf_max_interval = '5000'
        spf_start_interval = self.get_exist_spf_start_interval()
        if spf_start_interval is None:
            spf_start_interval = '50'
        spf_hold_interval = self.get_exist_spf_hold_interval()
        if spf_hold_interval is None:
            spf_hold_interval = '200'

        if self.route_id:
            if self.state == 'present':
                if self.route_id != self.get_exist_route():
                    self.route_id_changed = True
                    config_route_id_xml = CE_NC_CREATE_ROUTE_ID % self.route_id
            else:
                if self.route_id != self.get_exist_route():
                    self.module.fail_json(
                        msg='Error: The route id %s is not exist.' % self.route_id)
                self.route_id_changed = True
                configxmlstr = CE_NC_DELETE_OSPF % (
                    self.ospf, self.get_exist_route(), self.get_exist_vrf())
                conf_str = build_config_xml(configxmlstr)

                recv_xml = set_nc_config(self.module, conf_str)
                self.check_response(recv_xml, "OPERATE_VRF_AF")
                self.changed = True
                return
        if self.vrf != '_public_':
            if self.state == 'present':
                if self.vrf != self.get_exist_vrf():
                    self.vrf_changed = True
                    vrf = self.vrf
            else:
                if self.vrf != self.get_exist_vrf():
                    self.module.fail_json(
                        msg='Error: The vrf %s is not exist.' % self.vrf)
                self.vrf_changed = True
                configxmlstr = CE_NC_DELETE_OSPF % (
                    self.ospf, self.get_exist_route(), self.get_exist_vrf())
                conf_str = build_config_xml(configxmlstr)
                recv_xml = set_nc_config(self.module, conf_str)
                self.check_response(recv_xml, "OPERATE_VRF_AF")
                self.changed = True
                return
        if self.bandwidth:
            if self.state == 'present':
                if self.bandwidth != self.get_exist_bandwidth():
                    self.bandwidth_changed = True
                    bandwidth_reference = self.bandwidth
            else:
                if self.bandwidth != self.get_exist_bandwidth():
                    self.module.fail_json(
                        msg='Error: The bandwidth %s is not exist.' % self.bandwidth)
                if self.get_exist_bandwidth() != '100':
                    self.bandwidth_changed = True
                    bandwidth_reference = '100'
        if self.description:
            if self.state == 'present':
                if self.description != self.get_exist_description():
                    self.description_changed = True
                    description = self.description
            else:
                if self.description != self.get_exist_description():
                    self.module.fail_json(
                        msg='Error: The description %s is not exist.' % self.description)
                self.description_changed = True
                description = ''

        if self.lsaalflag is False:
            lsa_in_interval = ''
            if self.state == 'present':
                if self.lsaamaxinterval:
                    if self.lsaamaxinterval != self.get_exist_lsa_a_max_interval():
                        self.lsa_arrival_changed = True
                        lsa_arrival_max_interval = self.lsaamaxinterval
                if self.lsaastartinterval:
                    if self.lsaastartinterval != self.get_exist_lsa_a_start_interval():
                        self.lsa_arrival_changed = True
                        lsa_arrival_start_interval = self.lsaastartinterval
                if self.lsaaholdinterval:
                    if self.lsaaholdinterval != self.get_exist_lsa_a_hold_interval():
                        self.lsa_arrival_changed = True
                        lsa_arrival_hold_interval = self.lsaaholdinterval
            else:
                if self.lsaamaxinterval:
                    if self.lsaamaxinterval != self.get_exist_lsa_a_max_interval():
                        self.module.fail_json(
                            msg='Error: The lsaamaxinterval %s is not exist.' % self.lsaamaxinterval)
                    if self.get_exist_lsa_a_max_interval() != '1000':
                        lsa_arrival_max_interval = '1000'
                        self.lsa_arrival_changed = True
                if self.lsaastartinterval:
                    if self.lsaastartinterval != self.get_exist_lsa_a_start_interval():
                        self.module.fail_json(
                            msg='Error: The lsaastartinterval %s is not exist.' % self.lsaastartinterval)
                    if self.get_exist_lsa_a_start_interval() != '500':
                        lsa_arrival_start_interval = '500'
                        self.lsa_arrival_changed = True
                if self.lsaaholdinterval:
                    if self.lsaaholdinterval != self.get_exist_lsa_a_hold_interval():
                        self.module.fail_json(
                            msg='Error: The lsaaholdinterval %s is not exist.' % self.lsaaholdinterval)
                    if self.get_exist_lsa_a_hold_interval() != '500':
                        lsa_arrival_hold_interval = '500'
                        self.lsa_arrival_changed = True
        else:
            if self.state == 'present':
                lsaalflag = "false"
                if self.lsaalflag is True:
                    lsaalflag = "true"
                if lsaalflag != self.get_exist_lsa_a_interval_flag():
                    self.lsa_arrival_changed = True
                    if self.lsaainterval is None:
                        self.module.fail_json(
                            msg='Error: The lsaainterval is not supplied.')
                    else:
                        lsa_in_interval = self.lsaainterval
                else:
                    if self.lsaainterval:
                        if self.lsaainterval != self.get_exist_lsa_a_interval():
                            self.lsa_arrival_changed = True
                            lsa_in_interval = self.lsaainterval
            else:
                if self.lsaainterval:
                    if self.lsaainterval != self.get_exist_lsa_a_interval():
                        self.module.fail_json(
                            msg='Error: The lsaainterval %s is not exist.' % self.lsaainterval)
                    self.lsaalflag = False
                    lsa_in_interval = ''
                    self.lsa_arrival_changed = True

        if self.lsaointervalflag is False:
            if self.state == 'present':
                if self.lsaomaxinterval:
                    if self.lsaomaxinterval != self.getexistlsaomaxinterval():
                        self.lsa_originate_changed = True
                        lsa_originate_max_interval = self.lsaomaxinterval
                if self.lsaostartinterval:
                    if self.lsaostartinterval != self.getexistlsaostartinterval():
                        self.lsa_originate_changed = True
                        lsa_originate_start_interval = self.lsaostartinterval
                if self.lsaoholdinterval:
                    if self.lsaoholdinterval != self.getexistlsaoholdinterval():
                        self.lsa_originate_changed = True
                        lsa_originate_hold_interval = self.lsaoholdinterval
                if self.lsaointerval:
                    if self.lsaointerval != self.getexistlsaointerval():
                        self.lsa_originate_changed = True
                        lsa_originate_interval = self.lsaointerval
            else:
                if self.lsaomaxinterval:
                    if self.lsaomaxinterval != self.getexistlsaomaxinterval():
                        self.module.fail_json(
                            msg='Error: The lsaomaxinterval %s is not exist.' % self.lsaomaxinterval)
                    if self.getexistlsaomaxinterval() != '5000':
                        lsa_originate_max_interval = '5000'
                        self.lsa_originate_changed = True
                if self.lsaostartinterval:
                    if self.lsaostartinterval != self.getexistlsaostartinterval():
                        self.module.fail_json(
                            msg='Error: The lsaostartinterval %s is not exist.' % self.lsaostartinterval)
                    if self.getexistlsaostartinterval() != '500':
                        lsa_originate_start_interval = '500'
                        self.lsa_originate_changed = True
                if self.lsaoholdinterval:
                    if self.lsaoholdinterval != self.getexistlsaoholdinterval():
                        self.module.fail_json(
                            msg='Error: The lsaoholdinterval %s is not exist.' % self.lsaoholdinterval)
                    if self.getexistlsaoholdinterval() != '1000':
                        lsa_originate_hold_interval = '1000'
                        self.lsa_originate_changed = True
                if self.lsaointerval:
                    if self.lsaointerval != self.getexistlsaointerval():
                        self.module.fail_json(
                            msg='Error: The lsaointerval %s is not exist.' % self.lsaointerval)
                    if self.getexistlsaointerval() != '5':
                        lsa_originate_interval = '5'
                        self.lsa_originate_changed = True
        else:
            if self.state == 'present':
                if self.getexistlsaointerval_flag() != 'true':
                    self.lsa_originate_changed = True
                    lsa_originate_interval = '5'
                    lsa_originate_max_interval = '5000'
                    lsa_originate_start_interval = '500'
                    lsa_originate_hold_interval = '1000'
            else:
                if self.getexistlsaointerval_flag() == 'true':
                    self.lsaointervalflag = False
                    self.lsa_originate_changed = True
        if self.spfintervaltype != self.get_exist_spf_interval_type():
            self.spf_changed = True
        if self.spfintervaltype == 'timer':
            if self.spfinterval:
                if self.state == 'present':
                    if self.spfinterval != self.get_exist_spf_interval():
                        self.spf_changed = True
                        spf_interval = self.spfinterval
                        spf_interval_milli = ''
                else:
                    if self.spfinterval != self.get_exist_spf_interval():
                        self.module.fail_json(
                            msg='Error: The spfinterval %s is not exist.' % self.spfinterval)
                    self.spfintervaltype = 'intelligent-timer'
                    spf_interval = ''
                    self.spf_changed = True
        if self.spfintervaltype == 'millisecond':
            if self.spfintervalmi:
                if self.state == 'present':
                    if self.spfintervalmi != self.get_exist_spf_milli_interval():
                        self.spf_changed = True
                        spf_interval_milli = self.spfintervalmi
                        spf_interval = ''
                else:
                    if self.spfintervalmi != self.get_exist_spf_milli_interval():
                        self.module.fail_json(
                            msg='Error: The spfintervalmi %s is not exist.' % self.spfintervalmi)
                    self.spfintervaltype = 'intelligent-timer'
                    spf_interval_milli = ''
                    self.spf_changed = True
        if self.spfintervaltype == 'intelligent-timer':
            spf_interval = ''
            spf_interval_milli = ''
            if self.spfmaxinterval:
                if self.state == 'present':
                    if self.spfmaxinterval != self.get_exist_spf_max_interval():
                        self.spf_changed = True
                        spf_max_interval = self.spfmaxinterval
                else:
                    if self.spfmaxinterval != self.get_exist_spf_max_interval():
                        self.module.fail_json(
                            msg='Error: The spfmaxinterval %s is not exist.' % self.spfmaxinterval)
                    if self.get_exist_spf_max_interval() != '5000':
                        self.spf_changed = True
                        spf_max_interval = '5000'
            if self.spfstartinterval:
                if self.state == 'present':
                    if self.spfstartinterval != self.get_exist_spf_start_interval():
                        self.spf_changed = True
                        spf_start_interval = self.spfstartinterval
                else:
                    if self.spfstartinterval != self.get_exist_spf_start_interval():
                        self.module.fail_json(
                            msg='Error: The spfstartinterval %s is not exist.' % self.spfstartinterval)
                    if self.get_exist_spf_start_interval() != '50':
                        self.spf_changed = True
                        spf_start_interval = '50'
            if self.spfholdinterval:
                if self.state == 'present':
                    if self.spfholdinterval != self.get_exist_spf_hold_interval():
                        self.spf_changed = True
                        spf_hold_interval = self.spfholdinterval
                else:
                    if self.spfholdinterval != self.get_exist_spf_hold_interval():
                        self.module.fail_json(
                            msg='Error: The spfholdinterval %s is not exist.' % self.spfholdinterval)
                    if self.get_exist_spf_hold_interval() != '200':
                        self.spf_changed = True
                        spf_hold_interval = '200'

        if not self.description_changed and not self.vrf_changed and not self.lsa_arrival_changed \
                and not self.lsa_originate_changed and not self.spf_changed \
                and not self.route_id_changed and not self.bandwidth_changed:
            self.changed = False
            return
        else:
            self.changed = True
        lsaointervalflag = "false"
        lsaalflag = "false"
        if self.lsaointervalflag is True:
            lsaointervalflag = "true"
        if self.lsaalflag is True:
            lsaalflag = "true"
        configxmlstr = CE_NC_CREATE_OSPF_VRF % (
            self.ospf, config_route_id_xml, vrf,
            description, bandwidth_reference, lsaalflag,
            lsa_in_interval, lsa_arrival_max_interval, lsa_arrival_start_interval,
            lsa_arrival_hold_interval, lsaointervalflag, lsa_originate_interval,
            lsa_originate_max_interval, lsa_originate_start_interval, lsa_originate_hold_interval,
            self.spfintervaltype, spf_interval, spf_interval_milli,
            spf_max_interval, spf_start_interval, spf_hold_interval)

        conf_str = build_config_xml(configxmlstr)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "OPERATE_VRF_AF")

    def get_existing(self):
        """get existing info"""

        self.get_ospf_info()
        self.existing['ospf_info'] = self.ospf_info["ospfsite"]

    def set_update_cmd(self):
        """ set update command"""
        if not self.changed:
            return

        if self.state == 'present':
            if self.vrf_changed:
                if self.vrf != '_public_':
                    if self.route_id_changed:
                        self.updates_cmd.append(
                            'ospf %s router-id %s vpn-instance %s' % (self.ospf, self.route_id, self.vrf))
                    else:
                        self.updates_cmd.append(
                            'ospf %s vpn-instance %s ' % (self.ospf, self.vrf))
                else:
                    if self.route_id_changed:
                        self.updates_cmd.append(
                            'ospf %s router-id %s' % (self.ospf, self.route_id))
            else:
                if self.route_id_changed:
                    if self.vrf != '_public_':
                        self.updates_cmd.append(
                            'ospf %s router-id %s vpn-instance %s' % (self.ospf, self.route_id, self.get_exist_vrf()))
                    else:
                        self.updates_cmd.append(
                            'ospf %s router-id %s' % (self.ospf, self.route_id))
        else:
            if self.route_id_changed:
                self.updates_cmd.append('undo ospf %s' % self.ospf)
                return

        self.updates_cmd.append('ospf %s' % self.ospf)

        if self.description:
            if self.state == 'present':
                if self.description_changed:
                    self.updates_cmd.append(
                        'description %s' % self.description)
            else:
                if self.description_changed:
                    self.updates_cmd.append('undo description')
        if self.bandwidth_changed:
            if self.state == 'present':
                if self.get_exist_bandwidth() != '100':
                    self.updates_cmd.append(
                        'bandwidth-reference %s' % (self.get_exist_bandwidth()))
            else:
                self.updates_cmd.append('undo bandwidth-reference')
        if self.lsaalflag is True:
            if self.lsa_arrival_changed:
                if self.state == 'present':
                    self.updates_cmd.append(
                        'lsa-arrival-interval %s' % (self.get_exist_lsa_a_interval()))
                else:
                    self.updates_cmd.append(
                        'undo lsa-arrival-interval')

        if self.lsaalflag is False:
            if self.lsa_arrival_changed:
                if self.state == 'present':
                    if self.get_exist_lsa_a_max_interval() != '1000' \
                            or self.get_exist_lsa_a_start_interval() != '500'\
                            or self.get_exist_lsa_a_hold_interval() != '500':
                        self.updates_cmd.append('lsa-arrival-interval intelligent-timer %s %s %s'
                                                % (self.get_exist_lsa_a_max_interval(),
                                                   self.get_exist_lsa_a_start_interval(),
                                                   self.get_exist_lsa_a_hold_interval()))
                else:
                    if self.get_exist_lsa_a_max_interval() == '1000' \
                            and self.get_exist_lsa_a_start_interval() == '500'\
                            and self.get_exist_lsa_a_hold_interval() == '500':
                        self.updates_cmd.append(
                            'undo lsa-arrival-interval')
        if self.lsaointervalflag is False:
            if self.lsa_originate_changed:
                if self.state == 'present':
                    if self.getexistlsaointerval() != '5' \
                            or self.getexistlsaomaxinterval() != '5000' \
                            or self.getexistlsaostartinterval() != '500' \
                            or self.getexistlsaoholdinterval() != '1000':
                        self.updates_cmd.append('lsa-originate-interval other-type %s intelligent-timer %s %s %s'
                                                % (self.getexistlsaointerval(),
                                                   self.getexistlsaomaxinterval(),
                                                   self.getexistlsaostartinterval(),
                                                   self.getexistlsaoholdinterval()))
                else:
                    self.updates_cmd.append(
                        'undo lsa-originate-interval')
        if self.lsaointervalflag is True:
            if self.lsa_originate_changed:
                if self.state == 'present':
                    self.updates_cmd.append('lsa-originate-interval 0 ')
                else:
                    self.updates_cmd.append(
                        'undo lsa-originate-interval')
        if self.spfintervaltype == 'millisecond':
            if self.spf_changed:
                if self.state == 'present':
                    self.updates_cmd.append(
                        'spf-schedule-interval millisecond %s' % self.get_exist_spf_milli_interval())
                else:
                    self.updates_cmd.append(
                        'undo spf-schedule-interval')
        if self.spfintervaltype == 'timer':
            if self.spf_changed:
                if self.state == 'present':
                    self.updates_cmd.append(
                        'spf-schedule-interval %s' % self.get_exist_spf_interval())
                else:
                    self.updates_cmd.append(
                        'undo spf-schedule-interval')
        if self.spfintervaltype == 'intelligent-timer':
            if self.spf_changed:
                if self.state == 'present':
                    if self.get_exist_spf_max_interval() != '5000' \
                            or self.get_exist_spf_start_interval() != '50' \
                            or self.get_exist_spf_hold_interval() != '200':
                        self.updates_cmd.append('spf-schedule-interval intelligent-timer %s %s %s'
                                                % (self.get_exist_spf_max_interval(),
                                                   self.get_exist_spf_start_interval(),
                                                   self.get_exist_spf_hold_interval()))
                else:
                    self.updates_cmd.append(
                        'undo spf-schedule-interval')

    def get_end_state(self):
        """get end state info"""

        self.get_ospf_info()
        self.end_state['ospf_info'] = self.ospf_info["ospfsite"]

    def work(self):
        """worker"""

        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.operate_ospf_info()
        self.get_end_state()
        self.set_update_cmd()
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
    """Module main"""

    argument_spec = dict(
        ospf=dict(required=True, type='str'),
        route_id=dict(required=False, type='str'),
        vrf=dict(required=False, type='str', default='_public_'),
        description=dict(required=False, type='str'),
        bandwidth=dict(required=False, type='str'),
        lsaalflag=dict(type='bool', default=False),
        lsaainterval=dict(required=False, type='str'),
        lsaamaxinterval=dict(required=False, type='str'),
        lsaastartinterval=dict(required=False, type='str'),
        lsaaholdinterval=dict(required=False, type='str'),
        lsaointervalflag=dict(type='bool', default=False),
        lsaointerval=dict(required=False, type='str'),
        lsaomaxinterval=dict(required=False, type='str'),
        lsaostartinterval=dict(required=False, type='str'),
        lsaoholdinterval=dict(required=False, type='str'),
        spfintervaltype=dict(required=False, default='intelligent-timer',
                             choices=['intelligent-timer', 'timer', 'millisecond']),
        spfinterval=dict(required=False, type='str'),
        spfintervalmi=dict(required=False, type='str'),
        spfmaxinterval=dict(required=False, type='str'),
        spfstartinterval=dict(required=False, type='str'),
        spfholdinterval=dict(required=False, type='str'),
        state=dict(required=False, choices=['present', 'absent'], default='present'),
    )

    argument_spec.update(ce_argument_spec)
    module = OspfVrf(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
