# Collect facts related to the system package manager

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import subprocess
import typing as t

from ansible.module_utils.facts.collector import BaseFactCollector

# A list of dicts.  If there is a platform with more than one
# package manager, put the preferred one last.  If there is an
# ansible module, use that as the value for the 'name' key.
PKG_MGRS = [{'path': '/usr/bin/rpm-ostree', 'name': 'atomic_container'},

            # NOTE the `path` key for dnf/dnf5 is effectively discarded when matched for Red Hat OS family,
            # special logic to infer the default `pkg_mgr` is used in `PkgMgrFactCollector._check_rh_versions()`
            # leaving them here so a list of package modules can be constructed by iterating over `name` keys
            {'path': '/usr/bin/yum', 'name': 'dnf'},
            {'path': '/usr/bin/dnf-3', 'name': 'dnf'},
            {'path': '/usr/bin/dnf5', 'name': 'dnf5'},

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
            {'path': '/opt/homebrew/bin/brew', 'name': 'homebrew'},
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
            {'path': '/usr/bin/installp', 'name': 'installp'},
            ]


class OpenBSDPkgMgrFactCollector(BaseFactCollector):
    name = 'pkg_mgr'
    _fact_ids = set()  # type: t.Set[str]
    _platform = 'OpenBSD'

    def collect(self, module=None, collected_facts=None):
        return {'pkg_mgr': 'openbsd_pkg'}


# the fact ends up being 'pkg_mgr' so stick with that naming/spelling
class PkgMgrFactCollector(BaseFactCollector):
    name = 'pkg_mgr'
    _fact_ids = set()  # type: t.Set[str]
    _platform = 'Generic'
    required_facts = set(['distribution'])

    def __init__(self, *args, **kwargs):
        super(PkgMgrFactCollector, self).__init__(*args, **kwargs)
        self._default_unknown_pkg_mgr = 'unknown'

    def _check_rh_versions(self):
        if os.path.exists('/run/ostree-booted'):
            return "atomic_container"

        # Since /usr/bin/dnf and /usr/bin/microdnf can point to different versions of dnf in different distributions
        # the only way to infer the default package manager is to look at the binary they are pointing to.
        # /usr/bin/microdnf is likely used only in fedora minimal container so /usr/bin/dnf takes precedence
        for bin_path in ('/usr/bin/dnf', '/usr/bin/microdnf'):
            if os.path.exists(bin_path):
                return 'dnf5' if os.path.realpath(bin_path) == '/usr/bin/dnf5' else 'dnf'

        return self._default_unknown_pkg_mgr

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

    def pkg_mgrs(self, collected_facts):
        # Filter out the /usr/bin/pkg because on Altlinux it is actually the
        # perl-Package (not Solaris package manager).
        # Since the pkg5 takes precedence over apt, this workaround
        # is required to select the suitable package manager on Altlinux.
        if collected_facts['ansible_os_family'] == 'Altlinux':
            return filter(lambda pkg: pkg['path'] != '/usr/bin/pkg', PKG_MGRS)
        else:
            return PKG_MGRS

    def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}

        pkg_mgr_name = self._default_unknown_pkg_mgr
        for pkg in self.pkg_mgrs(collected_facts):
            if os.path.exists(pkg['path']):
                pkg_mgr_name = pkg['name']

        # Handle distro family defaults when more than one package manager is
        # installed or available to the distro, the ansible_fact entry should be
        # the default package manager officially supported by the distro.
        if collected_facts['ansible_os_family'] == "RedHat":
            pkg_mgr_name = self._check_rh_versions()
        elif collected_facts['ansible_os_family'] == 'Debian' and pkg_mgr_name != 'apt':
            # It's possible to install dnf, zypper, rpm, etc inside of
            # Debian. Doing so does not mean the system wants to use them.
            pkg_mgr_name = 'apt'
        elif collected_facts['ansible_os_family'] == 'Altlinux':
            if pkg_mgr_name == 'apt':
                pkg_mgr_name = 'apt_rpm'

        # Check if /usr/bin/apt-get is ordinary (dpkg-based) APT or APT-RPM
        if pkg_mgr_name == 'apt':
            pkg_mgr_name = self._check_apt_flavor(pkg_mgr_name)

        return {'pkg_mgr': pkg_mgr_name}
