# -*- coding: utf-8 -*-
# !/usr/bin/python
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

NE_COMMON_XML_OPERATION_MERGE = "merge"
NE_COMMON_XML_OPERATION_CREATE = "create"
NE_COMMON_XML_OPERATION_DELETE = "delete"
NE_COMMON_XML_OPERATION_CLEAR = "clear"

# SCHEAM L3VPN XPATH
# <l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
# YANG  L3VPN XPATH
# <l3vpn xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn">
# Query l3vpn packet, use yang or schema modified head namespace.
NE_COMMON_XML_GET_L3VPN_HEAD = """
    <filter type="subtree">
        <l3vpn xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn">
          <l3vpncomm>
            <l3vpnInstances>
                <l3vpnInstance>
"""

NE_COMMON_XML_GET_L3VPN_TAIL = """
            </l3vpnInstance>
          </l3vpnInstances>
        </l3vpncomm>
      </l3vpn>
    </filter>
"""

NE_COMMON_XML_GET_L3VPNCOMM_HEAD = """
    <filter type="subtree">
        <l3vpn xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn">
          <l3vpncomm>
"""

NE_COMMON_XML_GET_L3VPNCOMM_TAIL = """
        </l3vpncomm>
      </l3vpn>
    </filter>
"""

# Configure isis packet, use yang or schema modified head namespace.
NE_COMMON_XML_PROCESS_L3VPN_HEAD = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <l3vpn xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn">
         <l3vpncomm>
            <l3vpnInstances>
              <l3vpnInstance xc:operation="%s">
"""
NE_COMMON_XML_PROCESS_L3VPN_HEAD_COMMON = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <l3vpn xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn">
         <l3vpncomm>
            <l3vpnInstances>
              <l3vpnInstance>
"""

NE_COMMON_XML_PROCESS_L3VPN_TAIL = """
            </l3vpnInstance>
          </l3vpnInstances>
        </l3vpncomm>
      </l3vpn>
    </config>
"""

NE_COMMON_XML_PROCESS_L3VPNCOMM_HEAD = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <l3vpn xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn">
         <l3vpncomm>
"""

NE_COMMON_XML_PROCESS_L3VPNCOMM_TAIL = """
        </l3vpncomm>
      </l3vpn>
    </config>
"""


def constr_leaf_value(xml_str, leafName, leafValue):
    """construct the leaf update string """

    if leafValue is not None:
        xml_str += "<" + leafName + ">"
        xml_str += "%s" % leafValue
        xml_str += "</" + leafName + ">\r\n"
    return xml_str


def constr_leaf_novalue(xml_str, leafName):
    """construct the leaf update string """
    xml_str += "<" + leafName + "></" + leafName + ">\r\n"
    return xml_str


def constr_container_head(xml_str, container):
    """construct the container update string head  """
    xml_str += "<" + container + ">\r\n"
    return xml_str


def constr_container_tail(xml_str, container):
    """construct the container update string tail  """
    xml_str += "</" + container + ">\r\n"
    return xml_str


def constr_container_process_head(xml_str, container, operation):
    """construct the container update string process  """
    xml_str += "<" + container + "s>\r\n"
    xml_str += "<" + container + " xc:operation=\"" + operation + "\">\r\n"
    return xml_str


def constr_container_process_tail(xml_str, container):
    """construct the container update string process  """
    xml_str += "</" + container + ">\r\n"
    xml_str += "</" + container + "s>\r\n"
    return xml_str


def constr_leaf_process(xml_str, leafName, leafValue):
    """construct the leaf update string """
    if leafValue is not None:
        xml_str += "<" + leafName + " xc:operation=\"delete\">"
        xml_str += "%s" % leafValue
        xml_str += "</" + leafName + ">\r\n"
    return xml_str
