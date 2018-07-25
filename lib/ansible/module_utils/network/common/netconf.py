# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import sys

from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.connection import Connection, ConnectionError

try:
    from ncclient.xml_ import NCElement
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

try:
    from lxml.etree import Element, fromstring, XMLSyntaxError
except ImportError:
    from xml.etree.ElementTree import Element, fromstring
    if sys.version_info < (2, 7):
        from xml.parsers.expat import ExpatError as XMLSyntaxError
    else:
        from xml.etree.ElementTree import ParseError as XMLSyntaxError

NS_MAP = {'nc': "urn:ietf:params:xml:ns:netconf:base:1.0"}


def exec_rpc(module, *args, **kwargs):
    connection = NetconfConnection(module._socket_path)
    return connection.execute_rpc(*args, **kwargs)


class NetconfConnection(Connection):

    def __init__(self, socket_path):
        super(NetconfConnection, self).__init__(socket_path)

    def __rpc__(self, name, *args, **kwargs):
        """Executes the json-rpc and returns the output received
           from remote device.
           :name: rpc method to be executed over connection plugin that implements jsonrpc 2.0
           :args: Ordered list of params passed as arguments to rpc method
           :kwargs: Dict of valid key, value pairs passed as arguments to rpc method

           For usage refer the respective connection plugin docs.
        """
        self.check_rc = kwargs.pop('check_rc', True)
        self.ignore_warning = kwargs.pop('ignore_warning', True)

        response = self._exec_jsonrpc(name, *args, **kwargs)
        if 'error' in response:
            rpc_error = response['error'].get('data')
            return self.parse_rpc_error(to_bytes(rpc_error, errors='surrogate_then_replace'))

        return fromstring(to_bytes(response['result'], errors='surrogate_then_replace'))

    def parse_rpc_error(self, rpc_error):
        if self.check_rc:
            try:
                error_root = fromstring(rpc_error)
                root = Element('root')
                root.append(error_root)

                error_list = root.findall('.//nc:rpc-error', NS_MAP)
                if not error_list:
                    raise ConnectionError(to_text(rpc_error, errors='surrogate_then_replace'))

                warnings = []
                for error in error_list:
                    message_ele = error.find('./nc:error-message', NS_MAP)

                    if message_ele is None:
                        message_ele = error.find('./nc:error-info', NS_MAP)

                    message = message_ele.text if message_ele is not None else None

                    severity = error.find('./nc:error-severity', NS_MAP).text

                    if severity == 'warning' and self.ignore_warning and message is not None:
                        warnings.append(message)
                    else:
                        raise ConnectionError(to_text(rpc_error, errors='surrogate_then_replace'))
                return warnings
            except XMLSyntaxError:
                raise ConnectionError(rpc_error)


def transform_reply():
    return b'''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="no"/>

    <xsl:template match="/|comment()|processing-instruction()">
        <xsl:copy>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="*">
        <xsl:element name="{local-name()}">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="@*">
        <xsl:attribute name="{local-name()}">
            <xsl:value-of select="."/>
        </xsl:attribute>
    </xsl:template>
    </xsl:stylesheet>
    '''


# Note: Workaround for ncclient 0.5.3
def remove_namespaces(data):
    if not HAS_NCCLIENT:
        raise ImportError("ncclient is required but does not appear to be installed.  "
                          "It can be installed using `pip install ncclient`")
    return NCElement(data, transform_reply()).data_xml
