# Collect facts related to the system package manager
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

import os

from ansible.module_utils.facts.collector import BaseFactCollector

# A list of dicts.  If there is a platform with more than one
# package manager, put the preferred one last.  If there is an
# ansible module, use that as the value for the 'name' key.
PKG_MGRS = [{'path': '/usr/bin/yum', 'name': 'yum'},
            {'path': '/usr/bin/dnf', 'name': 'dnf'},
            {'path': '/usr/bin/apt-get', 'name': 'apt'},
            {'path': '/usr/bin/zypper', 'name': 'zypper'},
            {'path': '/usr/sbin/urpmi', 'name': 'urpmi'},
            {'path': '/usr/bin/pacman', 'name': 'pacman'},
            {'path': '/bin/opkg', 'name': 'opkg'},
            {'path': '/usr/pkg/bin/pkgin', 'name': 'pkgin'},
            {'path': '/opt/local/bin/pkgin', 'name': 'pkgin'},
            {'path': '/opt/tools/bin/pkgin', 'name': 'pkgin'},
            {'path': '/opt/local/bin/port', 'name': 'macports'},
            {'path': '/usr/local/bin/brew', 'name': 'homebrew'},
            {'path': '/sbin/apk', 'name': 'apk'},
            {'path': '/usr/sbin/pkg', 'name': 'pkgng'},
            {'path': '/usr/sbin/swlist', 'name': 'HP-UX'},
            {'path': '/usr/bin/emerge', 'name': 'portage'},
            {'path': '/usr/sbin/pkgadd', 'name': 'svr4pkg'},
            {'path': '/usr/bin/pkg', 'name': 'pkg5'},
            {'path': '/usr/bin/xbps-install', 'name': 'xbps'},
            {'path': '/usr/local/sbin/pkg', 'name': 'pkgng'},
            {'path': '/usr/bin/swupd', 'name': 'swupd'},
            {'path': '/usr/sbin/sorcery', 'name': 'sorcery'},
            {'path': '/usr/bin/rpm-ostree', 'name': 'atomic_container'},
            ]


class OpenBSDPkgMgrFactCollector(BaseFactCollector):
    name = 'pkg_mgr'
    _fact_ids = set()
    _platform = 'OpenBSD'

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}

        facts_dict['pkg_mgr'] = 'openbsd_pkg'
        return facts_dict


# the fact ends up being 'pkg_mgr' so stick with that naming/spelling
class PkgMgrFactCollector(BaseFactCollector):
    name = 'pkg_mgr'
    _fact_ids = set()
    _platform = 'Generic'
    required_facts = set(['distribution'])

    def _check_fedora_versions(self, collected_facts):
        try:
            if int(collected_facts['ansible_distribution_major_version']) < 15:
                pkg_mgr_name = 'yum'
            else:
                pkg_mgr_name = 'dnf'
        except ValueError:
            # If there's some new magical Fedora version in the future,
            # just default to dnf
            pkg_mgr_name = 'dnf'
        return pkg_mgr_name

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        collected_facts = collected_facts or {}

        pkg_mgr_name = 'unknown'
        for pkg in PKG_MGRS:
            if os.path.exists(pkg['path']):
                pkg_mgr_name = pkg['name']

        # apt is easily installable and supported by distros other than those
        # that are debian based, this handles some of those scenarios as they
        # are reported/requested
        if pkg_mgr_name == 'apt' and collected_facts['ansible_os_family'] in ["RedHat", "Altlinux"]:
            if collected_facts['ansible_distribution'] == 'Fedora':
                pkg_mgr_name = self._check_fedora_versions(collected_facts)

            elif collected_facts['ansible_distribution'] == 'ALT Linux':
                pkg_mgr_name = 'apt_rpm'

        # pacman has become available by distros other than those that are Arch
        # based by virtue of a dependency to the systemd mkosi project, this
        # handles some of those scenarios as they are reported/requested
        if pkg_mgr_name == 'pacman' and collected_facts['ansible_os_family'] in ["RedHat"]:
            if collected_facts['ansible_distribution'] == 'Fedora':
                pkg_mgr_name = self._check_fedora_versions(collected_facts)

        facts_dict['pkg_mgr'] = pkg_mgr_name
        return facts_dict
