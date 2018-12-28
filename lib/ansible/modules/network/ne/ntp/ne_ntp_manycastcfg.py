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

NE_GET_NTPMANYCASTCFG_CONFIG_HEAD = """
<filter type="subtree">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpManycastCfgs>
          <ntpManycastCfg>
"""

NE_GET_NTPMANYCASTCFG_CONFIG_TAIL = """
          </ntpManycastCfg>
        </ntpManycastCfgs>
      </ntp>
    </filter>
"""

NE_MERGE_NTPMANYCASTCFG_CONFIG_HEAD = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpManycastCfgs>
          <ntpManycastCfg xc:operation="merge">
"""

NE_MERGE_NTPMANYCASTCFG_CONFIG_TAIL = """
          </ntpManycastCfg>
        </ntpManycastCfgs>
      </ntp>
    </config>
"""

NE_CREATE_NTPMANYCASTCFG_CONFIG_HEAD = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpManycastCfgs>
          <ntpManycastCfg xc:operation="create">
"""

NE_CREATE_NTPMANYCASTCFG_CONFIG_TAIL = """
          </ntpManycastCfg>
        </ntpManycastCfgs>
      </ntp>
    </config>
"""

NE_DELETE_NTPMANYCASTCFG_CONFIG_HEAD = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpManycastCfgs>
          <ntpManycastCfg xc:operation="delete">
"""

NE_DELETE_NTPMANYCASTCFG_CONFIG_TAIL = """
          </ntpManycastCfg>
        </ntpManycastCfgs>
      </ntp>
    </config>
"""


class NtpManycastCfg(object):
    """NtpManycastCfg class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []
        self.config = ''

        self.ifName = self.module.params['ifName']
        self.type = self.module.params['type']
        self.addrFamily = self.module.params['addrFamily']
        self.ipv4Addr = self.module.params['ipv4Addr']
        self.ipv6Addr = self.module.params['ipv6Addr']
        self.ttlValue = self.module.params['ttlValue']
        self.authKeyId = self.module.params['authKeyId']
        self.portNumber = self.module.params['portNumber']

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
            self.config = NE_GET_NTPMANYCASTCFG_CONFIG_HEAD
        elif 'merge' == self.operation:
            self.config = NE_MERGE_NTPMANYCASTCFG_CONFIG_HEAD
        elif 'create' == self.operation:
            self.config = NE_CREATE_NTPMANYCASTCFG_CONFIG_HEAD
        elif 'delete' == self.operation:
            self.config = NE_DELETE_NTPMANYCASTCFG_CONFIG_HEAD

        self.populate_leaf_config()

        if 'get' == self.operation:
            self.config += NE_GET_NTPMANYCASTCFG_CONFIG_TAIL
        elif 'merge' == self.operation:
            self.config += NE_MERGE_NTPMANYCASTCFG_CONFIG_TAIL
        elif 'create' == self.operation:
            self.config += NE_CREATE_NTPMANYCASTCFG_CONFIG_TAIL
        elif 'delete' == self.operation:
            self.config += NE_DELETE_NTPMANYCASTCFG_CONFIG_TAIL

    def populate_leaf_config(self):
        if self.ifName:
            self.config += """<ifName>%s</ifName>""" % self.ifName
        if self.type:
            self.config += """<type>%s</type>""" % self.type
        if self.addrFamily:
            self.config += """<addrFamily>%s</addrFamily>""" % self.addrFamily
        if self.ipv4Addr:
            self.config += """<ipv4Addr>%s</ipv4Addr>""" % self.ipv4Addr
        if self.ipv6Addr:
            self.config += """<ipv6Addr>%s</ipv6Addr>""" % self.ipv6Addr
        if self.ttlValue:
            self.config += """<ttlValue>%s</ttlValue>""" % self.ttlValue
        if self.authKeyId:
            self.config += """<authKeyId>%s</authKeyId>""" % self.authKeyId
        if self.portNumber:
            self.config += """<portNumber>%s</portNumber>""" % self.portNumber


def main():
    """Main function entry"""

    argument_spec = dict(
        ifName=dict(required=False, type='str', default=''),
        type=dict(required=False, type='str'),
        addrFamily=dict(required=False, type='str'),
        ipv4Addr=dict(required=False, type='str'),
        ipv6Addr=dict(required=False, type='str'),
        ttlValue=dict(required=False, type='str'),
        authKeyId=dict(required=False, type='str'),
        portNumber=dict(required=False, type='str'),

        operation=dict(required=False, choices=['get', 'merge', 'create', 'delete'], default='get')
    )

    argument_spec.update(ne_argument_spec)
    NtpManycastCfg_obj = NtpManycastCfg(argument_spec)
    NtpManycastCfg_obj.run()


if __name__ == '__main__':
    main()
