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
version_added: "2.6"
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
  snmp_v2c_trap_src_ipv6:
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
  snmp_v2c_query_hosts_ipv6:
    description: >
       -ipv6 addresses or subnets that are allowed to query SNMP v2c,
        comma separated ("2001:db8:85a3:0:0:8a2e:370:7334")
    required: False
  snmp_v2c_trap_hosts_ipv6:
    description:
       -ipv6 addresses that will receieve snmp v2c traps, comma separated ("2001:db8:85a3:0:0:8a2e:370:7334")
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
  snmpv3_notify_hosts6:
    description:
      -list of ipv6 hosts to send snmpv3 traps to. Comma separated IPv6 list
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
  snmpv3_source_ipv6:
    description:
     -snmpv3 source ipv6 address for traps
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
  syslog_tcp:
    description:
     -enables or disables "reliable" syslog (TCP)
    required: False
    choices: ["enable", "disable"]
  syslog_filter:
    description:
     -sets the logging level for syslog
    required: False
    choices: ["emergency", "alert", "critical", "error", "warning", "notification", "information", "debug"]
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
    choices: ["enable","disable"]
  admin_fortianalyzer_target:
    description:
     -configures faz target
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
  dns_primary_ipv6:
    description:
      -primary ipv6 dns forwarder
    required: False
  dns_secondary_ipv6:
    description:
      -secondary ipv6 dns forwarder
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
    snmp_v2c_trap_hosts_ipv6: "2001:db8:85a3:0:0:8a2e:370:7334"
    snmp_v2c_query_hosts_ipv6: "2001:db8:85a3:0:0:8a2e:370:7334"

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
    snmpv3_notify_hosts6: "::"
    snmpv3_priv_proto: "aes256"
    snmpv3_priv_pwd: "fortinet"
    snmpv3_queries: "enable"
    snmpv3_query_port: "161"
    snmpv3_security_level: "auth_priv"
    snmpv3_source_ip: "0.0.0.0"
    snmpv3_source_ipv6: "::"
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
    syslog_tcp: "disable"
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
    admin_enable_fortiguard: "enable"
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
    dns_primary_ipv6: "::"
    dns_secondary_ipv6: "::"

- name: SET PROVISIONING TEMPLATE DEVICE TARGETS IN FORTIMANAGER
  fmgr_device_provision_template:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    provisioning_template: "ansibleTest"
    state: "present"
    adom: "ansible"
    provision_targets: "FGT1, FGT2"

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


def get_devprof(fmg, provisioning_template, adom):
    """
    GET the DevProf (check to see if exists)
    """
    datagram = {
        "name": provisioning_template
    }

    url = "/pm/devprof/adom/{adom}/devprof/{name}".format(adom=adom, name=provisioning_template)
    response = fmg.get(url, datagram)
    return response


def add_devprof(fmg, provisioning_template, adom):
    """
    GET the DevProf (check to see if exists)
    """
    datagram = {
        "name": provisioning_template,
        "type": "devprof",
        "description": "CreatedByAnsible",
    }
    url = "/pm/devprof/adom/{adom}".format(adom=adom)
    response = fmg.add(url, datagram)
    return response


def get_devprof_scope(fmg, provisioning_template, adom):
    """
    GETS a device provisioning template and its scope
    """
    datagram = {
        "name": provisioning_template,
        "type": "devprof",
        "description": "CreatedByAnsible",
    }

    url = "/pm/devprof/adom/{adom}".format(adom=adom)
    response = fmg.get(url, datagram)
    return response


def set_devprof_scope(fmg, provisioning_template, adom, provision_targets):
    """
    SETS a device provisioning template and its scope
    """
    datagram = {
        "name": provisioning_template,
        "type": "devprof",
        "description": "CreatedByAnsible",
    }

    targets = []
    for target in provision_targets.strip().split(","):
        # split the host on the space to get the mask out
        new_target = {"name": target}
        targets.append(new_target)

    datagram["scope member"] = targets

    url = "/pm/devprof/adom/{adom}".format(adom=adom)
    response = fmg.set(url, datagram)
    return response


def delete_devprof_scope(fmg, provisioning_template, adom, provision_targets):
    """
    DELETES the Current Scope for ProvTemplate
    """
    datagram = {
        "name": provisioning_template,
        "type": "devprof",
        "description": "CreatedByAnsible"
    }

    targets = []
    # if len(provision_targets) > 1:
    for target in provision_targets.strip().split(","):
        # split the host on the space to get the mask out
        new_target = {"name": target}
        targets.append(new_target)
    #
    # if len(provision_targets) == 1:
    #     new_target = {"name": str(provision_targets)}
    #     targets.append(new_target)

    datagram["scope member"] = targets

    url = "/pm/devprof/adom/{adom}".format(adom=adom)
    response = fmg.set(url, datagram)
    return response


def set_devprof_snmp(fmg, provisioning_template, snmp_status, adom):
    """
    ENABLE SNMP ON DevProf
    """
    datagram = {
        "status": snmp_status
    }

    url = "/pm/config/adom/{adom}/devprof/" \
          "{provisioning_template}/system/snmp/sysinfo".format(adom=adom,
                                                               provisioning_template=provisioning_template)
    response = fmg.set(url, datagram)
    return response


def delete_devprof_snmp(fmg, provisioning_template, snmp_status, adom):
    """
    DISABLE SNMP on Provision Template
    """
    datagram = {
        "status": snmp_status
    }

    url = "/pm/config/adom/{adom}/devprof/" \
          "{provisioning_template}/system/snmp/sysinfo".format(adom=adom,
                                                               provisioning_template=provisioning_template)

    response = fmg.delete(url, datagram)
    return response


