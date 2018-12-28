CREATE_RTP_IPPREFIX_XML = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <rtp xmlns="http://www.huawei.com/netconf/vrp/huawei-rtp">
            <prefixFilters>
              <prefixFilter xc:operation="create">
                <name>AnsilePrefix</name>
                <prefixFilterNodes>
                  <prefixFilterNode>
                    <nodeSequence>10</nodeSequence>
                    <matchMode>permit</matchMode>
                    <address>3.3.3.9</address>
                    <maskLength>16</maskLength>
                    <matchNetwork>false</matchNetwork>
                  </prefixFilterNode>
                </prefixFilterNodes>
              </prefixFilter>
            </prefixFilters>
          </rtp>
        </config>
"""

DELETE_RTP_IPPREFIX_XML = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <rtp xmlns="http://www.huawei.com/netconf/vrp/huawei-rtp">
            <prefixFilters>
              <prefixFilter xc:operation="delete">
                <name>AnsilePrefix</name>
              </prefixFilter>
            </prefixFilters>
          </rtp>
        </config>
"""

CREATE_RTP_IPPREFIX1_XML = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <rtp xmlns="http://www.huawei.com/netconf/vrp/huawei-rtp">
            <prefixFilters>
              <prefixFilter xc:operation="create">
                <name>AnsilePrefix1</name>
                <prefixFilterNodes>
                  <prefixFilterNode>
                    <nodeSequence>10</nodeSequence>
                    <matchMode>permit</matchMode>
                    <address>4.4.4.9</address>
                    <maskLength>16</maskLength>
                    <matchNetwork>false</matchNetwork>
                  </prefixFilterNode>
                </prefixFilterNodes>
              </prefixFilter>
            </prefixFilters>
          </rtp>
        </config>
"""

DELETE_RTP_IPPREFIX1_XML = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <rtp xmlns="http://www.huawei.com/netconf/vrp/huawei-rtp">
            <prefixFilters>
              <prefixFilter xc:operation="delete">
                <name>AnsilePrefix1</name>
              </prefixFilter>
            </prefixFilters>
          </rtp>
        </config>
"""
CREATE_BFD_XML = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <bfd xmlns="http://www.huawei.com/netconf/vrp/huawei-bfd">
            <bfdSchGlobal>
              <bfdEnable>true</bfdEnable>
            </bfdSchGlobal>
          </bfd>
        </config>
"""

DELETE_BFD_XML = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <bfd xmlns="http://www.huawei.com/netconf/vrp/huawei-bfd">
            <bfdSchGlobal>
              <bfdEnable>false</bfdEnable>
            </bfdSchGlobal>
          </bfd>
        </config>
"""

CREATE_INTF_LOOPBACK_XML = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <interfaces>
          <interface xc:operation="create">
            <ifName>LoopBack1</ifName>
          </interface>
        </interfaces>
      </ifm>
    </config>

"""

CREATE_INTF_LOOPBACK_ADDR_XML = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <interfaces>
          <interface>
            <ifName>LoopBack1</ifName>
            <ipv4Config>
              <am4CfgAddrs>
                <am4CfgAddr xc:operation="create">
                  <ifIpAddr>1.1.1.1</ifIpAddr>
                  <subnetMask>255.255.0.0</subnetMask>
                  <addrType>main</addrType>
                </am4CfgAddr>
              </am4CfgAddrs>
            </ipv4Config>
          </interface>
        </interfaces>
      </ifm>
    </config>

"""

DELETE_INTF_LOOPBACK_XML = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <interfaces>
          <interface xc:operation="delete">
            <ifName>LoopBack1</ifName>
          </interface>
        </interfaces>
      </ifm>
    </config>
"""

ALL_PRECOFING_XMLS = {
    "Create_ipPrefix": CREATE_RTP_IPPREFIX_XML,
    "Delete_ipPrefix": DELETE_RTP_IPPREFIX_XML,
    "Create_ipPrefix1": CREATE_RTP_IPPREFIX1_XML,
    "Delete_ipPrefix1": DELETE_RTP_IPPREFIX1_XML,
    "Create_bfd": CREATE_BFD_XML,
    "Delete_bfd": DELETE_BFD_XML,
    "Create_intf": CREATE_INTF_LOOPBACK_XML,
    "Create_intf_ipv4Config": CREATE_INTF_LOOPBACK_ADDR_XML,
    "Delete_intf": DELETE_INTF_LOOPBACK_XML
}
