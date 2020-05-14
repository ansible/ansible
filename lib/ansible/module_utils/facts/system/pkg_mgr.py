# Collect facts related to the system package manager

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import subprocess

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
            {'path': '/usr/sbin/swlist', 'name': 'swdepot'},
            {'path': '/usr/bin/emerge', 'name': 'portage'},
            {'path': '/usr/sbin/pkgadd', 'name': 'svr4pkg'},
            {'path': '/usr/bin/pkg', 'name': 'pkg5'},
            {'path': '/usr/bin/xbps-install', 'name': 'xbps'},
            {'path': '/usr/local/sbin/pkg', 'name': 'pkgng'},
            {'path': '/usr/bin/swupd', 'name': 'swupd'},
            {'path': '/usr/sbin/sorcery', 'name': 'sorcery'},
            {'path': '/usr/bin/rpm-ostree', 'name': 'atomic_container'},
            {'path': '/usr/bin/installp', 'name': 'installp'},
            {'path': '/QOpenSys/pkgs/bin/yum', 'name': 'yum'},
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

    def _check_rh_versions(self, pkg_mgr_name, collected_facts):
        if collected_facts['ansible_distribution'] == 'Fedora':
            if os.path.exists('/run/ostree-booted'):
                return "atomic_container"
            try:
                if int(collected_facts['ansible_distribution_major_version']) < 23:
                    for yum in [pkg_mgr for pkg_mgr in PKG_MGRS if pkg_mgr['name'] == 'yum']:
                        if os.path.exists(yum['path']):
                            pkg_mgr_name = 'yum'
                            break
                else:
                    for dnf in [pkg_mgr for pkg_mgr in PKG_MGRS if pkg_mgr['name'] == 'dnf']:
                        if os.path.exists(dnf['path']):
                            pkg_mgr_name = 'dnf'
                            break
            except ValueError:
                # If there's some new magical Fedora version in the future,
                # just default to dnf
                pkg_mgr_name = 'dnf'
        elif collected_facts['ansible_distribution'] == 'Amazon':
            pkg_mgr_name = 'yum'
        else:
            # If it's not one of the above and it's Red Hat family of distros, assume
            # RHEL or a clone. For versions of RHEL < 8 that Ansible supports, the
            # vendor supported official package manager is 'yum' and in RHEL 8+
            # (as far as we know at the time of this writing) it is 'dnf'.
            # If anyone wants to force a non-official package manager then they
            # can define a provider to either the package or yum action plugins.
            if int(collected_facts['ansible_distribution_major_version']) < 8:
                pkg_mgr_name = 'yum'
            else:
                pkg_mgr_name = 'dnf'
        return pkg_mgr_name

    def _check_apt_flavor(self, pkg_mgr_name):
        # Check if '/usr/bin/apt' is APT-RPM or an ordinary (dpkg-based) APT.
        # There's rpm package on Debian, so checking if /usr/bin/rpm exists
        # is not enough. Instead ask RPM if /usr/bin/apt-get belongs to some
        # RPM package.
        rpm_query = '/usr/bin/rpm -q --whatprovides /usr/bin/apt-get'.split()
        if os.path.exists('/usr/bin/rpm'):
            with open(os.devnull, 'w') as null:
                try:
                    subprocess.check_call(rpm_query, stdout=null, stderr=null)
                    pkg_mgr_name = 'apt_rpm'
                except subprocess.CalledProcessError:
                    # No apt-get in RPM database. Looks like Debian/Ubuntu
                    # with rpm package installed
                    pkg_mgr_name = 'apt'
        return pkg_mgr_name

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        collected_facts = collected_facts or {}

        pkg_mgr_name = 'unknown'
        for pkg in PKG_MGRS:
            if os.path.exists(pkg['path']):
                pkg_mgr_name = pkg['name']

        # Handle distro family defaults when more than one package manager is
        # installed or available to the distro, the ansible_fact entry should be
        # the default package manager officially supported by the distro.
        if collected_facts['ansible_os_family'] == "RedHat":
            pkg_mgr_name = self._check_rh_versions(pkg_mgr_name, collected_facts)
        elif collected_facts['ansible_os_family'] == 'Debian' and pkg_mgr_name != 'apt':
            # It's possible to install yum, dnf, zypper, rpm, etc inside of
            # Debian. Doing so does not mean the system wants to use them.
            pkg_mgr_name = 'apt'
        elif collected_facts['ansible_os_family'] == 'Altlinux':
            if pkg_mgr_name == 'apt':
                pkg_mgr_name = 'apt_rpm'

        # Check if /usr/bin/apt-get is ordinary (dpkg-based) APT or APT-RPM
        if pkg_mgr_name == 'apt':
            pkg_mgr_name = self._check_apt_flavor(pkg_mgr_name)

        facts_dict['pkg_mgr'] = pkg_mgr_name
        return facts_dict