def set_devprof_snmp_v2c(fmg, provisioning_template, adom, snmp_v2c_query_port, snmp_v2c_trap_port,
                         snmp_v2c_status, snmp_v2c_trap_status, snmp_v2c_query_status, snmp_v2c_name,
                         snmp_v2c_id, snmp_v2c_trap_src_ipv4, snmp_v2c_trap_src_ipv6, snmp_v2c_query_hosts_ipv4,
                         snmp_v2c_query_hosts_ipv6, snmp_v2c_trap_hosts_ipv4, snmp_v2c_trap_hosts_ipv6):
    """
    ENABLE SNMP ON DevProf
    """
    # transform options
    if snmp_v2c_trap_status == "enable":
        snmp_v2c_trap_status = 1
    if snmp_v2c_trap_status == "disable":
        snmp_v2c_trap_status = 0
    if snmp_v2c_query_status == "enable":
        snmp_v2c_query_status = 1
    if snmp_v2c_query_status == "disable":
        snmp_v2c_query_status = 0
    if snmp_v2c_status == "enable":
        snmp_v2c_status = 1
    if snmp_v2c_status == "disable":
        snmp_v2c_status = 0

    datagram = {
        "query-v2c-port": snmp_v2c_query_port,
        "trap-v2c-rport": snmp_v2c_trap_port,
        "status": snmp_v2c_status,
        "trap-v2c-status": snmp_v2c_trap_status,
        "query-v2c-status": snmp_v2c_query_status,
        "name": snmp_v2c_name,
        "id": snmp_v2c_id,
        "meta fields": {},
        "hosts": None,
        "hosts6": None,
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
    if snmp_v2c_trap_hosts_ipv4 or snmp_v2c_query_hosts_ipv4:
        hosts = []
        if snmp_v2c_query_hosts_ipv4:
            for ipv4_host in snmp_v2c_query_hosts_ipv4.strip().split(","):
                # split the host on the space to get the mask out
                new_ipv4_host = {"ha-direct": 1, "host-type": 1, "id": id_counter, "ip": ipv4_host.strip().split(),
                                 "meta fields": {}, "source-ip": "0.0.0.0"}
                hosts.append(new_ipv4_host)
                id_counter += 1

        if snmp_v2c_trap_hosts_ipv4:
            for ipv4_host in snmp_v2c_trap_hosts_ipv4.strip().split(","):
                # split the host on the space to get the mask out
                new_ipv4_host = {"ha-direct": 1, "host-type": 2, "id": id_counter, "ip": ipv4_host.strip().split(),
                                 "meta fields": {}, "source-ip": snmp_v2c_trap_src_ipv4}
                hosts.append(new_ipv4_host)
                id_counter += 1
        datagram["hosts"] = hosts

    id_counter = 1

    if snmp_v2c_trap_hosts_ipv6 or snmp_v2c_query_hosts_ipv6:
        hosts6 = []
        if snmp_v2c_query_hosts_ipv6:
            for ipv6_host in snmp_v2c_query_hosts_ipv6.strip().split(","):
                # split the host on the space to get the mask out
                new_ipv6_host = {"ha-direct": 1, "host-type": 1, "id": id_counter, "ipv6": ipv6_host,
                                 "meta fields": {}, "source-ipv6": ""}
                hosts6.append(new_ipv6_host)
                id_counter += 1

        if snmp_v2c_trap_hosts_ipv6:
            for ipv6_host in snmp_v2c_trap_hosts_ipv6.strip().split(","):
                # split the host on the space to get the mask out
                new_ipv6_host = {"ha-direct": 1, "host-type": 2, "id": id_counter, "ipv6": ipv6_host,
                                 "meta fields": {}, "source-ipv6": snmp_v2c_trap_src_ipv6}
                hosts6.append(new_ipv6_host)
                id_counter += 1
        datagram["hosts6"] = hosts6

    url = "/pm/config/adom/{adom}/devprof/" \
          "{provisioning_template}/system/snmp/community".format(adom=adom,
                                                                 provisioning_template=provisioning_template)

    response = fmg.set(url, datagram)
    return response


def delete_devprof_snmp_v2c(fmg, provisioning_template, adom, snmp_v2c_id):
    """
    DISABLE SNMP on Provision Template
    """
    datagram = {
        "confirm": 1
    }

    url = "/pm/config/adom/{adom}/" \
          "devprof/{provisioning_template}/" \
          "system/snmp/community/{snmp_v2c_id}".format(adom=adom,
                                                       provisioning_template=provisioning_template,
                                                       snmp_v2c_id=snmp_v2c_id)

    response = fmg.delete(url, datagram)
    return response


def set_devprof_snmp_v3(fmg, provisioning_template, adom, snmpv3_auth_proto, snmpv3_auth_pwd, snmpv3_name,
                        snmpv3_notify_hosts, snmpv3_notify_hosts6, snmpv3_priv_proto, snmpv3_priv_pwd,
                        snmpv3_queries, snmpv3_query_port, snmpv3_security_level, snmpv3_source_ip,
                        snmpv3_source_ipv6, snmpv3_status, snmpv3_trap_rport, snmpv3_trap_status):
    """
    ENABLE SNMP ON DevProf
    """
    datagram = dict()
    # transform options
    if snmpv3_trap_status == "enable":
        datagram["trap-status"] = 1
    if snmpv3_trap_status == "disable":
        datagram["trap-status"] = 0
    if snmpv3_queries == "enable":
        datagram["queries"] = 1
    if snmpv3_queries == "disable":
        datagram["queries"] = 0
    if snmpv3_status == "enable":
        datagram["status"] = 1
    if snmpv3_status == "disable":
        datagram["status"] = 0
    if snmpv3_auth_proto == "md5":
        datagram["auth-proto"] = 1
    if snmpv3_auth_proto == "sha":
        datagram["auth-proto"] = 2
    if snmpv3_priv_proto == "aes":
        datagram["auth-proto"] = 1
    if snmpv3_priv_proto == "des":
        datagram["priv-proto"] = 2
    if snmpv3_priv_proto == "aes256":
        datagram["priv-proto"] = 3
    if snmpv3_priv_proto == "aes256cisco":
        datagram["priv-proto"] = 4
    if snmpv3_security_level == "no-auth-no-priv":
        datagram["security-level"] = 1
    if snmpv3_security_level == "auth-no-priv":
        datagram["security-level"] = 2
    if snmpv3_security_level == "auth-priv":
        datagram["security-level"] = 3

    datagram["auth-pwd"] = snmpv3_auth_pwd
    datagram["priv-pwd"] = snmpv3_priv_pwd
    datagram["trap-rport"] = snmpv3_trap_rport
    datagram["query-port"] = snmpv3_query_port
    datagram["name"] = snmpv3_name
    datagram["notify-hosts"] = snmpv3_notify_hosts.strip().split(",")
    datagram["notify-hosts6"] = snmpv3_notify_hosts6.strip().split(",")
    datagram["events"] = 1647387997183
    datagram["trap-lport"] = 162

    datagram["source-ip"] = snmpv3_source_ip
    datagram["source-ipv6"] = snmpv3_source_ipv6
    datagram["ha-direct"] = 0

    url = "/pm/config/adom/{adom}/" \
          "devprof/{provisioning_template}/" \
          "system/snmp/user".format(adom=adom,
                                    provisioning_template=provisioning_template)

    response = fmg.set(url, datagram)
    return response


def delete_devprof_snmp_v3(fmg, provisioning_template, adom, snmpv3_name):
    """
    DISABLE SNMP on Provision Template
    """
    datagram = {
        "confirm": 1
    }

    url = "/pm/config/adom/{adom}/devprof/" \
          "{provisioning_template}/system/snmp" \
          "/user/{snmpv3_name}".format(adom=adom,
                                       provisioning_template=provisioning_template,
                                       snmpv3_name=snmpv3_name)

    response = fmg.delete(url, datagram)
    return response


def set_devprof_syslog(fmg, provisioning_template, syslog_status, syslog_port, syslog_tcp, syslog_server, adom):
    """
    Set the SYSLOG SETTINGS
    """
    datagram = {
        "status": syslog_status,
        "port": syslog_port,
        "server": syslog_server,
        "reliable": syslog_tcp,
    }
    url = "/pm/config/adom/{adom}/" \
          "devprof/{provisioning_template}/" \
          "log/syslogd/setting".format(adom=adom,
                                       provisioning_template=provisioning_template)

    response = fmg.set(url, datagram)
    return response


def delete_devprof_syslog(fmg, provisioning_template, syslog_status, syslog_port, syslog_tcp,
                          syslog_server, adom):
    """
    DISABLE SYSLOG SETTINGS
    """
    datagram = {
        "status": syslog_status,
        "port": syslog_port,
        "server": syslog_server,
        "reliable": syslog_tcp,
    }
    url = "/pm/config/adom/{adom}/" \
          "devprof/{provisioning_template}/" \
          "log/syslogd/setting".format(adom=adom,
                                       provisioning_template=provisioning_template)

    response = fmg.delete(url, datagram)
    return response


def set_devprof_syslog_filter(fmg, provisioning_template, syslog_filter, adom):
    """
    Set the SYSLOG SETTINGS
    """
    datagram = {
        "severity": syslog_filter
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/log/syslogd/filter".format(adom=adom,
                                       provisioning_template=provisioning_template)

    response = fmg.set(url, datagram)
    return response


def delete_devprof_syslog_filter(fmg, provisioning_template, syslog_filter, adom):
    """
    DISABLE SYSLOG SETTINGS
    """
    datagram = {
        "severity": syslog_filter
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/log/syslogd/filter".format(adom=adom,
                                       provisioning_template=provisioning_template)

    response = fmg.delete(url, datagram)
    return response


def set_devprof_ntp(fmg, provisioning_template, adom, ntp_status, ntp_sync_interval, ntp_type, ntp_server,
                    ntp_auth, ntp_auth_pwd, ntp_v3):
    """
    Set the NTP SETTINGS
    """
    # IF SET TO FORTIGUARD, BUILD A STRING SPECIFIC TO THAT
    if ntp_type == "fortiguard":
        datagram = dict()
        if ntp_status == "enable":
            datagram["ntpsync"] = 1
        if ntp_status == "disable":
            datagram["ntpsync"] = 0
        if ntp_sync_interval is None:
            datagram["syncinterval"] = 1
        else:
            datagram["syncinterval"] = ntp_sync_interval

        datagram["type"] = 0

        # SET THE BODY FOR THE FORTIGUARD REQUEST
        url = "/pm/config/adom/{adom}" \
              "/devprof/{provisioning_template}" \
              "/system/ntp".format(adom=adom,
                                   provisioning_template=provisioning_template)

        # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
        response = fmg.set(url, datagram)
        return response

    # IF THE NTP TYPE IS CUSTOM BUILD THE SERVER LIST
    if ntp_type == "custom":
        id_counter = 0
        key_counter = 0
        ntpservers = []
        datagram = dict()
        if ntp_status == "enable":
            datagram["ntpsync"] = 1
        if ntp_status == "disable":
            datagram["ntpsync"] = 0
        if ntp_sync_interval is None:
            datagram["syncinterval"] = 1
        else:
            datagram["syncinterval"] = ntp_sync_interval
            datagram["type"] = 1

        for server in ntp_server.strip().split(","):
            id_counter += 1
            server_fields = dict()

            key_counter += 1
            if ntp_auth == "enable":
                server_fields["authentication"] = 1
                server_fields["key"] = ntp_auth_pwd
                server_fields["key-id"] = key_counter
            else:
                server_fields["authentication"] = 0
                server_fields["key"] = ""
                server_fields["key-id"] = key_counter

            if ntp_v3 == "enable":
                server_fields["ntpv3"] = 1
            else:
                server_fields["ntpv3"] = 0

            # split the host on the space to get the mask out
            new_ntp_server = {"authentication": server_fields["authentication"],
                              "id": id_counter, "key": server_fields["key"],
                              "key-id": id_counter, "ntpv3": server_fields["ntpv3"],
                              "server": server}
            ntpservers.append(new_ntp_server)

        datagram["ntpserver"] = ntpservers

        # SET THE BODY FOR THE FORTIGUARD REQUEST
        url = "/pm/config/adom/{adom}" \
              "/devprof/{provisioning_template}" \
              "/system/ntp".format(adom=adom,
                                   provisioning_template=provisioning_template)

        # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
        response = fmg.set(url, datagram)
        return response


def delete_devprof_ntp(fmg, provisioning_template, adom, ntp_status, ntp_sync_interval, ntp_type, ntp_server,
                       ntp_auth, ntp_auth_pwd, ntp_v3):
    """
    DISABLE NTP SETTINGS
    """
    # IF SET TO FORTIGUARD, BUILD A STRING SPECIFIC TO THAT
    if ntp_type == "fortiguard":
        datagram = dict()
        if ntp_status == "enable":
            datagram["ntpsync"] = 1
        if ntp_status == "disable":
            datagram["ntpsync"] = 0
        if ntp_sync_interval is None:
            datagram["syncinterval"] = 1
        else:
            datagram["syncinterval"] = ntp_sync_interval

        datagram["type"] = 0

        # SET THE BODY FOR THE FORTIGUARD REQUEST
        url = "/pm/config/adom/{adom}" \
              "/devprof/{provisioning_template}" \
              "/system/ntp".format(adom=adom,
                                   provisioning_template=provisioning_template)

        # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
        response = fmg.delete(url, datagram)
        return response

    # IF THE NTP TYPE IS CUSTOM BUILD THE SERVER LIST
    if ntp_type == "custom":
        id_counter = 0
        key_counter = 0
        ntpservers = []
        datagram = dict()
        if ntp_status == "enable":
            datagram["ntpsync"] = 1
        if ntp_status == "disable":
            datagram["ntpsync"] = 0
        if ntp_sync_interval is None:
            datagram["syncinterval"] = 1
        else:
            datagram["syncinterval"] = ntp_sync_interval
            datagram["type"] = 1

        for server in ntp_server.strip().split(","):
            id_counter += 1
            server_fields = dict()

            key_counter += 1
            if ntp_auth == "enable":
                server_fields["authentication"] = 1
                server_fields["key"] = ntp_auth_pwd
                server_fields["key-id"] = key_counter
            else:
                server_fields["authentication"] = 0
                server_fields["key"] = ""
                server_fields["key-id"] = key_counter

            if ntp_v3 == "enable":
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
              "/system/ntp".format(adom=adom,
                                   provisioning_template=provisioning_template)

        # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
        response = fmg.delete(url, datagram)
        return response


def set_devprof_admin(fmg, provisioning_template, adom, admin_https_redirect, admin_https_port, admin_http_port,
                      admin_timeout, admin_language, admin_switch_controller, admin_gui_theme):
    """
        DISABLE NTP SETTINGS
    """
    if admin_https_redirect == "enable":
        datagram = {
            "admin-https-redirect": 0
        }
    else:
        datagram = {
            "admin-https-redirect": 1,
            "admin-port": admin_http_port,
            "admin-sport": admin_https_port,
            "admintimeout": admin_timeout,
            "language": admin_language,
            "gui-theme": admin_gui_theme,
            "switch-controller": admin_switch_controller,
        }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/global".format(adom=adom,
                                  provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.set(url, datagram)
    return response


def delete_devprof_admin(fmg, provisioning_template, adom, admin_https_redirect, admin_https_port,
                         admin_http_port, admin_timeout, admin_language, admin_switch_controller, admin_gui_theme):
    """
        DISABLE NTP SETTINGS
    """
    if admin_https_redirect == "enable":
        datagram = {
            "admin-https-redirect": 0
        }
    else:
        datagram = {
            "admin-https-redirect": 1,
            "admin-port": admin_http_port,
            "admin-sport": admin_https_port,
            "admintimeout": admin_timeout,
            "language": admin_language,
            "gui-theme": admin_gui_theme,
            "switch-controller": admin_switch_controller,
        }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/global".format(adom=adom,
                                  provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.delete(url, datagram)
    return response


def set_devprof_smtp(fmg, provisioning_template, adom, smtp_username, smtp_password, smtp_port, smtp_replyto,
                     smtp_conn_sec, smtp_server, smtp_source_ipv4, smtp_validate_cert):
    """
       ENABLE SMTP SETTINGS
    """
    datagram = {
        "port": smtp_port,
        "reply-to": smtp_replyto,
        "server": smtp_server,
        "source-ip": smtp_source_ipv4
    }

    if smtp_username:
        datagram["authenticate"] = 1
        datagram["username"] = smtp_username
        datagram["password"] = smtp_password

    if smtp_conn_sec == "none":
        datagram["security"] = 0
    if smtp_conn_sec == "starttls":
        datagram["security"] = 1
    if smtp_conn_sec == "smtps":
        datagram["security"] = 2

    if smtp_validate_cert == "enable":
        datagram["validate-server"] = 1
    else:
        datagram["validate-server"] = 0

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/email-server".format(adom=adom,
                                        provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.set(url, datagram)
    return response


def delete_devprof_smtp(fmg, provisioning_template, adom, smtp_username, smtp_password, smtp_port, smtp_replyto,
                        smtp_conn_sec, smtp_server, smtp_source_ipv4, smtp_validate_cert):
    """
        DISABLE SMTP SETTINGS
    """
    datagram = {
        "port": smtp_port,
        "reply-to": smtp_replyto,
        "server": smtp_server,
        "source-ip": smtp_source_ipv4,
    }

    if smtp_username:
        datagram["authenticate"] = 1
        datagram["username"] = smtp_username
        datagram["password"] = smtp_password

    if smtp_conn_sec == "none":
        datagram["security"] = 0
    if smtp_conn_sec == "starttls":
        datagram["security"] = 1
    if smtp_conn_sec == "smtps":
        datagram["security"] = 2

    if smtp_validate_cert == "enable":
        datagram["validate-server"] = 1
    else:
        datagram["validate-server"] = 0

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/email-server".format(adom=adom,
                                        provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.delete(url, datagram)
    return response


def set_devprof_dns(fmg, provisioning_template, adom, dns_suffix, dns_primary_ipv4, dns_secondary_ipv4,
                    dns_primary_ipv6, dns_secondary_ipv6):
    """
       ENABLE DNS SETTINGS
    """
    datagram = {
        "domain": dns_suffix,
        "primary": dns_primary_ipv4,
        "secondary": dns_secondary_ipv4,
        "ip6-primary": dns_primary_ipv6,
        "ip6-secondary": dns_secondary_ipv6,
    }
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/dns".format(adom=adom,
                               provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.set(url, datagram)
    return response


def delete_devprof_dns(fmg, provisioning_template, adom, dns_suffix, dns_primary_ipv4, dns_secondary_ipv4,
                       dns_primary_ipv6, dns_secondary_ipv6):
    """
        DISABLE DNS SETTINGS
    """
    datagram = {
        "domain": dns_suffix,
        "primary": dns_primary_ipv4,
        "secondary": dns_secondary_ipv4,
        "ip6-primary": dns_primary_ipv6,
        "ip6-secondary": dns_secondary_ipv6,
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/dns".format(adom=adom,
                               provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.delete(url, datagram)
    return response


def set_devprof_fg(fmg, provisioning_template, adom, admin_enable_fortiguard):
    """
       ENABLE FG SETTINGS
    """
    datagram = dict()
    if admin_enable_fortiguard == "enable":
        datagram["include-default-servers"] = 1
    else:
        datagram["include-default-servers"] = 0

    server_list = []
    datagram["server-list"] = server_list

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/system/central-management".format(adom=adom,
                                              provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.set(url, datagram)

    # make a second call to ensure the fortiguard target is set
    datagram2 = {
        "target": 2
    }
    url2 = "/pm/config/adom/{adom}" \
           "/devprof/{provisioning_template}" \
           "/device/profile/fortiguard".format(adom=adom,
                                               provisioning_template=provisioning_template),

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response2 = fmg.set(url2, datagram2)
    return response


def delete_devprof_fg(fmg, provisioning_template, adom, admin_enable_fortiguard, state):
    """
        DISABLE FG SETTINGS
    """
    datagram = dict()

    if admin_enable_fortiguard == "disable" or state == "absent":
        datagram["target"] = 0

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortiguard".format(adom=adom,
                                              provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.delete(url, datagram)
    return response


def set_devprof_faz(fmg, provisioning_template, adom, admin_fortianalyzer_target):
    """
       ENABLE FAZ SETTINGS
    """
    datagram = {
        "target-ip": admin_fortianalyzer_target,
        "target": 4,
    }
    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortianalyzer".format(adom=adom,
                                                 provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.set(url, datagram)
    return response


def delete_devprof_faz(fmg, provisioning_template, adom, admin_fortianalyzer_target):
    """
        DISABLE FAZ SETTINGS
    """
    datagram = {
        "target-ip": admin_fortianalyzer_target,
        "target": 4,
        "hastarget": "true",
    }

    url = "/pm/config/adom/{adom}" \
          "/devprof/{provisioning_template}" \
          "/device/profile/fortianalyzer".format(adom=adom,
                                                 provisioning_template=provisioning_template)

    # MAKE THE CALL BASED UPON THE BODY CREATED ABOVE
    response = fmg.delete(url, datagram)
    return response


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
        snmp_v2c_trap_src_ipv6=dict(required=False, type="str"),
        snmp_v2c_trap_hosts_ipv4=dict(required=False, type="str"),
        snmp_v2c_query_hosts_ipv4=dict(required=False, type="str"),
        snmp_v2c_query_hosts_ipv6=dict(required=False, type="str"),
        snmp_v2c_trap_hosts_ipv6=dict(required=False, type="str"),

        snmpv3_auth_proto=dict(required=False, type="str", choices=["md5", "sha"]),
        snmpv3_auth_pwd=dict(required=False, type="str", no_log=True),
        snmpv3_name=dict(required=False, type="str"),
        snmpv3_notify_hosts=dict(required=False, type="str"),
        snmpv3_notify_hosts6=dict(required=False, type="str"),
        snmpv3_priv_proto=dict(required=False, type="str", choices=["aes", "des", "aes256", "aes256cisco"]),
        snmpv3_priv_pwd=dict(required=False, type="str", no_log=True),
        snmpv3_queries=dict(required=False, type="str", choices=["enable", "disable"]),
        snmpv3_query_port=dict(required=False, type="int"),
        snmpv3_security_level=dict(required=False, type="str",
                                   choices=["no-auth-no-priv", "auth-no-priv", "auth-priv"]),
        snmpv3_source_ip=dict(required=False, type="str"),
        snmpv3_source_ipv6=dict(required=False, type="str"),
        snmpv3_status=dict(required=False, type="str", choices=["enable", "disable"]),
        snmpv3_trap_rport=dict(required=False, type="int"),
        snmpv3_trap_status=dict(required=False, type="str", choices=["enable", "disable"]),

        syslog_port=dict(required=False, type="int"),
        syslog_server=dict(required=False, type="str"),
        syslog_tcp=dict(required=False, type="str", choices=["enable", "disable"]),
        syslog_status=dict(required=False, type="str", choices=["enable", "disable"]),
        syslog_filter=dict(required=False, type="str", choices=["emergency", "alert", "critical", "error",
                                                                "warning", "notification", "information", "debug"]),

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
        admin_enable_fortiguard=dict(required=False, type="str", choices=["enable", "disable"]),
        admin_fortianalyzer_target=dict(required=False, type="str"),

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
        dns_primary_ipv6=dict(required=False, type="str"),
        dns_secondary_ipv6=dict(required=False, type="str")

    )

    module = AnsibleModule(argument_spec, supports_check_mode=True,)

    # handle params passed via provider and insure they are represented as the data type expected by fortimanager
    provisioning_template = module.params["provisioning_template"]
    if provisioning_template is None:
        provisioning_template = "default"
    adom = module.params["adom"]
    # if adom is empty, set to root
    if adom is None:
        adom = "root"
    state = module.params["state"]
    if state is None:
        state = "present"

    provision_targets = module.params["provision_targets"]

    snmp_status = module.params["snmp_status"]
    snmp_v2c_query_port = module.params["snmp_v2c_query_port"]
    snmp_v2c_trap_port = module.params["snmp_v2c_trap_port"]
    snmp_v2c_status = module.params["snmp_v2c_status"]
    snmp_v2c_trap_status = module.params["snmp_v2c_trap_status"]
    snmp_v2c_query_status = module.params["snmp_v2c_query_status"]
    snmp_v2c_name = module.params["snmp_v2c_name"]
    snmp_v2c_id = module.params["snmp_v2c_id"]
    snmp_v2c_trap_src_ipv4 = module.params["snmp_v2c_trap_src_ipv4"]
    snmp_v2c_trap_src_ipv6 = module.params["snmp_v2c_trap_src_ipv6"]
    snmp_v2c_trap_hosts_ipv4 = module.params["snmp_v2c_trap_hosts_ipv4"]
    snmp_v2c_query_hosts_ipv4 = module.params["snmp_v2c_query_hosts_ipv4"]
    snmp_v2c_query_hosts_ipv6 = module.params["snmp_v2c_query_hosts_ipv6"]
    snmp_v2c_trap_hosts_ipv6 = module.params["snmp_v2c_trap_hosts_ipv6"]

    snmpv3_auth_proto = module.params["snmpv3_auth_proto"]
    snmpv3_auth_pwd = module.params["snmpv3_auth_pwd"]
    snmpv3_name = module.params["snmpv3_name"]
    snmpv3_notify_hosts = module.params["snmpv3_notify_hosts"]
    snmpv3_notify_hosts6 = module.params["snmpv3_notify_hosts6"]
    snmpv3_priv_proto = module.params["snmpv3_priv_proto"]
    snmpv3_priv_pwd = module.params["snmpv3_priv_pwd"]
    snmpv3_queries = module.params["snmpv3_queries"]
    snmpv3_query_port = module.params["snmpv3_query_port"]
    snmpv3_security_level = module.params["snmpv3_security_level"]
    snmpv3_source_ip = module.params["snmpv3_source_ip"]
    snmpv3_source_ipv6 = module.params["snmpv3_source_ipv6"]
    snmpv3_status = module.params["snmpv3_status"]
    snmpv3_trap_rport = module.params["snmpv3_trap_rport"]
    snmpv3_trap_status = module.params["snmpv3_trap_status"]

    syslog_port = module.params["syslog_port"]
    syslog_server = module.params["syslog_server"]
    syslog_tcp = module.params["syslog_tcp"]
    syslog_status = module.params["syslog_status"]
    syslog_filter = module.params["syslog_filter"]

    ntp_status = module.params["ntp_status"]
    ntp_sync_interval = module.params["ntp_sync_interval"]
    ntp_type = module.params["ntp_type"]
    ntp_server = module.params["ntp_server"]
    ntp_auth = module.params["ntp_auth"]
    ntp_auth_pwd = module.params["ntp_auth_pwd"]
    ntp_v3 = module.params["ntp_v3"]

    admin_https_redirect = module.params["admin_https_redirect"]
    admin_https_port = module.params["admin_https_port"]
    admin_http_port = module.params["admin_http_port"]
    admin_timeout = module.params["admin_timeout"]
    admin_language = module.params["admin_language"]
    admin_switch_controller = module.params["admin_switch_controller"]
    admin_gui_theme = module.params["admin_gui_theme"]
    admin_enable_fortiguard = module.params["admin_enable_fortiguard"]
    admin_fortianalyzer_target = module.params["admin_fortianalyzer_target"]

    smtp_username = module.params["smtp_username"]
    smtp_password = module.params["smtp_password"]
    smtp_port = module.params["smtp_port"]
    smtp_replyto = module.params["smtp_replyto"]
    smtp_conn_sec = module.params["smtp_conn_sec"]
    smtp_server = module.params["smtp_server"]
    smtp_source_ipv4 = module.params["smtp_source_ipv4"]
    smtp_validate_cert = module.params["smtp_validate_cert"]

    dns_suffix = module.params["dns_suffix"]
    dns_primary_ipv4 = module.params["dns_primary_ipv4"]
    dns_secondary_ipv4 = module.params["dns_secondary_ipv4"]
    dns_primary_ipv6 = module.params["dns_primary_ipv6"]
    dns_secondary_ipv6 = module.params["dns_secondary_ipv6"]

    # validate required arguments are passed; not used in argument_spec to allow params to be called from provider
    # check if params are set
    if module.params["host"] is None or module.params["username"] is None:
        module.fail_json(msg="Host and username are required for connection")

        # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()
    if "FortiManager instance connnected" not in str(response):
        module.fail_json(msg="Connection to FortiManager Failed")
    else:
        # START SESSION LOGIC
        # VERIFY THE TEMPLATE EXISTS FIRST
        devprof = get_devprof(fmg, provisioning_template, adom)

        if not devprof[0] == 0:
            devprof_create_result = add_devprof(fmg, provisioning_template, adom)

        # PROCESS THE SNMP SETTINGS IF THE SNMP_STATUS VARIABLE IS SET
        if snmp_status is not None:
            if state == "present":
                # enable SNMP in the devprof template
                results = set_devprof_snmp(fmg, provisioning_template, snmp_status, adom)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set SNMP status", **results[1])
            elif state == "absent":
                # disable SNMP in the devprof template
                results = delete_devprof_snmp(fmg, provisioning_template, snmp_status, adom)
                if results[0] != 0 and results[0] != -10000:
                    module.fail_json(msg="Failed to delete SNMP status", **results[1])

        # PROCESS THE SNMP V2C COMMUNITY SETTINGS IF THEY ARE ALL HERE
        if all(v is not None for v in [snmp_v2c_query_port, snmp_v2c_trap_port, snmp_v2c_status, snmp_v2c_trap_status,
                                       snmp_v2c_query_status, snmp_v2c_name, snmp_v2c_id]):
            if state == "present":
                results = set_devprof_snmp_v2c(fmg, provisioning_template, adom, snmp_v2c_query_port,
                                               snmp_v2c_trap_port, snmp_v2c_status, snmp_v2c_trap_status,
                                               snmp_v2c_query_status, snmp_v2c_name, snmp_v2c_id,
                                               snmp_v2c_trap_src_ipv4, snmp_v2c_trap_src_ipv6,
                                               snmp_v2c_query_hosts_ipv4, snmp_v2c_query_hosts_ipv6,
                                               snmp_v2c_trap_hosts_ipv4, snmp_v2c_trap_hosts_ipv6)
                if results[0] == -10033:
                    module.warn("Duplicate SNMP Community Exists. "
                                "Change the ID in the playbook, or the other settings.")
                if results[0] != 0 and results[0] != -10033:
                    module.fail_json(msg="Failed to create SNMP V2C Community", **results[1])

            if state == "absent":
                results = delete_devprof_snmp_v2c(fmg, provisioning_template, adom, snmp_v2c_id)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete SNMP V2C Community", **results[1])

        # PROCESS THE SNMPV3 USER IF THERE
        if all(v is not None for v in[snmpv3_auth_proto, snmpv3_auth_pwd, snmpv3_name, snmpv3_notify_hosts,
                                      snmpv3_notify_hosts6, snmpv3_priv_proto, snmpv3_priv_pwd, snmpv3_queries,
                                      snmpv3_query_port, snmpv3_security_level, snmpv3_source_ip, snmpv3_source_ipv6,
                                      snmpv3_status, snmpv3_trap_rport, snmpv3_trap_status]):
            if state == "present":
                results = set_devprof_snmp_v3(fmg, provisioning_template, adom, snmpv3_auth_proto, snmpv3_auth_pwd,
                                              snmpv3_name, snmpv3_notify_hosts, snmpv3_notify_hosts6,
                                              snmpv3_priv_proto, snmpv3_priv_pwd, snmpv3_queries, snmpv3_query_port,
                                              snmpv3_security_level, snmpv3_source_ip, snmpv3_source_ipv6,
                                              snmpv3_status, snmpv3_trap_rport, snmpv3_trap_status)
                if results[0] == -10033:
                    module.warn("Duplicate SNMP User Exists. Change the ID in the playbook, or the other settings.")
                if not results[0] in [0, -10033, 10000, -3]:
                    module.fail_json(msg="Failed to create SNMP V3 Community", **results[1])

            if state == "absent":
                results = delete_devprof_snmp_v3(fmg, provisioning_template, adom, snmpv3_name)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete SNMP V3 Community", **results[1])

        # PROCESS THE SYSLOG SETTINGS IF THE ALL THE NEEDED SYSLOG VARIABLES ARE PRESENT
        if all(v is not None for v in [syslog_port, syslog_tcp, syslog_server, syslog_status]):
            if state == "present":
                # enable syslog in the devprof template
                results = set_devprof_syslog(fmg, provisioning_template, syslog_status, syslog_port, syslog_tcp,
                                             syslog_server, adom)

                if results[0] != 0:
                    module.fail_json(msg="Failed to set Syslog server", **results[1])
            elif state == "absent":
                # disable syslog in the devprof template
                results = delete_devprof_syslog(fmg, provisioning_template, syslog_status, syslog_port, syslog_tcp,
                                                syslog_server, adom)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete syslog server settings", **results[1])

        # IF THE SYSLOG FILTER IS PRESENT THEN RUN THAT
        if syslog_filter is not None:
            if state == "present":
                # set the syslog filter level
                results = set_devprof_syslog_filter(fmg, provisioning_template, syslog_filter, adom)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set syslog filter settings", **results[1])
            elif state == "absent":
                # remove the syslog filter level
                results = delete_devprof_syslog_filter(fmg, provisioning_template, syslog_filter, adom)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete syslog settings", **results[1])

        # PROCESS NTP OPTIONS
        if ntp_status:
            # VALIDATE INPUT
            if ntp_type == "custom" and ntp_server is None:
                module.exit_json(msg="You requested custom NTP type but did not provide ntp_server parameter.")
            if ntp_auth == "enable" and ntp_auth_pwd is None:
                module.exit_json(msg="You requested NTP Authentication but did not provide ntp_auth_pwd parameter.")
            if state == "present":
                results = set_devprof_ntp(fmg, provisioning_template, adom, ntp_status, ntp_sync_interval, ntp_type,
                                          ntp_server, ntp_auth, ntp_auth_pwd, ntp_v3)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set NTP settings", **results[1])
            elif state == "absent":
                results = delete_devprof_ntp(fmg, provisioning_template, adom, ntp_status, ntp_sync_interval, ntp_type,
                                             ntp_server, ntp_auth, ntp_auth_pwd, ntp_v3)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete NTP settings", **results[1])

        # PROCESS THE ADMIN OPTIONS
        if any(v is not None for v in (admin_https_redirect, admin_https_port, admin_http_port, admin_timeout,
                                       admin_language, admin_switch_controller, admin_gui_theme)):
            if state == "present":
                results = set_devprof_admin(fmg, provisioning_template, adom, admin_https_redirect, admin_https_port,
                                            admin_http_port, admin_timeout, admin_language,
                                            admin_switch_controller, admin_gui_theme)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set NTP settings", **results[1])
            if state == "absent":
                results = delete_devprof_admin(fmg, provisioning_template, adom, admin_https_redirect, admin_https_port,
                                               admin_http_port, admin_timeout, admin_language,
                                               admin_switch_controller, admin_gui_theme)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete NTP settings", **results[1])

        if admin_enable_fortiguard == "enable":
            if state == "present":
                results = set_devprof_fg(fmg, provisioning_template, adom, admin_enable_fortiguard)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set FortiGuard settings", **results[1])
            if state == "absent":
                results = delete_devprof_fg(fmg, provisioning_template, adom, admin_enable_fortiguard, state)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete FortiGuard settings", **results[1])

        # PROCESS THE SMTP OPTIONS
        if all(v is not None for v in (smtp_username, smtp_password, smtp_port, smtp_replyto,
                                       smtp_conn_sec, smtp_server,
                                       smtp_source_ipv4, smtp_validate_cert)):
            if state == "present":
                results = set_devprof_smtp(fmg, provisioning_template, adom, smtp_username, smtp_password, smtp_port,
                                           smtp_replyto, smtp_conn_sec, smtp_server, smtp_source_ipv4,
                                           smtp_validate_cert)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set SMTP settings", **results[1])

            if state == "absent":
                results = delete_devprof_smtp(fmg, provisioning_template, adom, smtp_username, smtp_password, smtp_port,
                                              smtp_replyto, smtp_conn_sec, smtp_server, smtp_source_ipv4,
                                              smtp_validate_cert)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete SMTP settings", **results[1])

        # PROCESS THE DNS OPTIONS
        if any(v is not None for v in (dns_suffix, dns_primary_ipv4, dns_secondary_ipv4,
                                       dns_primary_ipv6, dns_secondary_ipv6)):
            if state == "present":
                results = set_devprof_dns(fmg, provisioning_template, adom, dns_suffix, dns_primary_ipv4,
                                          dns_secondary_ipv4, dns_primary_ipv6, dns_secondary_ipv6)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set DNS settings", **results[1])

            if state == "absent":
                results = delete_devprof_dns(fmg, provisioning_template, adom, dns_suffix, dns_primary_ipv4,
                                             dns_secondary_ipv4, dns_primary_ipv6, dns_secondary_ipv6)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete DNS settings", **results[1])

        # PROCESS THE admin_fortianalyzer_target OPTIONS
        if admin_fortianalyzer_target is not None:
            if state == "present":
                results = set_devprof_faz(fmg, provisioning_template, adom, admin_fortianalyzer_target)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set FortiAnalyzer settings", **results[1])

            if state == "absent":
                results = delete_devprof_faz(fmg, provisioning_template, adom, admin_fortianalyzer_target)
                if not results[0] in [0, -10033, -10000, -3]:
                    module.fail_json(msg="Failed to delete FortiAnalyzer settings", **results[1])

        # PROCESS THE PROVISIONING TEMPLATE TARGET PARAMETER
        if provision_targets is not None:
            if state == "present":
                results = set_devprof_scope(fmg, provisioning_template, adom, provision_targets)
                if not results[0] == 0:
                    module.fail_json(msg="Failed to set provision template scope targets", **results[1])
            # pydevd.settrace('10.1.1.2', port=54654, stdoutToServer=True, stderrToServer=True)
            if state == "absent":
                # FIRST WE MUST GET THE CURRENT LIST AND COMPARE
                # BECAUSE WE CAN ONLY SET THE EXACT LIST
                # GET THE LIST OF TARGETS ON THE SERVER
                current_template = get_devprof_scope(fmg, provisioning_template, adom)
                targets_on_server = None
                try:
                    targets_on_server = current_template[1][1]["scope member"]
                    num_targets_on_server = len(targets_on_server)
                    loopcount = 0
                    targets_on_server_list = []
                    while loopcount < num_targets_on_server:
                        target = targets_on_server[loopcount].values()
                        targets_on_server_list.append(str(target[0]))
                        loopcount += 1
                except:
                    pass

                # IF THE ABOVE GET CHECK PASSED, THEN CONTINUE WITH PROCESSING
                if targets_on_server is not None:
                    # GET THE LIST OF TARGETS WE WANT TO DELETE
                    targets_to_delete = []
                    for target in provision_targets.strip().split(","):
                        # split the host on the space to get the mask out
                        # new_target = {"name": target}
                        new_target = target
                        targets_to_delete.append(new_target)

                    # NOW COMPARE THE SCOPE LIST WITH THE PROVISIONING TARGETS LIST
                    # AND SET THE SCOPE TO THE NEW LIST
                    remaining_targets = []
                    try:
                        remaining_targets = list(set(targets_on_server_list) - set(targets_to_delete))
                    except:
                        pass
                    # TURN THE LIST BACK INTO A STRING FOR THE METHOD
                    remaining_targets_string = ",".join(remaining_targets)
                    results = delete_devprof_scope(fmg, provisioning_template, adom, remaining_targets_string)
                    if not results[0] in [0, -10033, -10000, -3]:
                        module.fail_json(msg="Failed to provision template scope targets", **results[1])

                else:
                    # IF WE CAN'T FIND ANY EXISTING SCOPE MEMBERS, THEN FAIL GRACEFULLY
                    module.exit_json(msg="Couldn't find any existing scope targets to delete.")

        fmg.logout()

        return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
