#
# Copyright (c) 2017 Tim Rupp, <caphrim007@gmail.com>
# Copyright (c) 2017 F5 Networks Inc.
#
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

from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.shell import CliBase


class Cli(CliBase):

    CLI_PROMPTS_RE = [
        # One of the default prompts on 12.x
        re.compile(r"\[\w+\@[\w\-\.]+"),

        # Found on 11.6.1
        re.compile(r"[\w-]+\@\([\w\-\.]+\)"),
    ]

    CLI_ERRORS_RE = [
        re.compile(r"connection timed out", re.I),
        re.compile(r"syntax error: unexpected argument", re.I)
    ]

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, kickstart=False, **kwargs)

    def supports_tmos(self):
        conn = get_connection(self)
        rc, out, err = self.exec_command('show configuration sessions')
        return rc == 0


Cli = register_transport('cli', default=True)(Cli)
