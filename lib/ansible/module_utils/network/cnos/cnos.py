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
    'answer': dict()
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


def interfaceConfig(
    obj, deviceType, prompt, timeout, interfaceArg1,
        interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5,
        interfaceArg6, interfaceArg7, interfaceArg8, interfaceArg9):
    retVal = ""
    command = "interface "
    newPrompt = prompt
    if(interfaceArg1 == "port-aggregation"):
        command = command + " " + interfaceArg1 + " " + interfaceArg2 + "\n"
        # debugOutput(command)
        value = checkSanityofVariable(
            deviceType, "portchannel_interface_value", interfaceArg2)
        if(value == "ok"):
            newPrompt = "(config-if)#"
            retVal = retVal + \
                waitForDeviceResponse(command, newPrompt, timeout, obj)
        else:
            value = checkSanityofVariable(
                deviceType, "portchannel_interface_range", interfaceArg2)
            if(value == "ok"):
                newPrompt = "(config-if-range)#"
                retVal = retVal + \
                    waitForDeviceResponse(command, newPrompt, timeout, obj)
            else:
                value = checkSanityofVariable(
                    deviceType, "portchannel_interface_string", interfaceArg2)
                if(value == "ok"):
                    newPrompt = "(config-if-range)#"
                    if '/' in interfaceArg2:
                        newPrompt = "(config-if)#"
                    retVal = retVal + \
                        waitForDeviceResponse(command, newPrompt, timeout, obj)
                else:
                    retVal = "Error-102"
                    return retVal

        retVal = retVal + interfaceLevel2Config(
            obj, deviceType, newPrompt, timeout, interfaceArg3, interfaceArg4,
            interfaceArg5, interfaceArg6, interfaceArg7, interfaceArg8,
            interfaceArg9)
    elif(interfaceArg1 == "ethernet"):
        # command = command + interfaceArg1 + " 1/"
        value = checkSanityofVariable(
            deviceType, "ethernet_interface_value", interfaceArg2)
        if(value == "ok"):
            newPrompt = "(config-if)#"
            command = command + interfaceArg1 + " 1/" + interfaceArg2 + " \n"
            retVal = retVal + \
                waitForDeviceResponse(command, newPrompt, timeout, obj)
        else:
            value = checkSanityofVariable(
                deviceType, "ethernet_interface_range", interfaceArg2)
            if(value == "ok"):
                command = command + \
                    interfaceArg1 + " 1/" + interfaceArg2 + " \n"
                newPrompt = "(config-if-range)#"
                retVal = retVal + \
                    waitForDeviceResponse(command, newPrompt, timeout, obj)
            else:
                value = checkSanityofVariable(
                    deviceType, "ethernet_interface_string", interfaceArg2)
                if(value == "ok"):
                    command = command + \
                        interfaceArg1 + " " + interfaceArg2 + "\n"
                    newPrompt = "(config-if-range)#"
                    if '/' in interfaceArg2:
                        newPrompt = "(config-if)#"
                    retVal = retVal + \
                        waitForDeviceResponse(command, newPrompt, timeout, obj)
                else:
                    retVal = "Error-102"
                    return retVal

        retVal = retVal + interfaceLevel2Config(
            obj, deviceType, newPrompt, timeout, interfaceArg3, interfaceArg4,
            interfaceArg5, interfaceArg6, interfaceArg7, interfaceArg8,
            interfaceArg9)
    elif(interfaceArg1 == "loopback"):
        value = checkSanityofVariable(
            deviceType, "loopback_interface_value", interfaceArg2)
        if(value == "ok"):
            newPrompt = "(config-if)#"
            command = command + interfaceArg1 + " " + interfaceArg2 + "\n"
            retVal = retVal + \
                waitForDeviceResponse(command, newPrompt, timeout, obj)
        else:
            retVal = "Error-102"
            return retVal
        retVal = retVal + interfaceLevel2Config(
            obj, deviceType, newPrompt, timeout, interfaceArg3, interfaceArg4,
            interfaceArg5, interfaceArg6, interfaceArg7, interfaceArg8,
            interfaceArg9)
    elif(interfaceArg1 == "mgmt"):
        value = checkSanityofVariable(
            deviceType, "mgmt_interface_value", interfaceArg2)
        if(value == "ok"):
            newPrompt = "(config-if)#"
            command = command + interfaceArg1 + " " + interfaceArg2 + "\n"
            retVal = retVal + \
                waitForDeviceResponse(command, newPrompt, timeout, obj)
        else:
            retVal = "Error-102"
            return retVal
        retVal = retVal + interfaceLevel2Config(
            obj, deviceType, newPrompt, timeout, interfaceArg3, interfaceArg4,
            interfaceArg5, interfaceArg6, interfaceArg7, interfaceArg8,
            interfaceArg9)
    elif(interfaceArg1 == "vlan"):
        value = checkSanityofVariable(
            deviceType, "vlan_interface_value", interfaceArg2)
        if(value == "ok"):
            newPrompt = "(config-if)#"
            command = command + interfaceArg1 + " " + interfaceArg2 + "\n"
            retVal = retVal + \
                waitForDeviceResponse(command, newPrompt, timeout, obj)
        else:
            retVal = "Error-102"
            return retVal
        retVal = retVal + interfaceLevel2Config(
            obj, deviceType, newPrompt, timeout, interfaceArg3, interfaceArg4,
            interfaceArg5, interfaceArg6, interfaceArg7, interfaceArg8,
            interfaceArg9)
    else:
        retVal = "Error-102"

    return retVal
# EOM


def interfaceLevel2Config(
    obj, deviceType, prompt, timeout, interfaceL2Arg1, interfaceL2Arg2,
    interfaceL2Arg3, interfaceL2Arg4, interfaceL2Arg5, interfaceL2Arg6,
        interfaceL2Arg7):
    retVal = ""
    command = ""
    if(interfaceL2Arg1 == "aggregation-group"):
        # debugOutput("aggregation-group")
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

    elif (interfaceL2Arg1 == "bridge-port"):
        # debugOutput("bridge-port")
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

    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, prompt, timeout, obj)
    # Come back to config mode
    if((prompt == "(config-if)#") or (prompt == "(config-if-range)#")):
        command = "exit \n"
        # debugOutput(command)
        retVal = retVal + \
            waitForDeviceResponse(command, "(config)#", timeout, obj)

    return retVal
# EOM


def portChannelConfig(
        obj, deviceType, prompt, timeout, portChArg1, portChArg2, portChArg3,
        portChArg4, portChArg5, portChArg6, portChArg7):
    retVal = ""
    command = ""
    if(portChArg1 == "port-aggregation" and prompt == "(config)#"):
        command = command + portChArg1 + " load-balance ethernet "
        if(portChArg2 == "destination-ip" or
           portChArg2 == "destination-mac" or
           portChArg2 == "destination-port" or
           portChArg2 == "source-dest-ip" or
           portChArg2 == "source-dest-mac" or
           portChArg2 == "source-dest-port" or
           portChArg2 == "source-interface" or
           portChArg2 == "source-ip" or
           portChArg2 == "source-mac" or
           portChArg2 == "source-port"):

            # debugOutput(portChArg2)
            command = command + portChArg2 + " "
            if(portChArg3 is None):
                command = command + ""
            elif(portChArg3 == "source-interface"):
                command = command + portChArg3
            else:
                retVal = "Error-231"
                return retVal
        else:
            retVal = "Error-232"
            return retVal

