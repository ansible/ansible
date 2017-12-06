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

import socket
import sys

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.network_common import to_list, ComplexList
from ansible.module_utils.connection import exec_command
from ansible.module_utils.six import iteritems


try:
    from ncclient import manager, xml_
    from ncclient.operations.rpc import RPCError
    from ncclient.transport.errors import AuthenticationError
    from ncclient.operations.errors import TimeoutExpiredError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


_DEVICE_CLI_CONNECTION = None
_DEVICE_NC_CONNECTION = None

netengine_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'use_ssl': dict(type='bool'),
    'validate_certs': dict(type='bool'),
    'timeout': dict(type='int'),
    'transport': dict(default='cli', choices=['cli']),
}
netengine_argument_spec = {
    'provider': dict(type='dict', options=netengine_provider_spec),
}
netengine_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'use_ssl': dict(removed_in_version=2.9, type='bool'),
    'validate_certs': dict(removed_in_version=2.9, type='bool'),
    'timeout': dict(removed_in_version=2.9, type='int'),
    'transport': dict(removed_in_version=2.9, choices=['cli']),
}
netengine_argument_spec.update(netengine_top_spec)


def check_args(module, warnings):
    pass


def load_params(module):
    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in netengine_argument_spec:
            if module.params.get(key) is None and value is not None:
                module.params[key] = value


def get_connection(module):
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
            cmd = item['command']

            rc, out, err = self.exec_command(cmd)

            try:
                out = self._module.from_json(out)
                err = self._module.from_json(err)
            except ValueError:
                out = str(out).strip()
                err = str(err).strip()

            if out is not None and str(out).strip() != '':
                responses.append(out)

            if err is not None and str(err).strip() != '':
                responses.append(err)

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
        response=dict()
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
    conn = get_connection(module)
    return conn.load_config(config)


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
