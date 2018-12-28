# -*- coding: utf-8 -*-
# !/usr/bin/python


NE_COMMON_XML_OPERATION_MERGE = "merge"
NE_COMMON_XML_OPERATION_CREATE = "create"
NE_COMMON_XML_OPERATION_DELETE = "delete"


# Query mpls configure packet, use CE_SCHEMA_XPATH_MPLSCOMM for SCHEMA, use CE_YANG_XPATH_MPLSCOMM for YANG
NE_COMMON_XML_GET_MPLS_HEAD = """
    <filter type="subtree">
      <mpls xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls">
"""

NE_COMMON_XML_GET_MPLS_TAIL = """
      </mpls>
    </filter>
"""

NE_COMMON_XML_PROCESS_MPLS_HEAD = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <mpls xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls">
"""

NE_COMMON_XML_PROCESS_MPLS_TAIL = """
      </mpls>
    </config>
"""

NE_COMMON_XML_EXECUTE_MPLS_HEAD = """
    <action>
      <mpls xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls">
        <mplsLdp>
"""

NE_COMMON_XML_EXECUTE_MPLS_TAIL = """
        </mplsLdp>
      </mpls>
    </action>
"""


def constr_leaf_value(xml_str, leafName, leafValue):
    """construct the leaf update string"""
    if leafValue is not None:
        xml_str += "<" + leafName + ">"
        xml_str += "%s" % leafValue
        xml_str += "</" + leafName + ">\r\n"
    return xml_str


def constr_leaf_novalue(xml_str, leafName):
    """onstruct the leaf update string"""

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
