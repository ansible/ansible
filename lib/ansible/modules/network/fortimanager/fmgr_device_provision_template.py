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

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fmgr_device_provision_template
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manages Device Provisioning Templates in FortiManager.
description:
    - Allows the editing and assignment of device provisioning templates in FortiManager.

options:
  adom:
    description:
     - The ADOM the configuration should belong to.
    required: true

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values.
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  device_unique_name:
    description:
     - The unique device's name that you are editing.
    required: True

  provisioning_template:
    description:
     - The provisioning template you want to apply (default = default).
    required: True

  provision_targets:
    description:
     - The friendly names of devices in FortiManager to assign the provisioning template to. CSV separated list.
    required: True

  snmp_status:
    description:
     - Enables or disables SNMP globally.
    required: False
    choices: ["enable", "disable"]

  snmp_v2c_query_port:
    description:
     - Sets the snmp v2c community query port.
    required: False

  snmp_v2c_trap_port:
    description:
     - Sets the snmp v2c community trap port.
    required: False

  snmp_v2c_status:
    description:
     - Enables or disables the v2c community specified.
    required: False
    choices: ["enable", "disable"]

  snmp_v2c_trap_status:
    description:
     - Enables or disables the v2c community specified for traps.
    required: False
    choices: ["enable", "disable"]

  snmp_v2c_query_status:
    description:
     - Enables or disables the v2c community specified for queries.
    required: False
    choices: ["enable", "disable"]

  snmp_v2c_name:
    description:
     - Specifies the v2c community name.
    required: False

  snmp_v2c_id:
    description:
     - Primary key for the snmp community. this must be unique!
    required: False

  snmp_v2c_trap_src_ipv4:
    description:
     - Source ip the traps should come from IPv4.
    required: False

  snmp_v2c_trap_hosts_ipv4:
    description: >
       - IPv4 addresses of the hosts that should get SNMP v2c traps, comma separated, must include mask
       ("10.7.220.59 255.255.255.255, 10.7.220.60 255.255.255.255").
    required: False

  snmp_v2c_query_hosts_ipv4:
    description: >
       - IPv4 addresses or subnets that are allowed to query SNMP v2c, comma separated
       ("10.7.220.59 255.255.255.0, 10.7.220.0 255.255.255.0").
    required: False

  snmpv3_auth_proto:
    description:
        - SNMPv3 auth protocol.
    required: False
    choices: ["md5", "sha"]

  snmpv3_auth_pwd:
    description:
        - SNMPv3 auth pwd __ currently not encrypted! ensure this file is locked down permissions wise!
    required: False

  snmpv3_name:
    description:
      - SNMPv3 user name.
    required: False

  snmpv3_notify_hosts:
    description:
      - List of ipv4 hosts to send snmpv3 traps to. Comma separated IPv4 list.
    required: False

  snmpv3_priv_proto:
    description:
      - SNMPv3 priv protocol.
    required: False
    choices: ["aes", "des", "aes256", "aes256cisco"]

  snmpv3_priv_pwd:
    description:
     - SNMPv3 priv pwd currently not encrypted! ensure this file is locked down permissions wise!
    required: False

  snmpv3_queries:
    description:
     - Allow snmpv3_queries.
    required: False
    choices: ["enable", "disable"]

  snmpv3_query_port:
    description:
     - SNMPv3 query port.
    required: False

  snmpv3_security_level:
    description:
     - SNMPv3 security level.
    required: False
    choices: ["no-auth-no-priv", "auth-no-priv", "auth-priv"]

  snmpv3_source_ip:
    description:
     - SNMPv3 source ipv4 address for traps.
    required: False

  snmpv3_status:
    description:
     - SNMPv3 user is enabled or disabled.
    required: False
    choices: ["enable", "disable"]

  snmpv3_trap_rport:
    description:
     - SNMPv3 trap remote port.
    required: False

  snmpv3_trap_status:
    description:
     - SNMPv3 traps is enabled or disabled.
    required: False
    choices: ["enable", "disable"]

  syslog_port:
    description:
     - Syslog port that will be set.
    required: False

  syslog_server:
    description:
     - Server the syslogs will be sent to.
    required: False

  syslog_status:
    description:
     - Enables or disables syslogs.
    required: False
    choices: ["enable", "disable"]

  syslog_mode:
    description:
     - Remote syslog logging over UDP/Reliable TCP.
     - choice | udp | Enable syslogging over UDP.
     - choice | legacy-reliable | Enable legacy reliable syslogging by RFC3195 (Reliable Delivery for Syslog).
     - choice | reliable | Enable reliable syslogging by RFC6587 (Transmission of Syslog Messages over TCP).
    required: false
    choices: ["udp", "legacy-reliable", "reliable"]
    default: "udp"

  syslog_filter:
    description:
     - Sets the logging level for syslog.
    required: False
    choices: ["emergency", "alert", "critical", "error", "warning", "notification", "information", "debug"]

  syslog_facility:
    description:
     - Remote syslog facility.
     - choice | kernel | Kernel messages.
     - choice | user | Random user-level messages.
     - choice | mail | Mail system.
     - choice | daemon | System daemons.
     - choice | auth | Security/authorization messages.
     - choice | syslog | Messages generated internally by syslog.
     - choice | lpr | Line printer subsystem.
     - choice | news | Network news subsystem.
     - choice | uucp | Network news subsystem.
     - choice | cron | Clock daemon.
     - choice | authpriv | Security/authorization messages (private).
     - choice | ftp | FTP daemon.
     - choice | ntp | NTP daemon.
     - choice | audit | Log audit.
     - choice | alert | Log alert.
     - choice | clock | Clock daemon.
     - choice | local0 | Reserved for local use.
     - choice | local1 | Reserved for local use.
     - choice | local2 | Reserved for local use.
     - choice | local3 | Reserved for local use.
     - choice | local4 | Reserved for local use.
     - choice | local5 | Reserved for local use.
     - choice | local6 | Reserved for local use.
     - choice | local7 | Reserved for local use.
    required: false
    choices: ["kernel", "user", "mail", "daemon", "auth", "syslog",
        "lpr", "news", "uucp", "cron", "authpriv", "ftp", "ntp", "audit",
        "alert", "clock", "local0", "local1", "local2", "local3", "local4", "local5", "local6", "local7"]
    default: "syslog"

  syslog_enc_algorithm:
    description:
     - Enable/disable reliable syslogging with TLS encryption.
     - choice | high | SSL communication with high encryption algorithms.
     - choice | low | SSL communication with low encryption algorithms.
     - choice | disable | Disable SSL communication.
     - choice | high-medium | SSL communication with high and medium encryption algorithms.
    required: false
    choices: ["high", "low", "disable", "high-medium"]
    default: "disable"

  syslog_certificate:
    description:
     - Certificate used to communicate with Syslog server if encryption on.
    required: false

  ntp_status:
    description:
      - Enables or disables ntp.
    required: False
    choices: ["enable", "disable"]

  ntp_sync_interval:
    description:
     - Sets the interval in minutes for ntp sync.
    required: False

  ntp_type:
    description:
     - Enables fortiguard servers or custom servers are the ntp source.
    required: False
    choices: ["fortiguard", "custom"]

  ntp_server:
    description:
     - Only used with custom ntp_type -- specifies IP of server to sync to -- comma separated ip addresses for multiples.
    required: False

  ntp_auth:
    description:
     - Enables or disables ntp authentication.
    required: False
    choices: ["enable", "disable"]

  ntp_auth_pwd:
    description:
     - Sets the ntp auth password.
    required: False

  ntp_v3:
    description:
     - Enables or disables ntpv3 (default is ntpv4).
    required: False
    choices: ["enable", "disable"]

  admin_https_redirect:
    description:
     - Enables or disables https redirect from http.
    required: False
    choices: ["enable", "disable"]

  admin_https_port:
    description:
     - SSL admin gui port number.
    required: False

  admin_http_port:
    description:
     - Non-SSL admin gui port number.
    required: False

  admin_timeout:
    description:
     - Admin timeout in minutes.
    required: False

  admin_language:
    description:
     - Sets the admin gui language.
    required: False
    choices: ["english", "simch", "japanese", "korean", "spanish", "trach", "french", "portuguese"]

  admin_switch_controller:
    description:
     - Enables or disables the switch controller.
    required: False
    choices: ["enable", "disable"]

  admin_gui_theme:
    description:
     - Changes the admin gui theme.
    required: False
    choices: ["green", "red", "blue", "melongene", "mariner"]

  admin_enable_fortiguard:
    description:
     - Enables FortiGuard security updates to their default settings.
    required: False
    choices: ["none", "direct", "this-fmg"]

  admin_fortianalyzer_target:
    description:
     - Configures faz target.
    required: False

  admin_fortiguard_target:
    description:
     - Configures fortiguard target.
     - admin_enable_fortiguard must be set to "direct".
    required: False

  smtp_username:
    description:
     - SMTP auth username.
    required: False

  smtp_password:
    description:
     - SMTP password.
    required: False

  smtp_port:
    description:
     - SMTP port number.
    required: False

  smtp_replyto:
    description:
     - SMTP reply to address.
    required: False

  smtp_conn_sec:
    description:
     - defines the ssl level for smtp.
    required: False
    choices: ["none", "starttls", "smtps"]

  smtp_server:
    description:
     - SMTP server ipv4 address.
    required: False

  smtp_source_ipv4:
    description:
     - SMTP source ip address.
    required: False

  smtp_validate_cert:
    description:
     - Enables or disables valid certificate checking for smtp.
    required: False
    choices: ["enable", "disable"]

  dns_suffix:
    description:
     - Sets the local dns domain suffix.
    required: False

  dns_primary_ipv4:
    description:
     - primary ipv4 dns forwarder.
    required: False

  dns_secondary_ipv4:
    description:
     - secondary ipv4 dns forwarder.
    required: False

  delete_provisioning_template:
    description:
     -  If specified, all other options are ignored. The specified provisioning template will be deleted.
    required: False

