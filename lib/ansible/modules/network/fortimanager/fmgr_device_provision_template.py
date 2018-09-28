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
author: Luke Weighall, Andrew Welsh
short_description: Manages Device Provisioning Templates in FortiManager
description:
    - Allows the editing and assignment of device provisioning templates in FortiManager

options:
  adom:
    description:
     -The ADOM the configuration should belong to.
    required: true
  host:
    description:
     -The FortiManager's Address.
    required: true
  username:
    description:
     -The username used to authenticate with the FortiManager.
    required: false
  password:
    description:
     -The password associated with the username account.
    required: false
  state:
    description: >
     -The desired state of the specified object.
     -absent will delete the object if it exists.
     -present will create the configuration if needed.
    required: true
    default: present
    choices: ["absent", "present"]

  device_unique_name:
    description:
     -The unique device's name that you are editing
    required: True
  provisioning_template:
    description:
     -The provisioning template you want to apply (default = default)
    required: True
  provision_targets:
    description:
     -The friendly names of devices in FortiManager to assign the provisioning template to. Comma separated list.
    required: True
  snmp_status:
    description:
     -enables or disables SNMP globally
    required: False
    choices: ["enable", "disable"]
  snmp_v2c_query_port:
    description:
     -sets the snmp v2c community query port
    required: False
  snmp_v2c_trap_port:
    description:
     -sets the snmp v2c community trap port
    required: False
  snmp_v2c_status:
    description:
     -enables or disables the v2c community specified
    required: False
    choices: ["enable", "disable"]
  snmp_v2c_trap_status:
    description:
     -enables or disables the v2c community specified for traps
    required: False
    choices: ["enable", "disable"]
  snmp_v2c_query_status:
    description:
     -enables or disables the v2c community specified for queries
    required: False
    choices: ["enable", "disable"]
  snmp_v2c_name:
    description:
     -specifies the v2c community name
    required: False
  snmp_v2c_id:
    description:
     -primary key for the snmp community. this must be unique!
    required: False
  snmp_v2c_trap_src_ipv4:
    description:
       -source ip the traps should come from IPv4
    required: False
  snmp_v2c_trap_hosts_ipv4:
    description: >
       -ipv4 addresses of the hosts that should get SNMP v2c traps, comma separated, must include mask
       ("10.7.220.59 255.255.255.255, 10.7.220.60 255.255.255.255")
    required: False
  snmp_v2c_query_hosts_ipv4:
    description: >
       -ipv4 addresses or subnets that are allowed to query SNMP v2c, comma separated
       ("10.7.220.59 255.255.255.0, 10.7.220.0 255.255.255.0")
    required: False
  snmpv3_auth_proto:
    description:
        -snmpv3 auth protocol
    required: False
    choices: ["md5", "sha"]
  snmpv3_auth_pwd:
    description:
        -snmpv3 auth pwd __ currently not encrypted! ensure this file is locked down permissions wise!
    required: False
  snmpv3_name:
    description:
      -snmpv3 user name
    required: False
  snmpv3_notify_hosts:
    description:
      -list of ipv4 hosts to send snmpv3 traps to. Comma separated IPv4 list
    required: False
  snmpv3_priv_proto:
    description:
      -snmpv3 priv protocol
    required: False
    choices: ["aes", "des", "aes256", "aes256cisco"]
  snmpv3_priv_pwd:
    description:
     -snmpv3 priv pwd __ currently not encrypted! ensure this file is locked down permissions wise!
    required: False
  snmpv3_queries:
    description:
     -allow snmpv3_queries
    required: False
    choices: ["enable", "disable"]
  snmpv3_query_port:
    description:
     -snmpv3 query port
    required: False
  snmpv3_security_level:
    description:
     -snmpv3 security level
    required: False
    choices: ["no-auth-no-priv", "auth-no-priv", "auth-priv"]
  snmpv3_source_ip:
    description:
     -snmpv3 source ipv4 address for traps
    required: False
  snmpv3_status:
    description:
     -snmpv3 user is enabled or disabled
    required: False
    choices: ["enable", "disable"]
  snmpv3_trap_rport:
    description:
     -snmpv3 trap remote port
    required: False
  snmpv3_trap_status:
    description:
     -snmpv3 traps is enabled or disabled
    required: False
    choices: ["enable", "disable"]
  syslog_port:
    description:
     -syslog port that will be set
    required: False
  syslog_server:
    description:
     -server the syslogs will be sent to
    required: False
  syslog_status:
    description:
     -enables or disables syslogs
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
     -sets the logging level for syslog
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
      -enables or disables ntp
    required: False
    choices: ["enable", "disable"]
  ntp_sync_interval:
    description:
     -sets the interval in minutes for ntp sync
    required: False
  ntp_type:
    description:
     -enables fortiguard servers or custom servers are the ntp source
    required: False
    choices: ["fortiguard", "custom"]
  ntp_server:
    description:
     -only used with custom ntp_type -- specifies IP of server to sync to -- comma separated ip addresses for multiples
    required: False
  ntp_auth:
    description:
     -enables or disables ntp authentication
    required: False
    choices: ["enable", "disable"]
  ntp_auth_pwd:
    description:
     -sets the ntp auth password
    required: False
  ntp_v3:
    description:
     -enables or disables ntpv3 (default is ntpv4)
    required: False
    choices: ["enable", "disable"]
  admin_https_redirect:
    description:
     -enables or disables https redirect from http
    required: False
    choices: ["enable", "disable"]
  admin_https_port:
    description:
     -ssl admin gui port number
    required: False
  admin_http_port:
    description:
     -non-ssl admin gui port number
    required: False
  admin_timeout:
    description:
     -admin timeout in minutes
    required: False
  admin_language:
    description:
     -sets the admin gui language
    required: False
    choices: ["english", "simch", "japanese", "korean", "spanish", "trach", "french", "portuguese"]
  admin_switch_controller:
    description:
     -enables or disables the switch controller
    required: False
    choices: ["enable", "disable"]
  admin_gui_theme:
    description:
     -changes the admin gui theme
    required: False
    choices: ["green", "red", "blue", "melongene", "mariner"]
  admin_enable_fortiguard:
    description:
     -enables fortiguard security updates to their default settings. (custom fortiguard servers not yet supported)
    required: False
    choices: ["none", "direct", "this-fmg"]
  admin_fortianalyzer_target:
    description:
     -configures faz target
    required: False
  admin_fortiguard_target:
    description:
     - configures fortiguard target
     - admin_enable_fortiguard must be set to "direct"
    required: False
  smtp_username:
    description:
     -smtp auth username
    required: False
  smtp_password:
    description:
     -smtp password
    required: False
  smtp_port:
    description:
     -smtp port number
    required: False
  smtp_replyto:
    description:
     -smtp reply to address
    required: False
  smtp_conn_sec:
    description:
     -defines the ssl level for smtp
    required: False
    choices: ["none", "starttls", "smtps"]
  smtp_server:
    description:
     -smtp server ipv4 address
    required: False
  smtp_source_ipv4:
    description:
     -smtp source ip address
    required: False
  smtp_validate_cert:
    description:
     -enables or disables valid certificate checking for smtp
    required: False
    choices: ["enable", "disable"]
  dns_suffix:
    description:
     -sets the local dns domain suffix
    required: False
  dns_primary_ipv4:
    description:
     -primary ipv4 dns forwarder
    required: False
  dns_secondary_ipv4:
    description:
     -secondary ipv4 dns forwarder
    required: False
  delete_provisioning_template:
    description:
     - If specified, all other options are ignored. The specified provisioning template will be deleted.
    required: False

