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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_is_is_instance
version_added: "2.10"
author: xuxiaowei0512 (@CloudEngine-Ansible)
short_description: Manages isis process id configuration on HUAWEI CloudEngine devices.
description:
    - Manages  isis process id, creates a isis instance id or deletes a process id on HUAWEI CloudEngine devices.
options:
  instance_id:
    description:
      - Specifies the id of a isis process.The value is a number of 1 to 4294967295.
    required: true
    type: int
  vpn_name:
    description:
      - VPN Instance, Associate the VPN instance with the corresponding IS-IS process.
    required: false
    type: str
  state:
    description:
      - Determines whether the config should be present or not on the device.
    required: false
    default: present
    type: str
    choices: ['present', 'absent']
'''

EXAMPLES = '''
  - name: Set isis process
    ce_is_is_instance:
      instance_id: 3
      state: present

  - name: Unset isis process
    ce_is_is_instance:
      instance_id: 3
      state: absent

  - name: check isis process
    ce_is_is_instance:
      instance_id: 4294967296
      state: present

  - name: Set vpn name
    ce_is_is_instance:
      instance_id: 22
      vpn_name: vpn1
      state: present

  - name: check vpn name
    ce_is_is_instance:
      instance_id: 22
      vpn_name: vpn1234567896321452212221556asdasdasdasdsadvdv
      state: present
'''

RETURN = '''
proposed:
  description: k/v pairs of parameters passed into module
  returned: always
  type: dict
  sample: {
      "instance_id": 1,
      "vpn_name": null
  }
existing:
  description: k/v pairs of existing configuration
  returned: always
  type: dict
  sample: {
      "session": {}
  }
end_state:
  description: k/v pairs of configuration after module execution
  returned: always
  type: dict
  sample: {
      "session": {
          "instance_id": 1,
          "vpn_name": null
      }
  }
updates:
  description: commands sent to the device
  returned: always
  type: list
  sample: [
      "isis 1"
  ]
changed:
  description: check to see if a change was made on the device
  returned: always
  type: bool
  sample: true
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config

CE_NC_GET_ISIS = """
    <filter type="subtree">
      <isiscomm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
      %s
      </isiscomm>
    </filter>
"""

CE_NC_GET_ISIS_INSTANCE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <vpnName></vpnName>
          </isSite>
        </isSites>
"""


def is_valid_ip_vpn(vpname):
    """check ip vpn"""

    if not vpname:
        return False

    if vpname == "_public_":
        return False

    if len(vpname) < 1 or len(vpname) > 31:
        return False

    return True


class ISIS_Instance(object):
    """Manages ISIS Instance"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.instance_id = self.module.params['instance_id']
        self.vpn_name = self.module.params['vpn_name']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.isis_dict = dict()
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """init module"""
        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def get_isis_dict(self):
        """isis config dict"""
        isis_dict = dict()
        isis_dict["instance"] = dict()
        conf_str = CE_NC_GET_ISIS % (
            (CE_NC_GET_ISIS_INSTANCE % self.instance_id))

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return isis_dict

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)

        # get isis info
        glb = root.find("isiscomm/isSites/isSite")
        if glb:
            for attr in glb:
                isis_dict["instance"][attr.tag] = attr.text

        return isis_dict

    def config_session(self):
        """configures isis"""
        xml_str = ""
        instance = self.isis_dict["instance"]
        if not self.instance_id:
            return xml_str

        if self.state == "present":
            xml_str = "<instanceId>%s</instanceId>" % self.instance_id
            self.updates_cmd.append("isis %s" % self.instance_id)

            if self.vpn_name:
                xml_str += "<vpnName>%s</vpnName>" % self.vpn_name
                self.updates_cmd.append("vpn-instance %s" % self.vpn_name)
        else:
            # absent
            if self.instance_id and str(self.instance_id) == instance.get("instanceId"):
                xml_str = "<instanceId>%s</instanceId>" % self.instance_id
                self.updates_cmd.append("undo isis %s" % self.instance_id)

        if self.state == "present":
            return '<isSites><isSite operation="merge">' + xml_str + '</isSite></isSites>'
        else:
            if xml_str:
                return '<isSites><isSite operation="delete">' + xml_str + '</isSite></isSites>'

    def netconf_load_config(self, xml_str):
        """load isis config by netconf"""

        if not xml_str:
            return

        xml_cfg = """
            <config>
            <isiscomm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
            %s
            </isiscomm>
            </config>""" % xml_str
        set_nc_config(self.module, xml_cfg)
        self.changed = True

    def check_params(self):
        """Check all input params"""

        # check instance id
        if not self.instance_id:
            self.module.fail_json(msg="Error: Missing required arguments: instance_id.")

        if self.instance_id:
            if self.instance_id < 1 or self.instance_id > 4294967295:
                self.module.fail_json(msg="Error: Instance id is not ranges from 1 to 4294967295.")

        # check vpn_name
        if self.vpn_name:
            if not is_valid_ip_vpn(self.vpn_name):
                self.module.fail_json(msg="Error: Session vpn_name is invalid.")

    def get_proposed(self):
        """get proposed info"""
        # base config
        self.proposed["instance_id"] = self.instance_id
        self.proposed["vpn_name"] = self.vpn_name
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if not self.isis_dict:
            self.existing["instance"] = None

        self.existing["instance"] = self.isis_dict.get("instance")

    def get_end_state(self):
        """get end state info"""

        isis_dict = self.get_isis_dict()
        if not isis_dict:
            self.end_state["instance"] = None

        self.end_state["instance"] = isis_dict.get("instance")

        if self.end_state == self.existing:
            self.changed = False

    def work(self):
        """worker"""
        self.check_params()
        self.isis_dict = self.get_isis_dict()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        xml_str = ''
        if self.instance_id:
            cfg_str = self.config_session()
            if cfg_str:
                xml_str += cfg_str

        # update to device
        if xml_str:
            self.netconf_load_config(xml_str)
            self.changed = True

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
    """Module main"""
    argument_spec = dict(
        instance_id=dict(required=True, type='int'),
        vpn_name=dict(required=False, type='str'),
        state=dict(required=False, default='present', choices=['present', 'absent'])
    )

    module = ISIS_Instance(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
