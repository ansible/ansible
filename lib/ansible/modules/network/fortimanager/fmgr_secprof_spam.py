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

  host:
    description:
      - The FortiManager's Address.
    required: true

  username:
    description:
      - The username associated with the account.
    required: true

  password:
    description:
      - The password associated with the username account.
    required: true

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
      - choice | disable | Disable logging FortiGuard spam response.
      - choice | enable | Enable logging FortiGuard spam response.
    required: false
    choices: ["disable", "enable"]

  spam_log:
    description:
      - Enable/disable spam logging for email filtering.
      - choice | disable | Disable spam logging for email filtering.
      - choice | enable | Enable spam logging for email filtering.
    required: false
    choices: ["disable", "enable"]

  spam_iptrust_table:
    description:
      - Anti-spam IP trust table ID.
    required: false

  spam_filtering:
    description:
      - Enable/disable spam filtering.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

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
      - FLAG Based Options. Specify multiple in list form.
      - flag | bannedword | Content block.
      - flag | spamfsip | Email IP address FortiGuard AntiSpam black list check.
      - flag | spamfssubmit | Add FortiGuard AntiSpam spam submission text.
      - flag | spamfschksum | Email checksum FortiGuard AntiSpam check.
      - flag | spamfsurl | Email content URL FortiGuard AntiSpam check.
      - flag | spamhelodns | Email helo/ehlo domain DNS check.
      - flag | spamraddrdns | Email return address DNS check.
      - flag | spamrbl | Email DNSBL &amp; ORBL check.
      - flag | spamhdrcheck | Email mime header check.
      - flag | spamfsphish | Email content phishing URL FortiGuard AntiSpam check.
      - flag | spambwl | Black/white list.
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
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  external:
    description:
      - Enable/disable external Email inspection.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

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
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

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
      - choice | pass | Allow spam email to pass through.
      - choice | tag | Tag spam email with configured text in subject or header.
    required: false
    choices: ["pass", "tag"]

  imap_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  imap_tag_msg:
    description:
      - Subject text or header added to spam email.
    required: false

  imap_tag_type:
    description:
      - Tag subject or header for spam email.
      - FLAG Based Options. Specify multiple in list form.
      - flag | subject | Prepend text to spam email subject.
      - flag | header | Append a user defined mime header to spam email.
      - flag | spaminfo | Append spam info to spam email header.
    required: false
    choices: ["subject", "header", "spaminfo"]

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
      - choice | pass | Allow spam email to pass through.
      - choice | discard | Discard (block) spam email.
    required: false
    choices: ["pass", "discard"]

  mapi_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

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
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

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
      - choice | pass | Allow spam email to pass through.
      - choice | tag | Tag spam email with configured text in subject or header.
    required: false
    choices: ["pass", "tag"]

  pop3_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  pop3_tag_msg:
    description:
      - Subject text or header added to spam email.
    required: false

  pop3_tag_type:
    description:
      - Tag subject or header for spam email.
      - FLAG Based Options. Specify multiple in list form.
      - flag | subject | Prepend text to spam email subject.
      - flag | header | Append a user defined mime header to spam email.
      - flag | spaminfo | Append spam info to spam email header.
    required: false
    choices: ["subject", "header", "spaminfo"]

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
      - choice | pass | Allow spam email to pass through.
      - choice | tag | Tag spam email with configured text in subject or header.
      - choice | discard | Discard (block) spam email.
    required: false
    choices: ["pass", "tag", "discard"]

  smtp_hdrip:
    description:
      - Enable/disable SMTP email header IP checks for spamfsip, spamrbl and spambwl filters.
      - choice | disable | Disable SMTP email header IP checks for spamfsip, spamrbl and spambwl filters.
      - choice | enable | Enable SMTP email header IP checks for spamfsip, spamrbl and spambwl filters.
    required: false
    choices: ["disable", "enable"]

  smtp_local_override:
    description:
      - Enable/disable local filter to override SMTP remote check result.
      - choice | disable | Disable local filter to override SMTP remote check result.
      - choice | enable | Enable local filter to override SMTP remote check result.
    required: false
    choices: ["disable", "enable"]

  smtp_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  smtp_tag_msg:
    description:
      - Subject text or header added to spam email.
    required: false

  smtp_tag_type:
    description:
      - Tag subject or header for spam email.
      - FLAG Based Options. Specify multiple in list form.
      - flag | subject | Prepend text to spam email subject.
      - flag | header | Append a user defined mime header to spam email.
      - flag | spaminfo | Append spam info to spam email header.
    required: false
    choices: ["subject", "header", "spaminfo"]

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
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]
'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_spam:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
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
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

