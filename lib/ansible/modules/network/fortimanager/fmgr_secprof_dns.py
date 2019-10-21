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
module: fmgr_secprof_dns
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage DNS security profiles in FortiManager
description:
  -  Manage DNS security profiles in FortiManager

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

  youtube_restrict:
    type: str
    description:
      - Set safe search for YouTube restriction level.
      - choice | strict | Enable strict safe seach for YouTube.
      - choice | moderate | Enable moderate safe search for YouTube.
    required: false
    choices: ["strict", "moderate"]

  sdns_ftgd_err_log:
    type: str
    description:
      - Enable/disable FortiGuard SDNS rating error logging.
      - choice | disable | Disable FortiGuard SDNS rating error logging.
      - choice | enable | Enable FortiGuard SDNS rating error logging.
    required: false
    choices: ["disable", "enable"]

  sdns_domain_log:
    type: str
    description:
      - Enable/disable domain filtering and botnet domain logging.
      - choice | disable | Disable domain filtering and botnet domain logging.
      - choice | enable | Enable domain filtering and botnet domain logging.
    required: false
    choices: ["disable", "enable"]

  safe_search:
    type: str
    description:
      - Enable/disable Google, Bing, and YouTube safe search.
      - choice | disable | Disable Google, Bing, and YouTube safe search.
      - choice | enable | Enable Google, Bing, and YouTube safe search.
    required: false
    choices: ["disable", "enable"]

  redirect_portal:
    type: str
    description:
      - IP address of the SDNS redirect portal.
    required: false

  name:
    type: str
    description:
      - Profile name.
    required: false

  log_all_domain:
    type: str
    description:
      - Enable/disable logging of all domains visited (detailed DNS logging).
      - choice | disable | Disable logging of all domains visited.
      - choice | enable | Enable logging of all domains visited.
    required: false
    choices: ["disable", "enable"]

  external_ip_blocklist:
    type: str
    description:
      - One or more external IP block lists.
    required: false

  comment:
    type: str
    description:
      - Comment for the security profile to show in the FortiManager GUI.
    required: false

  block_botnet:
    type: str
    description:
      - Enable/disable blocking botnet C&C; DNS lookups.
      - choice | disable | Disable blocking botnet C&C; DNS lookups.
      - choice | enable | Enable blocking botnet C&C; DNS lookups.
    required: false
    choices: ["disable", "enable"]

  block_action:
    type: str
    description:
      - Action to take for blocked domains.
      - choice | block | Return NXDOMAIN for blocked domains.
      - choice | redirect | Redirect blocked domains to SDNS portal.
    required: false
    choices: ["block", "redirect"]

  domain_filter_domain_filter_table:
    type: str
    description:
      - DNS domain filter table ID.
    required: false

  ftgd_dns_options:
    type: str
    description:
      - FortiGuard DNS filter options.
      - FLAG Based Options. Specify multiple in list form.
      - flag | error-allow | Allow all domains when FortiGuard DNS servers fail.
      - flag | ftgd-disable | Disable FortiGuard DNS domain rating.
    required: false
    choices: ["error-allow", "ftgd-disable"]

  ftgd_dns_filters_action:
    type: str
    description:
      - Action to take for DNS requests matching the category.
      - choice | monitor | Allow DNS requests matching the category and log the result.
      - choice | block | Block DNS requests matching the category.
    required: false
    choices: ["monitor", "block"]

  ftgd_dns_filters_category:
    type: str
    description:
      - Category number.
    required: false

  ftgd_dns_filters_log:
    type: str
    description:
      - Enable/disable DNS filter logging for this DNS profile.
      - choice | disable | Disable DNS filter logging.
      - choice | enable | Enable DNS filter logging.
    required: false
    choices: ["disable", "enable"]


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_dns:
      name: "Ansible_DNS_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_dns:
      name: "Ansible_DNS_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "set"
      block_action: "block"


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


def fmgr_dnsfilter_profile_modify(fmgr, paramgram):
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
        url = '/pm/config/adom/{adom}/obj/dnsfilter/profile'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/dnsfilter/profile/{name}'.format(adom=adom, name=paramgram["name"])
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

        youtube_restrict=dict(required=False, type="str", choices=["strict", "moderate"]),
        sdns_ftgd_err_log=dict(required=False, type="str", choices=["disable", "enable"]),
        sdns_domain_log=dict(required=False, type="str", choices=["disable", "enable"]),
        safe_search=dict(required=False, type="str", choices=["disable", "enable"]),
        redirect_portal=dict(required=False, type="str"),
        name=dict(required=False, type="str"),
        log_all_domain=dict(required=False, type="str", choices=["disable", "enable"]),
        external_ip_blocklist=dict(required=False, type="str"),
        comment=dict(required=False, type="str"),
        block_botnet=dict(required=False, type="str", choices=["disable", "enable"]),
        block_action=dict(required=False, type="str", choices=["block", "redirect"]),

        domain_filter_domain_filter_table=dict(required=False, type="str"),

        ftgd_dns_options=dict(required=False, type="str", choices=["error-allow", "ftgd-disable"]),

        ftgd_dns_filters_action=dict(required=False, type="str", choices=["monitor", "block"]),
        ftgd_dns_filters_category=dict(required=False, type="str"),
        ftgd_dns_filters_log=dict(required=False, type="str", choices=["disable", "enable"]),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "youtube-restrict": module.params["youtube_restrict"],
        "sdns-ftgd-err-log": module.params["sdns_ftgd_err_log"],
        "sdns-domain-log": module.params["sdns_domain_log"],
        "safe-search": module.params["safe_search"],
        "redirect-portal": module.params["redirect_portal"],
        "name": module.params["name"],
        "log-all-domain": module.params["log_all_domain"],
        "external-ip-blocklist": module.params["external_ip_blocklist"],
        "comment": module.params["comment"],
        "block-botnet": module.params["block_botnet"],
        "block-action": module.params["block_action"],
        "domain-filter": {
            "domain-filter-table": module.params["domain_filter_domain_filter_table"],
        },
        "ftgd-dns": {
            "options": module.params["ftgd_dns_options"],
            "filters": {
                "action": module.params["ftgd_dns_filters_action"],
                "category": module.params["ftgd_dns_filters_category"],
                "log": module.params["ftgd_dns_filters_log"],
            }
        }
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
        results = fmgr_dnsfilter_profile_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
