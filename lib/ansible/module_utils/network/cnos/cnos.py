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
import json
try:
    from ansible.module_utils.network.cnos import cnos_errorcodes
    from ansible.module_utils.network.cnos import cnos_devicerules
    HAS_LIB = True
except Exception:
    HAS_LIB = False
from distutils.cmd import Command
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.network.common.utils import to_list, EntityCollection
from ansible.module_utils.connection import Connection, exec_command
from ansible.module_utils.connection import ConnectionError

_DEVICE_CONFIGS = {}
_CONNECTION = None
_VALID_USER_ROLES = ['network-admin', 'network-operator']

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


def get_user_roles():
    return _VALID_USER_ROLES


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


def get_capabilities(module):
    if hasattr(module, '_cnos_capabilities'):
        return module._cnos_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._cnos_capabilities = json.loads(capabilities)
    return module._cnos_capabilities


def load_config(module, config):
    try:
        conn = get_connection(module)
        conn.get('enable')
        resp = conn.edit_config(config)
        return resp.get('response')
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
        except Exception:
            retVal = retVal + "\n Error-101"
            flag = True
    if(retVal == ""):
        retVal = "\n Error-101"
    return retVal
# EOM


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
        except Exception:
            # debugOutput(prompt)
            if prompt == "(yes/no)?":
                pass
            elif prompt == "Password:":
                pass
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