'''


EXAMPLES = '''
- name: SET SNMP SYSTEM INFO
  fmgr_device_provision_template:
    provisioning_template: "default"
    snmp_status: "enable"
    mode: "set"

- name: SET SNMP SYSTEM INFO ANSIBLE ADOM
  fmgr_device_provision_template:
    provisioning_template: "default"
    snmp_status: "enable"
    mode: "set"
    adom: "ansible"

- name: SET SNMP SYSTEM INFO different template (SNMPv2)
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    snmp_status: "enable"
    mode: "set"
    adom: "ansible"
    snmp_v2c_query_port: "162"
    snmp_v2c_trap_port: "161"
    snmp_v2c_status: "enable"
    snmp_v2c_trap_status: "enable"
    snmp_v2c_query_status: "enable"
    snmp_v2c_name: "ansibleV2c"
    snmp_v2c_id: "1"
    snmp_v2c_trap_src_ipv4: "10.7.220.41"
    snmp_v2c_trap_hosts_ipv4: "10.7.220.59 255.255.255.255, 10.7.220.60 255.255.255.255"
    snmp_v2c_query_hosts_ipv4: "10.7.220.59 255.255.255.255, 10.7.220.0 255.255.255.0"

- name: SET SNMP SYSTEM INFO different template (SNMPv3)
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    snmp_status: "enable"
    mode: "set"
    adom: "ansible"
    snmpv3_auth_proto: "sha"
    snmpv3_auth_pwd: "fortinet"
    snmpv3_name: "ansibleSNMPv3"
    snmpv3_notify_hosts: "10.7.220.59,10.7.220.60"
    snmpv3_priv_proto: "aes256"
    snmpv3_priv_pwd: "fortinet"
    snmpv3_queries: "enable"
    snmpv3_query_port: "161"
    snmpv3_security_level: "auth_priv"
    snmpv3_source_ip: "0.0.0.0"
    snmpv3_status: "enable"
    snmpv3_trap_rport: "162"
    snmpv3_trap_status: "enable"

