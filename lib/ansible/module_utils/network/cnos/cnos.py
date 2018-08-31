# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by
# Ansible still belong to the author of the module, and may assign their own
# license to the complete work.
#
# Copyright (C) 2017 Lenovo, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Contains utility methods
# Lenovo Networking

import time
import socket
import re
try:
    from ansible.module_utils.network.cnos import cnos_errorcodes
    from ansible.module_utils.network.cnos import cnos_devicerules
    HAS_LIB = True
except:
    HAS_LIB = False
from distutils.cmd import Command
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network.common.utils import to_list, EntityCollection
from ansible.module_utils.connection import Connection, exec_command
from ansible.module_utils.connection import ConnectionError

_DEVICE_CONFIGS = {}
_CONNECTION = None

cnos_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']),
                     no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']),
                        type='path'),
    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']),
                      type='bool'),
    'auth_pass': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS']),
                      no_log=True),
    'timeout': dict(type='int'),
    'context': dict(),
    'passwords': dict()
}

cnos_argument_spec = {
    'provider': dict(type='dict', options=cnos_provider_spec),
}

command_spec = {
    'command': dict(key=True),
    'prompt': dict(),
    'answer': dict(),
    'check_all': dict()
}


def get_provider_argspec():
    return cnos_provider_spec


def check_args(module, warnings):
    pass


def get_connection(module):
    global _CONNECTION
    if _CONNECTION:
        return _CONNECTION
    _CONNECTION = Connection(module._socket_path)

    context = None
    try:
        context = module.params['context']
    except KeyError:
        context = None

    if context:
        if context == 'system':
            command = 'changeto system'
        else:
            command = 'changeto context %s' % context
        _CONNECTION.get(command)

    return _CONNECTION


def get_config(module, flags=None):
    flags = [] if flags is None else flags

    passwords = None
    try:
        passwords = module.params['passwords']
    except KeyError:
        passwords = None
    if passwords:
        cmd = 'more system:running-config'
    else:
        cmd = 'display running-config '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        conn = get_connection(module)
        out = conn.get(cmd)
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg


def to_commands(module, commands):
    if not isinstance(commands, list):
        raise AssertionError('argument must be of type <list>')

    transform = EntityCollection(module, command_spec)
    commands = transform(commands)

    for index, item in enumerate(commands):
        if module.check_mode and not item['command'].startswith('show'):
            module.warn('only show commands are supported when using check '
                        'mode, not executing `%s`' % item['command'])

    return commands


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    connection.get('enable')
    commands = to_commands(module, to_list(commands))

    responses = list()

    for cmd in commands:
        out = connection.get(**cmd)
        responses.append(to_text(out, errors='surrogate_then_replace'))

    return responses


def run_cnos_commands(module, commands, check_rc=True):
    retVal = ''
    enter_config = {'command': 'configure terminal', 'prompt': None,
                    'answer': None}
    exit_config = {'command': 'end', 'prompt': None, 'answer': None}
    commands.insert(0, enter_config)
    commands.append(exit_config)
    for cmd in commands:
        retVal = retVal + '>> ' + cmd['command'] + '\n'
    try:
        responses = run_commands(module, commands, check_rc)
        for response in responses:
            retVal = retVal + '<< ' + response + '\n'
    except Exception as e:
        errMsg = ''
        if hasattr(e, 'message'):
            errMsg = e.message
        else:
            errMsg = str(e)
        # Exception in Exceptions
        if 'VLAN_ACCESS_MAP' in errMsg:
            return retVal + '<<' + errMsg + '\n'
        if 'confederation identifier' in errMsg:
            return retVal + '<<' + errMsg + '\n'
        # Add more here if required
        retVal = retVal + '<< ' + 'Error-101 ' + errMsg + '\n'
    return str(retVal)


def load_config(module, config):
    try:
        conn = get_connection(module)
        conn.get('enable')
        conn.edit_config(config)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def get_defaults_flag(module):
    rc, out, err = exec_command(module, 'display running-config ?')
    out = to_text(out, errors='surrogate_then_replace')

    commands = set()
    for line in out.splitlines():
        if line:
            commands.add(line.strip().split()[0])

    if 'all' in commands:
        return 'all'
    else:
        return 'full'


def interfaceConfig(module, prompt, functionality, answer):
    retVal = ""
    command = "interface "
    newPrompt = prompt
    interfaceArg1 = functionality
    interfaceArg2 = module.params['interfaceRange']
    interfaceArg3 = module.params['interfaceArg1']
    interfaceArg4 = module.params['interfaceArg2']
    interfaceArg5 = module.params['interfaceArg3']
    interfaceArg6 = module.params['interfaceArg4']
    interfaceArg7 = module.params['interfaceArg5']
    interfaceArg8 = module.params['interfaceArg6']
    interfaceArg9 = module.params['interfaceArg7']
    deviceType = module.params['deviceType']

    if(interfaceArg1 == "port-channel"):
        command = command + " " + interfaceArg1 + " " + interfaceArg2
        # debugOutput(command)
        value = checkSanityofVariable(
            deviceType, "portchannel_interface_value", interfaceArg2)
        if(value == "ok"):
            cmd = [{'command': command, 'prompt': None, 'answer': None}]
        else:
            value = checkSanityofVariable(
                deviceType, "portchannel_interface_range", interfaceArg2)
            if(value == "ok"):
                cmd = [{'command': command, 'prompt': None, 'answer': None}]
            else:
                value = checkSanityofVariable(
                    deviceType, "portchannel_interface_string", interfaceArg2)
                if(value == "ok"):
                    cmd = [{'command': command, 'prompt': None,
                            'answer': None}]
                else:
                    retVal = "Error-102"
                    return retVal
        retVal = retVal + interfaceLevel2Config(module, cmd, prompt, answer)
    elif(interfaceArg1 == "ethernet"):
        value = checkSanityofVariable(
            deviceType, "ethernet_interface_value", interfaceArg2)
        if(value == "ok"):
            command = command + interfaceArg1 + " 1/" + interfaceArg2
            cmd = [{'command': command, 'prompt': None, 'answer': None}]
        else:
            value = checkSanityofVariable(
                deviceType, "ethernet_interface_range", interfaceArg2)
            if(value == "ok"):
                command = command + interfaceArg1 + " 1/" + interfaceArg2
                cmd = [{'command': command, 'prompt': None, 'answer': None}]
            else:
                value = checkSanityofVariable(
                    deviceType, "ethernet_interface_string", interfaceArg2)
                if(value == "ok"):
                    command = command + interfaceArg1 + " " + interfaceArg2
                    cmd = [{'command': command, 'prompt': None,
                            'answer': None}]
                else:
                    retVal = "Error-102"
                    return retVal

        retVal = retVal + interfaceLevel2Config(module, cmd, prompt, answer)
    elif(interfaceArg1 == "loopback"):
        value = checkSanityofVariable(
            deviceType, "loopback_interface_value", interfaceArg2)
        if(value == "ok"):
            command = command + interfaceArg1 + " " + interfaceArg2
            cmd = [{'command': command, 'prompt': None, 'answer': None}]
        else:
            retVal = "Error-102"
            return retVal
        retVal = retVal + interfaceLevel2Config(module, cmd, prompt, answer)
    elif(interfaceArg1 == "mgmt"):
        value = checkSanityofVariable(
            deviceType, "mgmt_interface_value", interfaceArg2)
        if(value == "ok"):
            command = command + interfaceArg1 + " " + interfaceArg2
            cmd = [{'command': command, 'prompt': None, 'answer': None}]
        else:
            retVal = "Error-102"
            return retVal
        retVal = retVal + interfaceLevel2Config(module, cmd, prompt, answer)
    elif(interfaceArg1 == "vlan"):
        value = checkSanityofVariable(
            deviceType, "vlan_interface_value", interfaceArg2)
        if(value == "ok"):
            command = command + interfaceArg1 + " " + interfaceArg2
            cmd = [{'command': command, 'prompt': None, 'answer': None}]
        else:
            retVal = "Error-102"
            return retVal
        retVal = retVal + interfaceLevel2Config(module, cmd, prompt, answer)
    else:
        retVal = "Error-102"

    return retVal
