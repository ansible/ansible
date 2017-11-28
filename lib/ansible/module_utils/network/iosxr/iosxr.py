# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2015 Peter Sprygada, <psprygada@ansible.com>
# Copyright (c) 2017 Red Hat Inc.
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
import json
import sys
from difflib import Differ
from io import BytesIO
from copy import deepcopy

from ansible.module_utils.six import StringIO
from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import Connection
from ansible.module_utils.netconf import NetconfConnection

try:
    from ncclient.xml_ import to_xml
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

try:
    from lxml import etree
except ImportError:
    pass

_DEVICE_CONFIGS = {}
_EDIT_OPS = frozenset(['merge', 'create', 'replace', 'delete'])

BASE_1_0 = "{urn:ietf:params:xml:ns:netconf:base:1.0}"

NS_DICT = {
    'BASE_NSMAP': {"xc": "urn:ietf:params:xml:ns:netconf:base:1.0"},
    'BANNERS_NSMAP': {None: "http://cisco.com/ns/yang/Cisco-IOS-XR-infra-infra-cfg"},
    'INTERFACES_NSMAP': {None: "http://openconfig.net/yang/interfaces"},
    'INSTALL_NSMAP': {None: "http://cisco.com/ns/yang/Cisco-IOS-XR-installmgr-admin-oper"},
    'HOST-NAMES_NSMAP': {None: "http://cisco.com/ns/yang/Cisco-IOS-XR-shellutil-cfg"}
}

iosxr_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'timeout': dict(type='int'),
    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'transport': dict(),
}

iosxr_argument_spec = {
    'provider': dict(type='dict', options=iosxr_provider_spec)
}

iosxr_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'ssh_keyfile': dict(removed_in_version=2.9, type='path'),
    'timeout': dict(removed_in_version=2.9, type='int'),
}
iosxr_argument_spec.update(iosxr_top_spec)


def get_provider_argspec():
    return iosxr_provider_spec


def check_args(module, warnings):
    pass


def get_connection(module):
    if hasattr(module, 'connection'):
        return module.connection

    capabilities = get_device_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module.connection = Connection(module._socket_path)
    elif network_api == 'netconf':
        module.connection = NetconfConnection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type {!s}'.format(network_api))

    return module.connection


def get_device_capabilities(module):
    if hasattr(module, 'capabilities'):
        return module.capabilities

    capabilities = Connection(module._socket_path).get_capabilities()
    module.capabilities = json.loads(capabilities)

    return module.capabilities


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
        print("utf8")
        return reply.encode('UTF-8')


# Note: Workaround for ncclient 0.5.3
def remove_namespaces(rpc_reply):
    xslt = transform_reply()
    parser = etree.XMLParser(remove_blank_text=True)
    xslt_doc = etree.parse(BytesIO(xslt), parser)
    transform = etree.XSLT(xslt_doc)

    return etree.fromstring(str(transform(etree.parse(StringIO(str(rpc_reply))))))


# Builds netconf xml rpc document from meta-data
# e.g:
#
# Module inputs:
# banner_params = [{'banner':'motd', 'text':'Ansible banner example', 'state':'present'}]
#
# Meta-data definition
# bannermap = collections.OrderedDict()
# bannermap.update([
#     ('banner', {'xpath' : 'banners/banner', 'tag' : True, 'attrib' : "operation"}),
#     ('a:banner', {'xpath' : 'banner/banner-name'}),
#     ('a:text', {'xpath' : 'banner/banner-text', 'operation' : 'edit'})
# ])
#
# Fields:
#   key: exact match to the key expected in arg spec (prefixes --> a: values from arg_spec, m: values from meta-data)
#   xpath: xpath of the element (based on YANG model)
#   tag: True if no text on the element
#   attrib: attribute to be embedded in the element (e.g. cx:operation="merge")
#   operation: if edit --> includes the element in edit_config() query else ignore for get() queries
#   value: if key is prefixed with "m:", provider value from here
#   leaf: True --> if there is only one tag element under a subtree
#
# Output:
# <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
#   <banners xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-infra-cfg">
#     <banner xc:operation="merge">
#       <banner-name>motd</banner-name>
#       <banner-text>Ansible banner example</banner-text>
#     </banner>
#   </banners>
# </config>

