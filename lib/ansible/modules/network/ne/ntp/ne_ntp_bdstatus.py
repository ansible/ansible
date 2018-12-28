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

NE_GET_NTPBDSTATUS_CONFIG_HEAD = """
<filter type="subtree">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpBdStatuss>
          <ntpBdStatus>
"""

NE_GET_NTPBDSTATUS_CONFIG_TAIL = """
          </ntpBdStatus>
        </ntpBdStatuss>
      </ntp>
    </filter>
"""


class NtpBdStatus(object):
    """NtpBdStatus class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []
        self.config = ''

        self.selfNdName = self.module.params['selfNdName']
        self.synNdName = self.module.params['synNdName']
        self.offset = self.module.params['offset']
        self.refTime = self.module.params['refTime']
        self.curTime = self.module.params['curTime']
        self.clockStatus = self.module.params['clockStatus']
        self.isNTPSerConf = self.module.params['isNTPSerConf']
        self.clockPrecision = self.module.params['clockPrecision']
        self.poll = self.module.params['poll']

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
            self.config = NE_GET_NTPBDSTATUS_CONFIG_HEAD

        self.populate_leaf_config()

        if 'get' == self.operation:
            self.config += NE_GET_NTPBDSTATUS_CONFIG_TAIL

    def populate_leaf_config(self):
        if self.selfNdName:
            self.config += """<selfNdName>%s</selfNdName>""" % self.selfNdName
        if self.synNdName:
            self.config += """<synNdName>%s</synNdName>""" % self.synNdName
        if self.offset:
            self.config += """<offset>%s</offset>""" % self.offset
        if self.refTime:
            self.config += """<refTime>%s</refTime>""" % self.refTime
        if self.curTime:
            self.config += """<curTime>%s</curTime>""" % self.curTime
        if self.clockStatus:
            self.config += """<clockStatus>%s</clockStatus>""" % self.clockStatus
        if self.isNTPSerConf:
            self.config += """<isNTPSerConf>%s</isNTPSerConf>""" % self.isNTPSerConf
        if self.clockPrecision:
            self.config += """<clockPrecision>%s</clockPrecision>""" % self.clockPrecision
        if self.poll:
            self.config += """<poll>%s</poll>""" % self.poll


def main():
    """Main function entry"""

    argument_spec = dict(
        selfNdName=dict(required=False, type='str', default=''),
        synNdName=dict(required=False, type='str'),
        offset=dict(required=False, type='str'),
        refTime=dict(required=False, type='str'),
        curTime=dict(required=False, type='str'),
        clockStatus=dict(required=False, type='str'),
        isNTPSerConf=dict(required=False, type='str'),
        clockPrecision=dict(required=False, type='str'),
        poll=dict(required=False, type='str'),

        operation=dict(required=False, choices=['get'], default='get')
    )

    argument_spec.update(ne_argument_spec)
    NtpBdStatus_obj = NtpBdStatus(argument_spec)
    NtpBdStatus_obj.run()


if __name__ == '__main__':
    main()