# EOM


def routerConfig(
    obj, deviceType, prompt, timeout, protocol, asNum, routerArg1,
    routerArg2, routerArg3, routerArg4, routerArg5, routerArg6, routerArg7,
        routerArg8):
    retVal = ""
    # Wait time to get response from server
    timeout = timeout
    if(protocol == "bgp"):
        # bgp config command happens here.
        command = "routing-protocol bgp "
        value = checkSanityofVariable(deviceType, "bgp_as_number", asNum)
        if(value == "ok"):
            # BGP command happens here. It creates if not present
            command = command + asNum + "\n"
            # debugOutput(command)
            retVal = waitForDeviceResponse(
                command, "(config-router)#", timeout, obj)
            retVal = retVal + bgpConfig(
                obj, deviceType, "(config-router)#", timeout, routerArg1,
                routerArg2, routerArg3, routerArg4, routerArg5, routerArg6,
                routerArg7, routerArg8)
        else:
            retVal = "Error-176"

    elif(protocol == "ospf"):
        retVal = "Command Value is Not supported as of now"

    else:
        retVal = "Error-177"

    return retVal
# EOM


def bgpNeighborAFConfig(
    obj, deviceType, prompt, timeout, bgpNeighborAFArg1, bgpNeighborAFArg2,
        bgpNeighborAFArg3):
    retVal = ""
    command = ""
    timeout = timeout
    if(bgpNeighborAFArg1 == "allowas-in"):
        command = command + bgpNeighborAFArg1 + " "
        if(bgpNeighborAFArg2 is not None):
            value = checkSanityofVariable(
                deviceType, "bgp_neighbor_af_occurances", bgpNeighborAFArg2)
            if(value == "ok"):
                command = command + bgpNeighborAFArg2
            else:
                retVal = "Error-325"
                return retVal
        else:
            command = command
    elif(bgpNeighborAFArg1 == "default-originate"):
        command = command + bgpNeighborAFArg1 + " "
        if(bgpNeighborAFArg2 is not None and bgpNeighborAFArg2 == "route-map"):
            command = command + bgpNeighborAFArg2 + " "
            value = checkSanityofVariable(
                deviceType, "bgp_neighbor_af_routemap", bgpNeighborAFArg2)
            if(value == "ok"):
                command = command + bgpNeighborAFArg3
            else:
                retVal = "Error-324"
                return retVal
    elif(bgpNeighborAFArg1 == "filter-list"):
        command = command + bgpNeighborAFArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_af_filtername", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2 + " "
            if(bgpNeighborAFArg3 == "in" or bgpNeighborAFArg3 == "out"):
                command = command + bgpNeighborAFArg3
            else:
                retVal = "Error-323"
                return retVal
        else:
            retVal = "Error-322"
            return retVal

    elif(bgpNeighborAFArg1 == "maximum-prefix"):
        command = command + bgpNeighborAFArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_af_maxprefix", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2 + " "
            if(bgpNeighborAFArg3 is not None):
                command = command + bgpNeighborAFArg3
            else:
                command = command.strip()
        else:
            retVal = "Error-326"
            return retVal

    elif(bgpNeighborAFArg1 == "next-hop-self"):
        command = command + bgpNeighborAFArg1

    elif(bgpNeighborAFArg1 == "prefix-list"):
        command = command + bgpNeighborAFArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_af_prefixname", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2 + " "
            if(bgpNeighborAFArg3 == "in" or bgpNeighborAFArg3 == "out"):
                command = command + bgpNeighborAFArg3
            else:
                retVal = "Error-321"
                return retVal
        else:
            retVal = "Error-320"
            return retVal

    elif(bgpNeighborAFArg1 == "route-map"):
        command = command + bgpNeighborAFArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_af_routemap", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2
        else:
            retVal = "Error-319"
            return retVal
    elif(bgpNeighborAFArg1 == "route-reflector-client"):
        command = command + bgpNeighborAFArg1

    elif(bgpNeighborAFArg1 == "send-community"):
        command = command + bgpNeighborAFArg1 + " "
        if(bgpNeighborAFArg2 is not None and bgpNeighborAFArg2 == "extended"):
            command = command + bgpNeighborAFArg2
        else:
            command = command

    elif(bgpNeighborAFArg1 == "soft-reconfiguration"):
        command = command + bgpNeighborAFArg1 + " inbound"

    elif(bgpNeighborAFArg1 == "unsuppress-map"):
        command = command + bgpNeighborAFArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_af_routemap", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2
        else:
            retVal = "Error-318"
            return retVal

    else:
        retVal = "Error-317"
        return retVal

    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, prompt, timeout, obj)
    command = "exit \n"
    retVal = retVal + \
        waitForDeviceResponse(
            command, "(config-router-neighbor)#", timeout, obj)
    return retVal
# EOM


