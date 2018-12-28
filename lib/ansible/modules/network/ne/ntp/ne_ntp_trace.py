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

NE_GET_NTPTRACE_CONFIG_HEAD = """
<filter type="subtree">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpTraces>
          <ntpTrace>
"""

NE_GET_NTPTRACE_CONFIG_TAIL = """
          </ntpTrace>
        </ntpTraces>
      </ntp>
    </filter>
"""


class NtpTrace(object):
    """NtpTrace class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []
        self.config = ''

        self.serverAddr = self.module.params['serverAddr']
        self.refClkAddr = self.module.params['refClkAddr']
        self.clockStratum = self.module.params['clockStratum']
        self.offset = self.module.params['offset']
        self.syncDist = self.module.params['syncDist']

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
            self.config = NE_GET_NTPTRACE_CONFIG_HEAD

        self.populate_leaf_config()

        if 'get' == self.operation:
            self.config += NE_GET_NTPTRACE_CONFIG_TAIL

    def populate_leaf_config(self):
        if self.serverAddr:
            self.config += """<serverAddr>%s</serverAddr>""" % self.serverAddr
        if self.refClkAddr:
            self.config += """<refClkAddr>%s</refClkAddr>""" % self.refClkAddr
        if self.clockStratum:
            self.config += """<clockStratum>%s</clockStratum>""" % self.clockStratum
        if self.offset:
            self.config += """<offset>%s</offset>""" % self.offset
        if self.syncDist:
            self.config += """<syncDist>%s</syncDist>""" % self.syncDist


def main():
    """Main function entry"""

    argument_spec = dict(
        serverAddr=dict(required=False, type='str', default=''),
        refClkAddr=dict(required=False, type='str'),
        clockStratum=dict(required=False, type='str'),
        offset=dict(required=False, type='str'),
        syncDist=dict(required=False, type='str'),

        operation=dict(required=False, choices=['get'], default='get')
    )

    argument_spec.update(ne_argument_spec)
    NtpTrace_obj = NtpTrace(argument_spec)
    NtpTrace_obj.run()


if __name__ == '__main__':
    main()
