#
# (c) 2018 Red Hat, Inc.
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
import sys
import json

from contextlib import contextmanager

from ansible.errors import AnsibleError
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.common.netconf import NetconfConnection

try:
    from ncclient.xml_ import NCElement
except ImportError:
    raise AnsibleError("ncclient is not installed")


def get_connection(module):
    if hasattr(module, '_netconf_connection'):
        return module._netconf_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'netconf':
        module._netconf_connection = NetconfConnection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._netconf_connection


def get_capabilities(module):
    if hasattr(module, '_netconf_capabilities'):
        return module._netconf_capabilities

    capabilities = Connection(module._socket_path).get_capabilities()
    module._netconf_capabilities = json.loads(capabilities)
    return module._netconf_capabilities


def lock_configuration(x, target=None):
    conn = get_connection(x)
    return conn.lock(target=target)


def unlock_configuration(x, target=None):
    conn = get_connection(x)
    return conn.unlock(target=target)


@contextmanager
def locked_config(module, target=None):
    try:
        lock_configuration(module, target=target)
        yield
    finally:
        unlock_configuration(module, target=target)


def transform_reply():
    reply = '''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
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
    if sys.version < '3':
        return reply
    else:
        return reply.encode('UTF-8')


# Note: Workaround for ncclient 0.5.3
def remove_namespaces(data):
    return NCElement(data, transform_reply()).data_xml