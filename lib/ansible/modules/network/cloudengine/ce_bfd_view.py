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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ce_bfd_view
version_added: "2.4"
short_description: Manages BFD session view configuration on HUAWEI CloudEngine devices.
description:
    - Manages BFD session view configuration on HUAWEI CloudEngine devices.
author: QijunPan (@CloudEngine-Ansible)
options:
    session_name:
        description:
            - Specifies the name of a BFD session.
              The value is a string of 1 to 15 case-sensitive characters without spaces.
        required: true
        default: null
    local_discr:
        description:
            - Specifies the local discriminator of a BFD session.
              The value is an integer that ranges from 1 to 16384.
        required: false
        default: null
    remote_discr:
        description:
            - Specifies the remote discriminator of a BFD session.
              The value is an integer that ranges from 1 to 4294967295.
        required: false
        default: null
    min_tx_interval:
        description:
            - Specifies the minimum interval for receiving BFD packets.
              The value is an integer that ranges from 50 to 1000, in milliseconds.
        required: false
        default: null
    min_rx_interval:
        description:
            - Specifies the minimum interval for sending BFD packets.
              The value is an integer that ranges from 50 to 1000, in milliseconds.
        required: false
        default: null
    detect_multi:
        description:
            - Specifies the local detection multiplier of a BFD session.
              The value is an integer that ranges from 3 to 50.
        required: false
        default: null
    wtr_interval:
        description:
            - Specifies the WTR time of a BFD session.
              The value is an integer that ranges from 1 to 60, in minutes.
              The default value is 0.
        required: false
        default: null
    tos_exp:
        description:
            - Specifies a priority for BFD control packets.
              The value is an integer ranging from 0 to 7.
              The default value is 7, which is the highest priority.
        required: false
        default: null
    admin_down:
        description:
            - Enables the BFD session to enter the AdminDown state.
              By default, a BFD session is enabled.
              The default value is bool type.
        required: false
        default: false
    description:
        description:
            - Specifies the description of a BFD session.
              The value is a string of 1 to 51 case-sensitive characters with spaces.
        required: false
        default: null
    state:
        description:
            - Determines whether the config should be present or not on the device.
        required: false
        default: present
        choices: ['present', 'absent']
"""

EXAMPLES = '''
- name: bfd view module test
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
  - name: Set the local discriminator of a BFD session to 80 and the remote discriminator to 800
    ce_bfd_view:
      session_name: atob
      local_discr: 80
      remote_discr: 800
      state: present
      provider: '{{ cli }}'

  - name: Set the minimum interval for receiving BFD packets to 500 ms
    ce_bfd_view:
      session_name: atob
      min_rx_interval: 500
      state: present
      provider: '{{ cli }}'
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "admin_down": false,
        "description": null,
        "detect_multi": null,
        "local_discr": 80,
        "min_rx_interval": null,
        "min_tx_interval": null,
        "remote_discr": 800,
        "session_name": "atob",
        "state": "present",
        "tos_exp": null,
        "wtr_interval": null
    }
existing:
    description: k/v pairs of existing configuration
    returned: always
    type: dict
    sample: {
        "session": {
            "adminDown": "false",
            "createType": "SESS_STATIC",
            "description": null,
            "detectMulti": "3",
            "localDiscr": null,
            "minRxInt": null,
            "minTxInt": null,
            "remoteDiscr": null,
            "sessName": "atob",
            "tosExp": null,
            "wtrTimerInt": null
        }
    }
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {
        "session": {
            "adminDown": "false",
            "createType": "SESS_STATIC",
            "description": null,
            "detectMulti": "3",
            "localDiscr": "80",
            "minRxInt": null,
            "minTxInt": null,
            "remoteDiscr": "800",
            "sessName": "atob",
            "tosExp": null,
            "wtrTimerInt": null
        }
    }
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: [
        "bfd atob",
        "discriminator local 80",
        "discriminator remote 800"
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import sys
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ce import get_nc_config, set_nc_config, ce_argument_spec


CE_NC_GET_BFD = """
    <filter type="subtree">
      <bfd xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
      %s
      </bfd>
    </filter>
"""

CE_NC_GET_BFD_GLB = """
        <bfdSchGlobal>
          <bfdEnable></bfdEnable>
        </bfdSchGlobal>
"""

CE_NC_GET_BFD_SESSION = """
        <bfdCfgSessions>
          <bfdCfgSession>
            <sessName>%s</sessName>
            <createType></createType>
            <localDiscr></localDiscr>
            <remoteDiscr></remoteDiscr>
            <minTxInt></minTxInt>
            <minRxInt></minRxInt>
            <detectMulti></detectMulti>
            <wtrTimerInt></wtrTimerInt>
            <tosExp></tosExp>
            <adminDown></adminDown>
            <description></description>
          </bfdCfgSession>
        </bfdCfgSessions>
