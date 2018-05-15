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
module: ce_vlan
version_added: "2.4"
short_description: Manages VLAN resources and attributes on Huawei CloudEngine switches.
description:
    - Manages VLAN configurations on Huawei CloudEngine switches.
author: QijunPan (@CloudEngine-Ansible)
options:
    vlan_id:
        description:
            - Single VLAN ID, in the range from 1 to 4094.
    vlan_range:
        description:
            - Range of VLANs such as C(2-10) or C(2,5,10-15), etc.
    name:
        description:
            - Name of VLAN, in the range from 1 to 31.
    description:
        description:
            - Specify VLAN description, in the range from 1 to 80.
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- name: vlan module test
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

  - name: Ensure a range of VLANs are not present on the switch
    ce_vlan:
      vlan_range: "2-10,20,50,55-60,100-150"
      state: absent
      provider: "{{ cli }}"

  - name: Ensure VLAN 50 exists with the name WEB
    ce_vlan:
      vlan_id: 50
      name: WEB
      state: absent
      provider: "{{ cli }}"

  - name: Ensure VLAN is NOT on the device
    ce_vlan:
      vlan_id: 50
      state: absent
      provider: "{{ cli }}"

'''

RETURN = '''
proposed_vlans_list:
    description: list of VLANs being proposed
    returned: always
    type: list
    sample: ["100"]
existing_vlans_list:
    description: list of existing VLANs on the switch prior to making changes
    returned: always
    type: list
    sample: ["1", "2", "3", "4", "5", "20"]
end_state_vlans_list:
    description: list of VLANs after the module is executed
    returned: always
    type: list
    sample:  ["1", "2", "3", "4", "5", "20", "100"]
proposed:
    description: k/v pairs of parameters passed into module (does not include
                 vlan_id or vlan_range)
    returned: always
    type: dict
    sample: {"vlan_id":"20", "name": "VLAN_APP", "description": "vlan for app" }
existing:
    description: k/v pairs of existing vlan or null when using vlan_range
    returned: always
    type: dict
    sample: {"vlan_id":"20", "name": "VLAN_APP", "description": "" }
end_state:
    description: k/v pairs of the VLAN after executing module or null
                 when using vlan_range
    returned: always
    type: dict
    sample: {"vlan_id":"20", "name": "VLAN_APP", "description": "vlan for app" }
