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

NE_NC_OPTYPE_MERGE = "merge"
NE_NC_OPTYPE_CREATE = "create"
NE_NC_OPTYPE_DELETE = "delete"

NE_NC_DELETE_FLAG = r' nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"'

NE_NC_GET_IFM_HEAD = """
    <filter type="subtree">
        <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
            <interfaces>
                <interface>
"""

NE_NC_GET_IFM_TAIL = """
          </interface>
        </interfaces>
      </ifm>
    </filter>
"""

NE_NC_SET_IFM_HEAD = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
         <interfaces>
            <interface xc:operation="%s">
"""

NE_NC_SET_IFM_TAIL = """
            </interface>
        </interfaces>
      </ifm>
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


def constr_leaf_process_delete(xml_str, leafName):
    """construct the leaf update string """
    xml_str += "<" + leafName + NE_NC_DELETE_FLAG + "></" + leafName + ">\r\n"
    return xml_str


def constr_container_head(xml_str, container):
    """construct the container update string head  """
    xml_str += "<" + container + ">\r\n"
    return xml_str


def constr_container_tail(xml_str, container):
    """construct the container update string tail  """
    xml_str += "</" + container + ">\r\n"
    return xml_str


def constr_container_head_with_operation(xml_str, container, operation):
    """construct the container update string process  """
    xml_str += "<" + container + " nc:operation=\"" + operation + \
               "\" xmlns:nc=\"urn:ietf:params:xml:ns:netconf:base:1.0\">\r\n"
    return xml_str


def constr_container_novalue(xml_str, container):
    """construct the container update string head  """
    xml_str += "<" + container + "/>\r\n"
    return xml_str