- name: SET SYSLOG INFO
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    mode: "set"
    adom: "ansible"
    syslog_server: "10.7.220.59"
    syslog_port: "514"
    syslog_mode: "disable"
    syslog_status: "enable"
    syslog_filter: "information"

- name: SET NTP TO FORTIGUARD
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    mode: "set"
    adom: "ansible"
    ntp_status: "enable"
    ntp_sync_interval: "60"
    type: "fortiguard"

- name: SET NTP TO CUSTOM SERVER
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    mode: "set"
    adom: "ansible"
    ntp_status: "enable"
    ntp_sync_interval: "60"
    ntp_type: "custom"
    ntp_server: "10.7.220.32,10.7.220.1"
    ntp_auth: "enable"
    ntp_auth_pwd: "fortinet"
    ntp_v3: "disable"

- name: SET ADMIN GLOBAL SETTINGS
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    mode: "set"
    adom: "ansible"
    admin_https_redirect: "enable"
    admin_https_port: "4433"
    admin_http_port: "8080"
    admin_timeout: "30"
    admin_language: "english"
    admin_switch_controller: "enable"
    admin_gui_theme: "blue"
    admin_enable_fortiguard: "direct"
    admin_fortiguard_target: "10.7.220.128"
    admin_fortianalyzer_target: "10.7.220.61"

- name: SET CUSTOM SMTP SERVER
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    mode: "set"
    adom: "ansible"
    smtp_username: "ansible"
    smtp_password: "fortinet"
    smtp_port: "25"
    smtp_replyto: "ansible@do-not-reply.com"
    smtp_conn_sec: "starttls"
    smtp_server: "10.7.220.32"
    smtp_source_ipv4: "0.0.0.0"
    smtp_validate_cert: "disable"

- name: SET DNS SERVERS
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    mode: "set"
    adom: "ansible"
    dns_suffix: "ansible.local"
    dns_primary_ipv4: "8.8.8.8"
    dns_secondary_ipv4: "4.4.4.4"

- name: SET PROVISIONING TEMPLATE DEVICE TARGETS IN FORTIMANAGER
  fmgr_device_provision_template:
    provisioning_template: "ansibleTest"
    mode: "set"
    adom: "ansible"
    provision_targets: "FGT1, FGT2"