'''

EXAMPLES = '''
- name: SET SNMP SYSTEM INFO
  fmgr_device_provision_template:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "default"
    snmp_status: "enable"
    state: "present"

- name: SET SNMP SYSTEM INFO ANSIBLE ADOM
  fmgr_device_provision_template:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "default"
    snmp_status: "enable"
    state: "present"
    adom: "ansible"

- name: SET SNMP SYSTEM INFO different template (SNMPv2)
  fmgr_device_provision_template:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    snmp_status: "enable"
    state: "present"
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
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    snmp_status: "enable"
    state: "present"
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
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    state: "present"
    adom: "ansible"
    syslog_server: "10.7.220.59"
    syslog_port: "514"
    syslog_mode: "disable"
    syslog_status: "enable"
    syslog_filter: "information"

- name: SET NTP TO FORTIGUARD
  fmgr_device_provision_template:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    state: "present"
    adom: "ansible"
    ntp_status: "enable"
    ntp_sync_interval: "60"
    type: "fortiguard"

- name: SET NTP TO CUSTOM SERVER
  fmgr_device_provision_template:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    state: "present"
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
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    state: "present"
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
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    state: "present"
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
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    state: "present"
    adom: "ansible"
    dns_suffix: "ansible.local"
    dns_primary_ipv4: "8.8.8.8"
    dns_secondary_ipv4: "4.4.4.4"

