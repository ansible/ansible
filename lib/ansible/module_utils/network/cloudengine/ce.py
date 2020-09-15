#
# This code is part of Ansible, but is an independent component.
#
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat, Inc.
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

import re
import socket
import sys
import traceback

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import exec_command, ConnectionError
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native
from ansible.module_utils.network.common.netconf import NetconfConnection


try:
    from ncclient.xml_ import to_xml, new_ele_ns
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

_DEVICE_CLI_CONNECTION = None
_DEVICE_NC_CONNECTION = None

ce_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'use_ssl': dict(type='bool'),
    'validate_certs': dict(type='bool'),
    'timeout': dict(type='int'),
    'transport': dict(default='cli', choices=['cli', 'netconf']),
}
ce_argument_spec = {
    'provider': dict(type='dict', options=ce_provider_spec),
}
ce_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'ssh_keyfile': dict(removed_in_version=2.9, type='path'),
    'use_ssl': dict(removed_in_version=2.9, type='bool'),
    'validate_certs': dict(removed_in_version=2.9, type='bool'),
    'timeout': dict(removed_in_version=2.9, type='int'),
    'transport': dict(removed_in_version=2.9, choices=['cli', 'netconf']),
}
ce_argument_spec.update(ce_top_spec)


def to_string(data):
    return re.sub(r'<data\s+.+?(/>|>)', r'<data\1', data)


def check_args(module, warnings):
    pass


def load_params(module):
    """load_params"""
    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in ce_argument_spec:
            if module.params.get(key) is None and value is not None:
                module.params[key] = value


def get_connection(module):
    """get_connection"""
    global _DEVICE_CLI_CONNECTION
    if not _DEVICE_CLI_CONNECTION:
        load_params(module)
        conn = Cli(module)
        _DEVICE_CLI_CONNECTION = conn
    return _DEVICE_CLI_CONNECTION


def rm_config_prefix(cfg):
    if not cfg:
        return cfg

    cmds = cfg.split("\n")
    for i in range(len(cmds)):
        if not cmds[i]:
            continue
        if '~' in cmds[i]:
            index = cmds[i].index('~')
            if cmds[i][:index] == ' ' * index:
                cmds[i] = cmds[i].replace("~", "", 1)
    return '\n'.join(cmds)


class Cli:

    def __init__(self, module):
        self._module = module
        self._device_configs = {}

    def exec_command(self, command):
        if isinstance(command, dict):
            command = self._module.jsonify(command)

        return exec_command(self._module, command)

    def get_config(self, flags=None):
        """Retrieves the current config from the device or cache
        """
        flags = [] if flags is None else flags

        cmd = 'display current-configuration '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        try:
            return self._device_configs[cmd]
        except KeyError:
            rc, out, err = self.exec_command(cmd)
            if rc != 0:
                self._module.fail_json(msg=err)
            cfg = str(out).strip()
            # remove default configuration prefix '~'
            for flag in flags:
                if "include-default" in flag:
                    cfg = rm_config_prefix(cfg)
                    break

            self._device_configs[cmd] = cfg
            return cfg

    def run_commands(self, commands, check_rc=True):
        """Run list of commands on remote device and return results
        """
        responses = list()

        for item in to_list(commands):

            rc, out, err = self.exec_command(item)

            if check_rc and rc != 0:
                self._module.fail_json(msg=cli_err_msg(item['command'].strip(), err))

            try:
                out = self._module.from_json(out)
            except ValueError:
                out = str(out).strip()

            responses.append(out)
        return responses

    def load_config(self, config):
        """Sends configuration commands to the remote device
        """
        rc, out, err = self.exec_command('mmi-mode enable')
        if rc != 0:
            self._module.fail_json(msg='unable to set mmi-mode enable', output=err)
        rc, out, err = self.exec_command('system-view immediately')
        if rc != 0:
            self._module.fail_json(msg='unable to enter system-view', output=err)

        for cmd in config:
            rc, out, err = self.exec_command(cmd)
            if rc != 0:
                self._module.fail_json(msg=cli_err_msg(cmd.strip(), err))

        self.exec_command('return')


def cli_err_msg(cmd, err):
    """ get cli exception message"""

    if not err:
        return "Error: Fail to get cli exception message."

    msg = list()
    err_list = str(err).split("\r\n")
    for err in err_list:
        err = err.strip('.,\r\n\t ')
        if not err:
            continue
        if cmd and cmd == err:
            continue
        if " at '^' position" in err:
            err = err.replace(" at '^' position", "").strip()
        err = err.strip('.,\r\n\t ')
        if err == "^":
            continue
        if len(err) > 2 and err[0] in ["<", "["] and err[-1] in [">", "]"]:
            continue
        err.strip('.,\r\n\t ')
        if err:
            msg.append(err)

    if cmd:
        msg.insert(0, "Command: %s" % cmd)

    return ", ".join(msg).capitalize() + "."


def to_command(module, commands):
    default_output = 'text'
    transform = ComplexList(dict(
        command=dict(key=True),
        output=dict(default=default_output),
        prompt=dict(),
        answer=dict()
    ), module)

    commands = transform(to_list(commands))

    return commands


