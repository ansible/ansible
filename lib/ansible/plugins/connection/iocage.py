# based on jail.py    (c) 2013, Michael Scherer <misc@zarb.org>
#                     (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2016, Stephan Lohse <dev-github@ploek.org>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import subprocess
from ansible.plugins.connection.jail import Connection as Jail

from ansible.errors import AnsibleError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(Jail):
    ''' Local iocage based connections '''

    transport = 'iocage'

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        self.ioc_jail = play_context.remote_addr

        self.iocage_cmd = Jail._search_executable('iocage')

        jail_uuid = self.get_jail_uuid()

        kwargs[Jail.modified_jailname_key] = 'ioc-{}'.format(jail_uuid)

        display.vvv(u"Jail {iocjail} has been translated to {rawjail}".format(
            iocjail=self.ioc_jail, rawjail=kwargs[Jail.modified_jailname_key]),
            host=kwargs[Jail.modified_jailname_key])

        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

    def get_jail_uuid(self):
        p = subprocess.Popen([self.iocage_cmd, 'get', 'host_hostuuid', self.ioc_jail],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

        stdout, stderr = p.communicate()
        # otherwise p.returncode would not be set
        p.wait()

        if p.returncode != 0:
            raise AnsibleError(u"iocage returned an error: {}".format(stdout))

        return stdout.strip('\n')

