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
module: fmgr_secprof_ssl_ssh
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage SSL and SSH security profiles in FortiManager
description:
  -  Manage SSL and SSH security profiles in FortiManager via the FMG API

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  host:
    description:
      - The FortiManager's address.
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

  whitelist:
    description:
      - Enable/disable exempting servers by FortiGuard whitelist.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  use_ssl_server:
    description:
      - Enable/disable the use of SSL server table for SSL offloading.
      - choice | disable | Don't use SSL server configuration.
      - choice | enable | Use SSL server configuration.
    required: false
    choices: ["disable", "enable"]

  untrusted_caname:
    description:
      - Untrusted CA certificate used by SSL Inspection.
    required: false

  ssl_exemptions_log:
    description:
      - Enable/disable logging SSL exemptions.
      - choice | disable | Disable logging SSL exemptions.
      - choice | enable | Enable logging SSL exemptions.
    required: false
    choices: ["disable", "enable"]

  ssl_anomalies_log:
    description:
      - Enable/disable logging SSL anomalies.
      - choice | disable | Disable logging SSL anomalies.
      - choice | enable | Enable logging SSL anomalies.
    required: false
    choices: ["disable", "enable"]

  server_cert_mode:
    description:
      - Re-sign or replace the server's certificate.
      - choice | re-sign | Multiple clients connecting to multiple servers.
      - choice | replace | Protect an SSL server.
    required: false
    choices: ["re-sign", "replace"]

  server_cert:
    description:
      - Certificate used by SSL Inspection to replace server certificate.
    required: false

  rpc_over_https:
    description:
      - Enable/disable inspection of RPC over HTTPS.
      - choice | disable | Disable inspection of RPC over HTTPS.
      - choice | enable | Enable inspection of RPC over HTTPS.
    required: false
    choices: ["disable", "enable"]

  name:
    description:
      - Name.
    required: false

  mapi_over_https:
    description:
      - Enable/disable inspection of MAPI over HTTPS.
      - choice | disable | Disable inspection of MAPI over HTTPS.
      - choice | enable | Enable inspection of MAPI over HTTPS.
    required: false
    choices: ["disable", "enable"]

  comment:
    description:
      - Optional comments.
    required: false

  caname:
    description:
      - CA certificate used by SSL Inspection.
    required: false

  ftps:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ftps_allow_invalid_server_cert:
    description:
      - When enabled, allows SSL sessions whose server certificate validation failed.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  ftps_client_cert_request:
    description:
      - Action based on client certificate request failure.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ftps_ports:
    description:
      - Ports to use for scanning (1 - 65535, default = 443).
    required: false

  ftps_status:
    description:
      - Configure protocol inspection status.
      - choice | disable | Disable.
      - choice | deep-inspection | Full SSL inspection.
    required: false
    choices: ["disable", "deep-inspection"]

  ftps_unsupported_ssl:
    description:
      - Action based on the SSL encryption used being unsupported.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ftps_untrusted_cert:
    description:
      - Allow, ignore, or block the untrusted SSL session server certificate.
      - choice | allow | Allow the untrusted server certificate.
      - choice | block | Block the connection when an untrusted server certificate is detected.
      - choice | ignore | Always take the server certificate as trusted.
    required: false
    choices: ["allow", "block", "ignore"]

  https:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  https_allow_invalid_server_cert:
    description:
      - When enabled, allows SSL sessions whose server certificate validation failed.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  https_client_cert_request:
    description:
      - Action based on client certificate request failure.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  https_ports:
    description:
      - Ports to use for scanning (1 - 65535, default = 443).
    required: false

  https_status:
    description:
      - Configure protocol inspection status.
      - choice | disable | Disable.
      - choice | certificate-inspection | Inspect SSL handshake only.
      - choice | deep-inspection | Full SSL inspection.
    required: false
    choices: ["disable", "certificate-inspection", "deep-inspection"]

  https_unsupported_ssl:
    description:
      - Action based on the SSL encryption used being unsupported.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  https_untrusted_cert:
    description:
      - Allow, ignore, or block the untrusted SSL session server certificate.
      - choice | allow | Allow the untrusted server certificate.
      - choice | block | Block the connection when an untrusted server certificate is detected.
      - choice | ignore | Always take the server certificate as trusted.
    required: false
    choices: ["allow", "block", "ignore"]

  imaps:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  imaps_allow_invalid_server_cert:
    description:
      - When enabled, allows SSL sessions whose server certificate validation failed.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  imaps_client_cert_request:
    description:
      - Action based on client certificate request failure.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  imaps_ports:
    description:
      - Ports to use for scanning (1 - 65535, default = 443).
    required: false

  imaps_status:
    description:
      - Configure protocol inspection status.
      - choice | disable | Disable.
      - choice | deep-inspection | Full SSL inspection.
    required: false
    choices: ["disable", "deep-inspection"]

  imaps_unsupported_ssl:
    description:
      - Action based on the SSL encryption used being unsupported.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  imaps_untrusted_cert:
    description:
      - Allow, ignore, or block the untrusted SSL session server certificate.
      - choice | allow | Allow the untrusted server certificate.
      - choice | block | Block the connection when an untrusted server certificate is detected.
      - choice | ignore | Always take the server certificate as trusted.
    required: false
    choices: ["allow", "block", "ignore"]

  pop3s:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  pop3s_allow_invalid_server_cert:
    description:
      - When enabled, allows SSL sessions whose server certificate validation failed.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  pop3s_client_cert_request:
    description:
      - Action based on client certificate request failure.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  pop3s_ports:
    description:
      - Ports to use for scanning (1 - 65535, default = 443).
    required: false

  pop3s_status:
    description:
      - Configure protocol inspection status.
      - choice | disable | Disable.
      - choice | deep-inspection | Full SSL inspection.
    required: false
    choices: ["disable", "deep-inspection"]

  pop3s_unsupported_ssl:
    description:
      - Action based on the SSL encryption used being unsupported.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  pop3s_untrusted_cert:
    description:
      - Allow, ignore, or block the untrusted SSL session server certificate.
      - choice | allow | Allow the untrusted server certificate.
      - choice | block | Block the connection when an untrusted server certificate is detected.
      - choice | ignore | Always take the server certificate as trusted.
    required: false
    choices: ["allow", "block", "ignore"]

  smtps:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  smtps_allow_invalid_server_cert:
    description:
      - When enabled, allows SSL sessions whose server certificate validation failed.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  smtps_client_cert_request:
    description:
      - Action based on client certificate request failure.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  smtps_ports:
    description:
      - Ports to use for scanning (1 - 65535, default = 443).
    required: false

  smtps_status:
    description:
      - Configure protocol inspection status.
      - choice | disable | Disable.
      - choice | deep-inspection | Full SSL inspection.
    required: false
    choices: ["disable", "deep-inspection"]

  smtps_unsupported_ssl:
    description:
      - Action based on the SSL encryption used being unsupported.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  smtps_untrusted_cert:
    description:
      - Allow, ignore, or block the untrusted SSL session server certificate.
      - choice | allow | Allow the untrusted server certificate.
      - choice | block | Block the connection when an untrusted server certificate is detected.
      - choice | ignore | Always take the server certificate as trusted.
    required: false
    choices: ["allow", "block", "ignore"]

  ssh:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ssh_inspect_all:
    description:
      - Level of SSL inspection.
      - choice | disable | Disable.
      - choice | deep-inspection | Full SSL inspection.
    required: false
    choices: ["disable", "deep-inspection"]

  ssh_ports:
    description:
      - Ports to use for scanning (1 - 65535, default = 443).
    required: false

  ssh_ssh_algorithm:
    description:
      - Relative strength of encryption algorithms accepted during negotiation.
      - choice | compatible | Allow a broader set of encryption algorithms for best compatibility.
      - choice | high-encryption | Allow only AES-CTR, AES-GCM ciphers and high encryption algorithms.
    required: false
    choices: ["compatible", "high-encryption"]

  ssh_ssh_policy_check:
    description:
      - Enable/disable SSH policy check.
      - choice | disable | Disable SSH policy check.
      - choice | enable | Enable SSH policy check.
    required: false
    choices: ["disable", "enable"]

  ssh_ssh_tun_policy_check:
    description:
      - Enable/disable SSH tunnel policy check.
      - choice | disable | Disable SSH tunnel policy check.
      - choice | enable | Enable SSH tunnel policy check.
    required: false
    choices: ["disable", "enable"]

  ssh_status:
    description:
      - Configure protocol inspection status.
      - choice | disable | Disable.
      - choice | deep-inspection | Full SSL inspection.
    required: false
    choices: ["disable", "deep-inspection"]

  ssh_unsupported_version:
    description:
      - Action based on SSH version being unsupported.
      - choice | block | Block.
      - choice | bypass | Bypass.
    required: false
    choices: ["block", "bypass"]

  ssl:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ssl_allow_invalid_server_cert:
    description:
      - When enabled, allows SSL sessions whose server certificate validation failed.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  ssl_client_cert_request:
    description:
      - Action based on client certificate request failure.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ssl_inspect_all:
    description:
      - Level of SSL inspection.
      - choice | disable | Disable.
      - choice | certificate-inspection | Inspect SSL handshake only.
      - choice | deep-inspection | Full SSL inspection.
    required: false
    choices: ["disable", "certificate-inspection", "deep-inspection"]

  ssl_unsupported_ssl:
    description:
      - Action based on the SSL encryption used being unsupported.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ssl_untrusted_cert:
    description:
      - Allow, ignore, or block the untrusted SSL session server certificate.
      - choice | allow | Allow the untrusted server certificate.
      - choice | block | Block the connection when an untrusted server certificate is detected.
      - choice | ignore | Always take the server certificate as trusted.
    required: false
    choices: ["allow", "block", "ignore"]

  ssl_exempt:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ssl_exempt_address:
    description:
      - IPv4 address object.
    required: false

  ssl_exempt_address6:
    description:
      - IPv6 address object.
    required: false

  ssl_exempt_fortiguard_category:
    description:
      - FortiGuard category ID.
    required: false

  ssl_exempt_regex:
    description:
      - Exempt servers by regular expression.
    required: false

  ssl_exempt_type:
    description:
      - Type of address object (IPv4 or IPv6) or FortiGuard category.
      - choice | fortiguard-category | FortiGuard category.
      - choice | address | Firewall IPv4 address.
      - choice | address6 | Firewall IPv6 address.
      - choice | wildcard-fqdn | Fully Qualified Domain Name with wildcard characters.
      - choice | regex | Regular expression FQDN.
    required: false
    choices: ["fortiguard-category", "address", "address6", "wildcard-fqdn", "regex"]

  ssl_exempt_wildcard_fqdn:
    description:
      - Exempt servers by wildcard FQDN.
    required: false

  ssl_server:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ssl_server_ftps_client_cert_request:
    description:
      - Action based on client certificate request failure during the FTPS handshake.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ssl_server_https_client_cert_request:
    description:
      - Action based on client certificate request failure during the HTTPS handshake.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ssl_server_imaps_client_cert_request:
    description:
      - Action based on client certificate request failure during the IMAPS handshake.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ssl_server_ip:
    description:
      - IPv4 address of the SSL server.
    required: false

  ssl_server_pop3s_client_cert_request:
    description:
      - Action based on client certificate request failure during the POP3S handshake.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ssl_server_smtps_client_cert_request:
    description:
      - Action based on client certificate request failure during the SMTPS handshake.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]

  ssl_server_ssl_other_client_cert_request:
    description:
      - Action based on client certificate request failure during an SSL protocol handshake.
      - choice | bypass | Bypass.
      - choice | inspect | Inspect.
      - choice | block | Block.
    required: false
    choices: ["bypass", "inspect", "block"]


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_ssl_ssh:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: Ansible_SSL_SSH_Profile
      mode: delete

  - name: CREATE Profile
    fmgr_secprof_ssl_ssh:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: Ansible_SSL_SSH_Profile
      comment: "Created by Ansible Module TEST"
      mode: set
      mapi_over_https: enable
      rpc_over_https: enable
      server_cert_mode: replace
      ssl_anomalies_log: enable
      ssl_exemptions_log: enable
      use_ssl_server: enable
      whitelist: enable
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

