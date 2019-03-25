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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_secprof_profile_group
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage security profiles within FortiManager
description:
  - Manage security profile group which allows you to create a group of security profiles and apply that to a policy.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values.
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  webfilter_profile:
    type: str
    description:
      - Name of an existing Web filter profile.
    required: false

  waf_profile:
    type: str
    description:
      - Name of an existing Web application firewall profile.
    required: false

  voip_profile:
    type: str
    description:
      - Name of an existing VoIP profile.
    required: false

  ssl_ssh_profile:
    type: str
    description:
      - Name of an existing SSL SSH profile.
    required: false

  ssh_filter_profile:
    type: str
    description:
      - Name of an existing SSH filter profile.
    required: false

  spamfilter_profile:
    type: str
    description:
      - Name of an existing Spam filter profile.
    required: false

  profile_protocol_options:
    type: str
    description:
      - Name of an existing Protocol options profile.
    required: false

  name:
    type: str
    description:
      - Profile group name.
    required: false

  mms_profile:
    type: str
    description:
      - Name of an existing MMS profile.
    required: false

  ips_sensor:
    type: str
    description:
      - Name of an existing IPS sensor.
    required: false

  icap_profile:
    type: str
    description:
      - Name of an existing ICAP profile.
    required: false

  dnsfilter_profile:
    type: str
    description:
      - Name of an existing DNS filter profile.
    required: false

  dlp_sensor:
    type: str
    description:
      - Name of an existing DLP sensor.
    required: false

  av_profile:
    type: str
    description:
      - Name of an existing Antivirus profile.
    required: false

  application_list:
    type: str
    description:
      - Name of an existing Application list.
    required: false


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_profile_group:
      name: "Ansible_TEST_Profile_Group"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_profile_group:
      name: "Ansible_TEST_Profile_Group"
      mode: "set"
      av_profile: "Ansible_AV_Profile"
      profile_protocol_options: "default"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import FMGRMethods
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict


###############
# START METHODS
###############


def fmgr_firewall_profile_group_modify(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    url = ""
    datagram = {}

    response = DEFAULT_RESULT_OBJ

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/firewall/profile-group'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/firewall/profile-group/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])

    return response


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        webfilter_profile=dict(required=False, type="str"),
        waf_profile=dict(required=False, type="str"),
        voip_profile=dict(required=False, type="str"),
        ssl_ssh_profile=dict(required=False, type="str"),
        ssh_filter_profile=dict(required=False, type="str"),
        spamfilter_profile=dict(required=False, type="str"),
        profile_protocol_options=dict(required=False, type="str"),
        name=dict(required=False, type="str"),
        mms_profile=dict(required=False, type="str"),
        ips_sensor=dict(required=False, type="str"),
        icap_profile=dict(required=False, type="str"),
        dnsfilter_profile=dict(required=False, type="str"),
        dlp_sensor=dict(required=False, type="str"),
        av_profile=dict(required=False, type="str"),
        application_list=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "webfilter-profile": module.params["webfilter_profile"],
        "waf-profile": module.params["waf_profile"],
        "voip-profile": module.params["voip_profile"],
        "ssl-ssh-profile": module.params["ssl_ssh_profile"],
        "ssh-filter-profile": module.params["ssh_filter_profile"],
        "spamfilter-profile": module.params["spamfilter_profile"],
        "profile-protocol-options": module.params["profile_protocol_options"],
        "name": module.params["name"],
        "mms-profile": module.params["mms_profile"],
        "ips-sensor": module.params["ips_sensor"],
        "icap-profile": module.params["icap_profile"],
        "dnsfilter-profile": module.params["dnsfilter_profile"],
        "dlp-sensor": module.params["dlp_sensor"],
        "av-profile": module.params["av_profile"],
        "application-list": module.params["application_list"],

    }
    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    results = DEFAULT_RESULT_OBJ

    try:
        results = fmgr_firewall_profile_group_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