def get_config(module, flags=None):
    flags = [] if flags is None else flags

    conn = get_connection(module)
    return conn.get_config(flags)


def run_commands(module, commands, check_rc=True):
    conn = get_connection(module)
    return conn.run_commands(to_command(module, commands), check_rc)


def load_config(module, config):
    """load_config"""
    conn = get_connection(module)
    return conn.load_config(config)


def ce_unknown_host_cb(host, fingerprint):
    """ ce_unknown_host_cb """

    return True


def get_nc_set_id(xml_str):
    """get netconf set-id value"""

    result = re.findall(r'<rpc-reply.+?set-id=\"(\d+)\"', xml_str)
    if not result:
        return None
    return result[0]


def get_xml_line(xml_list, index):
    """get xml specified line valid string data"""

    ele = None
    while xml_list and not ele:
        if index >= 0 and index >= len(xml_list):
            return None
        if index < 0 and abs(index) > len(xml_list):
            return None

        ele = xml_list[index]
        if not ele.replace(" ", ""):
            xml_list.pop(index)
            ele = None
    return ele


def merge_nc_xml(xml1, xml2):
    """merge xml1 and xml2"""

    xml1_list = xml1.split("</data>")[0].split("\n")
    xml2_list = xml2.split("<data>")[1].split("\n")

    while True:
        xml1_ele1 = get_xml_line(xml1_list, -1)
        xml1_ele2 = get_xml_line(xml1_list, -2)
        xml2_ele1 = get_xml_line(xml2_list, 0)
        xml2_ele2 = get_xml_line(xml2_list, 1)
        if not xml1_ele1 or not xml1_ele2 or not xml2_ele1 or not xml2_ele2:
            return xml1

        if "xmlns" in xml2_ele1:
            xml2_ele1 = xml2_ele1.lstrip().split(" ")[0] + ">"
        if "xmlns" in xml2_ele2:
            xml2_ele2 = xml2_ele2.lstrip().split(" ")[0] + ">"
        if xml1_ele1.replace(" ", "").replace("/", "") == xml2_ele1.replace(" ", "").replace("/", ""):
            if xml1_ele2.replace(" ", "").replace("/", "") == xml2_ele2.replace(" ", "").replace("/", ""):
                xml1_list.pop()
                xml2_list.pop(0)
            else:
                break
        else:
            break

    return "\n".join(xml1_list + xml2_list)


def get_nc_connection(module):
    global _DEVICE_NC_CONNECTION
    if not _DEVICE_NC_CONNECTION:
        load_params(module)
        conn = NetconfConnection(module._socket_path)
        _DEVICE_NC_CONNECTION = conn
    return _DEVICE_NC_CONNECTION


def set_nc_config(module, xml_str):
    """ set_config """

    conn = get_nc_connection(module)
    try:
        out = conn.edit_config(target='running', config=xml_str, default_operation='merge',
                               error_option='rollback-on-error')
    finally:
        # conn.unlock(target = 'candidate')
        pass
    return to_string(to_xml(out))


def get_nc_next(module, xml_str):
    """ get_nc_next for exchange capability """

    conn = get_nc_connection(module)
    result = None
    if xml_str is not None:
        response = conn.get(xml_str, if_rpc_reply=True)
        result = response.find('./*')
        set_id = response.get('set-id')
        while True and set_id is not None:
            try:
                fetch_node = new_ele_ns('get-next', 'http://www.huawei.com/netconf/capability/base/1.0', {'set-id': set_id})
                next_xml = conn.dispatch_rpc(etree.tostring(fetch_node))
                if next_xml is not None:
                    result.extend(next_xml.find('./*'))
                set_id = next_xml.get('set-id')
            except ConnectionError:
                break
    if result is not None:
        return to_string(to_xml(result))
    return result


def get_nc_config(module, xml_str):
    """ get_config """

    conn = get_nc_connection(module)
    if xml_str is not None:
        response = conn.get(xml_str)
    else:
        return None

    return to_string(to_xml(response))


def execute_nc_action(module, xml_str):
    """ huawei execute-action """

    conn = get_nc_connection(module)
    response = conn.execute_action(xml_str)
    return to_string(to_xml(response))


def execute_nc_cli(module, xml_str):
    """ huawei execute-cli """

    if xml_str is not None:
        try:
            conn = get_nc_connection(module)
            out = conn.execute_nc_cli(command=xml_str)
            return to_string(to_xml(out))
        except Exception as exc:
            raise Exception(exc)


def check_ip_addr(ipaddr):
    """ check ip address, Supports IPv4 and IPv6 """

    if not ipaddr or '\x00' in ipaddr:
        return False

    try:
        res = socket.getaddrinfo(ipaddr, 0, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM,
                                 0, socket.AI_NUMERICHOST)
        return bool(res)
    except socket.gaierror:
        err = sys.exc_info()[1]
        if err.args[0] == socket.EAI_NONAME:
            return False
        raise
