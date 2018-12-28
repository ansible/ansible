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

NE_GET_NTPSYSTEMCFG_CONFIG_HEAD = """
<filter type="subtree">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
          <ntpSystemCfg>
"""

NE_GET_NTPSYSTEMCFG_CONFIG_TAIL = """
          </ntpSystemCfg>
      </ntp>
    </filter>
"""

NE_MERGE_NTPSYSTEMCFG_CONFIG_HEAD = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
          <ntpSystemCfg xc:operation="merge">
"""

NE_MERGE_NTPSYSTEMCFG_CONFIG_TAIL = """
          </ntpSystemCfg>
      </ntp>
    </config>
"""


class NtpSystemCfg(object):
    """NtpSystemCfg class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []
        self.config = ''

        self.isAuthEnable = self.module.params['isAuthEnable']
        self.maxSessCount = self.module.params['maxSessCount']
        self.isKodEnable = self.module.params['isKodEnable']
        self.syncInterval = self.module.params['syncInterval']
        self.minDiscardIntvl = self.module.params['minDiscardIntvl']
        self.avgDiscardIntvl = self.module.params['avgDiscardIntvl']
        self.localPort = self.module.params['localPort']
        self.maxDistance = self.module.params['maxDistance']
        self.maxOffset = self.module.params['maxOffset']

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
            self.config = NE_GET_NTPSYSTEMCFG_CONFIG_HEAD
        elif 'merge' == self.operation:
            self.config = NE_MERGE_NTPSYSTEMCFG_CONFIG_HEAD

        self.populate_leaf_config()

        if 'get' == self.operation:
            self.config += NE_GET_NTPSYSTEMCFG_CONFIG_TAIL
        elif 'merge' == self.operation:
            self.config += NE_MERGE_NTPSYSTEMCFG_CONFIG_TAIL

    def populate_leaf_config(self):
        if self.isAuthEnable:
            self.config += """<isAuthEnable>%s</isAuthEnable>""" % self.isAuthEnable
        if self.maxSessCount:
            self.config += """<maxSessCount>%s</maxSessCount>""" % self.maxSessCount
        if self.isKodEnable:
            self.config += """<isKodEnable>%s</isKodEnable>""" % self.isKodEnable
        if self.syncInterval:
            self.config += """<syncInterval>%s</syncInterval>""" % self.syncInterval
        if self.minDiscardIntvl:
            self.config += """<minDiscardIntvl>%s</minDiscardIntvl>""" % self.minDiscardIntvl
        if self.avgDiscardIntvl:
            self.config += """<avgDiscardIntvl>%s</avgDiscardIntvl>""" % self.avgDiscardIntvl
        if self.localPort:
            self.config += """<localPort>%s</localPort>""" % self.localPort
        if self.maxDistance:
            self.config += """<maxDistance>%s</maxDistance>""" % self.maxDistance
        if self.maxOffset:
            self.config += """<maxOffset>%s</maxOffset>""" % self.maxOffset


def main():
    """Main function entry"""

    argument_spec = dict(
        isAuthEnable=dict(required=False, type='str', default=''),
        maxSessCount=dict(required=False, type='str'),
        isKodEnable=dict(required=False, type='str'),
        syncInterval=dict(required=False, type='str'),
        minDiscardIntvl=dict(required=False, type='str'),
        avgDiscardIntvl=dict(required=False, type='str'),
        localPort=dict(required=False, type='str'),
        maxDistance=dict(required=False, type='str'),
        maxOffset=dict(required=False, type='str'),

        operation=dict(required=False, choices=['get', 'merge'], default='get')
    )

    argument_spec.update(ne_argument_spec)
    NtpSystemCfg_obj = NtpSystemCfg(argument_spec)
    NtpSystemCfg_obj.run()


if __name__ == '__main__':
    main()