def build_xml_subtree(container_ele, xmap, param=None, opcode=None):
    loop_root = container_ele
    for key, meta in xmap.items():
        candidates = meta.get('xpath', "").split("/")

        if container_ele.tag == candidates[-2]:
            parent = container_ele
        elif loop_root.tag == candidates[-2]:
            parent = loop_root
        else:
            parent = loop_root.find(".//" + candidates[-2])

        if meta.get('tag', False):
            if parent.tag == container_ele.tag:
                child = etree.Element(candidates[-1])
                loop_root = child
            else:
                child = etree.SubElement(parent, candidates[-1])

            if meta.get('attrib', None) and opcode in ('delete', 'merge'):
                child.set(BASE_1_0 + meta.get('attrib'), opcode)

            if meta.get('leaf', False):
                container_ele.append(deepcopy(loop_root))
            continue

        if (opcode in ('delete', 'merge') and meta.get('operation', 'unknown') == 'edit') \
                or meta.get('operation', None) is None:
            if meta.get('ns', None) is True:
                child = etree.SubElement(parent, candidates[-1],
                                         nsmap=NS_DICT[key.upper() + "_NSMAP"])
            else:
                child = etree.SubElement(parent, candidates[-1])

            param_key = key.split(":")
            if param_key[0] == 'a' and param.get(param_key[1], None):
                child.text = param.get(param_key[1])

            if param_key[0] == 'm' and meta.get('value', None):
                child.text = meta.get('value')

        if meta.get('leaf', False):
            container_ele.append(deepcopy(loop_root))

    container_ele.append(deepcopy(loop_root))


def build_xml(container, xmap=None, params=None, opcode=None):
    if opcode == 'filter':
        root = etree.Element("filter", type="subtree")
    elif opcode in ('delete', 'merge'):
        root = etree.Element("config", nsmap=NS_DICT['BASE_NSMAP'])
    container_ele = etree.SubElement(root, container,
                                     nsmap=NS_DICT[container.upper() + "_NSMAP"])

    if xmap:
        if not params:
            build_xml_subtree(container_ele, xmap)
        else:
            for param in to_list(params):
                build_xml_subtree(container_ele, xmap, param, opcode=opcode)

    return root


def get_config_diff(module, running=None, candidate=None):
    conn = get_connection(module)
    capabilities = get_device_capabilities(module)
    network_api = capabilities.get('network_api')

    if network_api == 'cliconf':
        return conn.get('show commit changes diff')
    elif network_api == 'netconf':
        if running and candidate:
            running_data = running.split("\n", 1)[1].rsplit("\n", 1)[0]
            candidate_data = candidate.split("\n", 1)[1].rsplit("\n", 1)[0]
            if running_data != candidate_data:
                d = Differ()
                diff = list(d.compare(running_data.splitlines(), candidate_data.splitlines()))
                return True, '\n'.join(diff).strip()
        return False, None
    else:
        module.fail_json(msg=('unsupported network_api: {!s}'.format(network_api)))


def discard_config(module):
    conn = get_connection(module)
    conn.discard_changes()


def commit_config(module, comment=None, confirmed=False, confirm_timeout=None, persist=False, check=False):
    conn = get_connection(module)
    if check:
        reply = conn.validate()
    else:
        capabilities = get_device_capabilities(module)
        network_api = capabilities.get('network_api')
        if network_api == 'netconf':
            reply = conn.commit(confirmed=confirmed, timeout=confirm_timeout, persist=persist)
        elif network_api == 'cliconf':
            reply = conn.commit(comment=comment)

    return reply


def get_config(module, source='running', config_filter=None):
    global _DEVICE_CONFIGS
    if config_filter:
        key = (source + ' ' + ' '.join(config_filter)).strip().rstrip()
    else:
        key = source
    config = _DEVICE_CONFIGS.get(key)
    if config:
        return config
    else:
        conn = get_connection(module)
        out = conn.get_config(source=source, filter=config_filter)

        capabilities = get_device_capabilities(module)
        network_api = capabilities.get('network_api')
        if network_api == 'netconf':
            if not HAS_NCCLIENT:
                module.fail_json(msg=('ncclient is not installed'))
            out = to_xml(out)

        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS.update({key: cfg})
        return cfg


def load_config(module, command_filter, warnings, replace=False, admin=False, commit=False, comment=None):
    conn = get_connection(module)
    capabilities = get_device_capabilities(module)
    network_api = capabilities.get('network_api')

    if network_api == 'netconf':
        # ret = conn.lock(target = 'candidate')
        # ret = conn.discard_changes()
        try:
            out = conn.edit_config(command_filter)
        finally:
            # ret = conn.unlock(target = 'candidate')
            pass

    elif network_api == 'cliconf':
        command_filter.insert(0, 'configure terminal')
        if admin:
            command_filter.insert(0, 'admin')
        conn.edit_config(command_filter)
        diff = get_config_diff(module)
        if module._diff:
            if diff:
                module['diff'] = to_text(diff, errors='surrogate_or_strict')
        if commit:
            commit_config(module, comment=comment)
            conn.edit_config('end')
        else:
            conn.discard_changes()

        return diff
    else:
        module.fail_json(msg=('unsupported network_api: {!s}'.format(network_api)))


def run_command(module, commands):
    conn = get_connection(module)
    responses = list()
    for cmd in to_list(commands):
        out = conn.get(to_bytes(cmd['command'], errors='surrogate_or_strict'))
        responses.append(to_text(out, errors='surrogate_or_strict'))
    return responses
