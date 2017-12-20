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
import platform
import re

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector


def get_uname_version(module):
    rc, out, err = module.run_command(['uname', '-v'])
    if rc == 0:
        return out
    return None


def _file_exists(path, allow_empty=False):
    # not finding the file, exit early
    if not os.path.exists(path):
        return False

    # if just the path needs to exists (ie, it can be empty) we are done
    if allow_empty:
        return True

    # file exists but is empty and we dont allow_empty
    if os.path.getsize(path) == 0:
        return False

    # file exists with some content
    return True


class DistributionFiles:
    '''has-a various distro file parsers (os-release, etc) and logic for finding the right one.'''
    # every distribution name mentioned here, must have one of
    #  - allowempty == True
    #  - be listed in SEARCH_STRING
    #  - have a function get_distribution_DISTNAME implemented
    OSDIST_LIST = (
        {'path': '/etc/oracle-release', 'name': 'OracleLinux'},
        {'path': '/etc/slackware-version', 'name': 'Slackware'},
        {'path': '/etc/redhat-release', 'name': 'RedHat'},
        {'path': '/etc/vmware-release', 'name': 'VMwareESX', 'allowempty': True},
        {'path': '/etc/openwrt_release', 'name': 'OpenWrt'},
        {'path': '/etc/system-release', 'name': 'Amazon'},
        {'path': '/etc/alpine-release', 'name': 'Alpine'},
        {'path': '/etc/arch-release', 'name': 'Archlinux', 'allowempty': True},
        {'path': '/etc/os-release', 'name': 'Archlinux'},
        {'path': '/etc/os-release', 'name': 'SUSE'},
        {'path': '/etc/SuSE-release', 'name': 'SUSE'},
        {'path': '/etc/gentoo-release', 'name': 'Gentoo'},
        {'path': '/etc/os-release', 'name': 'Debian'},
        {'path': '/etc/lsb-release', 'name': 'Debian'},
        {'path': '/etc/lsb-release', 'name': 'Mandriva'},
        {'path': '/etc/altlinux-release', 'name': 'Altlinux'},
        {'path': '/etc/sourcemage-release', 'name': 'SMGL'},
        {'path': '/etc/os-release', 'name': 'NA'},
        {'path': '/etc/coreos/update.conf', 'name': 'Coreos'},
        {'path': '/usr/lib/os-release', 'name': 'ClearLinux'},
    )

    SEARCH_STRING = {
        'OracleLinux': 'Oracle Linux',
        'RedHat': 'Red Hat',
        'Altlinux': 'ALT Linux',
        'ClearLinux': 'Clear Linux Software for Intel Architecture',
        'SMGL': 'Source Mage GNU/Linux',
    }

    # We can't include this in SEARCH_STRING because a name match on its keys
    # causes a fallback to using the first whitespace seperated item from the file content
    # as the name. For os-release, that is in form 'NAME=Arch'
    OS_RELEASE_ALIAS = {
        'Archlinux': 'Arch Linux'
    }

    def __init__(self, module):
        self.module = module

    def _get_file_content(self, path):
        return get_file_content(path)

    def _get_dist_file_content(self, path, allow_empty=False):
        # cant find that dist file or it is incorrectly empty
        if not _file_exists(path, allow_empty=allow_empty):
            return False, None

        data = self._get_file_content(path)
        return True, data

    def _parse_dist_file(self, name, dist_file_content, path, collected_facts):
        dist_file_dict = {}
        if name in self.SEARCH_STRING:
            # look for the distribution string in the data and replace according to RELEASE_NAME_MAP
            # only the distribution name is set, the version is assumed to be correct from platform.dist()
            if self.SEARCH_STRING[name] in dist_file_content:
                # this sets distribution=RedHat if 'Red Hat' shows up in data
                dist_file_dict['distribution'] = name
            else:
                # this sets distribution to what's in the data, e.g. CentOS, Scientific, ...
                dist_file_dict['distribution'] = dist_file_content.split()[0]

            return True, dist_file_dict

        if name in self.OS_RELEASE_ALIAS:
            if self.OS_RELEASE_ALIAS[name] in dist_file_content:
                dist_file_dict['distribution'] = name
                return True, dist_file_dict
            return False, dist_file_dict

        # call a dedicated function for parsing the file content
        # TODO: replace with a map or a class
        try:
            # FIXME: most of these dont actually look at the dist file contents, but random other stuff
            distfunc_name = 'parse_distribution_file_' + name
            distfunc = getattr(self, distfunc_name)
            parsed, dist_file_dict = distfunc(name, dist_file_content, path, collected_facts)
            return parsed, dist_file_dict
        except AttributeError as exc:
            print('exc: %s' % exc)
            # this should never happen, but if it does fail quitely and not with a traceback
            return False, dist_file_dict

        return True, dist_file_dict
        # to debug multiple matching release files, one can use:
        # self.facts['distribution_debug'].append({path + ' ' + name:
        #         (parsed,
        #          self.facts['distribution'],
        #          self.facts['distribution_version'],
        #          self.facts['distribution_release'],
        #          )})

    def _guess_distribution(self):
        # try to find out which linux distribution this is
        dist = platform.dist()
        distribution_guess = {}
        distribution_guess['distribution'] = dist[0].capitalize() or 'NA'
        distribution_guess['distribution_version'] = dist[1] or 'NA'
        distribution_guess['distribution_major_version'] = dist[1].split('.')[0] or 'NA'
        distribution_guess['distribution_release'] = dist[2] or 'NA'
        return distribution_guess

    def process_dist_files(self):
        # Try to handle the exceptions now ...
        # self.facts['distribution_debug'] = []
        dist_file_facts = {}

        dist_guess = self._guess_distribution()
        dist_file_facts.update(dist_guess)

        for ddict in self.OSDIST_LIST:
            name = ddict['name']
            path = ddict['path']
            allow_empty = ddict.get('allowempty', False)

            has_dist_file, dist_file_content = self._get_dist_file_content(path, allow_empty=allow_empty)

            # but we allow_empty. For example, ArchLinux with an empty /etc/arch-release and a
            # /etc/os-release with a different name
            if has_dist_file and allow_empty:
                dist_file_facts['distribution'] = name
                dist_file_facts['distribution_file_path'] = path
                dist_file_facts['distribution_file_variety'] = name
                break

            if not has_dist_file:
                # keep looking
                continue

            parsed_dist_file, parsed_dist_file_facts = self._parse_dist_file(name, dist_file_content, path, dist_file_facts)

            # finally found the right os dist file and were able to parse it
            if parsed_dist_file:
                dist_file_facts['distribution'] = name
                dist_file_facts['distribution_file_path'] = path
                # distribution and file_variety are the same here, but distribution
                # will be changed/mapped to a more specific name.
                # ie, dist=Fedora, file_variety=RedHat
                dist_file_facts['distribution_file_variety'] = name
                dist_file_facts['distribution_file_parsed'] = parsed_dist_file
                dist_file_facts.update(parsed_dist_file_facts)
                break

        return dist_file_facts

    # TODO: FIXME: split distro file parsing into its own module or class
    def parse_distribution_file_Slackware(self, name, data, path, collected_facts):
        slackware_facts = {}
        if 'Slackware' not in data:
            return False, slackware_facts  # TODO: remove
        slackware_facts['distribution'] = name
        version = re.findall(r'\w+[.]\w+', data)
        if version:
            slackware_facts['distribution_version'] = version[0]
        return True, slackware_facts

    def parse_distribution_file_Amazon(self, name, data, path, collected_facts):
        amazon_facts = {}
        if 'Amazon' not in data:
            # return False  # TODO: remove   # huh?
            return False, amazon_facts  # TODO: remove
        amazon_facts['distribution'] = 'Amazon'
        amazon_facts['distribution_version'] = data.split()[-1]
        return True, amazon_facts

    def parse_distribution_file_OpenWrt(self, name, data, path, collected_facts):
        openwrt_facts = {}
        if 'OpenWrt' not in data:
            return False, openwrt_facts  # TODO: remove
        openwrt_facts['distribution'] = name
        version = re.search('DISTRIB_RELEASE="(.*)"', data)
        if version:
            openwrt_facts['distribution_version'] = version.groups()[0]
        release = re.search('DISTRIB_CODENAME="(.*)"', data)
        if release:
            openwrt_facts['distribution_release'] = release.groups()[0]
        return True, openwrt_facts

    def parse_distribution_file_Alpine(self, name, data, path, collected_facts):
        alpine_facts = {}
        alpine_facts['distribution'] = 'Alpine'
        alpine_facts['distribution_version'] = data
        return True, alpine_facts

    def parse_distribution_file_SUSE(self, name, data, path, collected_facts):
        suse_facts = {}
        if 'suse' not in data.lower():
            return False, suse_facts  # TODO: remove if tested without this
        if path == '/etc/os-release':
            for line in data.splitlines():
                distribution = re.search("^NAME=(.*)", line)
                if distribution:
                    suse_facts['distribution'] = distribution.group(1).strip('"')
                # example pattern are 13.04 13.0 13
                distribution_version = re.search(r'^VERSION_ID="?([0-9]+\.?[0-9]*)"?', line)
                if distribution_version:
                    suse_facts['distribution_version'] = distribution_version.group(1)
                if 'open' in data.lower():
                    release = re.search(r'^VERSION_ID="?[0-9]+\.?([0-9]*)"?', line)
                    if release:
                        suse_facts['distribution_release'] = release.groups()[0]
                elif 'enterprise' in data.lower() and 'VERSION_ID' in line:
                    # SLES doesn't got funny release names
                    release = re.search(r'^VERSION_ID="?[0-9]+\.?([0-9]*)"?', line)
                    if release.group(1):
                        release = release.group(1)
                    else:
                        release = "0"  # no minor number, so it is the first release
                    suse_facts['distribution_release'] = release
        elif path == '/etc/SuSE-release':
            if 'open' in data.lower():
                data = data.splitlines()
                distdata = get_file_content(path).splitlines()[0]
                suse_facts['distribution'] = distdata.split()[0]
                for line in data:
                    release = re.search('CODENAME *= *([^\n]+)', line)
                    if release:
                        suse_facts['distribution_release'] = release.groups()[0].strip()
            elif 'enterprise' in data.lower():
                lines = data.splitlines()
                distribution = lines[0].split()[0]
                if "Server" in data:
                    suse_facts['distribution'] = "SLES"
                elif "Desktop" in data:
                    suse_facts['distribution'] = "SLED"
                for line in lines:
                    release = re.search('PATCHLEVEL = ([0-9]+)', line)  # SLES doesn't got funny release names
                    if release:
                        suse_facts['distribution_release'] = release.group(1)
                        suse_facts['distribution_version'] = collected_facts['distribution_version'] + '.' + release.group(1)

        return True, suse_facts

    def parse_distribution_file_Debian(self, name, data, path, collected_facts):
        debian_facts = {}
        if 'Debian' in data or 'Raspbian' in data:
            debian_facts['distribution'] = 'Debian'
            release = re.search(r"PRETTY_NAME=[^(]+ \(?([^)]+?)\)", data)
            if release:
                debian_facts['distribution_release'] = release.groups()[0]

            # Last resort: try to find release from tzdata as either lsb is missing or this is very old debian
            if collected_facts['distribution_release'] == 'NA' and 'Debian' in data:
                dpkg_cmd = self.module.get_bin_path('dpkg')
                if dpkg_cmd:
                    cmd = "%s --status tzdata|grep Provides|cut -f2 -d'-'" % dpkg_cmd
                    rc, out, err = self.module.run_command(cmd)
                    if rc == 0:
                        debian_facts['distribution_release'] = out.strip()
        elif 'Ubuntu' in data:
            debian_facts['distribution'] = 'Ubuntu'
            # nothing else to do, Ubuntu gets correct info from python functions
        else:
            return False, debian_facts

        return True, debian_facts

    def parse_distribution_file_Mandriva(self, name, data, path, collected_facts):
        mandriva_facts = {}
        if 'Mandriva' in data:
            mandriva_facts['distribution'] = 'Mandriva'
            version = re.search('DISTRIB_RELEASE="(.*)"', data)
            if version:
                mandriva_facts['distribution_version'] = version.groups()[0]
            release = re.search('DISTRIB_CODENAME="(.*)"', data)
            if release:
                mandriva_facts['distribution_release'] = release.groups()[0]
            mandriva_facts['distribution'] = name
        else:
            return False, mandriva_facts

        return True, mandriva_facts

    def parse_distribution_file_NA(self, name, data, path, collected_facts):
        na_facts = {}
        for line in data.splitlines():
            distribution = re.search("^NAME=(.*)", line)
            if distribution and name == 'NA':
                na_facts['distribution'] = distribution.group(1).strip('"')
            version = re.search("^VERSION=(.*)", line)
            if version and collected_facts['distribution_version'] == 'NA':
                na_facts['distribution_version'] = version.group(1).strip('"')
        return True, na_facts

    def parse_distribution_file_Coreos(self, name, data, path, collected_facts):
        coreos_facts = {}
        # FIXME: pass in ro copy of facts for this kind of thing
        dist = platform.dist()
        distro = dist[0]

        if distro.lower() == 'coreos':
            if not data:
                # include fix from #15230, #15228
                # TODO: verify this is ok for above bugs
                return False, coreos_facts
            release = re.search("^GROUP=(.*)", data)
            if release:
                coreos_facts['distribution_release'] = release.group(1).strip('"')
        else:
            return False, coreos_facts  # TODO: remove if tested without this

        return True, coreos_facts


