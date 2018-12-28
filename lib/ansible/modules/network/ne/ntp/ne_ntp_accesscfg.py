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

NE_GET_NTPACCESSCFG_CONFIG_HEAD = """
<filter type="subtree">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpAccessCfgs>
          <ntpAccessCfg>
"""

NE_GET_NTPACCESSCFG_CONFIG_TAIL = """
          </ntpAccessCfg>
        </ntpAccessCfgs>
      </ntp>
    </filter>
"""

NE_MERGE_NTPACCESSCFG_CONFIG_HEAD = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpAccessCfgs>
          <ntpAccessCfg xc:operation="merge">
"""

NE_MERGE_NTPACCESSCFG_CONFIG_TAIL = """
          </ntpAccessCfg>
        </ntpAccessCfgs>
      </ntp>
    </config>
"""

NE_CREATE_NTPACCESSCFG_CONFIG_HEAD = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpAccessCfgs>
          <ntpAccessCfg xc:operation="create">
"""

NE_CREATE_NTPACCESSCFG_CONFIG_TAIL = """
          </ntpAccessCfg>
        </ntpAccessCfgs>
      </ntp>
    </config>
"""

NE_DELETE_NTPACCESSCFG_CONFIG_HEAD = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpAccessCfgs>
          <ntpAccessCfg xc:operation="delete">
"""

NE_DELETE_NTPACCESSCFG_CONFIG_TAIL = """
          </ntpAccessCfg>
        </ntpAccessCfgs>
      </ntp>
    </config>
"""


class NtpAccessCfg(object):
    """NtpAccessCfg class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []
        self.config = ''

        self.accessLevel = self.module.params['accessLevel']
        self.addrFamily = self.module.params['addrFamily']
        self.aclNumOrName = self.module.params['aclNumOrName']
        self.acl6NumOrName = self.module.params['acl6NumOrName']

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
            self.config = NE_GET_NTPACCESSCFG_CONFIG_HEAD
        elif 'merge' == self.operation:
            self.config = NE_MERGE_NTPACCESSCFG_CONFIG_HEAD
        elif 'create' == self.operation:
            self.config = NE_CREATE_NTPACCESSCFG_CONFIG_HEAD
        elif 'delete' == self.operation:
            self.config = NE_DELETE_NTPACCESSCFG_CONFIG_HEAD

        self.populate_leaf_config()

        if 'get' == self.operation:
            self.config += NE_GET_NTPACCESSCFG_CONFIG_TAIL
        elif 'merge' == self.operation:
            self.config += NE_MERGE_NTPACCESSCFG_CONFIG_TAIL
        elif 'create' == self.operation:
            self.config += NE_CREATE_NTPACCESSCFG_CONFIG_TAIL
        elif 'delete' == self.operation:
            self.config += NE_DELETE_NTPACCESSCFG_CONFIG_TAIL

    def populate_leaf_config(self):
        if self.accessLevel:
            self.config += """<accessLevel>%s</accessLevel>""" % self.accessLevel
        if self.addrFamily:
            self.config += """<addrFamily>%s</addrFamily>""" % self.addrFamily
        if self.aclNumOrName:
            self.config += """<aclNumOrName>%s</aclNumOrName>""" % self.aclNumOrName
        if self.acl6NumOrName:
            self.config += """<acl6NumOrName>%s</acl6NumOrName>""" % self.acl6NumOrName


def main():
    """Main function entry"""

    argument_spec = dict(
        accessLevel=dict(required=False, type='str', default=''),
        addrFamily=dict(required=False, type='str'),
        aclNumOrName=dict(required=False, type='str'),
        acl6NumOrName=dict(required=False, type='str'),

        operation=dict(required=False, choices=['get', 'merge', 'create', 'delete'], default='get')
    )

    argument_spec.update(ne_argument_spec)
    NtpAccessCfg_obj = NtpAccessCfg(argument_spec)
    NtpAccessCfg_obj.run()


if __name__ == '__main__':
    main()
