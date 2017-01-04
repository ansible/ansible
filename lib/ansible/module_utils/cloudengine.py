# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
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
import time

from ansible.module_utils.basic import json
from ansible.module_utils.network import NetworkError
from ansible.module_utils.network import add_argument,\
    register_transport, to_list
from ansible.module_utils.shell import CliBase

try:
    from ncclient import manager
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False
    pass


add_argument('use_ssl', dict(default=False, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))


def ce_unknown_host_cb(host, fingerprint):
    """ ce_unknown_host_cb """

    return True


class CeConfigMixin(object):
    """ CeConfigMixin """

    def get_config(self, include_defaults=False, include_all=False, regular="", **kwargs):
        """ get_config """

        cmd = 'display current-configuration '
        if include_all:
            cmd += ' all'
        if include_defaults:
            cmd += ' include-default'
        if regular:
            cmd += ' ' + regular

        return self.execute([cmd])[0]

    def load_config(self, config):
        """ load_config """

        checkpoint = 'ansible_%s' % int(time.time())
        try:
            self.execute(['system-view immediately',
                          'commit label %s' % checkpoint], output='text')
        except TypeError:
            self.execute(['system-view immediately',
                          'commit label %s' % checkpoint])

        try:
            try:
                self.configure(config)
            except NetworkError:
                self.load_checkpoint(checkpoint)
                raise
        finally:
            # get commit id and clear it
            responses = self.execute(
                'display configuration commit list '
                'label | include %s' % checkpoint)
            match = re.match(
                r'[\r\n]?\d+\s+(\d{10})\s+ansible.*', responses[0])
            if match is not None:
                try:
                    self.execute(['return',
                                  'clear configuration commit %s '
                                  'label' % match.group(1)], output='text')
                except TypeError:
                    self.execute(['return',
                                  'clear configuration commit %s '
                                  'label' % match.group(1)])

    def save_config(self, **kwargs):
        """ save_config """

        try:
            self.execute(['return', 'save'], output='text')
        except TypeError:
            self.execute(['return', 'save'])

    def load_checkpoint(self, checkpoint):
        """ load_checkpoint """

        try:
            self.execute(
                ['return', 'rollback configuration to '
                           'label %s' % checkpoint], output='text')
        except TypeError:
            self.execute(
                ['return', 'rollback configuration to'
                           ' label %s' % checkpoint])
        pass


class Netconf(object):
    """ Netconf """

    def __init__(self, **kwargs):

        if not HAS_NCCLIENT:
            raise Exception("the ncclient library is required")

        self.mc = None

        host = kwargs["host"]
        port = kwargs["port"]
        username = kwargs["username"]
        password = kwargs["password"]

        self.mc = manager.connect(host=host, port=port,
                                  username=username,
                                  password=password,
                                  unknown_host_cb=ce_unknown_host_cb,
                                  allow_agent=False,
                                  look_for_keys=False,
                                  hostkey_verify=False,
                                  device_params={'name': 'huawei'},
                                  timeout=30)

    def __del__(self):

        self.mc.close_session()

    def set_config(self, **kwargs):
        """ set_config """

        confstr = kwargs["config"]
        con_obj = self.mc.edit_config(target='running', config=confstr)

        return con_obj

    def get_config(self, **kwargs):
        """ get_config """

        filterstr = kwargs["filter"]
        con_obj = self.mc.get(filter=filterstr)

        return con_obj

    def execute_action(self, **kwargs):
        """huawei execute-action"""

        confstr = kwargs["action"]
        con_obj = self.mc.action(action=confstr)

        return con_obj

    def execute_cli(self, **kwargs):
        """huawei execute-cli"""

        confstr = kwargs["command"]
        con_obj = self.mc.cli(command=confstr)

        return con_obj


def get_netconf(**kwargs):
    """ get_netconf """

    return Netconf(**kwargs)


class Cli(CeConfigMixin, CliBase):
    """ Cli """

    CLI_PROMPTS_RE = [
        re.compile(r'[\r\n]?[<|\[]{1}.+[>|\]]{1}(?:\s*)$'),
    ]

    CLI_ERRORS_RE = [
        re.compile(r"% ?Error: "),
        re.compile(r"^% \w+", re.M),
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
        re.compile(r"syntax error"),
        re.compile(r"unknown command"),
        re.compile(r"Error\[\d+\]: ")
    ]

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def connect(self, params, **kwargs):
        """ connect """

        super(Cli, self).connect(params, kickstart=False, **kwargs)
        self.shell.send('screen-length 0 temporary')
        self.shell.send('mmi-mode enable')

    def run_commands(self, commands):
        """ run_commands """

        cmds = list(prepare_commands(commands))
        responses = self.execute(cmds)
        for index, cmd in enumerate(commands):
            raw = cmd.args.get('raw') or False
            if cmd.output == 'json' and not raw:
                try:
                    responses[index] = json.loads(responses[index])
                except ValueError:
                    raise NetworkError(
                        msg='unable to load response from device',
                        response=responses[index], command=str(cmd)
                    )
        return responses

    def configure(self, commands, **kwargs):
        """ configure """

        commands = prepare_config(commands)
        responses = self.execute(commands)
        responses.pop(0)
        return responses

Cli = register_transport('cli', default=True)(Cli)


def prepare_config(commands):
    """ prepare_config """

    prepared = list()
    prepared.extend(to_list(commands))
    prepared.append('return')
    return prepared


def prepare_commands(commands):
    """ prepare_commands """

    jsonify = lambda x: '%s | json' % x
    for cmd in to_list(commands):
        if cmd.output == 'json':
            cmd.command_string = jsonify(cmd)
        if cmd.command.endswith('| json'):
            cmd.output = 'json'
        yield cmd