class Distribution(object):
    """
    This subclass of Facts fills the distribution, distribution_version and distribution_release variables

    To do so it checks the existence and content of typical files in /etc containing distribution information

    This is unit tested. Please extend the tests to cover all distributions if you have them available.
    """

    # every distribution name mentioned here, must have one of
    #  - allowempty == True
    #  - be listed in SEARCH_STRING
    #  - have a function get_distribution_DISTNAME implemented
    OSDIST_LIST = (
        {'path': '/etc/oracle-release', 'name': 'OracleLinux'},
        {'path': '/etc/slackware-version', 'name': 'Slackware'},
        {'path': '/etc/redhat-release', 'name': 'RedHat'},
        {'path': '/etc/vmware-release', 'name': 'VMwareESX', 'allowempty': True},
        {'path': '/etc/openwrt_release', 'name': 'OpenWrt'},
        {'path': '/etc/system-release', 'name': 'Amazon'},
        {'path': '/etc/alpine-release', 'name': 'Alpine'},
        {'path': '/etc/arch-release', 'name': 'Archlinux', 'allowempty': True},
        {'path': '/etc/os-release', 'name': 'SUSE'},
        {'path': '/etc/SuSE-release', 'name': 'SUSE'},
        {'path': '/etc/gentoo-release', 'name': 'Gentoo'},
        {'path': '/etc/os-release', 'name': 'Debian'},
        {'path': '/etc/lsb-release', 'name': 'Mandriva'},
        {'path': '/etc/altlinux-release', 'name': 'Altlinux'},
        {'path': '/etc/sourcemage-release', 'name': 'SMGL'},
        {'path': '/etc/os-release', 'name': 'NA'},
        {'path': '/etc/coreos/update.conf', 'name': 'Coreos'},
        {'path': '/usr/lib/os-release', 'name': 'ClearLinux'},
    )

    SEARCH_STRING = {
        'OracleLinux': 'Oracle Linux',
        'RedHat': 'Red Hat',
        'Altlinux': 'ALT Linux',
        'ClearLinux': 'Clear Linux Software for Intel Architecture',
        'SMGL': 'Source Mage GNU/Linux',
    }

    OS_FAMILY_MAP = {'RedHat': ['RedHat', 'Fedora', 'CentOS', 'Scientific', 'SLC',
                                'Ascendos', 'CloudLinux', 'PSBM', 'OracleLinux', 'OVS',
                                'OEL', 'Amazon', 'Virtuozzo', 'XenServer'],
                     'Debian': ['Debian', 'Ubuntu', 'Raspbian', 'Neon', 'KDE neon',
                                'Linux Mint'],
                     'Suse': ['SuSE', 'SLES', 'SLED', 'openSUSE', 'openSUSE Tumbleweed',
                              'SLES_SAP', 'SUSE_LINUX', 'openSUSE Leap'],
                     'Archlinux': ['Archlinux', 'Antergos', 'Manjaro'],
                     'Mandrake': ['Mandrake', 'Mandriva'],
                     'Solaris': ['Solaris', 'Nexenta', 'OmniOS', 'OpenIndiana', 'SmartOS'],
                     'Slackware': ['Slackware'],
                     'Altlinux': ['Altlinux'],
                     'SGML': ['SGML'],
                     'Gentoo': ['Gentoo', 'Funtoo'],
                     'Alpine': ['Alpine'],
                     'AIX': ['AIX'],
                     'HP-UX': ['HPUX'],
                     'Darwin': ['MacOSX'],
                     'FreeBSD': ['FreeBSD']}

    OS_FAMILY = {}
    for family, names in OS_FAMILY_MAP.items():
        for name in names:
            OS_FAMILY[name] = family

    def __init__(self, module):
        self.module = module

    def get_distribution_facts(self):
        distribution_facts = {}

        # The platform module provides information about the running
        # system/distribution. Use this as a baseline and fix buggy systems
        # afterwards
        system = platform.system()
        distribution_facts['distribution'] = system
        distribution_facts['distribution_release'] = platform.release()
        distribution_facts['distribution_version'] = platform.version()

        systems_implemented = ('AIX', 'HP-UX', 'Darwin', 'FreeBSD', 'OpenBSD', 'SunOS', 'DragonFly', 'NetBSD')

        if system in systems_implemented:
            cleanedname = system.replace('-', '')
            distfunc = getattr(self, 'get_distribution_' + cleanedname)
            dist_func_facts = distfunc()
            distribution_facts.update(dist_func_facts)
        elif system == 'Linux':

            distribution_files = DistributionFiles(module=self.module)

            # linux_distribution_facts = LinuxDistribution(module).get_distribution_facts()
            dist_file_facts = distribution_files.process_dist_files()

            distribution_facts.update(dist_file_facts)

        distro = distribution_facts['distribution']

        # look for a os family alias for the 'distribution', if there isnt one, use 'distribution'
        distribution_facts['os_family'] = self.OS_FAMILY.get(distro, None) or distro

        return distribution_facts

    def get_distribution_AIX(self):
        aix_facts = {}
        rc, out, err = self.module.run_command("/usr/bin/oslevel")
        data = out.split('.')
        aix_facts['distribution_major_version'] = data[0]
        aix_facts['distribution_version'] = data[0]
        aix_facts['distribution_release'] = data[1]
        return aix_facts

    def get_distribution_HPUX(self):
        hpux_facts = {}
        rc, out, err = self.module.run_command(r"/usr/sbin/swlist |egrep 'HPUX.*OE.*[AB].[0-9]+\.[0-9]+'", use_unsafe_shell=True)
        data = re.search(r'HPUX.*OE.*([AB].[0-9]+\.[0-9]+)\.([0-9]+).*', out)
        if data:
            hpux_facts['distribution_version'] = data.groups()[0]
            hpux_facts['distribution_release'] = data.groups()[1]
        return hpux_facts

    def get_distribution_Darwin(self):
        darwin_facts = {}
        darwin_facts['distribution'] = 'MacOSX'
        rc, out, err = self.module.run_command("/usr/bin/sw_vers -productVersion")
        data = out.split()[-1]
        if data:
            darwin_facts['distribution_major_version'] = data.split('.')[0]
            darwin_facts['distribution_version'] = data
        return darwin_facts

    def get_distribution_FreeBSD(self):
        freebsd_facts = {}
        freebsd_facts['distribution_release'] = platform.release()
        data = re.search(r'(\d+)\.(\d+)-RELEASE.*', freebsd_facts['distribution_release'])
        if data:
            freebsd_facts['distribution_major_version'] = data.group(1)
            freebsd_facts['distribution_version'] = '%s.%s' % (data.group(1), data.group(2))
        return freebsd_facts

    def get_distribution_OpenBSD(self):
        openbsd_facts = {}
        openbsd_facts['distribution_version'] = platform.release()
        rc, out, err = self.module.run_command("/sbin/sysctl -n kern.version")
        match = re.match(r'OpenBSD\s[0-9]+.[0-9]+-(\S+)\s.*', out)
        if match:
            openbsd_facts['distribution_release'] = match.groups()[0]
        else:
            openbsd_facts['distribution_release'] = 'release'
        return openbsd_facts

    def get_distribution_DragonFly(self):
        return {}

    def get_distribution_NetBSD(self):
        netbsd_facts = {}
        # FIXME: poking at self.facts, should eventually make these each a collector
        platform_release = platform.release()
        netbsd_facts['distribution_major_version'] = platform_release.split('.')[0]
        return netbsd_facts

    def get_distribution_SMGL(self):
        smgl_facts = {}
        smgl_facts['distribution'] = 'Source Mage GNU/Linux'
        return smgl_facts

    def get_distribution_SunOS(self):
        sunos_facts = {}

        data = get_file_content('/etc/release').splitlines()[0]

        if 'Solaris' in data:
            ora_prefix = ''
            if 'Oracle Solaris' in data:
                data = data.replace('Oracle ', '')
                ora_prefix = 'Oracle '
            sunos_facts['distribution'] = data.split()[0]
            sunos_facts['distribution_version'] = data.split()[1]
            sunos_facts['distribution_release'] = ora_prefix + data
            return sunos_facts

        uname_v = get_uname_version(self.module)
        distribution_version = None

        if 'SmartOS' in data:
            sunos_facts['distribution'] = 'SmartOS'
            if _file_exists('/etc/product'):
                product_data = dict([l.split(': ', 1) for l in get_file_content('/etc/product').splitlines() if ': ' in l])
                if 'Image' in product_data:
                    distribution_version = product_data.get('Image').split()[-1]
        elif 'OpenIndiana' in data:
            sunos_facts['distribution'] = 'OpenIndiana'
        elif 'OmniOS' in data:
            sunos_facts['distribution'] = 'OmniOS'
            distribution_version = data.split()[-1]
        elif uname_v is not None and 'NexentaOS_' in uname_v:
            sunos_facts['distribution'] = 'Nexenta'
            distribution_version = data.split()[-1].lstrip('v')

        if sunos_facts.get('distribution', '') in ('SmartOS', 'OpenIndiana', 'OmniOS', 'Nexenta'):
            sunos_facts['distribution_release'] = data.strip()
            if distribution_version is not None:
                sunos_facts['distribution_version'] = distribution_version
            elif uname_v is not None:
                sunos_facts['distribution_version'] = uname_v.splitlines()[0].strip()
            return sunos_facts

        return sunos_facts


class DistributionFactCollector(BaseFactCollector):
    name = 'distribution'
    _fact_ids = set(['distribution_version',
                     'distribution_release',
                     'distribution_major_version'])

    def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}
        facts_dict = {}
        if not module:
            return facts_dict

        distribution = Distribution(module=module)
        distro_facts = distribution.get_distribution_facts()

        return distro_facts