def bgpNeighborConfig(
    obj, deviceType, prompt, timeout, bgpNeighborArg1, bgpNeighborArg2,
        bgpNeighborArg3, bgpNeighborArg4, bgpNeighborArg5):
    retVal = ""
    command = ""
    timeout = timeout

    if(bgpNeighborArg1 == "address-family"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_address_family", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2 + " unicast \n"
            # debugOutput(command)
            retVal = waitForDeviceResponse(
                command, "(config-router-neighbor-af)#", timeout, obj)
            retVal = retVal + bgpNeighborAFConfig(
                obj, deviceType, "(config-router-neighbor-af)#", timeout,
                bgpNeighborArg3, bgpNeighborArg4, bgpNeighborArg5)
            return retVal
        else:
            retVal = "Error-316"
            return retVal

    elif(bgpNeighborArg1 == "advertisement-interval"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "bfd"):
        command = command + bgpNeighborArg1 + " "
        if(bgpNeighborArg2 is not None and bgpNeighborArg2 == "mutihop"):
            command = command + bgpNeighborArg2
        else:
            command = command

    elif(bgpNeighborArg1 == "connection-retry-time"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_connection_retrytime", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-315"
            return retVal

    elif(bgpNeighborArg1 == "description"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_description", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-314"
            return retVal

    elif(bgpNeighborArg1 == "disallow-infinite-holdtime"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "dont-capability-negotiate"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "dynamic-capability"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "ebgp-multihop"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_maxhopcount", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-313"
            return retVal
    elif(bgpNeighborArg1 == "interface"):
        command = command + bgpNeighborArg1 + " "
        # TBD
    elif(bgpNeighborArg1 == "local-as"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_local_as", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2 + " "
            if(bgpNeighborArg3 is not None and
                    bgpNeighborArg3 == "no-prepend"):
                command = command + bgpNeighborArg3 + " "
                if(bgpNeighborArg4 is not None and
                        bgpNeighborArg4 == "replace-as"):
                    command = command + bgpNeighborArg4 + " "
                    if(bgpNeighborArg5 is not None and
                            bgpNeighborArg5 == "dual-as"):
                        command = command + bgpNeighborArg5
                    else:
                        command = command.strip()
                else:
                    command = command.strip()
            else:
                command = command.strip()
        else:
            retVal = "Error-312"
            return retVal

    elif(bgpNeighborArg1 == "maximum-peers"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_maxpeers", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-311"
            return retVal

    elif(bgpNeighborArg1 == "password"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_password", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-310"
            return retVal

    elif(bgpNeighborArg1 == "remove-private-AS"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "timers"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_timers_Keepalive", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2 + " "
            value = checkSanityofVariable(
                deviceType, "bgp_neighbor_timers_holdtime", bgpNeighborArg3)
            if(value == "ok"):
                command = command + bgpNeighborArg3
            else:
                retVal = "Error-309"
                return retVal
        else:
            retVal = "Error-308"
            return retVal

    elif(bgpNeighborArg1 == "transport"):
        command = command + bgpNeighborArg1 + " connection-mode passive "

    elif(bgpNeighborArg1 == "ttl-security"):
        command = command + bgpNeighborArg1 + " hops "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_ttl_hops", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-307"
            return retVal

    elif(bgpNeighborArg1 == "update-source"):
        command = command + bgpNeighborArg1 + " "
        if(bgpNeighborArg2 is not None):
            value = checkSanityofVariable(
                deviceType, "bgp_neighbor_update_options", bgpNeighborArg2)
            if(value == "ok"):
                command = command + bgpNeighborArg2 + " "
                if(bgpNeighborArg2 == "ethernet"):
                    value = checkSanityofVariable(
                        deviceType, "bgp_neighbor_update_ethernet",
                        bgpNeighborArg3)
                    if(value == "ok"):
                        command = command + bgpNeighborArg3
                    else:
                        retVal = "Error-304"
                        return retVal
                elif(bgpNeighborArg2 == "loopback"):
                    value = checkSanityofVariable(
                        deviceType, "bgp_neighbor_update_loopback",
                        bgpNeighborArg3)
                    if(value == "ok"):
                        command = command + bgpNeighborArg3
                    else:
                        retVal = "Error-305"
                        return retVal
                else:
                    value = checkSanityofVariable(
                        deviceType, "bgp_neighbor_update_vlan",
                        bgpNeighborArg3)
                    if(value == "ok"):
                        command = command + bgpNeighborArg3
                    else:
                        retVal = "Error-306"
                        return retVal
            else:
                command = command + bgpNeighborArg2
        else:
            retVal = "Error-303"
            return retVal

    elif(bgpNeighborArg1 == "weight"):
        command = command + bgpNeighborArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_neighbor_weight", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-302"
            return retVal

    else:
        retVal = "Error-301"
        return retVal

    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, prompt, timeout, obj)
    command = "exit \n"
    retVal = retVal + \
        waitForDeviceResponse(command, "(config-router)#", timeout, obj)
    return retVal
# EOM


def bgpAFConfig(
    obj, deviceType, prompt, timeout, bgpAFArg1, bgpAFArg2, bgpAFArg3,
        bgpAFArg4, bgpAFArg5, bgpAFArg6):
    retVal = ""
    command = ""
    timeout = timeout
    if(bgpAFArg1 == "aggregate-address"):
        command = command + bgpAFArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_aggregate_prefix", bgpAFArg2)
        if(value == "ok"):
            if(bgpAFArg2 is None):
                command = command.strip()
            elif(bgpAFArg2 == "as-set" or bgpAFArg2 == "summary-only"):
                command = command + bgpAFArg2 + " "
                if((bgpAFArg3 is not None) and (bgpAFArg2 == "as-set")):
                    command = command + "summary-only"
            else:
                retVal = "Error-297"
                return retVal
        else:
            retVal = "Error-296"
            return retVal
    elif(bgpAFArg1 == "client-to-client"):
        command = command + bgpAFArg1 + " reflection "
    elif(bgpAFArg1 == "dampening"):
        command = command + bgpAFArg1 + " "
        if(bgpAFArg2 == "route-map"):
            command = command + bgpAFArg2 + " "
            value = checkSanityofVariable(
                deviceType, "addrfamily_routemap_name", bgpAFArg3)
            if(value == "ok"):
                command = command + bgpAFArg3
            else:
                retVal = "Error-196"
                return retVal
        elif(bgpAFArg2 is not None):
            value = checkSanityofVariable(
                deviceType, "reachability_half_life", bgpAFArg2)
            if(value == "ok"):
                command = command + bgpAFArg2 + " "
                if(bgpAFArg3 is not None):
                    value1 = checkSanityofVariable(
                        deviceType, "start_reuse_route_value", bgpAFArg3)
                    value2 = checkSanityofVariable(
                        deviceType, "start_suppress_route_value", bgpAFArg4)
                    value3 = checkSanityofVariable(
                        deviceType, "max_duration_to_suppress_route",
                        bgpAFArg5)
                    if(value1 == "ok" and value2 == "ok" and value3 == "ok"):
                        command = command + bgpAFArg3 + " " + bgpAFArg4 + \
                            " " + bgpAFArg5 + " "
                        if(bgpAFArg6 is not None):
                            value = checkSanityofVariable(
                                deviceType,
                                "unreachability_halftime_for_penalty",
                                bgpAFArg6)
                            if(value == "ok"):
                                command = command + bgpAFArg6
                    else:
                        retVal = "Error-295"
                        return retVal
                else:
                    command = command.strip()
            else:
                retVal = "Error-294"
                return retVal

    elif(bgpAFArg1 == "distance"):
        command = command + bgpAFArg1 + " "
        value = checkSanityofVariable(
            deviceType, "distance_external_AS", bgpAFArg2)
        if(value == "ok"):
            command = command + bgpAFArg2 + " "
            value = checkSanityofVariable(
                deviceType, "distance_internal_AS", bgpAFArg3)
            if(value == "ok"):
                command = command + bgpAFArg3 + " "
                value = checkSanityofVariable(
                    deviceType, "distance_local_routes", bgpAFArg4)
                if(value == "ok"):
                    command = command + bgpAFArg4
                else:
                    retVal = "Error-291"
                    return retVal
            else:
                retVal = "Error-292"
                return retVal
        else:
            retVal = "Error-293"
            return retVal
    elif(bgpAFArg1 == "maximum-paths"):
        command = command + bgpAFArg1 + " "
        value = checkSanityofVariable(deviceType, "maxpath_option", bgpAFArg2)
        if(value == "ok"):
            command = command + bgpAFArg2 + " "
            value = checkSanityofVariable(
                deviceType, "maxpath_numbers", bgpAFArg3)
            if(value == "ok"):
                command = command + bgpAFArg3
            else:
                retVal = "Error-199"
                return retVal
        else:
            retVal = "Error-290"
            return retVal

    elif(bgpAFArg1 == "network"):
        command = command + bgpAFArg1 + " "
        if(bgpAFArg2 == "synchronization"):
            command = command + bgpAFArg2
        else:
            value = checkSanityofVariable(
                deviceType, "network_ip_prefix_with_mask", bgpAFArg2)
            if(value == "ok"):
                command = command + bgpAFArg2 + " "
                if(bgpAFArg3 is not None and bgpAFArg3 == "backdoor"):
                    command = command + bgpAFArg3
                elif(bgpAFArg3 is not None and bgpAFArg3 == "route-map"):
                    command = command + bgpAFArg3
                    value = checkSanityofVariable(
                        deviceType, "addrfamily_routemap_name", bgpAFArg4)
                    if(value == "ok"):
                        command = command + bgpAFArg4 + " "
                        if(bgpAFArg5 is not None and bgpAFArg5 == "backdoor"):
                            command = command + bgpAFArg5
                        else:
                            retVal = "Error-298"
                            return retVal
                    else:
                        retVal = "Error-196"
                        return retVal
                else:
                    command = command.strip()
            else:
                value = checkSanityofVariable(
                    deviceType, "network_ip_prefix_value", bgpAFArg2)
                if(value == "ok"):
                    command = command + bgpAFArg2 + " "
                    if(bgpAFArg3 is not None and bgpAFArg3 == "backdoor"):
                        command = command + bgpAFArg3
                    elif(bgpAFArg3 is not None and bgpAFArg3 == "route-map"):
                        command = command + bgpAFArg3
                        value = checkSanityofVariable(
                            deviceType, "addrfamily_routemap_name", bgpAFArg4)
                        if(value == "ok"):
                            command = command + bgpAFArg4 + " "
                            if(bgpAFArg5 is not None and
                                    bgpAFArg5 == "backdoor"):
                                command = command + bgpAFArg5
                            else:
                                retVal = "Error-298"
                                return retVal
                        else:
                            retVal = "Error-196"
                            return retVal
                    elif(bgpAFArg3 is not None and bgpAFArg3 == "mask"):
                        command = command + bgpAFArg3
                        value = checkSanityofVariable(
                            deviceType, "network_ip_prefix_mask", bgpAFArg4)
                        if(value == "ok"):
                            command = command + bgpAFArg4 + " "
                        else:
                            retVal = "Error-299"
                            return retVal
                    else:
                        command = command.strip()
                else:
                    retVal = "Error-300"
                    return retVal

    elif(bgpAFArg1 == "nexthop"):
        command = command + bgpAFArg1 + " trigger-delay critical "
        value = checkSanityofVariable(
            deviceType, "nexthop_crtitical_delay", bgpAFArg2)
        if(value == "ok"):
            command = command + bgpAFArg2 + " "
            value = checkSanityofVariable(
                deviceType, "nexthop_noncrtitical_delay", bgpAFArg3)
            if(value == "ok"):
                command = command + bgpAFArg3 + " "
            else:
                retVal = "Error-198"
                return retVal
        else:
            retVal = "Error-197"
            return retVal
    elif(bgpAFArg1 == "redistribute"):
        command = command + bgpAFArg1 + " "
        value = checkSanityofVariable(
            deviceType, "addrfamily_redistribute_option", bgpAFArg2)
        if(value == "ok"):
            if(bgpAFArg2 is not None):
                command = command + bgpAFArg2 + " " + "route-map "
                value = checkSanityofVariable(
                    deviceType, "addrfamily_routemap_name", bgpAFArg3)
                if(value == "ok"):
                    command = command + bgpAFArg3
                else:
                    retVal = "Error-196"
                    return retVal
        else:
            retVal = "Error-195"
            return retVal
    elif(bgpAFArg1 == "save" or bgpAFArg1 == "synchronization"):
        command = command + bgpAFArg1
    else:
        retVal = "Error-194"
        return retVal
    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, prompt, timeout, obj)
    command = "exit \n"
    retVal = retVal + \
        waitForDeviceResponse(command, "(config-router)#", timeout, obj)
    return retVal
# EOM


def bgpConfig(
    obj, deviceType, prompt, timeout, bgpArg1, bgpArg2, bgpArg3, bgpArg4,
        bgpAgr5, bgpArg6, bgpArg7, bgpArg8):
    retVal = ""
    command = ""
    # Wait time to get response from server
    timeout = timeout
    if(bgpArg1 == "address-family"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = checkSanityofVariable(
            deviceType, "bgp_address_family", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2 + " " + "unicast \n"
            debugOutput(command)
            retVal = waitForDeviceResponse(
                command, "(config-router-af)#", timeout, obj)
            retVal = retVal + bgpAFConfig(
                obj, deviceType, "(config-router-af)#", timeout,
                bgpArg3, bgpArg4, bgpAgr5, bgpArg6, bgpArg7, bgpArg8)
            return retVal
        else:
            retVal = "Error-178"
            return retVal

    elif(bgpArg1 == "bestpath"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        if(bgpArg2 == "always-compare-med"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "compare-confed-aspath"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "compare-routerid"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "dont-compare-originator-id"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "tie-break-on-age"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "as-path"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2 + " "
            if(bgpArg3 == "ignore" or bgpArg3 == "multipath-relax"):
                command = command + bgpArg3
            else:
                retVal = "Error-179"
                return retVal
        elif(bgpArg2 == "med"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2 + " "
            if(bgpArg3 == "confed" or
               bgpArg3 == "missing-as-worst" or
               bgpArg3 == "non-deterministic" or
               bgpArg3 == "remove-recv-med" or
               bgpArg3 == "remove-send-med"):
                command = command + bgpArg3
            else:
                retVal = "Error-180"
                return retVal
        else:
            retVal = "Error-181"
            return retVal

    elif(bgpArg1 == "bgp"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " as-local-count "
        value = checkSanityofVariable(
            deviceType, "bgp_bgp_local_count", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-182"
            return retVal

    elif(bgpArg1 == "cluster-id"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = checkSanityofVariable(deviceType, "cluster_id_as_ip", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            value = checkSanityofVariable(
                deviceType, "cluster_id_as_number", bgpArg2)
            if(value == "ok"):
                command = command + bgpArg2
            else:
                retVal = "Error-183"
                return retVal

    elif(bgpArg1 == "confederation"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        if(bgpArg2 == "identifier"):
            value = checkSanityofVariable(
                deviceType, "confederation_identifier", bgpArg3)
            if(value == "ok"):
                command = command + " " + bgpArg2 + " " + bgpArg3
            else:
                retVal = "Error-184"
                return retVal
        elif(bgpArg2 == "peers"):
            value = checkSanityofVariable(
                deviceType, "confederation_peers_as", bgpArg3)
            if(value == "ok"):
                command = command + " " + bgpArg2 + " " + bgpArg3
            else:
                retVal = "Error-185"
                return retVal
        else:
            retVal = "Error-186"
            return retVal

    elif(bgpArg1 == "enforce-first-as"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "fast-external-failover"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "graceful-restart"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " stalepath-time "
        value = checkSanityofVariable(
            deviceType, "stalepath_delay_value", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-187"
            return retVal

    elif(bgpArg1 == "graceful-restart-helper"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "log-neighbor-changes"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "maxas-limit"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = checkSanityofVariable(deviceType, "maxas_limit_as", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-188"
            return retVal

    elif(bgpArg1 == "neighbor"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = checkSanityofVariable(
            deviceType, "neighbor_ipaddress", bgpArg2)
        # retVal = "Error-102"
        # return retVal
        if(value == "ok"):
            command = command + bgpArg2
            if(bgpArg3 is not None):
                command = command + " remote-as "
                value = checkSanityofVariable(
                    deviceType, "neighbor_as", bgpArg3)
                if(value == "ok"):
                    command = command + bgpArg3 + "\n"
                    # debugOutput(command)
                    retVal = waitForDeviceResponse(
                        command, "(config-router-neighbor)#", timeout, obj)
                    retVal = retVal + bgpNeighborConfig(
                        obj, deviceType, "(config-router-neighbor)#",
                        timeout, bgpArg4, bgpAgr5, bgpArg6, bgpArg7, bgpArg8)
                    return retVal
        else:
            retVal = "Error-189"
            return retVal

    elif(bgpArg1 == "router-id"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = checkSanityofVariable(deviceType, "router_id", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-190"
            return retVal

    elif(bgpArg1 == "shutdown"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "synchronization"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "timers"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " bgp "
        value = checkSanityofVariable(
            deviceType, "bgp_keepalive_interval", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-191"
            return retVal
        if(bgpArg3 is not None):
            value = checkSanityofVariable(deviceType, "bgp_holdtime", bgpArg3)
            if(value == "ok"):
                command = command + " " + bgpArg3
            else:
                retVal = "Error-192"
                return retVal
        else:
            retVal = "Error-192"
            return retVal

    elif(bgpArg1 == "vrf"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " default"
    else:
        # debugOutput(bgpArg1)
        retVal = "Error-192"
        return retVal
    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, prompt, timeout, obj)
    # Come back to config mode
    command = "exit \n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, "(config)#", timeout, obj)

    return retVal
# EOM


def vlanConfig(
    obj, deviceType, prompt, timeout, vlanArg1, vlanArg2, vlanArg3,
        vlanArg4, vlanArg5):

    retVal = ""
    # Wait time to get response from server
    timeout = timeout
    # vlan config command happens here.
    command = "vlan "

    if(vlanArg1 == "access-map"):
        # debugOutput("access-map ")
        command = command + vlanArg1 + " "
        value = checkSanityofVariable(
            deviceType, "vlan_access_map_name", vlanArg2)
        if(value == "ok"):
            command = command + vlanArg2 + " \n"
            # debugOutput(command)
            retVal = waitForDeviceResponse(
                command, "(config-access-map)#", timeout, obj)
            retVal = retVal + vlanAccessMapConfig(
                obj, deviceType, "(config-access-map)#", timeout, vlanArg3,
                vlanArg4, vlanArg5)
            return retVal
        else:
            retVal = "Error-130"
            return retVal

    elif(vlanArg1 == "dot1q"):
        # debugOutput("dot1q")
        command = command + vlanArg1 + " tag native "
        if(vlanArg2 is not None):
            value = checkSanityofVariable(
                deviceType, "vlan_dot1q_tag", vlanArg2)
            if(value == "ok"):
                command = command + vlanArg2
            else:
                retVal = "Error-131"
                return retVal

    elif(vlanArg1 == "filter"):
        # debugOutput( "filter")
        command = command + vlanArg1 + " "
        if(vlanArg2 is not None):
            value = checkSanityofVariable(
                deviceType, "vlan_filter_name", vlanArg2)
            if(value == "ok"):
                command = command + vlanArg2 + " vlan-list "
                value = checkSanityofVariable(deviceType, "vlan_id", vlanArg3)
                if(value == "ok"):
                    command = command + vlanArg3
                else:
                    value = checkSanityofVariable(
                        deviceType, "vlan_id_range", vlanArg3)
                    if(value == "ok"):
                        command = command + vlanArg3
                    else:
                        retVal = "ERROR-133"
                    return retVal
            else:
                retVal = "Error-132"
                return retVal

    else:
        value = checkSanityofVariable(deviceType, "vlan_id", vlanArg1)
        if(value == "ok"):
            retVal = createVlan(obj, deviceType, "(config-vlan)#",
                                timeout, vlanArg1, vlanArg2, vlanArg3,
                                vlanArg4, vlanArg5)
            return retVal
        else:
            value = checkSanityofVariable(
                deviceType, "vlan_id_range", vlanArg1)
            if(value == "ok"):
                retVal = createVlan(obj, deviceType, "(config-vlan)#",
                                    timeout, vlanArg1, vlanArg2, vlanArg3,
                                    vlanArg4, vlanArg5)
                return retVal
            retVal = "Error-133"
            return retVal

    # debugOutput(command)
    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, prompt, timeout, obj)
    return retVal
# EOM


def vlanAccessMapConfig(
        obj, deviceType, prompt, timeout, vlanArg3, vlanArg4, vlanArg5):
    retVal = ""
    # Wait time to get response from server
    timeout = timeout
    command = ""
    if(vlanArg3 == "action"):
        command = command + vlanArg3 + " "
        value = checkSanityofVariable(
            deviceType, "vlan_accessmap_action", vlanArg4)
        if(value == "ok"):
            command = command + vlanArg4
        else:
            retVal = "Error-135"
            return retVal
    elif(vlanArg3 == "match"):
        command = command + vlanArg3 + " "
        if(vlanArg4 == "ip" or vlanArg4 == "mac"):
            command = command + vlanArg4 + " address "
            value = checkSanityofVariable(
                deviceType, "vlan_access_map_name", vlanArg5)
            if(value == "ok"):
                command = command + vlanArg5
            else:
                retVal = "Error-136"
                return retVal
        else:
            retVal = "Error-137"
            return retVal
    elif(vlanArg3 == "statistics"):
        command = vlanArg3 + " per-entry"
    else:
        retVal = "Error-138"
        return retVal

    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, prompt, timeout, obj)
    return retVal
# EOM


def checkVlanNameNotAssigned(
        obj, deviceType, prompt, timeout, vlanId, vlanName):
    retVal = "ok"
    command = "display vlan id " + vlanId + " \n"
    retVal = waitForDeviceResponse(command, prompt, timeout, obj)
    if(retVal.find(vlanName) != -1):
        return "Nok"
    else:
        return "ok"
# EOM


# Utility Method to create vlan
def createVlan(
        obj, deviceType, prompt, timeout, vlanArg1, vlanArg2, vlanArg3,
        vlanArg4, vlanArg5):

    # vlan config command happens here. It creates if not present
    command = "vlan " + vlanArg1 + "\n"
    # debugOutput(command)
    retVal = waitForDeviceResponse(command, prompt, timeout, obj)
    command = ""
    if(vlanArg2 == "name"):
        # debugOutput("name")
        command = vlanArg2 + " "
        value = checkSanityofVariable(deviceType, "vlan_name", vlanArg3)
        if(value == "ok"):
            value = checkVlanNameNotAssigned(obj, deviceType, prompt, timeout,
                                             vlanArg1, vlanArg3)
            if(value == "ok"):
                command = command + vlanArg3
            else:
                command = "\n"
        else:
            retVal = "Error-139"
            return retVal
    elif (vlanArg2 == "flood"):
        # debugOutput("flood")
        command = vlanArg2 + " "
        value = checkSanityofVariable(deviceType, "vlan_flood", vlanArg3)
        if(value == "ok"):
            command = command + vlanArg3
        else:
            retVal = "Error-140"
            return retVal

    elif(vlanArg2 == "state"):
        # debugOutput("state")
        command = vlanArg2 + " "
        value = checkSanityofVariable(deviceType, "vlan_state", vlanArg3)
        if(value == "ok"):
            command = command + vlanArg3
        else:
            retVal = "Error-141"
            return retVal

    elif(vlanArg2 == "ip"):
        # debugOutput("ip")
        command = vlanArg2 + " igmp snooping "
        # debugOutput("vlanArg3")
        if(vlanArg3 is None or vlanArg3 == ""):
            # debugOutput("None or empty")
            command = command.strip()
        elif(vlanArg3 == "fast-leave"):
            # debugOutput("fast-leave")
            command = command + vlanArg3

        elif (vlanArg3 == "last-member-query-interval"):
            # debugOutput("last-member-query-interval")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(
                deviceType, "vlan_last_member_query_interval", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-142"
                return retVal

        elif (vlanArg3 == "querier"):
            # debugOutput("querier")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(deviceType, "vlan_querier", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-143"
                return retVal
        elif (vlanArg3 == "querier-timeout"):
            # debugOutput("querier-timeout")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(
                deviceType, "vlan_querier_timeout", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-144"
                return retVal
        elif (vlanArg3 == "query-interval"):
            # debugOutput("query-interval")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(
                deviceType, "vlan_query_interval", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-145"
                return retVal
        elif (vlanArg3 == "query-max-response-time"):
            # debugOutput("query-max-response-time")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(
                deviceType, "vlan_query_max_response_time", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-146"
                return retVal
        elif (vlanArg3 == "report-suppression"):
            # debugOutput("report-suppression")
            command = command + vlanArg3

        elif (vlanArg3 == "robustness-variable"):
            # debugOutput("robustness-variable")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(
                deviceType, "vlan_robustness_variable", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-147"
                return retVal
        elif (vlanArg3 == "startup-query-count"):
            # debugOutput("startup-query-count")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(
                deviceType, "vlan_startup_query_count", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-148"
                return retVal
        elif (vlanArg3 == "startup-query-interval"):
            # debugOutput("startup-query-interval")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(
                deviceType, "vlan_startup_query_interval", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-149"
                return retVal
        elif (vlanArg3 == "static-group"):
            # debugOutput("static-group")
            # command = command + vlanArg3 + " "
            # value = checkSanityofVariable(deviceType, variableId, vlanArg4)
            # if(value == "ok"):
            #    command = command + vlanArg4

            # else :
            retVal = "Error-102"
            return retVal
        elif (vlanArg3 == "version"):
            # debugOutput("version")
            command = command + vlanArg3 + " "
            value = checkSanityofVariable(
                deviceType, "vlan_snooping_version", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-150"
                return retVal
        elif (vlanArg3 == "mrouter"):
            # debugOutput("mrouter")
            command = command + vlanArg3 + " interface "
            if(vlanArg4 == "ethernet"):
                command = command + vlanArg4 + " "
                value = checkSanityofVariable(
                    deviceType, "vlan_ethernet_interface", vlanArg5)
                if(value == "ok"):
                    command = command + vlanArg5
                else:
                    retVal = "Error-151"
                    return retVal
            elif(vlanArg4 == "port-aggregation"):
                command = command + vlanArg4 + " "
                value = checkSanityofVariable(
                    deviceType, "vlan_portagg_number", vlanArg5)
                if(value == "ok"):
                    command = command + vlanArg5
                else:
                    retVal = "Error-152"
                    return retVal
            else:
                retVal = "Error-153"
                return retVal
        else:
            command = command + vlanArg3

    else:
        retVal = "Error-154"
        return retVal
    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + "\n" + \
        waitForDeviceResponse(command, prompt, timeout, obj)
    # Come back to config mode
    command = "exit \n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, "(config)#", timeout, obj)

    return retVal
# EOM


def vlagConfig(
        obj, deviceType, prompt, timeout, vlagArg1, vlagArg2, vlagArg3,
        vlagArg4):

    retVal = ""
    # Wait time to get response from server
    timeout = timeout
    # vlag config command happens here.
    command = "vlag "

    if(vlagArg1 == "enable"):
        # debugOutput("enable")
        command = command + vlagArg1 + " "

    elif(vlagArg1 == "auto-recovery"):
        # debugOutput("auto-recovery")
        command = command + vlagArg1 + " "
        value = checkSanityofVariable(
            deviceType, "vlag_auto_recovery", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-160"
            return retVal

    elif(vlagArg1 == "config-consistency"):
        # debugOutput("config-consistency")
        command = command + vlagArg1 + " "
        value = checkSanityofVariable(
            deviceType, "vlag_config_consistency", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-161"
            return retVal

    elif(vlagArg1 == "isl"):
        # debugOutput("isl")
        command = command + vlagArg1 + " port-aggregation "
        value = checkSanityofVariable(
            deviceType, "vlag_port_aggregation", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-162"
            return retVal

    elif(vlagArg1 == "mac-address-table"):
        # debugOutput("mac-address-table")
        command = command + vlagArg1 + " refresh"

    elif(vlagArg1 == "peer-gateway"):
        # debugOutput("peer-gateway")
        command = command + vlagArg1 + " "

    elif(vlagArg1 == "priority"):
        # debugOutput("priority")
        command = command + vlagArg1 + " "
        value = checkSanityofVariable(deviceType, "vlag_priority", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-163"
            return retVal

    elif(vlagArg1 == "startup-delay"):
        # debugOutput("startup-delay")
        command = command + vlagArg1 + " "
        value = checkSanityofVariable(
            deviceType, "vlag_startup_delay", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-164"
            return retVal

    elif(vlagArg1 == "tier-id"):
        # debugOutput("tier-id")
        command = command + vlagArg1 + " "
        value = checkSanityofVariable(deviceType, "vlag_tier_id", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-165"
            return retVal

    elif(vlagArg1 == "vrrp"):
        # debugOutput("vrrp")
        command = command + vlagArg1 + " active"

    elif(vlagArg1 == "instance"):
        # debugOutput("instance")
        command = command + vlagArg1 + " "
        value = checkSanityofVariable(deviceType, "vlag_instance", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
            if(vlagArg3 is not None):
                command = command + " port-aggregation "
                value = checkSanityofVariable(
                    deviceType, "vlag_port_aggregation", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg3
                else:
                    retVal = "Error-162"
                    return retVal
            else:
                command = command + " enable "
        else:
            retVal = "Error-166"
            return retVal

    elif(vlagArg1 == "hlthchk"):
        # debugOutput("hlthchk")
        command = command + vlagArg1 + " "
        value = checkSanityofVariable(
            deviceType, "vlag_hlthchk_options", vlagArg2)
        if(value == "ok"):
            if(vlagArg2 == "keepalive-attempts"):
                value = checkSanityofVariable(
                    deviceType, "vlag_keepalive_attempts", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg2 + " " + vlagArg3
                else:
                    retVal = "Error-167"
                    return retVal
            elif(vlagArg2 == "keepalive-interval"):
                value = checkSanityofVariable(
                    deviceType, "vlag_keepalive_interval", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg2 + " " + vlagArg3
                else:
                    retVal = "Error-168"
                    return retVal
            elif(vlagArg2 == "retry-interval"):
                value = checkSanityofVariable(
                    deviceType, "vlag_retry_interval", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg2 + " " + vlagArg3
                else:
                    retVal = "Error-169"
                    return retVal
            elif(vlagArg2 == "peer-ip"):
                # Here I am not taking care of IPV6 option.
                value = checkSanityofVariable(
                    deviceType, "vlag_peerip", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg2 + " " + vlagArg3
                    if(vlagArg4 is not None):
                        value = checkSanityofVariable(
                            deviceType, "vlag_peerip_vrf", vlagArg4)
                        if(value == "ok"):
                            command = command + " vrf " + vlagArg4
                        else:
                            retVal = "Error-170"
                            return retVal
        else:
            retVal = "Error-171"
            return retVal

    else:
        retVal = "Error-172"
        return retVal

    # debugOutput(command)
    command = command + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, "(config)#", timeout, obj)

    return retVal
# EOM

# Utility Method to back up the start up config
# This method supports only TFTP or FTP
# Tuning of timeout parameter is pending


def doStartupConfigBackUp(
        protocol, timeout, confServerIp, confPath, confServerUser,
        confServerPwd, obj):
    # server = "10.241.105.214"
    server = confServerIp

    # username = "pbhosale"
    username = confServerUser

    # password = "Lab4man1"
    password = confServerPwd

    if((confPath is None) or (confPath is "")):
        confPath = "cnos_config"

    retVal = ""

    # config backup command happens here
    if(protocol == "ftp"):
        command = "cp startup-config " + protocol + " " + protocol + "://" + \
            username + "@" + server + "/" + confPath + " vrf management\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(password, "#", timeout, obj)
    elif(protocol == "tftp"):
        command = "cp startup-config " + protocol + " " + protocol + \
            "://" + server + "/" + confPath + " vrf management\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "#", 3, obj)
    else:
        return "Error-110"

    return retVal
# EOM

# Utility Method to back up the start up config
# This method supports only SCP or SFTP
# Tuning of timeout parameter is pending


def doSecureStartupConfigBackUp(
        protocol, timeout, confServerIp, confPath, confServerUser,
        confServerPwd, obj):
    # server = "10.241.105.214"
    server = confServerIp

    # username = "pbhosale"
    username = confServerUser

    # password = "Lab4man1"
    password = confServerPwd

    if((confPath is None) or (confPath is "")):
        confPath = "cnos_config"

    retVal = ""

    # config backup command happens here
    command = "cp startup-config " + protocol + " " + protocol + "://" + \
        username + "@" + server + "/" + confPath + " vrf management\n"
    # debugOutput(command)
    response = waitForDeviceResponse(command, "(yes/no)", 3, obj)
    if(response.lower().find("error-101")):
        command = password + "\n"
        retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)
        return retVal
    retVal = retVal + response
    if(protocol == "scp"):
        command = "yes \n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "timeout:", 3, obj)
        command = "0\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    elif(protocol == "sftp"):
        command = "yes \n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    else:
        return "Error-110"

    # Password entry happens here
    # debugOutput(command)
    command = password + "\n"
    retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)

    return retVal
# EOM

# Utility Method to restore the Running config
# This method supports only TFTP or FTP
# Tuning of timeout parameter is pending


def doStartUpConfigRollback(
        protocol, timeout, confServerIp, confPath, confServerUser,
        confServerPwd, obj):
    # server = "10.241.105.214"
    server = confServerIp

    # username = "pbhosale"
    username = confServerUser

    # password = "Lab4man1"
    password = confServerPwd

    if((confPath is None) or (confPath is "")):
        confPath = "cnos_config"

    retVal = ""

    # config backup command happens here
    if(protocol == "ftp"):
        command = "cp " + protocol + " " + protocol + "://" + username + \
            "@" + server + "/" + confPath + " startup-config vrf management\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "[n]", timeout, obj)
        command = "y\n"
        retVal = retVal + waitForDeviceResponse(password, "#", timeout, obj)
    elif(protocol == "tftp"):
        command = "cp " + protocol + " " + protocol + "://" + \
            server + "/" + confPath + " startup-config vrf management\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "[n]", timeout, obj)
        command = "y\n"
        retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)
    else:
        return "Error-110"

    return retVal
# EOM

# Utility Method to restore the start up config
# This method supports only SCP or SFTP
# Tuning of timeout parameter is pending


def doSecureStartUpConfigRollback(
        protocol, timeout, confServerIp, confPath, confServerUser,
        confServerPwd, obj):
    # server = "10.241.105.214"
    server = confServerIp

    # username = "pbhosale"
    username = confServerUser

    # password = "Lab4man1"
    password = confServerPwd

    if((confPath is None) or (confPath is "")):
        confPath = "cnos_config"

    retVal = ""

    # config backup command happens here

    # cp sftp sftp://root@10.241.106.118/cnos_config/running_config.conf
    # startup-config vrf management
    command = "cp " + protocol + " " + protocol + "://" + username + \
        "@" + server + "/" + confPath + " startup-config vrf management \n"

    # debugOutput(command)
    response = waitForDeviceResponse(command, "(yes/no)", 3, obj)
    if(response.lower().find("error-101")):
        command = password + "\n"
        retVal = retVal + waitForDeviceResponse(command, "[n]", timeout, obj)
        command = "y\n"
        retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)
        return retVal
    retVal = retVal + response
    if(protocol == "scp"):
        command = "yes \n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "timeout:", 3, obj)
        command = "0\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    elif(protocol == "sftp"):
        command = "yes \n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    else:
        return "Error-110"

    # Password entry happens here
    # debugOutput(command)
    command = password + "\n"
    retVal = retVal + waitForDeviceResponse(command, "[n]", timeout, obj)
    command = "y\n"
    retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)

    return retVal
# EOM

# Utility Method to back up the Running config
# This method supports only TFTP or FTP
# Tuning of timeout parameter is pending


def doRunningConfigBackUp(
        protocol, timeout, confServerIp, confPath, confServerUser,
        confServerPwd, obj):
    # server = "10.241.105.214"
    server = confServerIp

    # username = "pbhosale"
    username = confServerUser

    # password = "Lab4man1"
    password = confServerPwd

    if((confPath is None) or (confPath is "")):
        confPath = "cnos_config"

    retVal = ""

    # config backup command happens here
    if(protocol == "ftp"):
        command = "cp running-config " + protocol + " " + protocol + "://" + \
            username + "@" + server + "/" + confPath + " vrf management\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(password, "#", timeout, obj)
    elif(protocol == "tftp"):
        command = "cp running-config " + protocol + " " + protocol + \
            "://" + server + "/" + confPath + " vrf management\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "#", 3, obj)
    else:
        return "Error-110"

    return retVal
# EOM


# Utility Method to back up the running config
# This method supports only SCP or SFTP
# Tuning of timeout parameter is pending
def doSecureRunningConfigBackUp(
        protocol, timeout, confServerIp, confPath, confServerUser,
        confServerPwd, obj):
    # server = "10.241.105.214"
    server = confServerIp

    # username = "pbhosale"
    username = confServerUser

    # password = "Lab4man1"
    password = confServerPwd

    if((confPath is None) or (confPath is "")):
        confPath = "cnos_config"

    retVal = ""

    # config backup command happens here
    command = "cp running-config " + protocol + " " + protocol + "://" + \
        username + "@" + server + "/" + confPath + " vrf management\n"
    # debugOutput(command)
    response = waitForDeviceResponse(command, "(yes/no)", 3, obj)
    if(response.lower().find("error-101")):
        command = password + "\n"
        retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)
        return retVal
    retVal = retVal + response
    if(protocol == "scp"):
        command = "yes \n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "timeout:", 3, obj)
        command = "0\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    elif(protocol == "sftp"):
        command = "yes \n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    else:
        return "Error-110"

    # Password entry happens here
    # debugOutput(command)
    command = password + "\n"
    retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)

    return retVal
# EOM

# Utility Method to restore the Running config
# This method supports only TFTP or FTP
# Tuning of timeout parameter is pending


def doRunningConfigRollback(
        protocol, timeout, confServerIp, confPath, confServerUser,
        confServerPwd, obj):
    # server = "10.241.105.214"
    server = confServerIp

    # username = "pbhosale"
    username = confServerUser

    # password = "Lab4man1"
    password = confServerPwd

    if((confPath is None) or (confPath is "")):
        confPath = "cnos_config"

    retVal = ""

    # config backup command happens here
    if(protocol == "ftp"):
        command = "cp " + protocol + " " + protocol + "://" + username + \
            "@" + server + "/" + confPath + " running-config vrf management\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(password, "#", timeout, obj)
    elif(protocol == "tftp"):
        command = "cp " + protocol + " " + protocol + "://" + \
            server + "/" + confPath + " running-config vrf management\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)
    else:
        return "Error-110"

    return retVal
# EOM

# Utility Method to restore the running config
# This method supports only SCP or SFTP
# Tuning of timeout parameter is pending


def doSecureRunningConfigRollback(
        protocol, timeout, confServerIp, confPath, confServerUser,
        confServerPwd, obj):
    # server = "10.241.105.214"
    server = confServerIp

    # username = "pbhosale"
    username = confServerUser

    # password = "Lab4man1"
    password = confServerPwd

    if((confPath is None) or (confPath is "")):
        confPath = "cnos_config"

    retVal = ""

    # config backup command happens here

    # cp sftp sftp://root@10.241.106.118/cnos_config/running_config.conf
    # running-config vrf management
    command = "cp " + protocol + " " + protocol + "://" + username + \
        "@" + server + "/" + confPath + " running-config vrf management \n"

    # debugOutput(command)
    response = waitForDeviceResponse(command, "(yes/no)", 3, obj)
    if(response.lower().find("error-101")):
        command = password + "\n"
        retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)
        return retVal
    retVal = retVal + response

    if(protocol == "scp"):
        command = "yes \n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "timeout:", 3, obj)
        command = "0\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    elif(protocol == "sftp"):
        command = "yes \n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    else:
        return "Error-110"

    # Password entry happens here
    # debugOutput(command)
    command = password + "\n"
    retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)

    return retVal
# EOM

# Utility Method to download an image from FTP/TFTP server to device.
# This method supports only FTP or TFTP
# Tuning of timeout parameter is pending


def doImageTransfer(
    protocol, timeout, imgServerIp, imgPath, imgType, imgServerUser,
        imgServerPwd, obj):
    # server = "10.241.106.118"
    server = imgServerIp
    # username = "root"
    username = imgServerUser
    # password = "root123"
    password = imgServerPwd

    type = "os"
    if(imgType is not None):
        type = imgType.lower()

    if((imgPath is None) or (imgPath is "")):
        imgPath = "cnos_images"

    retVal = ""

    # Image transfer command happens here
    if(protocol == "ftp"):
        command = "cp " + protocol + " " + protocol + "://" + username + \
            "@" + server + "/" + imgPath + " system-image " + type + \
            " vrf management\n"
    elif(protocol == "tftp"):
        command = "cp " + protocol + " " + protocol + "://" + server + \
            "/" + imgPath + " system-image " + type + " vrf management\n"
    else:
        return "Error-110"
    # debugOutput(command)
    response = waitForDeviceResponse(command, "[n]", 3, obj)
    if(response.lower().find("error-101")):
        retVal = retVal
    else:
        retVal = retVal + response

    # Confirmation command happens here
    command = "y\n"
    # debugOutput(command)
    if(protocol == "ftp"):
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
        # Password entry happens here Only for FTP
        command = password + " \n"
        # debugOutput(command)
    # Change to standby image y
    retVal = retVal + waitForDeviceResponse(command, "[n]", timeout, obj)
    command = "y\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)
    return retVal
# EOM

# Utility Method to download an image from SFTP/SCP server to device.
# This method supports only SCP or SFTP
# Tuning of timeout parameter is pending


def doSecureImageTransfer(
    protocol, timeout, imgServerIp, imgPath, imgType, imgServerUser,
        imgServerPwd, obj):
    # server = "10.241.105.214"
    server = imgServerIp
    # username = "pbhosale"
    username = imgServerUser
    # password = "Lab4man1"
    password = imgServerPwd

    type = "scp"
    if(imgType is not None):
        type = imgType.lower()

    if((imgPath is None) or (imgPath is "")):
        imgPath = "cnos_images"

    retVal = ""

    # Image transfer command happens here
    command = "cp " + protocol + " " + protocol + "://" + username + "@" + \
        server + "/" + imgPath + " system-image " + type + " vrf management \n"
    # debugOutput(command)
    response = waitForDeviceResponse(command, "[n]", 3, obj)
    if(response.lower().find("error-101")):
        retVal = retVal
    else:
        retVal = retVal + response
    # Confirmation command happens here
    if(protocol == "scp"):
        command = "y\n"
        # debugOutput(command)
        response = waitForDeviceResponse(command, "(yes/no)?", 3, obj)
        if(response.lower().find("error-101")):
            retVal = retVal
        else:
            retVal = retVal + response
        command = "Yes\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "timeout:", 3, obj)
        command = "0\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    elif(protocol == "sftp"):
        command = "y\n"
        # debugOutput(command)
        response = waitForDeviceResponse(command, "(yes/no)?", 3, obj)
        if(response.lower().find("error-101")):
            retVal = retVal
        else:
            retVal = retVal + response

        command = "Yes\n"
        # debugOutput(command)
        retVal = retVal + waitForDeviceResponse(command, "Password:", 3, obj)
    else:
        return "Error-110"

    # Password entry happens here
    command = password + "\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, "[n]", timeout, obj)
    # Change to standby image y
    command = "y\n"
    # debugOutput(command)
    retVal = retVal + waitForDeviceResponse(command, "#", timeout, obj)
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
    index = output.lower().find("error")
    startIndex = index + 6
    if(index == -1):
        index = output.lower().find("invalid")
        startIndex = index + 8
        if(index == -1):
            index = output.lower().find("cannot be enabled in l2 interface")
            startIndex = index + 34
            if(index == -1):
                index = output.lower().find("incorrect")
                startIndex = index + 10
                if(index == -1):
                    index = output.lower().find("failure")
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
        except socket.Error:
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
        except socket.Error:
            result = False
        if(result is True):
            return "ok"
        else:
            return "Error-121"

    elif(variableType == "IPV6Address"):
        try:
            socket.inet_pton(socket.AF_INET6, variableValue)
            result = True
        except socket.Error:
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
    f = open('debugOuput.txt', 'a')
    f.write(str(command))  # python will convert \n to os.linesep
    f.close()  # you can omit in most cases as the destructor will call it
# EOM