# EOM


def interfaceLevel2Config(module, cmd, prompt, answer):
    retVal = ""
    command = ""
    interfaceL2Arg1 = module.params['interfaceArg1']
    interfaceL2Arg2 = module.params['interfaceArg2']
    interfaceL2Arg3 = module.params['interfaceArg3']
    interfaceL2Arg4 = module.params['interfaceArg4']
    interfaceL2Arg5 = module.params['interfaceArg5']
    interfaceL2Arg6 = module.params['interfaceArg6']
    interfaceL2Arg7 = module.params['interfaceArg7']
    deviceType = module.params['deviceType']

    if(interfaceL2Arg1 == "channel-group"):
        # debugOutput("channel-group")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "aggregation_group_no", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " mode "
            value = checkSanityofVariable(
                deviceType, "aggregation_group_mode", interfaceL2Arg3)
            if(value == "ok"):
                command = command + interfaceL2Arg3
            else:
                retVal = "Error-200"
                return retVal
        else:
            retVal = "Error-201"
            return retVal

    elif (interfaceL2Arg1 == "bfd"):
        # debugOutput("bfd")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "bfd_options", interfaceL2Arg2)
        if(value == "ok"):
            if(interfaceL2Arg2 == "echo"):
                command = command + interfaceL2Arg2
            elif(interfaceL2Arg2 == "interval"):
                command = command + interfaceL2Arg2 + " "
                value = checkSanityofVariable(
                    deviceType, "bfd_interval", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3
                    value = checkSanityofVariable(
                        deviceType, "bfd_minrx", interfaceL2Arg4)
                    if(value == "ok"):
                        command = command + " minrx " + interfaceL2Arg4
                        value = checkSanityofVariable(
                            deviceType, "bfd_ multiplier", interfaceL2Arg5)
                        if(value == "ok"):
                            command = command + " multiplier " + \
                                interfaceL2Arg5
                        else:
                            retVal = "Error-236"
                            return retVal
                    else:
                        retVal = "Error-235"
                        return retVal
                else:
                    retVal = "Error-234"
                    return retVal
            elif(interfaceL2Arg2 == "authentication"):
                command = command + interfaceL2Arg2 + " "
                value = checkSanityofVariable(
                    deviceType, "bfd_auth_options", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " "
                    if((interfaceL2Arg3 == "keyed-md5") or
                        (interfaceL2Arg3 == "keyed-sha1") or
                        (interfaceL2Arg3 == "meticulous-keyed-md5") or
                        (interfaceL2Arg3 == "meticulous-keyed-sha1") or
                            (interfaceL2Arg3 == "simple")):
                        value = checkSanityofVariable(
                            deviceType, "bfd_key_options", interfaceL2Arg4)
                        if(value == "ok"):
                            command = command + interfaceL2Arg4 + " "
                            if(interfaceL2Arg4 == "key-chain"):
                                value = checkSanityofVariable(
                                    deviceType, "bfd_key_chain",
                                    interfaceL2Arg5)
                                if(value == "ok"):
                                    command = command + interfaceL2Arg5
                                else:
                                    retVal = "Error-237"
                                    return retVal
                            elif(interfaceL2Arg4 == "key-id"):
                                value = checkSanityofVariable(
                                    deviceType, "bfd_key_id", interfaceL2Arg5)
                                if(value == "ok"):
                                    command = command + interfaceL2Arg5
                                    command = command + " key "
                                    value = checkSanityofVariable(
                                        deviceType, "bfd_key_name",
                                        interfaceL2Arg6)
                                    if(value == "ok"):
                                        command = command + interfaceL2Arg6
                                    else:
                                        retVal = "Error-238"
                                        return retVal
                                else:
                                    retVal = "Error-239"
                                    return retVal
                        else:
                            retVal = "Error-240"
                            return retVal
                else:
                    retVal = "Error-241"
                    return retVal

            elif(interfaceL2Arg2 == "ipv4" or interfaceL2Arg2 == "ipv6"):
                command = command + interfaceL2Arg2 + " "
                value = checkSanityofVariable(
                    deviceType, "bfd_ipv4_options", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " "
                    if(interfaceL2Arg3 == "authentication"):
                        value = checkSanityofVariable(
                            deviceType, "bfd_auth_options", interfaceL2Arg4)
                        if(value == "ok"):
                            command = command + interfaceL2Arg4 + " "
                            if((interfaceL2Arg4 == "keyed-md5") or
                                (interfaceL2Arg4 == "keyed-sha1") or
                                (interfaceL2Arg4 == "meticulous-keyed-md5") or
                                (interfaceL2Arg4 == "meticulous-keyed-sha1") or
                                    (interfaceL2Arg4 == "simple")):
                                value = checkSanityofVariable(
                                    deviceType, "bfd_key_options",
                                    interfaceL2Arg5)
                                if(value == "ok"):
                                    command = command + interfaceL2Arg5 + " "
                                    if(interfaceL2Arg5 == "key-chain"):
                                        value = checkSanityofVariable(
                                            deviceType, "bfd_key_chain",
                                            interfaceL2Arg6)
                                        if(value == "ok"):
                                            command = command + interfaceL2Arg6
                                        else:
                                            retVal = "Error-237"
                                            return retVal
                                    elif(interfaceL2Arg5 == "key-id"):
                                        value = checkSanityofVariable(
                                            deviceType, "bfd_key_id",
                                            interfaceL2Arg6)
                                        if(value == "ok"):
                                            command = command + \
                                                interfaceL2Arg6 + " key "
                                            value = checkSanityofVariable(
                                                deviceType, "bfd_key_name",
                                                interfaceL2Arg7)
                                            if(value == "ok"):
                                                command = command + \
                                                    interfaceL2Arg7
                                            else:
                                                retVal = "Error-238"
                                                return retVal
                                        else:
                                            retVal = "Error-239"
                                            return retVal

                                    else:
                                        retVal = "Error-240"
                                        return retVal
                                else:
                                    retVal = "Error-240"
                                    return retVal
                        else:
                            retVal = "Error-241"
                            return retVal
                    elif(interfaceL2Arg3 == "echo"):
                        command = command + interfaceL2Arg3
                    elif(interfaceL2Arg3 == "interval"):
                        command = command + interfaceL2Arg3 + " "
                        value = checkSanityofVariable(
                            deviceType, "bfd_interval", interfaceL2Arg4)
                        if(value == "ok"):
                            command = command + interfaceL2Arg4
                            value = checkSanityofVariable(
                                deviceType, "bfd_minrx", interfaceL2Arg5)
                            if(value == "ok"):
                                command = command + " minrx " + interfaceL2Arg5
                                value = checkSanityofVariable(
                                    deviceType, "bfd_ multiplier",
                                    interfaceL2Arg6)
                                if(value == "ok"):
                                    command = command + " multiplier " + \
                                        interfaceL2Arg6
                                else:
                                    retVal = "Error-236"
                                    return retVal
                            else:
                                retVal = "Error-235"
                                return retVal
                        else:
                            retVal = "Error-234"
                            return retVal
                else:
                    command = command.strip()  # None is taken care here

            elif(interfaceL2Arg2 == "neighbor"):
                command = command + interfaceL2Arg2 + " src-ip "
                value = checkSanityofVariable(
                    deviceType, "bfd_neighbor_ip", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " dest-ip "
                    value = checkSanityofVariable(
                        deviceType, "bfd_neighbor_ip", interfaceL2Arg4)
                    if(value == "ok"):
                        command = command + interfaceL2Arg4 + " "
                        if(interfaceL2Arg5 is not None):
                            value = checkSanityofVariable(
                                deviceType, "bfd_neighbor_options",
                                interfaceL2Arg5)
                            if(value == "ok"):
                                command = command + interfaceL2Arg5 + " "
                                if(interfaceL2Arg6 is not None):
                                    if((interfaceL2Arg6 == "admin-down") or
                                            (interfaceL2Arg6 ==
                                                "non-persistent")):
                                        command = command + \
                                            interfaceL2Arg6 + " "
                                        if((interfaceL2Arg7 is not None) and
                                                (interfaceL2Arg7 ==
                                                    "admin-down")):
                                            command = command + interfaceL2Arg7
                                        else:
                                            retVal = "Error-277"
                                            return retVal
                                    else:
                                        retVal = "Error-277"
                                        return retVal
                                # Else is not there are its optionsal
                            # Else is not there as this is optional
                        # Else is not there as this is optional
                    else:
                        retVal = "Error-242"
                        return retVal
                else:
                    retVal = "Error-243"
                    return retVal

            else:
                retVal = "Error-205"
                return retVal
        else:
            retVal = "Error-205"
            return retVal

    elif (interfaceL2Arg1 == "switchport"):
        # debugOutput("switchport")
        command = interfaceL2Arg1 + " "
        if(interfaceL2Arg2 is None):
            command = command.strip()
        elif(interfaceL2Arg2 == "access"):
            command = command + interfaceL2Arg2 + " vlan "
            value = checkSanityofVariable(
                deviceType, "bfd_access_vlan", interfaceL2Arg3)
            if(value == "ok"):
                command = command + interfaceL2Arg3
            else:
                retVal = "Error-202"
                return retVal
        elif(interfaceL2Arg2 == "mode"):
            command = command + interfaceL2Arg2 + " "
            value = checkSanityofVariable(
                deviceType, "bfd_bridgeport_mode", interfaceL2Arg3)
            if(value == "ok"):
                command = command + interfaceL2Arg3
            else:
                retVal = "Error-203"
                return retVal
        elif(interfaceL2Arg2 == "trunk"):
            command = command + interfaceL2Arg2 + " "
            value = checkSanityofVariable(
                deviceType, "trunk_options", interfaceL2Arg3)
            if(value == "ok"):
                command = command + interfaceL2Arg3 + " "
                if((interfaceL2Arg3 == "allowed") or
                        (interfaceL2Arg3 == "native")):
                    command = command + "vlan "  # Only permiting one vlan id
                    if(interfaceL2Arg4 == "all" or interfaceL2Arg4 == "none"):
                        command = command + interfaceL2Arg4
                    elif(interfaceL2Arg4 == "add" or
                            interfaceL2Arg4 == "remove" or
                            interfaceL2Arg4 == "none"):
                        command = command + interfaceL2Arg4 + " "
                        value = checkSanityofVariable(
                            deviceType, "bfd_access_vlan", interfaceL2Arg5)
                        if(value == "ok"):
                            command = command + interfaceL2Arg5
                        else:
                            retVal = "Error-202"
                            return retVal
                    else:
                        value = checkSanityofVariable(
                            deviceType, "bfd_access_vlan", interfaceL2Arg4)
                        if(value == "ok"):
                            command = command + interfaceL2Arg4
                        else:
                            retVal = "Error-202"
                            return retVal
                else:
                    retVal = "Error-204"
                    return retVal
            else:
                retVal = "Error-204"
                return retVal
        else:
            retVal = "Error-205"
            return retVal

    elif (interfaceL2Arg1 == "description"):
        # debugOutput("description")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "portCh_description", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            retVal = "Error-206"
            return retVal
    elif (interfaceL2Arg1 == "duplex"):
        # debugOutput("duplex")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "duplex_option", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            retVal = "Error-207"
            return retVal
    elif (interfaceL2Arg1 == "flowcontrol"):
        # debugOutput("flowcontrol")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "flowcontrol_options", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " "
            if(interfaceL2Arg3 == "on" or interfaceL2Arg3 == "off"):
                command = command + interfaceL2Arg3
            else:
                retVal = "Error-208"
                return retVal
        else:
            retVal = "Error-209"
            return retVal
    elif (interfaceL2Arg1 == "ip"):
        # debugOutput("ip")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "portchannel_ip_options", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " "
            if(interfaceL2Arg2 == "access-group"):
                value = checkSanityofVariable(
                    deviceType, "accessgroup_name", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " "
                    if(interfaceL2Arg4 == "in" or interfaceL2Arg4 == "out"):
                        command = command + interfaceL2Arg4
                    else:
                        retVal = "Error-245"
                        return retVal
                else:
                    retVal = "Error-246"
                    return retVal
            elif(interfaceL2Arg2 == "address"):
                if(interfaceL2Arg3 == "dhcp"):
                    command = command + interfaceL2Arg3
                elif(interfaceL2Arg3 is not None):
                    value = checkSanityofVariable(
                        deviceType, "portchannel_ipv4", interfaceL2Arg3)
                    if(value == "ok"):
                        command = command + interfaceL2Arg3 + " "
                        value = checkSanityofVariable(
                            deviceType, "portchannel_ipv4", interfaceL2Arg4)
                        if(value == "ok"):
                            command = command + interfaceL2Arg4 + " "
                            if(interfaceL2Arg5 == "secondary"):
                                command = command + interfaceL2Arg5
                            else:
                                retVal = "Error-278"
                                return retVal
                        else:
                            retVal = "Error-279"
                            return retVal
                    else:
                        value = checkSanityofVariable(
                            deviceType, "portchannel_ipv4_mask",
                            interfaceL2Arg3)
                        if(value == "ok"):
                            command = command + interfaceL2Arg3 + " "
                            if(interfaceL2Arg4 == "secondary"):
                                command = command + interfaceL2Arg4
                            elif(interfaceL2Arg4 is None):
                                command = command.strip()
                            else:
                                retVal = "Error-278"
                                return retVal
                        else:
                            retVal = "Error-279"
                            return retVal

            elif(interfaceL2Arg2 == "arp"):
                value = checkSanityofVariable(
                    deviceType, "arp_ipaddress", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " "
                    value = checkSanityofVariable(
                        deviceType, "arp_macaddress", interfaceL2Arg4)
                    if(value == "ok"):
                        command = command + interfaceL2Arg4 + " "
                    else:
                        retVal = "Error-247"
                        return retVal
                elif(interfaceL2Arg3 == "timeout"):
                    command = command + interfaceL2Arg3 + " "
                    value = checkSanityofVariable(
                        deviceType, "arp_timeout_value", interfaceL2Arg4)
                    if(value == "ok"):
                        command = command + interfaceL2Arg4 + " "
                    else:
                        retVal = "Error-248"
                        return retVal
                else:
                    retVal = "Error-249"
                    return retVal
            elif(interfaceL2Arg2 == "dhcp"):
                if(interfaceL2Arg3 == "client"):
                    command = command + interfaceL2Arg3 + " "
                    if(interfaceL2Arg4 == "class-id"):
                        command = command + interfaceL2Arg3 + " "
                        if(interfaceL2Arg4 is not None):
                            command = command + interfaceL2Arg4
                    elif(interfaceL2Arg4 == "request"):
                        command = command + interfaceL2Arg4 + " "
                        if(interfaceL2Arg5 == "bootfile-name" or
                                interfaceL2Arg5 == "host-name" or
                                interfaceL2Arg5 == "log-server" or
                                interfaceL2Arg5 == "tftp-server-name"):
                            command = command + interfaceL2Arg5 + " "
                        else:
                            retVal = "Error-250"
                            return retVal
                    else:
                        retVal = "Error-251"
                        return retVal
                elif(interfaceL2Arg3 == "relay"):
                    command = command + interfaceL2Arg3 + " address "
                    value = checkSanityofVariable(
                        deviceType, "relay_ipaddress", interfaceL2Arg4)
                    if(value == "ok"):
                        command = command + interfaceL2Arg4
                    else:
                        retVal = "Error-252"
                        return retVal
                else:
                    retVal = "Error-253"
                    return retVal
            elif(interfaceL2Arg2 == "ospf"):
                value = checkSanityofVariable(
                    deviceType, "ip_ospf_options", interfaceL2Arg3)
                if(value == "ok"):
                    retVal = "Error-102"
                    return retVal
                else:
                    retVal = "Error-254"
                    return retVal

            elif(interfaceL2Arg2 == "port"):
                command = command + "access-group "
                value = checkSanityofVariable(
                    deviceType, "accessgroup_name", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " in"
                else:
                    retVal = "Error-246"
                    return retVal
            elif(interfaceL2Arg2 == "port-unreachable"):
                command = command + interfaceL2Arg2

            elif(interfaceL2Arg2 == "redirects"):
                command = command + interfaceL2Arg2

            elif(interfaceL2Arg2 == "router"):
                command = command + interfaceL2Arg2 + " 0 "
                if(interfaceL2Arg3 == "area" or
                        interfaceL2Arg3 == "multi-area"):
                    command = command + interfaceL2Arg3
                    value = checkSanityofVariable(
                        deviceType, "ospf_id_decimal_value", interfaceL2Arg4)
                    if(value == "ok"):
                        command = command + interfaceL2Arg4
                    else:
                        value = checkSanityofVariable(
                            deviceType, "ospf_id_ipaddres_value",
                            interfaceL2Arg4)
                        if(value == "ok"):
                            command = command + interfaceL2Arg4
                        else:
                            retVal = "Error-255"
                            return retVal
                else:
                    retVal = "Error-256"
                    return retVal

            elif(interfaceL2Arg2 == "unreachables"):
                command = command + interfaceL2Arg2
            else:
                retVal = "Error-244"
                return retVal
        else:
            retVal = "Error-244"
            return retVal

    elif (interfaceL2Arg1 == "ipv6"):
        # debugOutput("ipv6")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "portchannel_ipv6_options", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " "
            if(interfaceL2Arg2 == "address"):
                if(interfaceL2Arg3 == "dhcp"):
                    command = command + interfaceL2Arg3
                else:
                    value = checkSanityofVariable(
                        deviceType, "portchannel_ipv6_address",
                        interfaceL2Arg3)
                    if(value == "ok"):
                        command = command + interfaceL2Arg3 + " "
                        if(interfaceL2Arg4 == "anycast" or
                                interfaceL2Arg4 == "secondary"):
                            command = command + interfaceL2Arg4
                        else:
                            retVal = "Error-276"
                            return retVal
                    else:
                        retVal = "Error-275"
                        return retVal
            elif(interfaceL2Arg2 == "dhcp"):
                value = checkSanityofVariable(
                    deviceType, "portchannel_ipv6_dhcp", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + "relay address " + interfaceL2Arg3
                    if(interfaceL2Arg4 is not None):
                        if(interfaceL2Arg4 == "ethernet"):
                            value = checkSanityofVariable(
                                deviceType, "portchannel_ipv6_dhcp_ethernet",
                                interfaceL2Arg4)
                            if(value == "ok"):
                                command = command + " interface ethernet " + \
                                    interfaceL2Arg4
                            else:
                                retVal = "Error-271"
                                return retVal
                        elif(interfaceL2Arg4 == "vlan"):
                            value = checkSanityofVariable(
                                deviceType, "portchannel_ipv6_dhcp_vlan",
                                interfaceL2Arg4)
                            if(value == "ok"):
                                command = command + " interface vlan " + \
                                    interfaceL2Arg4
                            else:
                                retVal = "Error-272"
                                return retVal
                        else:
                            retVal = "Error-270"
                            return retVal
                else:
                    retVal = "Error-269"
                    return retVal

            elif(interfaceL2Arg2 == "link-local"):
                value = checkSanityofVariable(
                    deviceType, "portchannel_ipv6_linklocal", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-273"
                    return retVal
            elif(interfaceL2Arg2 == "nd"):
                retVal = "Error-102"
                return retVal
            elif(interfaceL2Arg2 == "neighbor"):
                value = checkSanityofVariable(
                    deviceType, "portchannel_ipv6_neighbor_address",
                    interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " "
                    value = checkSanityofVariable(
                        deviceType, "portchannel_ipv6_neighbor_mac",
                        interfaceL2Arg4)
                    if(value == "ok"):
                        command = command + interfaceL2Arg4
                    else:
                        retVal = "Error-267"
                        return retVal
                else:
                    retVal = "Error-268"
                    return retVal
            else:
                retVal = "Error-266"
                return retVal
        else:
            retVal = "Error-102"
            return retVal

    elif (interfaceL2Arg1 == "lacp"):
        # debugOutput("lacp")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "lacp_options", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " "
            if(interfaceL2Arg2 == "port-priority"):
                value = checkSanityofVariable(
                    deviceType, "port_priority", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-210"
                    return retVal
            elif(interfaceL2Arg2 == "suspend-individual"):
                command = command + interfaceL2Arg3
            elif(interfaceL2Arg2 == "timeout"):
                command = command + interfaceL2Arg2 + " "
                if(interfaceL2Arg3 == "long" or interfaceL2Arg3 == "short"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-211"
                    return retVal
            else:
                retVal = "Error-212"
                return retVal
        else:
            retVal = "Error-212"
            return retVal

    elif (interfaceL2Arg1 == "lldp"):
        # debugOutput("lldp")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "lldp_options", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " "
            if(interfaceL2Arg2 == "receive" or
                    interfaceL2Arg2 == "trap-notification" or
                    interfaceL2Arg2 == "transmit"):
                command = command.strip()
            elif(interfaceL2Arg2 == "tlv-select"):
                value = checkSanityofVariable(
                    deviceType, "lldp_tlv_options", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-213"
                    return retVal
            else:
                retVal = "Error-214"
                return retVal
        else:
            retVal = "Error-214"
            return retVal

    elif (interfaceL2Arg1 == "load-interval"):
        # debugOutput("load-interval")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "load_interval_delay", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            if(interfaceL2Arg2 == "counter"):
                command = command + interfaceL2Arg2 + " "
                value = checkSanityofVariable(
                    deviceType, "load_interval_counter", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " "
                    value = checkSanityofVariable(
                        deviceType, "load_interval_delay", interfaceL2Arg4)
                    if(value == "ok"):
                        command = command + interfaceL2Arg4
                    else:
                        retVal = "Error-215"
                        return retVal
                else:
                    retVal = "Error-216"
                    return retVal
            else:
                retVal = "Error-217"
                return retVal

    elif (interfaceL2Arg1 == "mac"):
        # debugOutput("mac")
        command = interfaceL2Arg1 + " port access-group "
        value = checkSanityofVariable(
            deviceType, "mac_accessgroup_name", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            retVal = "Error-218"
            return retVal
    elif (interfaceL2Arg1 == "mac-address"):
        # debugOutput("mac-address")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "mac_address", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            retVal = "Error-219"
            return retVal

    elif (interfaceL2Arg1 == "mac-learn"):
        # debugOutput("mac-learn")
        command = interfaceL2Arg1 + " disable"

    elif (interfaceL2Arg1 == "microburst-detection"):
        # debugOutput("microburst-detection")
        command = interfaceL2Arg1 + " enable threshold "
        value = checkSanityofVariable(
            deviceType, "microburst_threshold", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            retVal = "Error-220"
            return retVal

    elif (interfaceL2Arg1 == "mtu"):
        # debugOutput("mtu")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(deviceType, "mtu_value", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            retVal = "Error-221"
            return retVal

    elif (interfaceL2Arg1 == "service"):
        # debugOutput("service")
        command = interfaceL2Arg1 + " instance "
        value = checkSanityofVariable(
            deviceType, "service_instance", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            retVal = "Error-222"
            return retVal

    elif (interfaceL2Arg1 == "service-policy"):
        # debugOutput("service-policy")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "service_policy_options", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " "
            if(interfaceL2Arg2 == "input" or interfaceL2Arg2 == "output"):
                value = checkSanityofVariable(
                    deviceType, "service_policy_name", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-223"
                    return retVal
            elif(interfaceL2Arg2 == "copp-system-policy"):
                command = command + "class all"
            elif(interfaceL2Arg2 == "type" and interfaceL2Arg3 == "qos"):
                command = command + interfaceL2Arg3 + " "
                if(interfaceL2Arg4 == "input" or interfaceL2Arg4 == "output"):
                    value = checkSanityofVariable(
                        deviceType, "service_policy_name", interfaceL2Arg5)
                    if(value == "ok"):
                        command = command + interfaceL2Arg5
                else:
                    retVal = "Error-223"
                    return retVal
            elif(interfaceL2Arg2 == "type" and interfaceL2Arg3 == "queuing"):
                command = command + interfaceL2Arg3 + " "
                if(interfaceL2Arg4 == "input" or interfaceL2Arg4 == "output"):
                    value = checkSanityofVariable(
                        deviceType, "service_policy_name", interfaceL2Arg5)
                    if(value == "ok"):
                        command = command + interfaceL2Arg5
                else:
                    retVal = "Error-223"
                    return retVal
            else:
                retVal = "Error-224"
                return retVal

    elif (interfaceL2Arg1 == "shutdown"):
        # debugOutput("shutdown")
        command = interfaceL2Arg1

    elif (interfaceL2Arg1 == "no shutdown"):
        # debugOutput("no shutdown")
        command = interfaceL2Arg1

    elif (interfaceL2Arg1 == "snmp"):
        # debugOutput("snmp")
        command = interfaceL2Arg1 + "  trap link-status "

    elif (interfaceL2Arg1 == "spanning-tree"):
        # debugOutput("spanning-tree")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "spanning_tree_options", interfaceL2Arg2)
        if(value == "ok"):
            if(interfaceL2Arg2 == "bpdufilter"):
                command = command + interfaceL2Arg2 + " "
                if(interfaceL2Arg3 == "enable" or
                        interfaceL2Arg3 == "disable"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-257"
                    return retVal
            elif(interfaceL2Arg2 == "bpduguard"):
                command = command + interfaceL2Arg2 + " "
                if(interfaceL2Arg3 == "enable" or
                        interfaceL2Arg3 == "disable"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-258"
                    return retVal
            elif(interfaceL2Arg2 == "cost"):
                command = command + interfaceL2Arg2 + " "
                value = checkSanityofVariable(
                    deviceType, "spanning_tree_cost", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3
                elif(interfaceL2Arg3 == "auto"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-259"
                    return retVal
            elif(interfaceL2Arg2 == "disable" or interfaceL2Arg2 == "enable"):
                command = command + interfaceL2Arg2 + " "
            elif(interfaceL2Arg2 == "guard"):
                command = command + interfaceL2Arg2 + " "
                if(interfaceL2Arg3 == "loop" or interfaceL2Arg3 == "root"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-260"
                    return retVal
            elif(interfaceL2Arg2 == "link-type"):
                command = command + interfaceL2Arg2 + " "
                if(interfaceL2Arg3 == "auto" or
                        interfaceL2Arg3 == "point-to-point" or
                        interfaceL2Arg3 == "shared"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-261"
                    return retVal

            elif(interfaceL2Arg2 == "mst"):
                command = command + interfaceL2Arg2 + " "
                value = checkSanityofVariable(
                    deviceType, "spanning_tree_interfacerange",
                    interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3 + " "
                    if(interfaceL2Arg4 == "cost"):
                        command = command + interfaceL2Arg4 + " "
                        value = checkSanityofVariable(
                            deviceType, "spanning_tree_cost", interfaceL2Arg5)
                        if(value == "ok"):
                            command = command + interfaceL2Arg5
                        elif(interfaceL2Arg5 == "auto"):
                            command = command + interfaceL2Arg5
                        else:
                            retVal = "Error-259"
                            return retVal
                    elif(interfaceL2Arg4 == "port-priority"):
                        command = command + interfaceL2Arg4 + " "
                        value = checkSanityofVariable(
                            deviceType, "spanning_tree_portpriority",
                            interfaceL2Arg5)
                        if(value == "ok"):
                            command = command + interfaceL2Arg5
                        else:
                            retVal = "Error-259"
                            return retVal
                    else:
                        retVal = "Error-259"
                        return retVal
                else:
                    retVal = "Error-263"
                    return retVal
            elif(interfaceL2Arg2 == "port"):
                command = command + interfaceL2Arg2 + " type edge"
            elif(interfaceL2Arg2 == "port-priority"):
                command = command + interfaceL2Arg2 + " "
                value = checkSanityofVariable(
                    deviceType, "spanning_tree_portpriority", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3
                else:
                    retVal = "Error-264"
                    return retVal

            elif(interfaceL2Arg2 == "vlan"):
                command = command + interfaceL2Arg2 + " "
                value = checkSanityofVariable(
                    deviceType, "vlan_id_range", interfaceL2Arg3)
                if(value == "ok"):
                    command = command + interfaceL2Arg3
                    if(interfaceL2Arg4 == "cost"):
                        command = command + interfaceL2Arg4 + " "
                        value = checkSanityofVariable(
                            deviceType, "spanning_tree_cost", interfaceL2Arg5)
                        if(value == "ok"):
                            command = command + interfaceL2Arg5
                        elif(interfaceL2Arg5 == "auto"):
                            command = command + interfaceL2Arg5
                        else:
                            retVal = "Error-263"
                            return retVal
                    elif(interfaceL2Arg4 == "port-priority"):
                        command = command + interfaceL2Arg4 + " "
                        value = checkSanityofVariable(
                            deviceType, "spanning_tree_portpriority",
                            interfaceL2Arg5)
                        if(value == "ok"):
                            command = command + interfaceL2Arg5
                        else:
                            retVal = "Error-264"
                            return retVal
                    else:
                        retVal = "Error-264"
                        return retVal
                else:
                    retVal = "Error-134"
                    return retVal
            else:
                retVal = "Error-263"
                return retVal
    elif (interfaceL2Arg1 == "speed"):
        # debugOutput("speed")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "interface_speed", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
        else:
            retVal = "Error-225"
            return retVal
    elif (interfaceL2Arg1 == "storm-control"):
        # debugOutput("storm-control")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(
            deviceType, "stormcontrol_options", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " level "
            value = checkSanityofVariable(
                deviceType, "stormcontrol_level", interfaceL2Arg3)
            if(value == "ok"):
                command = command + interfaceL2Arg3

            else:
                retVal = "Error-226"
                return retVal
        else:
            retVal = "Error-227"
            return retVal

    elif (interfaceL2Arg1 == "vlan"):
        # debugOutput("vlan")
        command = interfaceL2Arg1 + " dot1q tag native "
        value = checkSanityofVariable(
            deviceType, "portchannel_dot1q_tag", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2
            if(interfaceL2Arg2 == "egress-only"):
                command = command + " enable"
        else:
            retVal = "Error-228"
            return retVal

    elif (interfaceL2Arg1 == "vrrp"):
        # debugOutput("vrrp")
        command = interfaceL2Arg1 + " "
        value = checkSanityofVariable(deviceType, "vrrp_id", interfaceL2Arg2)
        if(value == "ok"):
            command = command + interfaceL2Arg2 + " "
            if(interfaceL2Arg3 == "ipv6"):
                command = command + interfaceL2Arg3 + " "
            elif(interfaceL2Arg3 is None):
                command = command + ""
            else:
                retVal = "Error-229"
                return retVal
        else:
            retVal = "Error-230"
            return retVal

    else:
        retVal = "Error-233"
        return retVal

    # debugOutput(command)
    inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
    cmd.extend(inner_cmd)
    retVal = retVal + str(run_cnos_commands(module, cmd))
    # Come back to config mode
    if((prompt == "(config-if)#") or (prompt == "(config-if-range)#")):
        command = "exit"
        # debugOutput(command)
        cmd = [{'command': command, 'prompt': None, 'answer': None}]
        # retVal = retVal + str(run_cnos_commands(module, cmd))
    return retVal
# EOM


# Method Method for enter enable mode
#


def enterEnableModeForDevice(enablePassword, timeout, obj):
    command = "enable\n"
    pwdPrompt = "password:"
    # debugOutput(enablePassword)
    # debugOutput('\n')
    obj.settimeout(int(timeout))
    # Executing enable
    obj.send(command)
    flag = False
    retVal = ""
    count = 5
    while not flag:
        # If wait time is execeeded.
        if(count == 0):
            flag = True
        else:
            count = count - 1
        # A delay of one second
        time.sleep(1)
        try:
            buffByte = obj.recv(9999)
            buff = buffByte.decode()
            retVal = retVal + buff
            # debugOutput(buff)
            gotit = buff.find(pwdPrompt)
            if(gotit != -1):
                time.sleep(1)
                if(enablePassword is None or enablePassword == ""):
                    return "\n Error-106"
                obj.send(enablePassword)
                obj.send("\r")
                obj.send("\n")
                time.sleep(1)
                innerBuffByte = obj.recv(9999)
                innerBuff = innerBuffByte.decode()
                retVal = retVal + innerBuff
                # debugOutput(innerBuff)
                innerGotit = innerBuff.find("#")
                if(innerGotit != -1):
                    return retVal
            else:
                gotit = buff.find("#")
                if(gotit != -1):
                    return retVal
        except:
            retVal = retVal + "\n Error-101"
            flag = True
    if(retVal == ""):
        retVal = "\n Error-101"
    return retVal
# EOM

# Method for device response than time delay
#


def waitForDeviceResponse(command, prompt, timeout, obj):
    obj.settimeout(int(timeout))
    obj.send(command)
    flag = False
    retVal = ""
    while not flag:
        time.sleep(1)
        try:
            buffByte = obj.recv(9999)
            buff = buffByte.decode()
            retVal = retVal + buff
            # debugOutput(retVal)
            gotit = buff.find(prompt)
            if(gotit != -1):
                flag = True
        except:
            # debugOutput(prompt)
            if prompt == "(yes/no)?":
                retVal = retVal
            elif prompt == "Password:":
                retVal = retVal
            else:
                retVal = retVal + "\n Error-101"
            flag = True
    return retVal
# EOM


def checkOutputForError(output):
    retVal = ""
    index = output.lower().find('error')
    startIndex = index + 6
    if(index == -1):
        index = output.lower().find('invalid')
        startIndex = index + 8
        if(index == -1):
            index = output.lower().find('cannot be enabled in l2 interface')
            startIndex = index + 34
            if(index == -1):
                index = output.lower().find('incorrect')
                startIndex = index + 10
                if(index == -1):
                    index = output.lower().find('failure')
                    startIndex = index + 8
                    if(index == -1):
                        return None

    endIndex = startIndex + 3
    errorCode = output[startIndex:endIndex]
    result = errorCode.isdigit()
    if(result is not True):
        return "Device returned an Error. Please check Results for more \
        information"

    errorFile = "dictionary/ErrorCodes.lvo"
    try:
        # with open(errorFile, 'r') as f:
        f = open(errorFile, 'r')
        for line in f:
            if('=' in line):
                data = line.split('=')
                if(data[0].strip() == errorCode):
                    errorString = data[1].strip()
                    return errorString
    except Exception:
        errorString = cnos_errorcodes.getErrorString(errorCode)
        errorString = errorString.strip()
        return errorString
    return "Error Code Not Found"
# EOM


def checkSanityofVariable(deviceType, variableId, variableValue):
    retVal = ""
    ruleFile = "dictionary/" + deviceType + "_rules.lvo"
    ruleString = getRuleStringForVariable(deviceType, ruleFile, variableId)
    retVal = validateValueAgainstRule(ruleString, variableValue)
    return retVal
# EOM


def getRuleStringForVariable(deviceType, ruleFile, variableId):
    retVal = ""
    try:
        # with open(ruleFile, 'r') as f:
        f = open(ruleFile, 'r')
        for line in f:
            # debugOutput(line)
            if(':' in line):
                data = line.split(':')
                # debugOutput(data[0])
                if(data[0].strip() == variableId):
                    retVal = line
    except Exception:
        ruleString = cnos_devicerules.getRuleString(deviceType, variableId)
        retVal = ruleString.strip()
    return retVal
# EOM


def validateValueAgainstRule(ruleString, variableValue):

    retVal = ""
    if(ruleString == ""):
        return 1
    rules = ruleString.split(':')
    variableType = rules[1].strip()
    varRange = rules[2].strip()
    if(variableType == "INTEGER"):
        result = checkInteger(variableValue)
        if(result is True):
            return "ok"
        else:
            return "Error-111"
    elif(variableType == "FLOAT"):
        result = checkFloat(variableValue)
        if(result is True):
            return "ok"
        else:
            return "Error-112"

    elif(variableType == "INTEGER_VALUE"):
        int_range = varRange.split('-')
        r = range(int(int_range[0].strip()), int(int_range[1].strip()))
        if(checkInteger(variableValue) is not True):
            return "Error-111"
        result = int(variableValue) in r
        if(result is True):
            return "ok"
        else:
            return "Error-113"

    elif(variableType == "INTEGER_VALUE_RANGE"):
        int_range = varRange.split('-')
        varLower = int_range[0].strip()
        varHigher = int_range[1].strip()
        r = range(int(varLower), int(varHigher))
        val_range = variableValue.split('-')
        try:
            valLower = val_range[0].strip()
            valHigher = val_range[1].strip()
        except Exception:
            return "Error-113"
        if((checkInteger(valLower) is not True) or
                (checkInteger(valHigher) is not True)):
            # debugOutput("Error-114")
            return "Error-114"
        result = (int(valLower) in r) and (int(valHigher)in r) \
            and (int(valLower) < int(valHigher))
        if(result is True):
            return "ok"
        else:
            # debugOutput("Error-113")
            return "Error-113"

    elif(variableType == "INTEGER_OPTIONS"):
        int_options = varRange.split(',')
        if(checkInteger(variableValue) is not True):
            return "Error-111"
        for opt in int_options:
            if(opt.strip() is variableValue):
                result = True
                break
        if(result is True):
            return "ok"
        else:
            return "Error-115"

    elif(variableType == "LONG"):
        result = checkLong(variableValue)
        if(result is True):
            return "ok"
        else:
            return "Error-116"

    elif(variableType == "LONG_VALUE"):
        long_range = varRange.split('-')
        r = range(int(long_range[0].strip()), int(long_range[1].strip()))
        if(checkLong(variableValue) is not True):
            # debugOutput(variableValue)
            return "Error-116"
        result = int(variableValue) in r
        if(result is True):
            return "ok"
        else:
            return "Error-113"

    elif(variableType == "LONG_VALUE_RANGE"):
        long_range = varRange.split('-')
        r = range(int(long_range[0].strip()), int(long_range[1].strip()))
        val_range = variableValue.split('-')
        if((checkLong(val_range[0]) is not True) or
                (checkLong(val_range[1]) is not True)):
            return "Error-117"
        result = (val_range[0] in r) and (
            val_range[1] in r) and (val_range[0] < val_range[1])
        if(result is True):
            return "ok"
        else:
            return "Error-113"
    elif(variableType == "LONG_OPTIONS"):
        long_options = varRange.split(',')
        if(checkLong(variableValue) is not True):
            return "Error-116"
        for opt in long_options:
            if(opt.strip() == variableValue):
                result = True
                break
        if(result is True):
            return "ok"
        else:
            return "Error-115"

    elif(variableType == "TEXT"):
        if(variableValue == ""):
            return "Error-118"
        if(True is isinstance(variableValue, str)):
            return "ok"
        else:
            return "Error-119"

    elif(variableType == "NO_VALIDATION"):
        if(variableValue == ""):
            return "Error-118"
        else:
            return "ok"

    elif(variableType == "TEXT_OR_EMPTY"):
        if(variableValue is None or variableValue == ""):
            return "ok"
        if(result == isinstance(variableValue, str)):
            return "ok"
        else:
            return "Error-119"

    elif(variableType == "MATCH_TEXT"):
        if(variableValue == ""):
            return "Error-118"
        if(isinstance(variableValue, str)):
            if(varRange == variableValue):
                return "ok"
            else:
                return "Error-120"
        else:
            return "Error-119"

    elif(variableType == "MATCH_TEXT_OR_EMPTY"):
        if(variableValue is None or variableValue == ""):
            return "ok"
        if(isinstance(variableValue, str)):
            if(varRange == variableValue):
                return "ok"
            else:
                return "Error-120"
        else:
            return "Error-119"

    elif(variableType == "TEXT_OPTIONS"):
        str_options = varRange.split(',')
        if(isinstance(variableValue, str) is not True):
            return "Error-119"
        result = False
        for opt in str_options:
            if(opt.strip() == variableValue):
                result = True
                break
        if(result is True):
            return "ok"
        else:
            return "Error-115"

    elif(variableType == "TEXT_OPTIONS_OR_EMPTY"):
        if(variableValue is None or variableValue == ""):
            return "ok"
        str_options = varRange.split(',')
        if(isinstance(variableValue, str) is not True):
            return "Error-119"
        for opt in str_options:
            if(opt.strip() == variableValue):
                result = True
                break
        if(result is True):
            return "ok"
        else:
            return "Error-115"

    elif(variableType == "IPV4Address"):
        try:
            socket.inet_pton(socket.AF_INET, variableValue)
            result = True
        except socket.error:
            result = False
        if(result is True):
            return "ok"
        else:
            return "Error-121"
    elif(variableType == "IPV4AddressWithMask"):
        if(variableValue is None or variableValue == ""):
            return "Error-119"
        str_options = variableValue.split('/')
        ipaddr = str_options[0]
        mask = str_options[1]
        try:
            socket.inet_pton(socket.AF_INET, ipaddr)
            if(checkInteger(mask) is True):
                result = True
            else:
                result = False
        except socket.error:
            result = False
        if(result is True):
            return "ok"
        else:
            return "Error-121"

    elif(variableType == "IPV6Address"):
        try:
            socket.inet_pton(socket.AF_INET6, variableValue)
            result = True
        except socket.error:
            result = False
        if(result is True):
            return "ok"
        else:
            return "Error-122"

    return retVal
# EOM


def disablePaging(remote_conn):
    remote_conn.send("terminal length 0\n")
    time.sleep(1)
    # Clear the buffer on the screen
    outputByte = remote_conn.recv(1000)
    output = outputByte.decode()
    return output
# EOM


def checkInteger(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
# EOM


def checkFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
# EOM


def checkLong(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def debugOutput(command):
    f = open('debugOutput.txt', 'a')
    f.write(str(command))  # python will convert \n to os.linesep
    f.close()  # you can omit in most cases as the destructor will call it
# EOM
