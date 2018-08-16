# Based on jail.py
# (c) 2013, Michael Scherer <misc@zarb.org>
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2016, Stephan Lohse <dev-github@ploek.org>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Stephan Lohse <dev-github@ploek.org>
    connection: iocage
    short_description: Run tasks in iocage jails
    description:
        - Run commands or put/fetch files to an existing iocage jail
    version_added: "2.0"
    options:
      remote_addr:
        description:
            - Path to the jail
        default: The set user as per docker's configuration
        vars:
            - name: ansible_host
            - name: ansible_iocage_host
      remote_user:
        description:
            - User to execute as inside the jail
        vars:
            - name: ansible_user
            - name: ansible_iocage_user
"""

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

        kwargs[Jail.modified_jailname_key] = 'ioc-{0}'.format(jail_uuid)

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
            raise AnsibleError(u"iocage returned an error: {0}".format(stdout))

        return stdout.strip('\n')