updates:
    description: command string sent to the device
    returned: always
    type: list
    sample: ["vlan 20", "name VLAN20"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, execute_nc_action, ce_argument_spec

CE_NC_CREATE_VLAN = """
<config>
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vlans>
      <vlan operation="create">
        <vlanId>%s</vlanId>
        <vlanName>%s</vlanName>
        <vlanDesc>%s</vlanDesc>
        <vlanType></vlanType>
        <subVlans/>
      </vlan>
    </vlans>
  </vlan>
</config>
"""

CE_NC_DELETE_VLAN = """
<config>
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vlans>
      <vlan operation="delete">
        <vlanId>%s</vlanId>
      </vlan>
    </vlans>
  </vlan>
</config>
"""

CE_NC_MERGE_VLAN_DES = """
<config>
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vlans>
      <vlan operation="merge">
        <vlanId>%s</vlanId>
        <vlanDesc>%s</vlanDesc>
        <vlanType></vlanType>
        <subVlans/>
      </vlan>
    </vlans>
  </vlan>
</config>
"""

CE_NC_MERGE_VLAN_NAME = """
<config>
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vlans>
      <vlan operation="merge">
        <vlanId>%s</vlanId>
        <vlanName>%s</vlanName>
        <vlanType></vlanType>
        <subVlans/>
      </vlan>
    </vlans>
  </vlan>
</config>
"""


CE_NC_MERGE_VLAN = """
<config>
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vlans>
      <vlan operation="merge">
        <vlanId>%s</vlanId>
        <vlanName>%s</vlanName>
        <vlanDesc>%s</vlanDesc>
        <vlanType></vlanType>
        <subVlans/>
      </vlan>
    </vlans>
  </vlan>
</config>
"""

CE_NC_GET_VLAN = """
<filter type="subtree">
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vlans>
      <vlan>
        <vlanId>%s</vlanId>
        <vlanDesc/>
        <vlanName/>
      </vlan>
    </vlans>
  </vlan>
</filter>
"""

CE_NC_GET_VLANS = """
<filter type="subtree">
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vlans>
      <vlan>
        <vlanId/>
        <vlanName/>
      </vlan>
    </vlans>
  </vlan>
</filter>
"""

CE_NC_CREATE_VLAN_BATCH = """
<action>
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <shVlanBatchCrt>
      <vlans>%s:%s</vlans>
    </shVlanBatchCrt>
  </vlan>
</action>
"""

CE_NC_DELETE_VLAN_BATCH = """
<action>
  <vlan xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <shVlanBatchDel>
      <vlans>%s:%s</vlans>
    </shVlanBatchDel>
  </vlan>
</action>
"""


class Vlan(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # vlan config info
        self.vlan_id = self.module.params['vlan_id']
        self.vlan_range = self.module.params['vlan_range']
        self.name = self.module.params['name']
        self.description = self.module.params['description']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.vlan_exist = False
        self.vlan_attr_exist = None
        self.vlans_list_exist = list()
        self.vlans_list_change = list()
        self.updates_cmd = list()
        self.results = dict()
        self.vlan_attr_end = dict()

    def init_module(self):
        """
        init ansible NetworkModule.
        """

        required_one_of = [["vlan_id", "vlan_range"]]
        mutually_exclusive = [["vlan_id", "vlan_range"]]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def config_vlan(self, vlan_id, name='', description=''):
        """Create vlan."""

        if name is None:
            name = ''
        if description is None:
            description = ''

        conf_str = CE_NC_CREATE_VLAN % (vlan_id, name, description)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CREATE_VLAN")
        self.changed = True

    def merge_vlan(self, vlan_id, name, description):
        """Merge vlan."""

        conf_str = None

        if not name and description:
            conf_str = CE_NC_MERGE_VLAN_DES % (vlan_id, description)
        if not description and name:
            conf_str = CE_NC_MERGE_VLAN_NAME % (vlan_id, name)
        if description and name:
            conf_str = CE_NC_MERGE_VLAN % (vlan_id, name, description)

        if not conf_str:
            return

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "MERGE_VLAN")
        self.changed = True

    def create_vlan_batch(self, vlan_list):
        """Create vlan batch."""

        if not vlan_list:
            return

        vlan_bitmap = self.vlan_list_to_bitmap(vlan_list)
        xmlstr = CE_NC_CREATE_VLAN_BATCH % (vlan_bitmap, vlan_bitmap)

        recv_xml = execute_nc_action(self.module, xmlstr)
        self.check_response(recv_xml, "CREATE_VLAN_BATCH")
        self.updates_cmd.append('vlan batch %s' % (
            self.vlan_range.replace(',', ' ').replace('-', ' to ')))
        self.changed = True

    def delete_vlan_batch(self, vlan_list):
        """Delete vlan batch."""

        if not vlan_list:
            return

        vlan_bitmap = self.vlan_list_to_bitmap(vlan_list)
        xmlstr = CE_NC_DELETE_VLAN_BATCH % (vlan_bitmap, vlan_bitmap)

        recv_xml = execute_nc_action(self.module, xmlstr)
        self.check_response(recv_xml, "DELETE_VLAN_BATCH")
        self.updates_cmd.append('undo vlan batch %s' % (
            self.vlan_range.replace(',', ' ').replace('-', ' to ')))
        self.changed = True

    def undo_config_vlan(self, vlanid):
        """Delete vlan."""

        conf_str = CE_NC_DELETE_VLAN % vlanid
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "DELETE_VLAN")
        self.changed = True
        self.updates_cmd.append('undo vlan %s' % self.vlan_id)

    def get_vlan_attr(self, vlan_id):
        """ get vlan attributes."""

        conf_str = CE_NC_GET_VLAN % vlan_id
        xml_str = get_nc_config(self.module, conf_str)
        attr = dict()

        if "<data/>" in xml_str:
            return attr
        else:
            re_find = re.findall(r'.*<vlanId>(.*)</vlanId>.*\s*'
                                 r'<vlanName>(.*)</vlanName>.*\s*'
                                 r'<vlanDesc>(.*)</vlanDesc>.*', xml_str)
            if re_find:
                attr = dict(vlan_id=re_find[0][0], name=re_find[0][1],
                            description=re_find[0][2])

            return attr

    def get_vlans_name(self):
        """ get all vlan vid and its name  list,
        sample: [ ("20", "VLAN_NAME_20"), ("30", "VLAN_NAME_30") ]"""

        conf_str = CE_NC_GET_VLANS
        xml_str = get_nc_config(self.module, conf_str)
        vlan_list = list()

        if "<data/>" in xml_str:
            return vlan_list
        else:
            vlan_list = re.findall(
                r'.*<vlanId>(.*)</vlanId>.*\s*<vlanName>(.*)</vlanName>.*', xml_str)
            return vlan_list

    def get_vlans_list(self):
        """ get all vlan vid list, sample: [ "20", "30", "31" ]"""

        conf_str = CE_NC_GET_VLANS
        xml_str = get_nc_config(self.module, conf_str)
        vlan_list = list()

        if "<data/>" in xml_str:
            return vlan_list
        else:
            vlan_list = re.findall(
                r'.*<vlanId>(.*)</vlanId>.*', xml_str)
            return vlan_list

    def vlan_series(self, vlanid_s):
        """ convert vlan range to list """

        vlan_list = []
        peerlistlen = len(vlanid_s)
        if peerlistlen != 2:
            self.module.fail_json(msg='Error: Format of vlanid is invalid.')
        for num in range(peerlistlen):
            if not vlanid_s[num].isdigit():
                self.module.fail_json(
                    msg='Error: Format of vlanid is invalid.')
        if int(vlanid_s[0]) > int(vlanid_s[1]):
            self.module.fail_json(msg='Error: Format of vlanid is invalid.')
        elif int(vlanid_s[0]) == int(vlanid_s[1]):
            vlan_list.append(str(vlanid_s[0]))
            return vlan_list
        for num in range(int(vlanid_s[0]), int(vlanid_s[1])):
            vlan_list.append(str(num))
        vlan_list.append(vlanid_s[1])

        return vlan_list

    def vlan_region(self, vlanid_list):
        """ convert vlan range to vlan list """

        vlan_list = []
        peerlistlen = len(vlanid_list)
        for num in range(peerlistlen):
            if vlanid_list[num].isdigit():
                vlan_list.append(vlanid_list[num])
            else:
                vlan_s = self.vlan_series(vlanid_list[num].split('-'))
                vlan_list.extend(vlan_s)

        return vlan_list

    def vlan_range_to_list(self, vlan_range):
        """ convert vlan range to vlan list """

        vlan_list = self.vlan_region(vlan_range.split(','))

        return vlan_list

    def vlan_list_to_bitmap(self, vlanlist):
        """ convert vlan list to vlan bitmap """

        vlan_bit = ['0'] * 1024
        bit_int = [0] * 1024

        vlan_list_len = len(vlanlist)
        for num in range(vlan_list_len):
            tagged_vlans = int(vlanlist[num])
            if tagged_vlans <= 0 or tagged_vlans > 4094:
                self.module.fail_json(
                    msg='Error: Vlan id is not in the range from 1 to 4094.')
            j = tagged_vlans / 4
            bit_int[j] |= 0x8 >> (tagged_vlans % 4)
            vlan_bit[j] = hex(bit_int[j])[2]

        vlan_xml = ''.join(vlan_bit)

        return vlan_xml

    def check_params(self):
        """Check all input params"""

        if not self.vlan_id and self.description:
            self.module.fail_json(
                msg='Error: Vlan description could be set only at one vlan.')

        if not self.vlan_id and self.name:
            self.module.fail_json(
                msg='Error: Vlan name could be set only at one vlan.')

        # check vlan id
        if self.vlan_id:
            if not self.vlan_id.isdigit():
                self.module.fail_json(
                    msg='Error: Vlan id is not digit.')
            if int(self.vlan_id) <= 0 or int(self.vlan_id) > 4094:
                self.module.fail_json(
                    msg='Error: Vlan id is not in the range from 1 to 4094.')

        # check vlan description
        if self.description:
            if len(self.description) > 81 or len(self.description.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: vlan description is not in the range from 1 to 80.')

        # check vlan name
        if self.name:
            if len(self.name) > 31 or len(self.name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Vlan name is not in the range from 1 to 31.')

    def get_proposed(self):
        """
        get proposed config.
        """

        if self.vlans_list_change:
            if self.state == 'present':
                proposed_vlans_tmp = list(self.vlans_list_change)
                proposed_vlans_tmp.extend(self.vlans_list_exist)
                self.results['proposed_vlans_list'] = list(
                    set(proposed_vlans_tmp))
            else:
                self.results['proposed_vlans_list'] = list(
                    set(self.vlans_list_exist) - set(self.vlans_list_change))
            self.results['proposed_vlans_list'].sort()
        else:
            self.results['proposed_vlans_list'] = self.vlans_list_exist

        if self.vlan_id:
            if self.state == "present":
                self.results['proposed'] = dict(
                    vlan_id=self.vlan_id,
                    name=self.name,
                    description=self.description
                )
            else:
                self.results['proposed'] = None
        else:
            self.results['proposed'] = None

    def get_existing(self):
        """
        get existing config.
        """

        self.results['existing_vlans_list'] = self.vlans_list_exist

        if self.vlan_id:
            if self.vlan_attr_exist:
                self.results['existing'] = dict(
                    vlan_id=self.vlan_attr_exist['vlan_id'],
                    name=self.vlan_attr_exist['name'],
                    description=self.vlan_attr_exist['description']
                )
            else:
                self.results['existing'] = None
        else:
            self.results['existing'] = None

    def get_end_state(self):
        """
        get end state config.
        """

        self.results['end_state_vlans_list'] = self.get_vlans_list()

        if self.vlan_id:
            if self.vlan_attr_end:
                self.results['end_state'] = dict(
                    vlan_id=self.vlan_attr_end['vlan_id'],
                    name=self.vlan_attr_end['name'],
                    description=self.vlan_attr_end['description']
                )
            else:
                self.results['end_state'] = None

        else:
            self.results['end_state'] = None

    def work(self):
        """
        worker.
        """

        # check param
        self.check_params()

        # get all vlan info
        self.vlans_list_exist = self.get_vlans_list()

        # get vlan attributes
        if self.vlan_id:
            self.vlans_list_change.append(self.vlan_id)
            self.vlan_attr_exist = self.get_vlan_attr(self.vlan_id)
            if self.vlan_attr_exist:
                self.vlan_exist = True

        if self.vlan_range:
            new_vlans_tmp = self.vlan_range_to_list(self.vlan_range)
            if self.state == 'present':
                self.vlans_list_change = list(
                    set(new_vlans_tmp) - set(self.vlans_list_exist))
            else:
                self.vlans_list_change = [
                    val for val in new_vlans_tmp if val in self.vlans_list_exist]

        if self.state == 'present':
            if self.vlan_id:
                if not self.vlan_exist:
                    # create a new vlan
                    self.config_vlan(self.vlan_id, self.name, self.description)
                elif self.description and self.description != self.vlan_attr_exist['description']:
                    # merge vlan description
                    self.merge_vlan(self.vlan_id, self.name, self.description)
                elif self.name and self.name != self.vlan_attr_exist['name']:
                    # merge vlan name
                    self.merge_vlan(self.vlan_id, self.name, self.description)

                # update command for results
                if self.changed:
                    self.updates_cmd.append('vlan %s' % self.vlan_id)
                    if self.name:
                        self.updates_cmd.append('name %s' % self.name)
                    if self.description:
                        self.updates_cmd.append(
                            'description %s' % self.description)
            elif self.vlan_range and self.vlans_list_change:
                self.create_vlan_batch(self.vlans_list_change)
        else:  # absent
            if self.vlan_id:
                if self.vlan_exist:
                    # delete the vlan
                    self.undo_config_vlan(self.vlan_id)
            elif self.vlan_range and self.vlans_list_change:
                self.delete_vlan_batch(self.vlans_list_change)

        # result
        if self.vlan_id:
            self.vlan_attr_end = self.get_vlan_attr(self.vlan_id)

        self.get_existing()
        self.get_proposed()
        self.get_end_state()

        self.results['changed'] = self.changed
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        vlan_id=dict(required=False),
        vlan_range=dict(required=False, type='str'),
        name=dict(required=False, type='str'),
        description=dict(required=False, type='str'),
        state=dict(choices=['absent', 'present'],
                   default='present', required=False),
    )

    argument_spec.update(ce_argument_spec)
    vlancfg = Vlan(argument_spec)
    vlancfg.work()


if __name__ == '__main__':
    main()