- name: SET PROVISIONING TEMPLATE DEVICE TARGETS IN FORTIMANAGER
  fmgr_device_provision_template:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    state: "present"
    adom: "ansible"
    provision_targets: "FGT1, FGT2"

- name: DELETE ENTIRE PROVISIONING TEMPLATE
  fmgr_device_provision_template:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    delete_provisioning_template: "ansibleTest"
    state: "absent"
    adom: "ansible"

'''
RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager

    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


def get_devprof(fmg, paramgram):
    """
    GET the DevProf (check to see if exists)
    """
    datagram = {
        # "name": paramgram["provisioning_template"]
    }

    url = "/pm/devprof/adom/{adom}/{name}".format(adom=paramgram["adom"], name=paramgram["provisioning_template"])
    response = fmg.get(url, datagram)

    return response


def del_devprof(fmg, paramgram):
    """
    DELETE the DevProf
    """

    datagram = {
        # "name": paramgram["delete_provisioning_template"]
    }

    url = "/pm/devprof/adom/{adom}/{name}".format(adom=paramgram["adom"],
                                                  name=paramgram["delete_provisioning_template"])
    response = fmg.delete(url, datagram)

    return response


def add_devprof(fmg, paramgram):
    """
    GET the DevProf (check to see if exists)
    """
    datagram = {
        "name": paramgram["provisioning_template"],
        "type": "devprof",
        "description": "CreatedByAnsible",
    }
    url = "/pm/devprof/adom/{adom}".format(adom=paramgram["adom"])
    response = fmg.add(url, datagram)

    return response


def get_devprof_scope(fmg, paramgram):
    """
    GETS a device provisioning template and its scope
    """
    datagram = {
        "name": paramgram["provisioning_template"],
        "type": "devprof",
        "description": "CreatedByAnsible",
    }

    url = "/pm/devprof/adom/{adom}".format(adom=paramgram["adom"])
    response = fmg.get(url, datagram)

    return response


def set_devprof_scope(fmg, paramgram):
    """
    SETS a device provisioning template and its scope
    """
    datagram = {
        "name": paramgram["provisioning_template"],
        "type": "devprof",
        "description": "CreatedByAnsible",
    }

    targets = []
    for target in paramgram["provision_targets"].strip().split(","):
        # split the host on the space to get the mask out
        new_target = {"name": target}
        targets.append(new_target)

    datagram["scope member"] = targets

    url = "/pm/devprof/adom/{adom}".format(adom=paramgram["adom"])
    response = fmg.set(url, datagram)

    return response


def delete_devprof_scope(fmg, paramgram):
    """
    DELETES the Current Scope for ProvTemplate
    """
    datagram = {
        "name": paramgram["provisioning_template"],
        "type": "devprof",
        "description": "CreatedByAnsible",
        "scope member": paramgram["targets_to_add"]
    }

    url = "/pm/devprof/adom/{adom}".format(adom=paramgram["adom"])
    response = fmg.set(url, datagram)

    return response


def set_devprof_snmp(fmg, paramgram):
    """
    ENABLE SNMP ON DevProf
    """
    datagram = {
        "status": paramgram["snmp_status"]
    }

    url = "/pm/config/adom/{adom}/devprof/" \
          "{provisioning_template}/system/snmp/sysinfo".format(adom=paramgram["adom"],
                                                               provisioning_template=paramgram["provisioning_template"])
    response = fmg.set(url, datagram)

    return response


def delete_devprof_snmp(fmg, paramgram):
    """
    DISABLE SNMP on Provision Template
    """
    datagram = {
        "status": paramgram["snmp_status"]
    }

    url = "/pm/config/adom/{adom}/devprof/" \
          "{provisioning_template}/system/snmp/sysinfo".format(adom=paramgram["adom"],
                                                               provisioning_template=paramgram["provisioning_template"])

    response = fmg.delete(url, datagram)

    return response


def set_devprof_snmp_v2c(fmg, paramgram):
    """
    ENABLE SNMP ON DevProf
    """
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
          "{provisioning_template}/system/snmp/community".format(adom=paramgram["adom"],
                                                                 provisioning_template=paramgram[
                                                                     "provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_snmp_v2c(fmg, paramgram):
    """
    DISABLE SNMP on Provision Template
    """
    datagram = {
        "confirm": 1
    }

    url = "/pm/config/adom/{adom}/" \
          "devprof/{provisioning_template}/" \
          "system/snmp/community/{snmp_v2c_id}".format(adom=paramgram["adom"],
                                                       provisioning_template=paramgram["provisioning_template"],
                                                       snmp_v2c_id=paramgram["snmp_v2c_id"])

    response = fmg.delete(url, datagram)

    return response


def set_devprof_snmp_v3(fmg, paramgram):
    """
    ENABLE SNMP ON DevProf
    """
    datagram = dict()
    # transform options
    if paramgram["snmpv3_trap_status"] == "enable":
        datagram["trap-status"] = 1
    if paramgram["snmpv3_trap_status"] == "disable":
        datagram["trap-status"] = 0
    if paramgram["snmpv3_queries"] == "enable":
        datagram["queries"] = 1
    if paramgram["snmpv3_queries"] == "disable":
        datagram["queries"] = 0
    if paramgram["snmpv3_status"] == "enable":
        datagram["status"] = 1
    if paramgram["snmpv3_status"] == "disable":
        datagram["status"] = 0
    if paramgram["snmpv3_auth_proto"] == "md5":
        datagram["auth-proto"] = 1
    if paramgram["snmpv3_auth_proto"] == "sha":
        datagram["auth-proto"] = 2
    if paramgram["snmpv3_priv_proto"] == "aes":
        datagram["auth-proto"] = 1
    if paramgram["snmpv3_priv_proto"] == "des":
        datagram["priv-proto"] = 2
    if paramgram["snmpv3_priv_proto"] == "aes256":
        datagram["priv-proto"] = 3
    if paramgram["snmpv3_priv_proto"] == "aes256cisco":
        datagram["priv-proto"] = 4
    if paramgram["snmpv3_security_level"] == "no-auth-no-priv":
        datagram["security-level"] = 1
    if paramgram["snmpv3_security_level"] == "auth-no-priv":
        datagram["security-level"] = 2
    if paramgram["snmpv3_security_level"] == "auth-priv":
        datagram["security-level"] = 3

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
          "system/snmp/user".format(adom=paramgram["adom"],
                                    provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_snmp_v3(fmg, paramgram):
    """
    DISABLE SNMP on Provision Template
    """
    datagram = {
        "confirm": 1
    }

    url = "/pm/config/adom/{adom}/devprof/" \
          "{provisioning_template}/system/snmp" \
          "/user/{snmpv3_name}".format(adom=paramgram["adom"],
                                       provisioning_template=paramgram["provisioning_template"],
                                       snmpv3_name=paramgram["snmpv3_name"])

    response = fmg.delete(url, datagram)

    return response


def set_devprof_syslog(fmg, paramgram):
    """
    Set the SYSLOG SETTINGS
    """
    datagram = {
        "status": paramgram["syslog_status"],
        "port": paramgram["syslog_port"],
        "server": paramgram["syslog_server"],
        "mode": paramgram["syslog_mode"],
        "facility": paramgram["syslog_facility"]
    }

    if paramgram["syslog_enc_algorithm"] in ["high", "low", "high-medium"] \
            and paramgram["syslog_certificate"] is not None:
        datagram["certificate"] = paramgram["certificate"]
        datagram["enc-algorithm"] = paramgram["syslog_enc_algorithm"]

    url = "/pm/config/adom/{adom}/" \
          "devprof/{provisioning_template}/" \
          "log/syslogd/setting".format(adom=paramgram["adom"],
                                       provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_syslog(fmg, paramgram):
    """
    DISABLE SYSLOG SETTINGS
    """
    datagram = {
        "status": paramgram["syslog_status"],
        "port": paramgram["syslog_port"],
        "server": paramgram["syslog_server"],
        "mode": paramgram["syslog_mode"],
        "facility": paramgram["syslog_facility"]
    }
    url = "/pm/config/adom/{adom}/" \
          "devprof/{provisioning_template}/" \
          "log/syslogd/setting".format(adom=paramgram["adom"],
                                       provisioning_template=paramgram["provisioning_template"])

    response = fmg.delete(url, datagram)

    return response


def set_devprof_syslog_filter(fmg, paramgram):
    """
    Set the SYSLOG SETTINGS
    """
    datagram = {
        "severity": paramgram["syslog_filter"]
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/log/syslogd/filter".format(adom=paramgram["adom"],
                                       provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_syslog_filter(fmg, paramgram):
    """
    DISABLE SYSLOG SETTINGS
    """
    datagram = {
        "severity": paramgram["syslog_filter"]
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/log/syslogd/filter".format(adom=paramgram["adom"],
                                       provisioning_template=paramgram["provisioning_template"])
    response = fmg.delete(url, datagram)

    return response


def set_devprof_ntp(fmg, paramgram):
    """
    Set the NTP SETTINGS
    """
    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    # IF SET TO FORTIGUARD, BUILD A STRING SPECIFIC TO THAT
    if paramgram["ntp_type"] == "fortiguard":
        datagram = dict()
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
        datagram = dict()
        if paramgram["ntp_status"] == "enable":
            datagram["ntpsync"] = 1
        if paramgram["ntp_status"] == "disable":
            datagram["ntpsync"] = 0
        try:
            datagram["syncinterval"] = paramgram["ntp_sync_interval"]
        except:
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

    # SET THE BODY FOR THE FORTIGUARD REQUEST
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/ntp".format(adom=paramgram["adom"],
                               provisioning_template=paramgram["provisioning_template"])
    response = fmg.set(url, datagram)
    return response


def delete_devprof_ntp(fmg, paramgram):
    """
    DISABLE NTP SETTINGS
    """
    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    # IF SET TO FORTIGUARD, BUILD A STRING SPECIFIC TO THAT
    if paramgram["ntp_type"] == "fortiguard":
        datagram = dict()
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
        datagram = dict()
        if paramgram["ntp_status"] == "enable":
            datagram["ntpsync"] = 1
        if paramgram["ntp_status"] == "disable":
            datagram["ntpsync"] = 0
        if paramgram["ntp_sync_interval"] is None:
            datagram["syncinterval"] = 1
        else:
            datagram["syncinterval"] = paramgram["ntp_sync_interval"]
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
                server_fields["ntpv3"] = 1
            else:
                server_fields["ntpv3"] = 0

            # split the host on the space to get the mask out
            new_ntp_server = {"authentication": server_fields["authentication"], "id": id_counter,
                              "key": server_fields["key"], "key-id": id_counter, "ntpv3": server_fields["ntpv3"],
                              "server": server}
            ntpservers.append(new_ntp_server)

        datagram["ntpserver"] = ntpservers

    # SET THE BODY FOR THE FORTIGUARD REQUEST
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/ntp".format(adom=paramgram["adom"],
                               provisioning_template=paramgram["provisioning_template"])
    response = fmg.delete(url, datagram)
    return response


def set_devprof_admin(fmg, paramgram):
    """
        DISABLE NTP SETTINGS
    """
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
          "/system/global".format(adom=paramgram["adom"],
                                  provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_admin(fmg, paramgram):
    """
        CHANGE ADMIN SETTINGS
    """
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
          "/system/global".format(adom=paramgram["adom"],
                                  provisioning_template=paramgram["provisioning_template"])

    response = fmg.delete(url, datagram)

    return response


def set_devprof_smtp(fmg, paramgram):
    """
       ENABLE SMTP SETTINGS
    """
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
          "/system/email-server".format(adom=paramgram["adom"],
                                        provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_smtp(fmg, paramgram):
    """
        DISABLE SMTP SETTINGS
    """
    datagram = {
        "port": paramgram["smtp_port"],
        "reply-to": paramgram["smtp_replyto"],
        "server": paramgram["smtp_server"],
        "source-ip": paramgram["smtp_source_ipv4"],
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
          "/system/email-server".format(adom=paramgram["adom"],
                                        provisioning_template=paramgram["provisioning_template"])

    response = fmg.delete(url, datagram)

    return response


def set_devprof_dns(fmg, paramgram):
    """
       ENABLE DNS SETTINGS
    """
    datagram = {
        "domain": paramgram["dns_suffix"],
        "primary": paramgram["dns_primary_ipv4"],
        "secondary": paramgram["dns_secondary_ipv4"],
    }
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/dns".format(adom=paramgram["adom"],
                               provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_dns(fmg, paramgram):
    """
        DISABLE DNS SETTINGS
    """
    datagram = {
        "domain": paramgram["dns_suffix"],
        "primary": paramgram["dns_primary_ipv4"],
        "secondary": paramgram["dns_secondary_ipv4"],
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/dns".format(adom=paramgram["adom"],
                               provisioning_template=paramgram["provisioning_template"])

    response = fmg.delete(url, datagram)

    return response


def set_devprof_toggle_fg(fmg, paramgram):
    """
       TOGGLE FG SETTINGS
    """
    # pydevd.settrace('10.0.0.122', port=54654, stdoutToServer=True, stderrToServer=True)
    datagram = dict()
    if paramgram["admin_enable_fortiguard"] in ["direct", "this-fmg"]:
        datagram["include-default-servers"] = "enable"
    elif paramgram["admin_enable_fortiguard"] == "none":
        datagram["include-default-servers"] = "disable"

    datagram["server-list"] = list()

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/central-management".format(adom=paramgram["adom"],
                                              provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def set_devprof_fg(fmg, paramgram):
    """
       ENABLE FG SETTINGS
    """
    # pydevd.settrace('10.0.0.122', port=54654, stdoutToServer=True, stderrToServer=True)
    datagram = {
        "target": paramgram["admin_enable_fortiguard"],
        "target-ip": None
    }
    if paramgram["admin_fortiguard_target"] is not None and datagram["target"] == "direct":
        datagram["target-ip"] = paramgram["admin_fortiguard_target"]

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortiguard".format(adom=paramgram["adom"],
                                              provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_fg(fmg, paramgram):
    """
        DISABLE FG SETTINGS
    """
    datagram = {
        "target": paramgram["admin_enable_fortiguard"],
        "target-ip": None
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortiguard".format(adom=paramgram["adom"],
                                              provisioning_template=paramgram["provisioning_template"])

    response = fmg.delete(url, datagram)

    return response


def set_devprof_faz(fmg, paramgram):
    """
       ENABLE FAZ SETTINGS
    """
    datagram = {
        "target-ip": paramgram["admin_fortianalyzer_target"],
        "target": 4,
    }
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortianalyzer".format(adom=paramgram["adom"],
                                                 provisioning_template=paramgram["provisioning_template"])

    response = fmg.set(url, datagram)

    return response


def delete_devprof_faz(fmg, paramgram):
    """
        DISABLE FAZ SETTINGS
    """
    datagram = {
        "target-ip": paramgram["admin_fortianalyzer_target"],
        "target": 4,
        "hastarget": "true",
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortianalyzer".format(adom=paramgram["adom"],
                                                 provisioning_template=paramgram["provisioning_template"])

    response = fmg.delete(url, datagram)

    return response


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


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
        host=dict(required=True, type="str"),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        state=dict(required=False, type="str", default="present", choices=["absent", "present"]),

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

    module = AnsibleModule(argument_spec, supports_check_mode=True, )

    paramgram = {
        "adom": module.params["adom"],
        "state": module.params["state"],
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

    # validate required arguments are passed; not used in argument_spec to allow params to be called from provider
    # check if params are set
    results = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    if module.params["host"] is None or module.params["username"] is None or module.params["password"] is None:
        module.fail_json(msg="Host and username are required for connection")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    # START SESSION LOGIC
    # CHECK IF WE ARE DELETING AN ENTIRE TEMPLATE. IF THAT'S THE CASE DO IT FIRST AND IGNORE THE REST.
    if paramgram["delete_provisioning_template"] is not None:
        results = del_devprof(fmg, paramgram)
        fmgr_logout(fmg, module, results=results, good_codes=[0, -10, -1],
                    msg="Failed to delete provisioning template", logout_on_success=True)

    # CHECK TO SEE IF THE DEVPROF TEMPLATE EXISTS
    devprof = get_devprof(fmg, paramgram)
    if not devprof[0] == 0:
        results = add_devprof(fmg, paramgram)
        fmgr_logout(fmg, module, results=results, good_codes=[0, -2])

    # PROCESS THE SNMP SETTINGS IF THE SNMP_STATUS VARIABLE IS SET
    if paramgram["snmp_status"] is not None:
        if paramgram["state"] == "present":
            # enable SNMP in the devprof template
            results = set_devprof_snmp(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0])
        elif paramgram["state"] == "absent":
            # disable SNMP in the devprof template
            results = delete_devprof_snmp(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10000],
                        msg="Failed to delete SNMP status")

    # PROCESS THE SNMP V2C COMMUNITY SETTINGS IF THEY ARE ALL HERE
    if all(v is not None for v in (paramgram["snmp_v2c_query_port"], paramgram["snmp_v2c_trap_port"],
                                   paramgram["snmp_v2c_status"], paramgram["snmp_v2c_trap_status"],
                                   paramgram["snmp_v2c_query_status"], paramgram["snmp_v2c_name"],
                                   paramgram["snmp_v2c_id"])):
        if paramgram["state"] == "present":
            results = set_devprof_snmp_v2c(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033],
                        msg="Failed to create SNMP V2C Community")

        if paramgram["state"] == "absent":
            results = delete_devprof_snmp_v2c(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete SNMP V2C Community")

    # PROCESS THE SNMPV3 USER IF THERE
    if all(v is not None for v in (
            [paramgram["snmpv3_auth_proto"], paramgram["snmpv3_auth_pwd"], paramgram["snmpv3_name"],
             paramgram["snmpv3_notify_hosts"], paramgram["snmpv3_priv_proto"],
             paramgram["snmpv3_priv_pwd"],
             paramgram["snmpv3_queries"],
             paramgram["snmpv3_query_port"], paramgram["snmpv3_security_level"],
             paramgram["snmpv3_source_ip"],
             paramgram["snmpv3_status"], paramgram["snmpv3_trap_rport"], paramgram["snmpv3_trap_status"]])):
        if paramgram["state"] == "present":
            results = set_devprof_snmp_v3(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to create SNMP V3 Community")

        if paramgram["state"] == "absent":
            results = delete_devprof_snmp_v3(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to create SNMP V3 Community")

    # PROCESS THE SYSLOG SETTINGS IF THE ALL THE NEEDED SYSLOG VARIABLES ARE PRESENT
    if all(v is not None for v in [paramgram["syslog_port"], paramgram["syslog_mode"],
                                   paramgram["syslog_server"], paramgram["syslog_status"]]):
        if paramgram["state"] == "present":
            # enable syslog in the devprof template
            results = set_devprof_syslog(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to set Syslog server")
        elif paramgram["state"] == "absent":
            # disable syslog in the devprof template
            results = delete_devprof_syslog(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete syslog server settings")

    # IF THE SYSLOG FILTER IS PRESENT THEN RUN THAT
    if paramgram["syslog_filter"] is not None:
        if paramgram["state"] == "present":
            # set the syslog filter level
            results = set_devprof_syslog_filter(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0],
                        msg="Failed to set syslog settings")
        elif paramgram["state"] == "absent":
            # remove the syslog filter level
            results = delete_devprof_syslog_filter(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete syslog settings")

    # PROCESS NTP OPTIONS
    if paramgram["ntp_status"]:
        # VALIDATE INPUT
        if paramgram["ntp_type"] == "custom" and paramgram["ntp_server"] is None:
            module.exit_json(msg="You requested custom NTP type but did not provide ntp_server parameter.")
        if paramgram["ntp_auth"] == "enable" and paramgram["ntp_auth_pwd"] is None:
            module.exit_json(
                msg="You requested NTP Authentication but did not provide ntp_auth_pwd parameter.")
        if paramgram["state"] == "present":
            results = set_devprof_ntp(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to set NTP settings")
        elif paramgram["state"] == "absent":
            results = delete_devprof_ntp(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete NTP settings")

    # PROCESS THE ADMIN OPTIONS
    if any(v is not None for v in (
            paramgram["admin_https_redirect"], paramgram["admin_https_port"], paramgram["admin_http_port"],
            paramgram["admin_timeout"],
            paramgram["admin_language"], paramgram["admin_switch_controller"],
            paramgram["admin_gui_theme"])):
        if paramgram["state"] == "present":
            results = set_devprof_admin(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to set NTP settings")
        if paramgram["state"] == "absent":
            results = delete_devprof_admin(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete NTP settings")

    # PROCESS FORTIGUARD OPTIONS
    if paramgram["admin_enable_fortiguard"] is not None:
        if paramgram["state"] == "present":
            results = set_devprof_toggle_fg(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to toggle Fortiguard on/off")
            results = set_devprof_fg(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to set Fortiguard settings")
        if paramgram["state"] == "absent" or str.lower(paramgram["admin_enable_fortiguard"]) == "none":
            results = delete_devprof_fg(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete Fortiguard settings")
            results = set_devprof_toggle_fg(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to toggle Fortiguard on/off")

    # PROCESS THE SMTP OPTIONS
    if all(v is not None for v in (
            paramgram["smtp_username"], paramgram["smtp_password"], paramgram["smtp_port"],
            paramgram["smtp_replyto"],
            paramgram["smtp_conn_sec"], paramgram["smtp_server"],
            paramgram["smtp_source_ipv4"], paramgram["smtp_validate_cert"])):
        if paramgram["state"] == "present":
            results = set_devprof_smtp(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to set SMTP settings")

        if paramgram["state"] == "absent":
            results = delete_devprof_smtp(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete SMTP settings")

    # PROCESS THE DNS OPTIONS
    if any(v is not None for v in
           (paramgram["dns_suffix"], paramgram["dns_primary_ipv4"], paramgram["dns_secondary_ipv4"])):
        if paramgram["state"] == "present":
            results = set_devprof_dns(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to set DNS settings")

        if paramgram["state"] == "absent":
            results = delete_devprof_dns(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete DNS settings")

    # PROCESS THE admin_fortianalyzer_target OPTIONS
    if paramgram["admin_fortianalyzer_target"] is not None:
        if paramgram["state"] == "present":
            results = set_devprof_faz(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to set FAZ settings")

        if paramgram["state"] == "absent":
            results = delete_devprof_faz(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete FAZ settings")

    # PROCESS THE PROVISIONING TEMPLATE TARGET PARAMETER
    if paramgram["provision_targets"] is not None:
        if paramgram["state"] == "present":
            results = set_devprof_scope(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0], msg="Failed to set provision targets")

        if paramgram["state"] == "absent":
            # WE NEED TO FIGURE OUT WHAT'S THERE FIRST, BEFORE WE CAN RUN THIS
            targets_to_add = list()
            try:
                current_scope = get_devprof_scope(fmg, paramgram)
                targets_to_remove = paramgram["provision_targets"].strip().split(",")
                targets = current_scope[1][1]["scope member"]
                for target in targets:
                    if target["name"] not in targets_to_remove:
                        target_append = {"name": target["name"]}
                        targets_to_add.append(target_append)
            except:
                pass
            paramgram["targets_to_add"] = targets_to_add
            results = delete_devprof_scope(fmg, paramgram)
            fmgr_logout(fmg, module, results=results, good_codes=[0, -10033, -10000, -3],
                        msg="Failed to delete provision targets")

    fmg.logout()
    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
