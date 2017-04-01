#!/usr/bin/python
# -*- coding: utf-8 -*-

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
# You should have received a copy of the GNU General Public licenses
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: rpmostree_compose
short_description: Compose OSTree
description:
    - Entrypoint for tree composition, used on servers to prepare trees for replication by client systems
version_added: "2.4"
author: "Trishna Guha @trishnaguha"
notes:
    - Distribution should be Red Hat based (RHEL, CentOS, Fedora)
requirements:
    - rpm-ostree
    - "python >= 2.6"
options:
    repo:
        description:
            - Path to OSTree repository
        required: True
        default: None
    cachedir:
        description:
            - Cached state
        required: False
        default: None
    manifest:
        description:
            - The manifest docker-json TREEFILE required for compose
        required: True
        default: None
'''

EXAMPLES = '''
---
# rpm-ostree compose
- rpmostree_compose:
    repo: /srv/repo
    cachedir: /srv/cache
    manifest: /path/to/fedora-atomic-docker-host.json
'''

RETURN = '''
changed: [hostname]
'''

import os
from ansible.module_utils.basic import AnsibleModule


class RPMOSTreeCompose(object):

    def __init__(self, module):
        self.module = module

    @property
    def distribution(self):
        """
        Returns distribution RHEL/ CentOS/ Fedora <str>
        """
        with open('/etc/os-release', 'r') as release_file:
            for data in release_files:
                if data.startswith('ID='):
                    return data.split('=')[-1].strip()

    @property
    def is_yum(self):
        """
        Returns True if package manger is YUM
        """
        if self.distribution in ["rhel", "centos"]:
            return True
        return False

    @property
    def is_dnf(self):
        """
        Returns True if package manager is DNF
        """
        if self.distribution == 'fedora':
            return True
        return False

    @property
    def is_installed(self):
        """
        Returns True if rpm-ostree is installed
        """
        (rc, out, err) = self.module.run_command("rpm -q rpm-ostree")
        if rc == 0:
            return True
        return False

    @property
    def is_atomic(self):
        """
        Returns True if platform is Atomic host
        """
        if os.path.exists("/run/ostree-booted"):
            return True
        return False

    def install_rpmostree(self):
        """
        Installs RPM-OSTree package
        """
        if self.is_yum:
            self.module.run_command("yum -y install rpm-ostree")
        elif self.is_dnf:
            self.module.run_command("dnf -y install rpm-ostree")

    def compose(self):
        """
        Performs the compose of OSTree
        """
        params = self.module.params
        repo = params['repo']
        cachedir = params['cachedir']
        manifest = params['manifest']

        self.module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')

        if not self.is_atomic:
            if not self.is_installed:
                self.install_rpmostree()

        if cachedir is None:
            args = 'rpm-ostree compose tree --repo={1} {2}'.format(repo, manifest)
        else:
            args = 'rpm-ostree compose tree --cachedir={0} --repo={1} {2}'.format(cachedir, repo, manifest)

        self.module.run_command(args)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(default=None, required=True),
            cachedir=dict(default=None, required=False),
            manifest=dict(default=None, required=True),
        ),
    )
    changed = False
    try:
        com = RPMOSTreeCompose(module)
        com.compose()
        changed = True
        module.exit_json(changed=changed)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
