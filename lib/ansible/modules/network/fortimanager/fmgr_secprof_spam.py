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
module: fmgr_secprof_spam
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: spam filter profile for FMG
description:
  -  Manage spam filter security profiles within FortiManager via API

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  spam_rbl_table:
    description:
      - Anti-spam DNSBL table ID.
    required: false

  spam_mheader_table:
    description:
      - Anti-spam MIME header table ID.
    required: false

  spam_log_fortiguard_response:
    description:
      - Enable/disable logging FortiGuard spam response.
    required: false
    choices:
      - disable
      - enable

  spam_log:
    description:
      - Enable/disable spam logging for email filtering.
    required: false
    choices:
      - disable
      - enable

  spam_iptrust_table:
    description:
      - Anti-spam IP trust table ID.
    required: false

  spam_filtering:
    description:
      - Enable/disable spam filtering.
    required: false
    choices:
      - disable
      - enable

  spam_bword_threshold:
    description:
      - Spam banned word threshold.
    required: false

  spam_bword_table:
    description:
      - Anti-spam banned word table ID.
    required: false

  spam_bwl_table:
    description:
      - Anti-spam black/white list table ID.
    required: false

  replacemsg_group:
    description:
      - Replacement message group.
    required: false

  options:
    description:
      - None
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - bannedword
      - spamfsip
      - spamfssubmit
      - spamfschksum
      - spamfsurl
      - spamhelodns
      - spamraddrdns
      - spamrbl
      - spamhdrcheck
      - spamfsphish
      - spambwl

  name:
    description:
      - Profile name.
    required: false

  flow_based:
    description:
      - Enable/disable flow-based spam filtering.
    required: false
    choices:
      - disable
      - enable

  external:
    description:
      - Enable/disable external Email inspection.
    required: false
    choices:
      - disable
      - enable

  comment:
    description:
      - Comment.
    required: false

  gmail:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  gmail_log:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  imap:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  imap_action:
    description:
      - Action for spam email.
    required: false
    choices:
      - pass
      - tag

  imap_log:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  imap_tag_msg:
    description:
      - Subject text or header added to spam email.
    required: false

  imap_tag_type:
    description:
      - Tag subject or header for spam email.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - subject
      - header
      - spaminfo

  mapi:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  mapi_action:
    description:
      - Action for spam email.
    required: false
    choices:
      - pass
      - discard

  mapi_log:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  msn_hotmail:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  msn_hotmail_log:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  pop3:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  pop3_action:
    description:
      - Action for spam email.
    required: false
    choices:
      - pass
      - tag

  pop3_log:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  pop3_tag_msg:
    description:
      - Subject text or header added to spam email.
    required: false

  pop3_tag_type:
    description:
      - Tag subject or header for spam email.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - subject
      - header
      - spaminfo

  smtp:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  smtp_action:
    description:
      - Action for spam email.
    required: false
    choices:
      - pass
      - tag
      - discard

  smtp_hdrip:
    description:
      - Enable/disable SMTP email header IP checks for spamfsip, spamrbl and spambwl filters.
    required: false
    choices:
      - disable
      - enable

  smtp_local_override:
    description:
      - Enable/disable local filter to override SMTP remote check result.
    required: false
    choices:
      - disable
      - enable

  smtp_log:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  smtp_tag_msg:
    description:
      - Subject text or header added to spam email.
    required: false

  smtp_tag_type:
    description:
      - Tag subject or header for spam email.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - subject
      - header
      - spaminfo

  yahoo_mail:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  yahoo_mail_log:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable
'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_spam:
      name: "Ansible_Spam_Filter_Profile"
      mode: "delete"

  - name: Create FMGR_SPAMFILTER_PROFILE
    fmgr_secprof_spam:
      host: "{{ inventory_hostname }}"
      username: "{{ username }}"
      password: "{{ password }}"
      mode: "set"
      adom: "root"
      spam_log_fortiguard_response: "enable"
      spam_iptrust_table:
      spam_filtering: "enable"
      spam_bword_threshold: 10
      options: ["bannedword", "spamfsip", "spamfsurl", "spamrbl", "spamfsphish", "spambwl"]
      name: "Ansible_Spam_Filter_Profile"
      flow_based: "enable"
      external: "enable"
      comment: "Created by Ansible"
      gmail_log: "enable"
      spam_log: "enable"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict

###############
# START METHODS
###############