###############
# START METHODS
###############


def fmgr_spamfilter_profile_addsetdelete(fmg, paramgram):
    """
    fmgr_spamfilter_profile -- Your Description here, bruh
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/spamfilter/profile'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/spamfilter/profile/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if mode == "set":
        response = fmg.set(url, datagram)
    # IF MODE = UPDATE -- USER THE 'UPDATE' API CALL MODE
    elif mode == "update":
        response = fmg.update(url, datagram)
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    elif mode == "add":
        response = fmg.add(url, datagram)
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    elif mode == "delete":
        response = fmg.delete(url, datagram)

    return response


# ADDITIONAL COMMON FUNCTIONS
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """
    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

        if results[0] not in good_codes:
            if logout_on_fail:
                fmg.logout()
                module.fail_json(msg=msg, **results[1])
        else:
            if logout_on_success:
                fmg.logout()
                module.exit_json(msg="API Called worked, but logout handler has been asked to logout on success",
                                 **results[1])
    return msg


# FUNCTION/METHOD FOR CONVERTING CIDR TO A NETMASK
# DID NOT USE IP ADDRESS MODULE TO KEEP INCLUDES TO A MINIMUM
def fmgr_cidr_to_netmask(cidr):
    cidr = int(cidr)
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    return(str((0xff000000 & mask) >> 24) + '.' +
           str((0x00ff0000 & mask) >> 16) + '.' +
           str((0x0000ff00 & mask) >> 8) + '.' +
           str((0x000000ff & mask)))


# utility function: removing keys wih value of None, nothing in playbook for that key
def fmgr_del_none(obj):
    if isinstance(obj, dict):
        return type(obj)((fmgr_del_none(k), fmgr_del_none(v))
                         for k, v in obj.items() if k is not None and (v is not None and not fmgr_is_empty_dict(v)))
    else:
        return obj


# utility function: remove keys that are need for the logic but the FMG API won't accept them
def fmgr_prepare_dict(obj):
    list_of_elems = ["mode", "adom", "host", "username", "password"]
    if isinstance(obj, dict):
        obj = dict((key, fmgr_prepare_dict(value)) for (key, value) in obj.items() if key not in list_of_elems)
    return obj


def fmgr_is_empty_dict(obj):
    return_val = False
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, dict):
                    if len(v) == 0:
                        return_val = True
                    elif len(v) > 0:
                        for k1, v1 in v.items():
                            if v1 is None:
                                return_val = True
                            elif v1 is not None:
                                return_val = False
                                return return_val
                elif v is None:
                    return_val = True
                elif v is not None:
                    return_val = False
                    return return_val
        elif len(obj) == 0:
            return_val = True

    return return_val


def fmgr_split_comma_strings_into_lists(obj):
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, str):
                    new_list = list()
                    if "," in v:
                        new_items = v.split(",")
                        for item in new_items:
                            new_list.append(item.strip())
                        obj[k] = new_list

    return obj


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
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

    module = AnsibleModule(argument_spec, supports_check_mode=False)

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

    list_overrides = ['gmail', 'imap', 'mapi', 'msn-hotmail', 'pop3', 'smtp', 'yahoo-mail']
    for list_variable in list_overrides:
        override_data = list()
        try:
            override_data = module.params[list_variable]
        except:
            pass
        try:
            if override_data:
                del paramgram[list_variable]
                paramgram[list_variable] = override_data
        except:
            pass

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    password = module.params["password"]
    username = module.params["username"]
    if host is None or username is None or password is None:
        module.fail_json(msg="Host and username and password are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])

    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    results = fmgr_spamfilter_profile_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
