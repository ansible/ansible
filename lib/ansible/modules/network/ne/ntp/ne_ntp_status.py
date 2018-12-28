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

NE_GET_NTPSTATUS_CONFIG_HEAD = """
<filter type="subtree">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
          <ntpStatus>
"""

NE_GET_NTPSTATUS_CONFIG_TAIL = """
          </ntpStatus>
      </ntp>
    </filter>
"""


class NtpStatus(object):
    """NtpStatus class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []
        self.config = ''

        self.clockStatus = self.module.params['clockStatus']
        self.clockStratum = self.module.params['clockStratum']
        self.clockSrc = self.module.params['clockSrc']
        self.nominamFreq = self.module.params['nominamFreq']
        self.actualFreq = self.module.params['actualFreq']
        self.clockPrecision = self.module.params['clockPrecision']
        self.offset = self.module.params['offset']
        self.rootDelay = self.module.params['rootDelay']
        self.rootDispersion = self.module.params['rootDispersion']
        self.peerDispersion = self.module.params['peerDispersion']
        self.refTime = self.module.params['refTime']
        self.vpnName = self.module.params['vpnName']
        self.syncState = self.module.params['syncState']

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
            self.config = NE_GET_NTPSTATUS_CONFIG_HEAD

        self.populate_leaf_config()

        if 'get' == self.operation:
            self.config += NE_GET_NTPSTATUS_CONFIG_TAIL

    def populate_leaf_config(self):
        if self.clockStatus:
            self.config += """<clockStatus>%s</clockStatus>""" % self.clockStatus
        if self.clockStratum:
            self.config += """<clockStratum>%s</clockStratum>""" % self.clockStratum
        if self.clockSrc:
            self.config += """<clockSrc>%s</clockSrc>""" % self.clockSrc
        if self.nominamFreq:
            self.config += """<nominamFreq>%s</nominamFreq>""" % self.nominamFreq
        if self.actualFreq:
            self.config += """<actualFreq>%s</actualFreq>""" % self.actualFreq
        if self.clockPrecision:
            self.config += """<clockPrecision>%s</clockPrecision>""" % self.clockPrecision
        if self.offset:
            self.config += """<offset>%s</offset>""" % self.offset
        if self.rootDelay:
            self.config += """<rootDelay>%s</rootDelay>""" % self.rootDelay
        if self.rootDispersion:
            self.config += """<rootDispersion>%s</rootDispersion>""" % self.rootDispersion
        if self.peerDispersion:
            self.config += """<peerDispersion>%s</peerDispersion>""" % self.peerDispersion
        if self.refTime:
            self.config += """<refTime>%s</refTime>""" % self.refTime
        if self.vpnName:
            self.config += """<vpnName>%s</vpnName>""" % self.vpnName
        if self.syncState:
            self.config += """<syncState>%s</syncState>""" % self.syncState


def main():
    """Main function entry"""

    argument_spec = dict(
        clockStatus=dict(required=False, type='str', default=''),
        clockStratum=dict(required=False, type='str'),
        clockSrc=dict(required=False, type='str'),
        nominamFreq=dict(required=False, type='str'),
        actualFreq=dict(required=False, type='str'),
        clockPrecision=dict(required=False, type='str'),
        offset=dict(required=False, type='str'),
        rootDelay=dict(required=False, type='str'),
        rootDispersion=dict(required=False, type='str'),
        peerDispersion=dict(required=False, type='str'),
        refTime=dict(required=False, type='str'),
        vpnName=dict(required=False, type='str'),
        syncState=dict(required=False, type='str'),

        operation=dict(required=False, choices=['get'], default='get')
    )

    argument_spec.update(ne_argument_spec)
    NtpStatus_obj = NtpStatus(argument_spec)
    NtpStatus_obj.run()


if __name__ == '__main__':
    main()
