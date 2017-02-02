# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
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
import os
import time

from ansible.module_utils.network_common import to_list

_DEVICE_CONFIGS = {}

def get_config(module, flags=[]):
    cmd = 'show running-config '
    cmd += ' '.join(flags)
    cmd = cmd.strip()

    try:
        return _DEVICE_CONFIGS[cmd]
    except KeyError:
        rc, out, err = module.exec_command(cmd)
        if rc != 0:
            module.fail_json(msg='unable to retrieve current config', stderr=err)
        cfg = str(out).strip()
        _DEVICE_CONFIGS[cmd] = cfg
        return cfg

def check_authorization(module):
    for cmd in ['show clock', 'prompt()']:
        rc, out, err = module.exec_command(cmd)
    return out.endswith('#')

def supports_sessions(module):
    rc, out, err = module.exec_command('show configuration sessions')
    return rc == 0

def run_commands(module, commands):
    """Run list of commands on remote device and return results
    """
    responses = list()

    for cmd in to_list(commands):
        cmd = module.jsonify(cmd)
        rc, out, err = module.exec_command(cmd)

        if rc != 0:
            module.fail_json(msg=err)

        try:
            out = module.from_json(out)
        except ValueError:
            out = str(out).strip()

        responses.append(out)
    return responses

def send_config(module, commands):
    multiline = False
    for command in to_list(commands):
        if command == 'end':
            pass

        if command.startswith('banner') or multiline:
            multiline = True
            command = module.jsonify({'command': command, 'sendonly': True})
        elif command == 'EOF' and multiline:
            multiline = False

        rc, out, err = module.exec_command(command)
        if rc != 0:
            return (rc, out, err)
    return (rc, 'ok','')


def configure(module, commands):
    """Sends configuration commands to the remote device
    """
    if not check_authorization(module):
        module.fail_json(msg='configuration operations require privilege escalation')

    rc, out, err = module.exec_command('configure')
    if rc != 0:
        module.fail_json(msg='unable to enter configuration mode', output=err)

    rc, out, err = send_config(module, commands)
    if rc != 0:
        module.fail_json(msg=err)

    module.exec_command('end')
    return {}

def load_config(module, commands, commit=False, replace=False):
    """Loads the config commands onto the remote device
    """
    if not check_authorization(module):
        module.fail_json(msg='configuration operations require privilege escalation')

    use_session = os.getenv('ANSIBLE_EOS_USE_SESSIONS', True)
    try:
        use_session = int(use_session)
    except ValueError:
        pass

    if not all((bool(use_session), supports_sessions(module))):
        return configure(module, commands)

    session = 'ansible_%s' % int(time.time())

    result = {'session': session}

    rc, out, err = module.exec_command('configure session %s' % session)
    if rc != 0:
        module.fail_json(msg='unable to enter configuration mode', output=err)

    if replace:
        module.exec_command('rollback clean-config', check_rc=True)

    rc, out, err = send_config(module, commands)
    if rc != 0:
        module.exec_command('abort')
        module.fail_json(msg=err, commands=commands)

    rc, out, err = module.exec_command('show session-config diffs')
    if rc == 0:
        result['diff'] = out.strip()

    if commit:
        module.exec_command('commit')
    else:
        module.exec_command('abort')

    return result
