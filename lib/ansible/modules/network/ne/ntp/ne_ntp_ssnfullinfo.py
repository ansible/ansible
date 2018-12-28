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

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

NE_GET_NTPSSNFULLINFO_CONFIG_HEAD = """
<filter type="subtree">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpSsnFullInfos>
          <ntpSsnFullInfo>
"""

NE_GET_NTPSSNFULLINFO_CONFIG_TAIL = """
          </ntpSsnFullInfo>
        </ntpSsnFullInfos>
      </ntp>
    </filter>
"""


class NtpSsnFullInfo(object):
    """NtpSsnFullInfo class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []
        self.config = ''

        self.clockSrc = self.module.params['clockSrc']
        self.vpnName = self.module.params['vpnName']
        self.clockStratum = self.module.params['clockStratum']
        self.clockStatus = self.module.params['clockStatus']
        self.refClockId = self.module.params['refClockId']
        self.localMode = self.module.params['localMode']
        self.localPoll = self.module.params['localPoll']
        self.peerMode = self.module.params['peerMode']
        self.peerPoll = self.module.params['peerPoll']
        self.offset = self.module.params['offset']
        self.delay = self.module.params['delay']
        self.dispersion = self.module.params['dispersion']
        self.rootDelay = self.module.params['rootDelay']
        self.rootDispersion = self.module.params['rootDispersion']
        self.reacheability = self.module.params['reacheability']
        self.syncDist = self.module.params['syncDist']
        self.syncState = self.module.params['syncState']
        self.precision = self.module.params['precision']
        self.version = self.module.params['version']
        self.interfaceId = self.module.params['interfaceId']
        self.refTime = self.module.params['refTime']
        self.orgTime = self.module.params['orgTime']
        self.recvTime = self.module.params['recvTime']
        self.xmitTime = self.module.params['xmitTime']
        self.filterDelay = self.module.params['filterDelay']
        self.filterOffset = self.module.params['filterOffset']
        self.filterDisp = self.module.params['filterDisp']
        self.refClkStatus = self.module.params['refClkStatus']
        self.timeCode = self.module.params['timeCode']
        self.flags = self.module.params['flags']
        self.poll = self.module.params['poll']
        self.when = self.module.params['when']

        self.operation = self.module.params['operation']

    def run(self):
        """Excute task"""

        self.populate_config()
        self.deliver_config()
        self.show_result()

    def show_result(self):
        self.module.exit_json(**self.results)

    def deliver_config(self):
        if 'get' == self.operation:
            xml_str = get_nc_config(self.module, self.config)
        else:
            xml_str = set_nc_config(self.module, self.config)

        self.results["response"].append(xml_str)

    def populate_config(self):
        if 'get' == self.operation:
            self.config = NE_GET_NTPSSNFULLINFO_CONFIG_HEAD

        self.populate_leaf_config()

        if 'get' == self.operation:
            self.config += NE_GET_NTPSSNFULLINFO_CONFIG_TAIL

    def populate_leaf_config(self):
        if self.clockSrc:
            self.config += """<clockSrc>%s</clockSrc>""" % self.clockSrc
        if self.vpnName:
            self.config += """<vpnName>%s</vpnName>""" % self.vpnName
        if self.clockStratum:
            self.config += """<clockStratum>%s</clockStratum>""" % self.clockStratum
        if self.clockStatus:
            self.config += """<clockStatus>%s</clockStatus>""" % self.clockStatus
        if self.refClockId:
            self.config += """<refClockId>%s</refClockId>""" % self.refClockId
        if self.localMode:
            self.config += """<localMode>%s</localMode>""" % self.localMode
        if self.localPoll:
            self.config += """<localPoll>%s</localPoll>""" % self.localPoll
        if self.peerMode:
            self.config += """<peerMode>%s</peerMode>""" % self.peerMode
        if self.peerPoll:
            self.config += """<peerPoll>%s</peerPoll>""" % self.peerPoll
        if self.offset:
            self.config += """<offset>%s</offset>""" % self.offset
        if self.delay:
            self.config += """<delay>%s</delay>""" % self.delay
        if self.dispersion:
            self.config += """<dispersion>%s</dispersion>""" % self.dispersion
        if self.rootDelay:
            self.config += """<rootDelay>%s</rootDelay>""" % self.rootDelay
        if self.rootDispersion:
            self.config += """<rootDispersion>%s</rootDispersion>""" % self.rootDispersion
        if self.reacheability:
            self.config += """<reacheability>%s</reacheability>""" % self.reacheability
        if self.syncDist:
            self.config += """<syncDist>%s</syncDist>""" % self.syncDist
        if self.syncState:
            self.config += """<syncState>%s</syncState>""" % self.syncState
        if self.precision:
            self.config += """<precision>%s</precision>""" % self.precision
        if self.version:
            self.config += """<version>%s</version>""" % self.version
        if self.interfaceId:
            self.config += """<interfaceId>%s</interfaceId>""" % self.interfaceId
        if self.refTime:
            self.config += """<refTime>%s</refTime>""" % self.refTime
        if self.orgTime:
            self.config += """<orgTime>%s</orgTime>""" % self.orgTime
        if self.recvTime:
            self.config += """<recvTime>%s</recvTime>""" % self.recvTime
        if self.xmitTime:
            self.config += """<xmitTime>%s</xmitTime>""" % self.xmitTime
        if self.filterDelay:
            self.config += """<filterDelay>%s</filterDelay>""" % self.filterDelay
        if self.filterOffset:
            self.config += """<filterOffset>%s</filterOffset>""" % self.filterOffset
        if self.filterDisp:
            self.config += """<filterDisp>%s</filterDisp>""" % self.filterDisp
        if self.refClkStatus:
            self.config += """<refClkStatus>%s</refClkStatus>""" % self.refClkStatus
        if self.timeCode:
            self.config += """<timeCode>%s</timeCode>""" % self.timeCode
        if self.flags:
            self.config += """<flags>%s</flags>""" % self.flags
        if self.poll:
            self.config += """<poll>%s</poll>""" % self.poll
        if self.when:
            self.config += """<when>%s</when>""" % self.when


def main():
    """Main function entry"""

    argument_spec = dict(
        clockSrc=dict(required=False, type='str', default=''),
        vpnName=dict(required=False, type='str'),
        clockStratum=dict(required=False, type='str'),
        clockStatus=dict(required=False, type='str'),
        refClockId=dict(required=False, type='str'),
        localMode=dict(required=False, type='str'),
        localPoll=dict(required=False, type='str'),
        peerMode=dict(required=False, type='str'),
        peerPoll=dict(required=False, type='str'),
        offset=dict(required=False, type='str'),
        delay=dict(required=False, type='str'),
        dispersion=dict(required=False, type='str'),
        rootDelay=dict(required=False, type='str'),
        rootDispersion=dict(required=False, type='str'),
        reacheability=dict(required=False, type='str'),
        syncDist=dict(required=False, type='str'),
        syncState=dict(required=False, type='str'),
        precision=dict(required=False, type='str'),
        version=dict(required=False, type='str'),
        interfaceId=dict(required=False, type='str'),
        refTime=dict(required=False, type='str'),
        orgTime=dict(required=False, type='str'),
        recvTime=dict(required=False, type='str'),
        xmitTime=dict(required=False, type='str'),
        filterDelay=dict(required=False, type='str'),
        filterOffset=dict(required=False, type='str'),
        filterDisp=dict(required=False, type='str'),
        refClkStatus=dict(required=False, type='str'),
        timeCode=dict(required=False, type='str'),
        flags=dict(required=False, type='str'),
        poll=dict(required=False, type='str'),
        when=dict(required=False, type='str'),

        operation=dict(required=False, choices=['get'], default='get')
    )

    argument_spec.update(ne_argument_spec)
    NtpSsnFullInfo_obj = NtpSsnFullInfo(argument_spec)
    NtpSsnFullInfo_obj.run()


if __name__ == '__main__':
    main()