- name: DELETE ENTIRE PROVISIONING TEMPLATE
  fmgr_device_provision_template:
    delete_provisioning_template: "ansibleTest"
    mode: "delete"
    adom: "ansible"

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
from ansible.module_utils.network.fortimanager.common import FMGRMethods
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def get_devprof(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    response = DEFAULT_RESULT_OBJ
    datagram = {}

    url = "/pm/devprof/adom/{adom}/{name}".format(adom=paramgram["adom"], name=paramgram["provisioning_template"])
    response = fmgr.process_request(url, datagram, FMGRMethods.GET)

    return response


def set_devprof(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    response = DEFAULT_RESULT_OBJ
    if paramgram["mode"] in ['set', 'add', 'update']:
        datagram = {
            "name": paramgram["provisioning_template"],
            "type": "devprof",
            "description": "CreatedByAnsible",
        }
        url = "/pm/devprof/adom/{adom}".format(adom=paramgram["adom"])

    elif paramgram["mode"] == "delete":
        datagram = {}

        url = "/pm/devprof/adom/{adom}/{name}".format(adom=paramgram["adom"],
                                                      name=paramgram["delete_provisioning_template"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def get_devprof_scope(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    response = DEFAULT_RESULT_OBJ
    datagram = {
        "name": paramgram["provisioning_template"],
        "type": "devprof",
        "description": "CreatedByAnsible",
    }

    url = "/pm/devprof/adom/{adom}".format(adom=paramgram["adom"])
    response = fmgr.process_request(url, datagram, FMGRMethods.GET)

    return response


def set_devprof_scope(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    response = DEFAULT_RESULT_OBJ
    if paramgram["mode"] in ['set', 'add', 'update']:
        datagram = {
            "name": paramgram["provisioning_template"],
            "type": "devprof",
            "description": "CreatedByAnsible",
        }

        targets = []
        for target in paramgram["provision_targets"].split(","):
            # split the host on the space to get the mask out
            new_target = {"name": target.strip()}
            targets.append(new_target)

        datagram["scope member"] = targets

        url = "/pm/devprof/adom/{adom}".format(adom=paramgram["adom"])

    elif paramgram["mode"] == "delete":
        datagram = {
            "name": paramgram["provisioning_template"],
            "type": "devprof",
            "description": "CreatedByAnsible",
            "scope member": paramgram["targets_to_add"]
        }

        url = "/pm/devprof/adom/{adom}".format(adom=paramgram["adom"])

    response = fmgr.process_request(url, datagram, FMGRMethods.SET)
    return response


def set_devprof_snmp(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    datagram = {
        "status": paramgram["snmp_status"]
    }
    url = "/pm/config/adom/{adom}/devprof/" \
          "{provisioning_template}/system/snmp/sysinfo".format(adom=adom,
                                                               provisioning_template=paramgram["provisioning_template"])

    response = fmgr.process_request(url, datagram, FMGRMethods.SET)
    return response


def set_devprof_snmp_v2c(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    if paramgram["mode"] in ['set', 'add', 'update']:
        datagram = {
            "query-v2c-port": paramgram["snmp_v2c_query_port"],
            "trap-v2c-rport": paramgram["snmp_v2c_trap_port"],
            "status": paramgram["snmp_v2c_status"],
            "trap-v2c-status": paramgram["snmp_v2c_trap_status"],
            "query-v2c-status": paramgram["snmp_v2c_query_status"],
            "name": paramgram["snmp_v2c_name"],
            "id": paramgram["snmp_v2c_id"],
            "meta fields": dict(),
            "hosts": list(),
            "events": 411578417151,
            "query-v1-status": 0,
            "query-v1-port": 161,
            "trap-v1-status": 0,
            "trap-v1-lport": 162,
            "trap-v1-rport": 162,
            "trap-v2c-lport": 162,
        }

        # BUILD THE HOST STRINGS
        id_counter = 1
        if paramgram["snmp_v2c_trap_hosts_ipv4"] or paramgram["snmp_v2c_query_hosts_ipv4"]:
            hosts = []
            if paramgram["snmp_v2c_query_hosts_ipv4"]:
                for ipv4_host in paramgram["snmp_v2c_query_hosts_ipv4"].strip().split(","):
                    # split the host on the space to get the mask out
                    new_ipv4_host = {"ha-direct": "enable",
                                     "host-type": "query",
                                     "id": id_counter,
                                     "ip": ipv4_host.strip().split(),
                                     "meta fields": {},
                                     "source-ip": "0.0.0.0"}
                    hosts.append(new_ipv4_host)
                    id_counter += 1

            if paramgram["snmp_v2c_trap_hosts_ipv4"]:
                for ipv4_host in paramgram["snmp_v2c_trap_hosts_ipv4"].strip().split(","):
                    # split the host on the space to get the mask out
                    new_ipv4_host = {"ha-direct": "enable",
                                     "host-type": "trap",
                                     "id": id_counter,
                                     "ip": ipv4_host.strip().split(),
                                     "meta fields": {},
                                     "source-ip": paramgram["snmp_v2c_trap_src_ipv4"]}
                    hosts.append(new_ipv4_host)
                    id_counter += 1
            datagram["hosts"] = hosts

        url = "/pm/config/adom/{adom}/devprof/" \
              "{provisioning_template}/system/snmp/community".format(adom=adom,
                                                                     provisioning_template=paramgram[
                                                                         "provisioning_template"])
    elif paramgram["mode"] == "delete":
        datagram = {
            "confirm": 1
        }

        url = "/pm/config/adom/{adom}/" \
              "devprof/{provisioning_template}/" \
              "system/snmp/community/{snmp_v2c_id}".format(adom=adom,
                                                           provisioning_template=paramgram["provisioning_template"],
                                                           snmp_v2c_id=paramgram["snmp_v2c_id"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_snmp_v3(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    if paramgram["mode"] in ['set', 'add', 'update']:
        datagram = {}
        datagram["auth-pwd"] = paramgram["snmpv3_auth_pwd"]
        datagram["priv-pwd"] = paramgram["snmpv3_priv_pwd"]
        datagram["trap-rport"] = paramgram["snmpv3_trap_rport"]
        datagram["query-port"] = paramgram["snmpv3_query_port"]
        datagram["name"] = paramgram["snmpv3_name"]
        datagram["notify-hosts"] = paramgram["snmpv3_notify_hosts"].strip().split(",")
        datagram["events"] = 1647387997183
        datagram["trap-lport"] = 162

        datagram["source-ip"] = paramgram["snmpv3_source_ip"]
        datagram["ha-direct"] = 0

        url = "/pm/config/adom/{adom}/" \
              "devprof/{provisioning_template}/" \
              "system/snmp/user".format(adom=adom,
                                        provisioning_template=paramgram["provisioning_template"])
    elif paramgram["mode"] == "delete":
        datagram = {
            "confirm": 1
        }

        url = "/pm/config/adom/{adom}/devprof/" \
              "{provisioning_template}/system/snmp" \
              "/user/{snmpv3_name}".format(adom=adom,
                                           provisioning_template=paramgram["provisioning_template"],
                                           snmpv3_name=paramgram["snmpv3_name"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_syslog(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ

    datagram = {
        "status": paramgram["syslog_status"],
        "port": paramgram["syslog_port"],
        "server": paramgram["syslog_server"],
        "mode": paramgram["syslog_mode"],
        "facility": paramgram["syslog_facility"]
    }

    if paramgram["mode"] in ['set', 'add', 'update']:
        if paramgram["syslog_enc_algorithm"] in ["high", "low", "high-medium"] \
                and paramgram["syslog_certificate"] is not None:
            datagram["certificate"] = paramgram["certificate"]
            datagram["enc-algorithm"] = paramgram["syslog_enc_algorithm"]

        url = "/pm/config/adom/{adom}/" \
              "devprof/{provisioning_template}/" \
              "log/syslogd/setting".format(adom=adom,
                                           provisioning_template=paramgram["provisioning_template"])
    elif paramgram["mode"] == "delete":
        url = "/pm/config/adom/{adom}/" \
              "devprof/{provisioning_template}/" \
              "log/syslogd/setting".format(adom=adom,
                                           provisioning_template=paramgram["provisioning_template"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_syslog_filter(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]
    datagram = {
        "severity": paramgram["syslog_filter"]
    }
    response = DEFAULT_RESULT_OBJ

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/log/syslogd/filter".format(adom=adom,
                                       provisioning_template=paramgram["provisioning_template"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_ntp(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ

    # IF SET TO FORTIGUARD, BUILD A STRING SPECIFIC TO THAT
    if paramgram["ntp_type"] == "fortiguard":
        datagram = {}
        if paramgram["ntp_status"] == "enable":
            datagram["ntpsync"] = 1
        if paramgram["ntp_status"] == "disable":
            datagram["ntpsync"] = 0
        if paramgram["ntp_sync_interval"] is None:
            datagram["syncinterval"] = 1
        else:
            datagram["syncinterval"] = paramgram["ntp_sync_interval"]

        datagram["type"] = 0

    # IF THE NTP TYPE IS CUSTOM BUILD THE SERVER LIST
    if paramgram["ntp_type"] == "custom":
        id_counter = 0
        key_counter = 0
        ntpservers = []
        datagram = {}
        if paramgram["ntp_status"] == "enable":
            datagram["ntpsync"] = 1
        if paramgram["ntp_status"] == "disable":
            datagram["ntpsync"] = 0
        try:
            datagram["syncinterval"] = paramgram["ntp_sync_interval"]
        except BaseException:
            datagram["syncinterval"] = 1
        datagram["type"] = 1

        for server in paramgram["ntp_server"].strip().split(","):
            id_counter += 1
            server_fields = dict()

            key_counter += 1
            if paramgram["ntp_auth"] == "enable":
                server_fields["authentication"] = 1
                server_fields["key"] = paramgram["ntp_auth_pwd"]
                server_fields["key-id"] = key_counter
            else:
                server_fields["authentication"] = 0
                server_fields["key"] = ""
                server_fields["key-id"] = key_counter

            if paramgram["ntp_v3"] == "enable":
                server_fields["ntp_v3"] = 1
            else:
                server_fields["ntp_v3"] = 0

            # split the host on the space to get the mask out
            new_ntp_server = {"authentication": server_fields["authentication"],
                              "id": id_counter, "key": server_fields["key"],
                              "key-id": id_counter, "ntpv3": server_fields["ntp_v3"],
                              "server": server}
            ntpservers.append(new_ntp_server)
        datagram["ntpserver"] = ntpservers

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/ntp".format(adom=adom,
                               provisioning_template=paramgram["provisioning_template"])
    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_admin(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    datagram = {
        "admin-https-redirect": paramgram["admin_https_redirect"],
        "admin-port": paramgram["admin_http_port"],
        "admin-sport": paramgram["admin_https_port"],
        "admintimeout": paramgram["admin_timeout"],
        "language": paramgram["admin_language"],
        "gui-theme": paramgram["admin_gui_theme"],
        "switch-controller": paramgram["admin_switch_controller"],
    }
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/global".format(adom=adom,
                                  provisioning_template=paramgram["provisioning_template"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_smtp(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    datagram = {
        "port": paramgram["smtp_port"],
        "reply-to": paramgram["smtp_replyto"],
        "server": paramgram["smtp_server"],
        "source-ip": paramgram["smtp_source_ipv4"]
    }

    if paramgram["smtp_username"]:
        datagram["authenticate"] = 1
        datagram["username"] = paramgram["smtp_username"]
        datagram["password"] = paramgram["smtp_password"]

    if paramgram["smtp_conn_sec"] == "none":
        datagram["security"] = 0
    if paramgram["smtp_conn_sec"] == "starttls":
        datagram["security"] = 1
    if paramgram["smtp_conn_sec"] == "smtps":
        datagram["security"] = 2

    if paramgram["smtp_validate_cert"] == "enable":
        datagram["validate-server"] = 1
    else:
        datagram["validate-server"] = 0

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/email-server".format(adom=adom,
                                        provisioning_template=paramgram["provisioning_template"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_dns(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    datagram = {
        "domain": paramgram["dns_suffix"],
        "primary": paramgram["dns_primary_ipv4"],
        "secondary": paramgram["dns_secondary_ipv4"],
    }
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/dns".format(adom=adom,
                               provisioning_template=paramgram["provisioning_template"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_toggle_fg(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]
    response = DEFAULT_RESULT_OBJ
    datagram = {}
    if paramgram["admin_enable_fortiguard"] in ["direct", "this-fmg"]:
        datagram["include-default-servers"] = "enable"
    elif paramgram["admin_enable_fortiguard"] == "none":
        datagram["include-default-servers"] = "disable"

    datagram["server-list"] = list()

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/central-management".format(adom=adom,
                                              provisioning_template=paramgram["provisioning_template"])
    response = fmgr.process_request(url, datagram, FMGRMethods.SET)

    return response


def set_devprof_fg(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    datagram = {
        "target": paramgram["admin_enable_fortiguard"],
        "target-ip": None
    }

    if paramgram["mode"] in ['set', 'add', 'update']:
        if paramgram["admin_fortiguard_target"] is not None and datagram["target"] == "direct":
            datagram["target-ip"] = paramgram["admin_fortiguard_target"]

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortiguard".format(adom=adom,
                                              provisioning_template=paramgram["provisioning_template"])

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def set_devprof_faz(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    paramgram["mode"] = paramgram["mode"]
    adom = paramgram["adom"]
    response = DEFAULT_RESULT_OBJ
    datagram = {
        "target-ip": paramgram["admin_fortianalyzer_target"],
        "target": "others",
    }
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortianalyzer".format(adom=adom,
                                                 provisioning_template=paramgram["provisioning_template"])
    if paramgram["mode"] == "delete":
        datagram["hastarget"] = "False"

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        provisioning_template=dict(required=False, type="str"),
        provision_targets=dict(required=False, type="str"),

        device_unique_name=dict(required=False, type="str"),
        snmp_status=dict(required=False, type="str", choices=["enable", "disable"]),
        snmp_v2c_query_port=dict(required=False, type="int"),
        snmp_v2c_trap_port=dict(required=False, type="int"),
        snmp_v2c_status=dict(required=False, type="str", choices=["enable", "disable"]),
        snmp_v2c_trap_status=dict(required=False, type="str", choices=["enable", "disable"]),
        snmp_v2c_query_status=dict(required=False, type="str", choices=["enable", "disable"]),
        snmp_v2c_name=dict(required=False, type="str", no_log=True),
        snmp_v2c_id=dict(required=False, type="int"),
        snmp_v2c_trap_src_ipv4=dict(required=False, type="str"),
        snmp_v2c_trap_hosts_ipv4=dict(required=False, type="str"),
        snmp_v2c_query_hosts_ipv4=dict(required=False, type="str"),

        snmpv3_auth_proto=dict(required=False, type="str", choices=["md5", "sha"]),
        snmpv3_auth_pwd=dict(required=False, type="str", no_log=True),
        snmpv3_name=dict(required=False, type="str"),
        snmpv3_notify_hosts=dict(required=False, type="str"),
        snmpv3_priv_proto=dict(required=False, type="str", choices=["aes", "des", "aes256", "aes256cisco"]),
        snmpv3_priv_pwd=dict(required=False, type="str", no_log=True),
        snmpv3_queries=dict(required=False, type="str", choices=["enable", "disable"]),
        snmpv3_query_port=dict(required=False, type="int"),
        snmpv3_security_level=dict(required=False, type="str",
                                   choices=["no-auth-no-priv", "auth-no-priv", "auth-priv"]),
        snmpv3_source_ip=dict(required=False, type="str"),
        snmpv3_status=dict(required=False, type="str", choices=["enable", "disable"]),
        snmpv3_trap_rport=dict(required=False, type="int"),
        snmpv3_trap_status=dict(required=False, type="str", choices=["enable", "disable"]),

        syslog_port=dict(required=False, type="int"),
        syslog_server=dict(required=False, type="str"),
        syslog_mode=dict(required=False, type="str", choices=["udp", "legacy-reliable", "reliable"], default="udp"),
        syslog_status=dict(required=False, type="str", choices=["enable", "disable"]),
        syslog_filter=dict(required=False, type="str", choices=["emergency", "alert", "critical", "error",
                                                                "warning", "notification", "information", "debug"]),
        syslog_enc_algorithm=dict(required=False, type="str", choices=["high", "low", "disable", "high-medium"],
                                  default="disable"),
        syslog_facility=dict(required=False, type="str", choices=["kernel", "user", "mail", "daemon", "auth",
                                                                  "syslog", "lpr", "news", "uucp", "cron", "authpriv",
                                                                  "ftp", "ntp", "audit", "alert", "clock", "local0",
                                                                  "local1", "local2", "local3", "local4", "local5",
                                                                  "local6", "local7"], default="syslog"),
        syslog_certificate=dict(required=False, type="str"),

        ntp_status=dict(required=False, type="str", choices=["enable", "disable"]),
        ntp_sync_interval=dict(required=False, type="int"),
        ntp_type=dict(required=False, type="str", choices=["fortiguard", "custom"]),
        ntp_server=dict(required=False, type="str"),
        ntp_auth=dict(required=False, type="str", choices=["enable", "disable"]),
        ntp_auth_pwd=dict(required=False, type="str", no_log=True),
        ntp_v3=dict(required=False, type="str", choices=["enable", "disable"]),

        admin_https_redirect=dict(required=False, type="str", choices=["enable", "disable"]),
        admin_https_port=dict(required=False, type="int"),
        admin_http_port=dict(required=False, type="int"),
        admin_timeout=dict(required=False, type="int"),
        admin_language=dict(required=False, type="str",
                            choices=["english", "simch", "japanese", "korean",
                                     "spanish", "trach", "french", "portuguese"]),
        admin_switch_controller=dict(required=False, type="str", choices=["enable", "disable"]),
        admin_gui_theme=dict(required=False, type="str", choices=["green", "red", "blue", "melongene", "mariner"]),
        admin_enable_fortiguard=dict(required=False, type="str", choices=["none", "direct", "this-fmg"]),
        admin_fortianalyzer_target=dict(required=False, type="str"),
        admin_fortiguard_target=dict(required=False, type="str"),

        smtp_username=dict(required=False, type="str"),
        smtp_password=dict(required=False, type="str", no_log=True),
        smtp_port=dict(required=False, type="int"),
        smtp_replyto=dict(required=False, type="str"),
        smtp_conn_sec=dict(required=False, type="str", choices=["none", "starttls", "smtps"]),
        smtp_server=dict(required=False, type="str"),
        smtp_source_ipv4=dict(required=False, type="str"),
        smtp_validate_cert=dict(required=False, type="str", choices=["enable", "disable"]),

        dns_suffix=dict(required=False, type="str"),
        dns_primary_ipv4=dict(required=False, type="str"),
        dns_secondary_ipv4=dict(required=False, type="str"),
        delete_provisioning_template=dict(required=False, type="str")
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    paramgram = {
        "adom": module.params["adom"],
        "mode": module.params["mode"],
        "provision_targets": module.params["provision_targets"],
        "provisioning_template": module.params["provisioning_template"],

        "snmp_status": module.params["snmp_status"],
        "snmp_v2c_query_port": module.params["snmp_v2c_query_port"],
        "snmp_v2c_trap_port": module.params["snmp_v2c_trap_port"],
        "snmp_v2c_status": module.params["snmp_v2c_status"],
        "snmp_v2c_trap_status": module.params["snmp_v2c_trap_status"],
        "snmp_v2c_query_status": module.params["snmp_v2c_query_status"],
        "snmp_v2c_name": module.params["snmp_v2c_name"],
        "snmp_v2c_id": module.params["snmp_v2c_id"],
        "snmp_v2c_trap_src_ipv4": module.params["snmp_v2c_trap_src_ipv4"],
        "snmp_v2c_trap_hosts_ipv4": module.params["snmp_v2c_trap_hosts_ipv4"],
        "snmp_v2c_query_hosts_ipv4": module.params["snmp_v2c_query_hosts_ipv4"],

        "snmpv3_auth_proto": module.params["snmpv3_auth_proto"],
        "snmpv3_auth_pwd": module.params["snmpv3_auth_pwd"],
        "snmpv3_name": module.params["snmpv3_name"],
        "snmpv3_notify_hosts": module.params["snmpv3_notify_hosts"],
        "snmpv3_priv_proto": module.params["snmpv3_priv_proto"],
        "snmpv3_priv_pwd": module.params["snmpv3_priv_pwd"],
        "snmpv3_queries": module.params["snmpv3_queries"],
        "snmpv3_query_port": module.params["snmpv3_query_port"],
        "snmpv3_security_level": module.params["snmpv3_security_level"],
        "snmpv3_source_ip": module.params["snmpv3_source_ip"],
        "snmpv3_status": module.params["snmpv3_status"],
        "snmpv3_trap_rport": module.params["snmpv3_trap_rport"],
        "snmpv3_trap_status": module.params["snmpv3_trap_status"],

        "syslog_port": module.params["syslog_port"],
        "syslog_server": module.params["syslog_server"],
        "syslog_mode": module.params["syslog_mode"],
        "syslog_status": module.params["syslog_status"],
        "syslog_filter": module.params["syslog_filter"],
        "syslog_facility": module.params["syslog_facility"],
        "syslog_enc_algorithm": module.params["syslog_enc_algorithm"],
        "syslog_certificate": module.params["syslog_certificate"],

        "ntp_status": module.params["ntp_status"],
        "ntp_sync_interval": module.params["ntp_sync_interval"],
        "ntp_type": module.params["ntp_type"],
        "ntp_server": module.params["ntp_server"],
        "ntp_auth": module.params["ntp_auth"],
        "ntp_auth_pwd": module.params["ntp_auth_pwd"],
        "ntp_v3": module.params["ntp_v3"],

        "admin_https_redirect": module.params["admin_https_redirect"],
        "admin_https_port": module.params["admin_https_port"],
        "admin_http_port": module.params["admin_http_port"],
        "admin_timeout": module.params["admin_timeout"],
        "admin_language": module.params["admin_language"],
        "admin_switch_controller": module.params["admin_switch_controller"],
        "admin_gui_theme": module.params["admin_gui_theme"],
        "admin_enable_fortiguard": module.params["admin_enable_fortiguard"],
        "admin_fortianalyzer_target": module.params["admin_fortianalyzer_target"],
        "admin_fortiguard_target": module.params["admin_fortiguard_target"],

        "smtp_username": module.params["smtp_username"],
        "smtp_password": module.params["smtp_password"],
        "smtp_port": module.params["smtp_port"],
        "smtp_replyto": module.params["smtp_replyto"],
        "smtp_conn_sec": module.params["smtp_conn_sec"],
        "smtp_server": module.params["smtp_server"],
        "smtp_source_ipv4": module.params["smtp_source_ipv4"],
        "smtp_validate_cert": module.params["smtp_validate_cert"],

        "dns_suffix": module.params["dns_suffix"],
        "dns_primary_ipv4": module.params["dns_primary_ipv4"],
        "dns_secondary_ipv4": module.params["dns_secondary_ipv4"],
        "delete_provisioning_template": module.params["delete_provisioning_template"]
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
        # CHECK IF WE ARE DELETING AN ENTIRE TEMPLATE. IF THAT'S THE CASE DO IT FIRST AND IGNORE THE REST.
        if paramgram["delete_provisioning_template"] is not None:
            results = set_devprof(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0, -10, -1],
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram),
                                 stop_on_success=True)
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # CHECK TO SEE IF THE DEVPROF TEMPLATE EXISTS
        devprof = get_devprof(fmgr, paramgram)
        if devprof[0] != 0:
            results = set_devprof(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0, -2], stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # PROCESS THE SNMP SETTINGS IF THE SNMP_STATUS VARIABLE IS SET
        if paramgram["snmp_status"] is not None:
            results = set_devprof_snmp(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0], stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

        # PROCESS THE SNMP V2C COMMUNITY SETTINGS IF THEY ARE ALL HERE
        if all(v is not None for v in (paramgram["snmp_v2c_query_port"], paramgram["snmp_v2c_trap_port"],
                                       paramgram["snmp_v2c_status"], paramgram["snmp_v2c_trap_status"],
                                       paramgram["snmp_v2c_query_status"], paramgram["snmp_v2c_name"],
                                       paramgram["snmp_v2c_id"])):
            results = set_devprof_snmp_v2c(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0, -10033], stop_on_success=True,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

        # PROCESS THE SNMPV3 USER IF THERE
        if all(v is not None for v in (
                [paramgram["snmpv3_auth_proto"], paramgram["snmpv3_auth_pwd"], paramgram["snmpv3_name"],
                 paramgram["snmpv3_notify_hosts"], paramgram["snmpv3_priv_proto"],
                 paramgram["snmpv3_priv_pwd"],
                 paramgram["snmpv3_queries"],
                 paramgram["snmpv3_query_port"], paramgram["snmpv3_security_level"],
                 paramgram["snmpv3_source_ip"],
                 paramgram["snmpv3_status"], paramgram["snmpv3_trap_rport"], paramgram["snmpv3_trap_status"]])):

            results = set_devprof_snmp_v3(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0, -10033, -10000, -3],
                                 stop_on_success=True,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # PROCESS THE SYSLOG SETTINGS IF THE ALL THE NEEDED SYSLOG VARIABLES ARE PRESENT
        if all(v is not None for v in [paramgram["syslog_port"], paramgram["syslog_mode"],
                                       paramgram["syslog_server"], paramgram["syslog_status"]]):
            # enable syslog in the devprof template
            results = set_devprof_syslog(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0, -10033, -10000, -3],
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # IF THE SYSLOG FILTER IS PRESENT THEN RUN THAT
        if paramgram["syslog_filter"] is not None:
            results = set_devprof_syslog_filter(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0],
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # PROCESS NTP OPTIONS
        if paramgram["ntp_status"]:
            # VALIDATE INPUT
            if paramgram["ntp_type"] == "custom" and paramgram["ntp_server"] is None:
                module.exit_json(msg="You requested custom NTP type but did not provide ntp_server parameter.")
            if paramgram["ntp_auth"] == "enable" and paramgram["ntp_auth_pwd"] is None:
                module.exit_json(
                    msg="You requested NTP Authentication but did not provide ntp_auth_pwd parameter.")

            results = set_devprof_ntp(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0],
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)
    try:
        # PROCESS THE ADMIN OPTIONS
        if any(v is not None for v in (
                paramgram["admin_https_redirect"], paramgram["admin_https_port"], paramgram["admin_http_port"],
                paramgram["admin_timeout"],
                paramgram["admin_language"], paramgram["admin_switch_controller"],
                paramgram["admin_gui_theme"])):

            results = set_devprof_admin(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0], stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # PROCESS FORTIGUARD OPTIONS
        if paramgram["admin_enable_fortiguard"] is not None:

            results = set_devprof_toggle_fg(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0], stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
            results = set_devprof_fg(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0], stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # PROCESS THE SMTP OPTIONS
        if all(v is not None for v in (
                paramgram["smtp_username"], paramgram["smtp_password"], paramgram["smtp_port"],
                paramgram["smtp_replyto"],
                paramgram["smtp_conn_sec"], paramgram["smtp_server"],
                paramgram["smtp_source_ipv4"], paramgram["smtp_validate_cert"])):

            results = set_devprof_smtp(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0], stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # PROCESS THE DNS OPTIONS
        if any(v is not None for v in
               (paramgram["dns_suffix"], paramgram["dns_primary_ipv4"], paramgram["dns_secondary_ipv4"])):
            results = set_devprof_dns(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0], stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # PROCESS THE admin_fortianalyzer_target OPTIONS
        if paramgram["admin_fortianalyzer_target"] is not None:

            results = set_devprof_faz(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results, good_codes=[0], stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # PROCESS THE PROVISIONING TEMPLATE TARGET PARAMETER
        if paramgram["provision_targets"] is not None:
            if paramgram["mode"] != "delete":
                results = set_devprof_scope(fmgr, paramgram)
                fmgr.govern_response(module=module, results=results, good_codes=[0], stop_on_success=False,
                                     ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

            if paramgram["mode"] == "delete":
                # WE NEED TO FIGURE OUT WHAT'S THERE FIRST, BEFORE WE CAN RUN THIS
                targets_to_add = list()
                try:
                    current_scope = get_devprof_scope(fmgr, paramgram)
                    targets_to_remove = paramgram["provision_targets"].strip().split(",")
                    targets = current_scope[1][1]["scope member"]
                    for target in targets:
                        if target["name"] not in targets_to_remove:
                            target_append = {"name": target["name"]}
                            targets_to_add.append(target_append)
                except BaseException:
                    pass
                paramgram["targets_to_add"] = targets_to_add
                results = set_devprof_scope(fmgr, paramgram)
                fmgr.govern_response(module=module, results=results, good_codes=[0, -10033, -10000, -3],
                                     ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