def fmgr_spamfilter_profile_modify(fmgr, paramgram):
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

    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/spamfilter/profile'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/spamfilter/profile/{name}'.format(adom=adom, name=paramgram["name"])
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

        spam_rbl_table=dict(required=False, type="str"),
        spam_mheader_table=dict(required=False, type="str"),
        spam_log_fortiguard_response=dict(required=False, type="str", choices=["disable", "enable"]),
        spam_log=dict(required=False, type="str", choices=["disable", "enable"]),
        spam_iptrust_table=dict(required=False, type="str"),
        spam_filtering=dict(required=False, type="str", choices=["disable", "enable"]),
        spam_bword_threshold=dict(required=False, type="int"),
        spam_bword_table=dict(required=False, type="str"),
        spam_bwl_table=dict(required=False, type="str"),
        replacemsg_group=dict(required=False, type="str"),
        options=dict(required=False, type="list", choices=["bannedword",
                                                           "spamfsip",
                                                           "spamfssubmit",
                                                           "spamfschksum",
                                                           "spamfsurl",
                                                           "spamhelodns",
                                                           "spamraddrdns",
                                                           "spamrbl",
                                                           "spamhdrcheck",
                                                           "spamfsphish",
                                                           "spambwl"]),
        name=dict(required=False, type="str"),
        flow_based=dict(required=False, type="str", choices=["disable", "enable"]),
        external=dict(required=False, type="str", choices=["disable", "enable"]),
        comment=dict(required=False, type="str"),
        gmail=dict(required=False, type="dict"),
        gmail_log=dict(required=False, type="str", choices=["disable", "enable"]),
        imap=dict(required=False, type="dict"),
        imap_action=dict(required=False, type="str", choices=["pass", "tag"]),
        imap_log=dict(required=False, type="str", choices=["disable", "enable"]),
        imap_tag_msg=dict(required=False, type="str"),
        imap_tag_type=dict(required=False, type="str", choices=["subject", "header", "spaminfo"]),
        mapi=dict(required=False, type="dict"),
        mapi_action=dict(required=False, type="str", choices=["pass", "discard"]),
        mapi_log=dict(required=False, type="str", choices=["disable", "enable"]),
        msn_hotmail=dict(required=False, type="dict"),
        msn_hotmail_log=dict(required=False, type="str", choices=["disable", "enable"]),
        pop3=dict(required=False, type="dict"),
        pop3_action=dict(required=False, type="str", choices=["pass", "tag"]),
        pop3_log=dict(required=False, type="str", choices=["disable", "enable"]),
        pop3_tag_msg=dict(required=False, type="str"),
        pop3_tag_type=dict(required=False, type="str", choices=["subject", "header", "spaminfo"]),
        smtp=dict(required=False, type="dict"),
        smtp_action=dict(required=False, type="str", choices=["pass", "tag", "discard"]),
        smtp_hdrip=dict(required=False, type="str", choices=["disable", "enable"]),
        smtp_local_override=dict(required=False, type="str", choices=["disable", "enable"]),
        smtp_log=dict(required=False, type="str", choices=["disable", "enable"]),
        smtp_tag_msg=dict(required=False, type="str"),
        smtp_tag_type=dict(required=False, type="str", choices=["subject", "header", "spaminfo"]),
        yahoo_mail=dict(required=False, type="dict"),
        yahoo_mail_log=dict(required=False, type="str", choices=["disable", "enable"]),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "spam-rbl-table": module.params["spam_rbl_table"],
        "spam-mheader-table": module.params["spam_mheader_table"],
        "spam-log-fortiguard-response": module.params["spam_log_fortiguard_response"],
        "spam-log": module.params["spam_log"],
        "spam-iptrust-table": module.params["spam_iptrust_table"],
        "spam-filtering": module.params["spam_filtering"],
        "spam-bword-threshold": module.params["spam_bword_threshold"],
        "spam-bword-table": module.params["spam_bword_table"],
        "spam-bwl-table": module.params["spam_bwl_table"],
        "replacemsg-group": module.params["replacemsg_group"],
        "options": module.params["options"],
        "name": module.params["name"],
        "flow-based": module.params["flow_based"],
        "external": module.params["external"],
        "comment": module.params["comment"],
        "gmail": {
            "log": module.params["gmail_log"],
        },
        "imap": {
            "action": module.params["imap_action"],
            "log": module.params["imap_log"],
            "tag-msg": module.params["imap_tag_msg"],
            "tag-type": module.params["imap_tag_type"],
        },
        "mapi": {
            "action": module.params["mapi_action"],
            "log": module.params["mapi_log"],
        },
        "msn-hotmail": {
            "log": module.params["msn_hotmail_log"],
        },
        "pop3": {
            "action": module.params["pop3_action"],
            "log": module.params["pop3_log"],
            "tag-msg": module.params["pop3_tag_msg"],
            "tag-type": module.params["pop3_tag_type"],
        },
        "smtp": {
            "action": module.params["smtp_action"],
            "hdrip": module.params["smtp_hdrip"],
            "local-override": module.params["smtp_local_override"],
            "log": module.params["smtp_log"],
            "tag-msg": module.params["smtp_tag_msg"],
            "tag-type": module.params["smtp_tag_type"],
        },
        "yahoo-mail": {
            "log": module.params["yahoo_mail_log"],
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

    list_overrides = ['gmail', 'imap', 'mapi', 'msn-hotmail', 'pop3', 'smtp', 'yahoo-mail']
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)

    results = DEFAULT_RESULT_OBJ
    try:

        results = fmgr_spamfilter_profile_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