"""


class BfdView(object):
    """Manages BFD View"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.session_name = self.module.params['session_name']
        self.local_discr = self.module.params['local_discr']
        self.remote_discr = self.module.params['remote_discr']
        self.min_tx_interval = self.module.params['min_tx_interval']
        self.min_rx_interval = self.module.params['min_rx_interval']
        self.detect_multi = self.module.params['detect_multi']
        self.wtr_interval = self.module.params['wtr_interval']
        self.tos_exp = self.module.params['tos_exp']
        self.admin_down = self.module.params['admin_down']
        self.description = self.module.params['description']
        self.state = self.module.params['state']

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.bfd_dict = dict()
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """init module"""

        self.module = AnsibleModule(argument_spec=self.spec,
                                    supports_check_mode=True)

    def get_bfd_dict(self):
        """bfd config dict"""

        bfd_dict = dict()
        bfd_dict["global"] = dict()
        bfd_dict["session"] = dict()
        conf_str = CE_NC_GET_BFD % (CE_NC_GET_BFD_GLB + (CE_NC_GET_BFD_SESSION % self.session_name))

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return bfd_dict

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)

        # get bfd global info
        glb = root.find("data/bfd/bfdSchGlobal")
        if glb:
            for attr in glb:
                bfd_dict["global"][attr.tag] = attr.text

        # get bfd session info
        sess = root.find("data/bfd/bfdCfgSessions/bfdCfgSession")
        if sess:
            for attr in sess:
                bfd_dict["session"][attr.tag] = attr.text

        return bfd_dict

    def config_session(self):
        """configures bfd session"""

        xml_str = ""
        cmd_list = list()
        cmd_session = ""

        if not self.session_name:
            return xml_str

        if self.bfd_dict["global"].get("bfdEnable", "false") != "true":
            self.module.fail_json(msg="Error: Please enable BFD globally first.")

        if not self.bfd_dict["session"]:
            self.module.fail_json(msg="Error: BFD session is not exist.")

        session = self.bfd_dict["session"]
        xml_str = "<sessName>%s</sessName>" % self.session_name
        cmd_session = "bfd %s" % self.session_name

        # BFD session view
        if self.local_discr is not None:
            if self.state == "present" and str(self.local_discr) != session.get("localDiscr"):
                xml_str += "<localDiscr>%s</localDiscr>" % self.local_discr
                cmd_list.append("discriminator local %s" % self.local_discr)
            elif self.state == "absent" and str(self.local_discr) == session.get("localDiscr"):
                xml_str += "<localDiscr/>"
                cmd_list.append("undo discriminator local")

        if self.remote_discr is not None:
            if self.state == "present" and str(self.remote_discr) != session.get("remoteDiscr"):
                xml_str += "<remoteDiscr>%s</remoteDiscr>" % self.remote_discr
                cmd_list.append("discriminator remote %s" % self.remote_discr)
            elif self.state == "absent" and str(self.remote_discr) == session.get("remoteDiscr"):
                xml_str += "<remoteDiscr/>"
                cmd_list.append("undo discriminator remote")

        if self.min_tx_interval is not None:
            if self.state == "present" and str(self.min_tx_interval) != session.get("minTxInt"):
                xml_str += "<minTxInt>%s</minTxInt>" % self.min_tx_interval
                cmd_list.append("min-tx-interval %s" % self.min_tx_interval)
            elif self.state == "absent" and str(self.min_tx_interval) == session.get("minTxInt"):
                xml_str += "<minTxInt/>"
                cmd_list.append("undo min-tx-interval")

        if self.min_rx_interval is not None:
            if self.state == "present" and str(self.min_rx_interval) != session.get("minRxInt"):
                xml_str += "<minRxInt>%s</minRxInt>" % self.min_rx_interval
                cmd_list.append("min-rx-interval %s" % self.min_rx_interval)
            elif self.state == "absent" and str(self.min_rx_interval) == session.get("minRxInt"):
                xml_str += "<minRxInt/>"
                cmd_list.append("undo min-rx-interval")

        if self.detect_multi is not None:
            if self.state == "present" and str(self.detect_multi) != session.get("detectMulti"):
                xml_str += " <detectMulti>%s</detectMulti>" % self.detect_multi
                cmd_list.append("detect-multiplier %s" % self.detect_multi)
            elif self.state == "absent" and str(self.detect_multi) == session.get("detectMulti"):
                xml_str += " <detectMulti/>"
                cmd_list.append("undo detect-multiplier")

        if self.wtr_interval is not None:
            if self.state == "present" and str(self.wtr_interval) != session.get("wtrTimerInt"):
                xml_str += " <wtrTimerInt>%s</wtrTimerInt>" % self.wtr_interval
                cmd_list.append("wtr %s" % self.wtr_interval)
            elif self.state == "absent" and str(self.wtr_interval) == session.get("wtrTimerInt"):
                xml_str += " <wtrTimerInt/>"
                cmd_list.append("undo wtr")

        if self.tos_exp is not None:
            if self.state == "present" and str(self.tos_exp) != session.get("tosExp"):
                xml_str += " <tosExp>%s</tosExp>" % self.tos_exp
                cmd_list.append("tos-exp %s" % self.tos_exp)
            elif self.state == "absent" and str(self.tos_exp) == session.get("tosExp"):
                xml_str += " <tosExp/>"
                cmd_list.append("undo tos-exp")

        if self.admin_down and session.get("adminDown", "false") == "false":
            xml_str += " <adminDown>true</adminDown>"
            cmd_list.append("shutdown")
        elif not self.admin_down and session.get("adminDown", "false") == "true":
            xml_str += " <adminDown>false</adminDown>"
            cmd_list.append("undo shutdown")

        if self.description:
            if self.state == "present" and self.description != session.get("description"):
                xml_str += "<description>%s</description>" % self.description
                cmd_list.append("description %s" % self.description)
            elif self.state == "absent" and self.description == session.get("description"):
                xml_str += "<description/>"
                cmd_list.append("undo description")

        if xml_str.endswith("</sessName>"):
            # no config update
            return ""
        else:
            cmd_list.insert(0, cmd_session)
            self.updates_cmd.extend(cmd_list)
            return '<bfdCfgSessions><bfdCfgSession operation="merge">' + xml_str\
                   + '</bfdCfgSession></bfdCfgSessions>'

    def netconf_load_config(self, xml_str):
        """load bfd config by netconf"""

        if not xml_str:
            return

        xml_cfg = """
            <config>
            <bfd xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
            %s
            </bfd>
            </config>""" % xml_str

        set_nc_config(self.min_rx_interval, xml_cfg)
        self.changed = True

    def check_params(self):
        """Check all input params"""

        # check session_name
        if not self.session_name:
            self.module.fail_json(msg="Error: Missing required arguments: session_name.")

        if self.session_name:
            if len(self.session_name) < 1 or len(self.session_name) > 15:
                self.module.fail_json(msg="Error: Session name is invalid.")

        # check local_discr
        if self.local_discr is not None:
            if self.local_discr < 1 or self.local_discr > 16384:
                self.module.fail_json(msg="Error: Session local_discr is not ranges from 1 to 16384.")

        # check remote_discr
        if self.remote_discr is not None:
            if self.remote_discr < 1 or self.remote_discr > 4294967295:
                self.module.fail_json(msg="Error: Session remote_discr is not ranges from 1 to 4294967295.")

        # check min_tx_interval
        if self.min_tx_interval is not None:
            if self.min_tx_interval < 50 or self.min_tx_interval > 1000:
                self.module.fail_json(msg="Error: Session min_tx_interval is not ranges from 50 to 1000.")

        # check min_rx_interval
        if self.min_rx_interval is not None:
            if self.min_rx_interval < 50 or self.min_rx_interval > 1000:
                self.module.fail_json(msg="Error: Session min_rx_interval is not ranges from 50 to 1000.")

        # check detect_multi
        if self.detect_multi is not None:
            if self.detect_multi < 3 or self.detect_multi > 50:
                self.module.fail_json(msg="Error: Session detect_multi is not ranges from 3 to 50.")

        # check wtr_interval
        if self.wtr_interval is not None:
            if self.wtr_interval < 1 or self.wtr_interval > 60:
                self.module.fail_json(msg="Error: Session wtr_interval is not ranges from 1 to 60.")

        # check tos_exp
        if self.tos_exp is not None:
            if self.tos_exp < 0 or self.tos_exp > 7:
                self.module.fail_json(msg="Error: Session tos_exp is not ranges from 0 to 7.")

        # check description
        if self.description:
            if len(self.description) < 1 or len(self.description) > 51:
                self.module.fail_json(msg="Error: Session description is invalid.")

    def get_proposed(self):
        """get proposed info"""

        # base config
        self.proposed["session_name"] = self.session_name
        self.proposed["local_discr"] = self.local_discr
        self.proposed["remote_discr"] = self.remote_discr
        self.proposed["min_tx_interval"] = self.min_tx_interval
        self.proposed["min_rx_interval"] = self.min_rx_interval
        self.proposed["detect_multi"] = self.detect_multi
        self.proposed["wtr_interval"] = self.wtr_interval
        self.proposed["tos_exp"] = self.tos_exp
        self.proposed["admin_down"] = self.admin_down
        self.proposed["description"] = self.description
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if not self.bfd_dict:
            return

        self.existing["session"] = self.bfd_dict.get("session")

    def get_end_state(self):
        """get end state info"""

        bfd_dict = self.get_bfd_dict()
        if not bfd_dict:
            return

        self.end_state["session"] = bfd_dict.get("session")

    def work(self):
        """worker"""

        self.check_params()
        self.bfd_dict = self.get_bfd_dict()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        xml_str = ''
        if self.session_name:
            xml_str += self.config_session()

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
        session_name=dict(required=True, type='str'),
        local_discr=dict(required=False, type='int'),
        remote_discr=dict(required=False, type='int'),
        min_tx_interval=dict(required=False, type='int'),
        min_rx_interval=dict(required=False, type='int'),
        detect_multi=dict(required=False, type='int'),
        wtr_interval=dict(required=False, type='int'),
        tos_exp=dict(required=False, type='int'),
        admin_down=dict(required=False, type='bool', default=False),
        description=dict(required=False, type='str'),
        state=dict(required=False, default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ce_argument_spec)
    module = BfdView(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