###############
# START METHODS
###############


def fmgr_firewall_ssl_ssh_profile_addsetdelete(fmg, paramgram):
    """
    fmgr_firewall_ssl_ssh_profile -- Your Description here, bruh
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/firewall/ssl-ssh-profile'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/firewall/ssl-ssh-profile/{name}'.format(adom=adom, name=paramgram["name"])
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
        except Exception:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except Exception:
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

        whitelist=dict(required=False, type="str", choices=["disable", "enable"]),
        use_ssl_server=dict(required=False, type="str", choices=["disable", "enable"]),
        untrusted_caname=dict(required=False, type="str"),
        ssl_exemptions_log=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_anomalies_log=dict(required=False, type="str", choices=["disable", "enable"]),
        server_cert_mode=dict(required=False, type="str", choices=["re-sign", "replace"]),
        server_cert=dict(required=False, type="str"),
        rpc_over_https=dict(required=False, type="str", choices=["disable", "enable"]),
        name=dict(required=False, type="str"),
        mapi_over_https=dict(required=False, type="str", choices=["disable", "enable"]),
        comment=dict(required=False, type="str"),
        caname=dict(required=False, type="str"),
        ftps=dict(required=False, type="list"),
        ftps_allow_invalid_server_cert=dict(required=False, type="str", choices=["disable", "enable"]),
        ftps_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ftps_ports=dict(required=False, type="str"),
        ftps_status=dict(required=False, type="str", choices=["disable", "deep-inspection"]),
        ftps_unsupported_ssl=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ftps_untrusted_cert=dict(required=False, type="str", choices=["allow", "block", "ignore"]),
        https=dict(required=False, type="list"),
        https_allow_invalid_server_cert=dict(required=False, type="str", choices=["disable", "enable"]),
        https_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        https_ports=dict(required=False, type="str"),
        https_status=dict(required=False, type="str", choices=["disable", "certificate-inspection", "deep-inspection"]),
        https_unsupported_ssl=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        https_untrusted_cert=dict(required=False, type="str", choices=["allow", "block", "ignore"]),
        imaps=dict(required=False, type="list"),
        imaps_allow_invalid_server_cert=dict(required=False, type="str", choices=["disable", "enable"]),
        imaps_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        imaps_ports=dict(required=False, type="str"),
        imaps_status=dict(required=False, type="str", choices=["disable", "deep-inspection"]),
        imaps_unsupported_ssl=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        imaps_untrusted_cert=dict(required=False, type="str", choices=["allow", "block", "ignore"]),
        pop3s=dict(required=False, type="list"),
        pop3s_allow_invalid_server_cert=dict(required=False, type="str", choices=["disable", "enable"]),
        pop3s_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        pop3s_ports=dict(required=False, type="str"),
        pop3s_status=dict(required=False, type="str", choices=["disable", "deep-inspection"]),
        pop3s_unsupported_ssl=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        pop3s_untrusted_cert=dict(required=False, type="str", choices=["allow", "block", "ignore"]),
        smtps=dict(required=False, type="list"),
        smtps_allow_invalid_server_cert=dict(required=False, type="str", choices=["disable", "enable"]),
        smtps_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        smtps_ports=dict(required=False, type="str"),
        smtps_status=dict(required=False, type="str", choices=["disable", "deep-inspection"]),
        smtps_unsupported_ssl=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        smtps_untrusted_cert=dict(required=False, type="str", choices=["allow", "block", "ignore"]),
        ssh=dict(required=False, type="list"),
        ssh_inspect_all=dict(required=False, type="str", choices=["disable", "deep-inspection"]),
        ssh_ports=dict(required=False, type="str"),
        ssh_ssh_algorithm=dict(required=False, type="str", choices=["compatible", "high-encryption"]),
        ssh_ssh_policy_check=dict(required=False, type="str", choices=["disable", "enable"]),
        ssh_ssh_tun_policy_check=dict(required=False, type="str", choices=["disable", "enable"]),
        ssh_status=dict(required=False, type="str", choices=["disable", "deep-inspection"]),
        ssh_unsupported_version=dict(required=False, type="str", choices=["block", "bypass"]),
        ssl=dict(required=False, type="list"),
        ssl_allow_invalid_server_cert=dict(required=False, type="str", choices=["disable", "enable"]),
        ssl_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ssl_inspect_all=dict(required=False, type="str", choices=["disable", "certificate-inspection",
                                                                  "deep-inspection"]),
        ssl_unsupported_ssl=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ssl_untrusted_cert=dict(required=False, type="str", choices=["allow", "block", "ignore"]),
        ssl_exempt=dict(required=False, type="list"),
        ssl_exempt_address=dict(required=False, type="str"),
        ssl_exempt_address6=dict(required=False, type="str"),
        ssl_exempt_fortiguard_category=dict(required=False, type="str"),
        ssl_exempt_regex=dict(required=False, type="str"),
        ssl_exempt_type=dict(required=False, type="str", choices=["fortiguard-category", "address", "address6",
                                                                  "wildcard-fqdn", "regex"]),
        ssl_exempt_wildcard_fqdn=dict(required=False, type="str"),
        ssl_server=dict(required=False, type="list"),
        ssl_server_ftps_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ssl_server_https_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ssl_server_imaps_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ssl_server_ip=dict(required=False, type="str"),
        ssl_server_pop3s_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ssl_server_smtps_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect", "block"]),
        ssl_server_ssl_other_client_cert_request=dict(required=False, type="str", choices=["bypass", "inspect",
                                                                                           "block"]),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "whitelist": module.params["whitelist"],
        "use-ssl-server": module.params["use_ssl_server"],
        "untrusted-caname": module.params["untrusted_caname"],
        "ssl-exemptions-log": module.params["ssl_exemptions_log"],
        "ssl-anomalies-log": module.params["ssl_anomalies_log"],
        "server-cert-mode": module.params["server_cert_mode"],
        "server-cert": module.params["server_cert"],
        "rpc-over-https": module.params["rpc_over_https"],
        "name": module.params["name"],
        "mapi-over-https": module.params["mapi_over_https"],
        "comment": module.params["comment"],
        "caname": module.params["caname"],
        "ftps": {
            "allow-invalid-server-cert": module.params["ftps_allow_invalid_server_cert"],
            "client-cert-request": module.params["ftps_client_cert_request"],
            "ports": module.params["ftps_ports"],
            "status": module.params["ftps_status"],
            "unsupported-ssl": module.params["ftps_unsupported_ssl"],
            "untrusted-cert": module.params["ftps_untrusted_cert"],
        },
        "https": {
            "allow-invalid-server-cert": module.params["https_allow_invalid_server_cert"],
            "client-cert-request": module.params["https_client_cert_request"],
            "ports": module.params["https_ports"],
            "status": module.params["https_status"],
            "unsupported-ssl": module.params["https_unsupported_ssl"],
            "untrusted-cert": module.params["https_untrusted_cert"],
        },
        "imaps": {
            "allow-invalid-server-cert": module.params["imaps_allow_invalid_server_cert"],
            "client-cert-request": module.params["imaps_client_cert_request"],
            "ports": module.params["imaps_ports"],
            "status": module.params["imaps_status"],
            "unsupported-ssl": module.params["imaps_unsupported_ssl"],
            "untrusted-cert": module.params["imaps_untrusted_cert"],
        },
        "pop3s": {
            "allow-invalid-server-cert": module.params["pop3s_allow_invalid_server_cert"],
            "client-cert-request": module.params["pop3s_client_cert_request"],
            "ports": module.params["pop3s_ports"],
            "status": module.params["pop3s_status"],
            "unsupported-ssl": module.params["pop3s_unsupported_ssl"],
            "untrusted-cert": module.params["pop3s_untrusted_cert"],
        },
        "smtps": {
            "allow-invalid-server-cert": module.params["smtps_allow_invalid_server_cert"],
            "client-cert-request": module.params["smtps_client_cert_request"],
            "ports": module.params["smtps_ports"],
            "status": module.params["smtps_status"],
            "unsupported-ssl": module.params["smtps_unsupported_ssl"],
            "untrusted-cert": module.params["smtps_untrusted_cert"],
        },
        "ssh": {
            "inspect-all": module.params["ssh_inspect_all"],
            "ports": module.params["ssh_ports"],
            "ssh-algorithm": module.params["ssh_ssh_algorithm"],
            "ssh-policy-check": module.params["ssh_ssh_policy_check"],
            "ssh-tun-policy-check": module.params["ssh_ssh_tun_policy_check"],
            "status": module.params["ssh_status"],
            "unsupported-version": module.params["ssh_unsupported_version"],
        },
        "ssl": {
            "allow-invalid-server-cert": module.params["ssl_allow_invalid_server_cert"],
            "client-cert-request": module.params["ssl_client_cert_request"],
            "inspect-all": module.params["ssl_inspect_all"],
            "unsupported-ssl": module.params["ssl_unsupported_ssl"],
            "untrusted-cert": module.params["ssl_untrusted_cert"],
        },
        "ssl-exempt": {
            "address": module.params["ssl_exempt_address"],
            "address6": module.params["ssl_exempt_address6"],
            "fortiguard-category": module.params["ssl_exempt_fortiguard_category"],
            "regex": module.params["ssl_exempt_regex"],
            "type": module.params["ssl_exempt_type"],
            "wildcard-fqdn": module.params["ssl_exempt_wildcard_fqdn"],
        },
        "ssl-server": {
            "ftps-client-cert-request": module.params["ssl_server_ftps_client_cert_request"],
            "https-client-cert-request": module.params["ssl_server_https_client_cert_request"],
            "imaps-client-cert-request": module.params["ssl_server_imaps_client_cert_request"],
            "ip": module.params["ssl_server_ip"],
            "pop3s-client-cert-request": module.params["ssl_server_pop3s_client_cert_request"],
            "smtps-client-cert-request": module.params["ssl_server_smtps_client_cert_request"],
            "ssl-other-client-cert-request": module.params["ssl_server_ssl_other_client_cert_request"],
        }
    }

    list_overrides = ['ftps', 'https', 'imaps', 'pop3s', 'smtps', 'ssh', 'ssl', 'ssl-exempt', 'ssl-server']
    for list_variable in list_overrides:
        override_data = list()
        try:
            override_data = module.params[list_variable]
        except Exception:
            pass
        try:
            if override_data:
                del paramgram[list_variable]
                paramgram[list_variable] = override_data
        except Exception:
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

    results = fmgr_firewall_ssl_ssh_profile_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
