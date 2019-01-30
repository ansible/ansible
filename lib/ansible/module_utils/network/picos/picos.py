""" #!/usr/bin/python """
# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2019, Pica8 <simon.yang@pica8.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
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

# shell_pattern = "/bin/sh -c '%s'"
shell_pattern = "/pica/bin/pica_sh -c 'start shell sh;%s;exit'"
cli_pattern = "/pica/bin/pica_sh -c '%s'"
config_pattern = "/pica/bin/pica_sh -c 'configure;%s;exit'"
config_commit_pattern = "/pica/bin/pica_sh -c 'configure;%s;commit'"
config_script_pattern = "/pica/bin/pica_sh -c 'configure;execute %s;commit'"


def command_helper(module, command, command_pattern, errmsg=None):
    """Run a command, catch any errors"""
    (_rc, output, _err) = module.run_command(command_pattern % command, use_unsafe_shell=True)
    if _rc or 'ERROR' in output or 'ERROR' in _err:
        module.fail_json(msg=errmsg or output)
    return str(output)


def run_command(module, command_list, command_string, command_pattern, description=''):
    commands = []
    if command_list:
        commands = command_list
    elif command_string:
        if ';' in command_string:
            commands = command_string.split(';')
        else:
            commands = command_string.splitlines()

    # Run all of the net commands
    output_lines = []
    if description != '':
        output_lines.append(description)
    for line in commands:
        if line.strip():
            output_lines += [command_helper(module, line.strip(), command_pattern, "Failed on line: %s" % line)]
    output = "\n".join(output_lines)
    return output


def run_commands(module, commands):
    if isinstance(commands, list):
        return run_command(module, commands, None, shell_pattern)
    elif isinstance(commands, str):
        return run_command(module, None, commands, shell_pattern)
    else:
        e = 'Error in run_commands() - invalid parameter: commands=%s' % commands
        return list([e])
