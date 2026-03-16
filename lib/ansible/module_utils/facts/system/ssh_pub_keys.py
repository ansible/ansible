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

from __future__ import annotations

import typing as t

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector


class SshPubKeyFactCollector(BaseFactCollector):
    name = 'ssh_pub_keys'
    _fact_ids = set(['ssh_host_pub_keys',
                     'ssh_host_key_dsa_public',
                     'ssh_host_key_rsa_public',
                     'ssh_host_key_ecdsa_public',
                     'ssh_host_key_ed25519_public'])  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        ssh_pub_key_facts = {}
        algos = ('dsa', 'rsa', 'ecdsa', 'ed25519')

        # list of directories to check for ssh keys
        # used in the order listed here, the first one with keys is used
        keydirs = ['/etc/ssh', '/etc/openssh', '/etc']

        for keydir in keydirs:
            for algo in algos:
                factname = 'ssh_host_key_%s_public' % algo
                if factname in ssh_pub_key_facts:
                    # a previous keydir was already successful, stop looking
                    # for keys
                    return ssh_pub_key_facts
                key_filename = '%s/ssh_host_%s_key.pub' % (keydir, algo)
                keydata = get_file_content(key_filename)
                if keydata is not None:
                    (keytype, key) = keydata.split()[0:2]
                    ssh_pub_key_facts[factname] = key
                    ssh_pub_key_facts[factname + '_keytype'] = keytype

        return ssh_pub_key_facts
