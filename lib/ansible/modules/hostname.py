#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Hiroaki Nakamura <hnakamur@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: hostname
author:
    - Adrian Likins (@alikins)
    - Hideki Saito (@saito-hideki)
version_added: "1.4"
short_description: Manage hostname
requirements: [ hostname ]
description:
    - Set system's hostname. Supports most OSs/Distributions including those using C(systemd).
    - Windows, HP-UX, and AIX are not currently supported.
notes:
    - This module does B(NOT) modify C(/etc/hosts). You need to modify it yourself using other modules such as M(ansible.builtin.template)
      or M(ansible.builtin.replace).
    - On macOS, this module uses C(scutil) to set C(HostName), C(ComputerName), and C(LocalHostName). Since C(LocalHostName)
      cannot contain spaces or most special characters, this module will replace characters when setting C(LocalHostName).
options:
    name:
        description:
            - Name of the host.
            - If the value is a fully qualified domain name that does not resolve from the given host,
              this will cause the module to hang for a few seconds while waiting for the name resolution attempt to timeout.
        type: str
        required: true
    use:
        description:
            - Which strategy to use to update the hostname.
            - If not set we try to autodetect, but this can be problematic, particularly with containers as they can present misleading information.
            - Note that 'systemd' should be specified for RHEL/EL/CentOS 7+. Older distributions should use 'redhat'.
        choices: ['alpine', 'debian', 'freebsd', 'generic', 'macos', 'macosx', 'darwin', 'openbsd', 'openrc', 'redhat', 'sles', 'solaris', 'systemd']
        type: str
        version_added: '2.9'
extends_documentation_fragment:
- action_common_attributes
- action_common_attributes.facts
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    facts:
        support: full
    platform:
        platforms: posix
'''

EXAMPLES = '''
- name: Set a hostname
  ansible.builtin.hostname:
    name: web01

- name: Set a hostname specifying strategy
  ansible.builtin.hostname:
    name: web01
    use: systemd
'''

import os
import platform
import socket
import traceback

from ansible.module_utils.basic import (
    AnsibleModule,
    get_distribution,
    get_distribution_version,
)
from ansible.module_utils.common.sys_info import get_platform_subclass
from ansible.module_utils.facts.system.service_mgr import ServiceMgrFactCollector
from ansible.module_utils.facts.utils import get_file_lines
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six import PY3, text_type

STRATS = {
    'alpine': 'Alpine',
    'debian': 'Debian',
    'freebsd': 'FreeBSD',
    'generic': 'Generic',
    'macos': 'Darwin',
    'macosx': 'Darwin',
    'darwin': 'Darwin',
    'openbsd': 'OpenBSD',
    'openrc': 'OpenRC',
    'redhat': 'RedHat',
    'sles': 'SLES',
    'solaris': 'Solaris',
    'systemd': 'Systemd',
}


class UnimplementedStrategy(object):
    def __init__(self, module):
        self.module = module

    def update_current_and_permanent_hostname(self):
        self.unimplemented_error()

    def update_current_hostname(self):
        self.unimplemented_error()

    def update_permanent_hostname(self):
        self.unimplemented_error()

    def get_current_hostname(self):
        self.unimplemented_error()

    def set_current_hostname(self, name):
        self.unimplemented_error()

    def get_permanent_hostname(self):
        self.unimplemented_error()

    def set_permanent_hostname(self, name):
        self.unimplemented_error()

    def unimplemented_error(self):
        system = platform.system()
        distribution = get_distribution()
        if distribution is not None:
            msg_platform = '%s (%s)' % (system, distribution)
        else:
            msg_platform = system
        self.module.fail_json(
            msg='hostname module cannot be used on platform %s' % msg_platform)


class Hostname(object):
    """
    This is a generic Hostname manipulation class that is subclassed
    based on platform.

    A subclass may wish to set different strategy instance to self.strategy.

    All subclasses MUST define platform and distribution (which may be None).
    """

    platform = 'Generic'
    distribution = None
    strategy_class = UnimplementedStrategy

    def __new__(cls, *args, **kwargs):
        new_cls = get_platform_subclass(Hostname)
        return super(cls, new_cls).__new__(new_cls)

    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.use = module.params['use']

        if self.use is not None:
            strat = globals()['%sStrategy' % STRATS[self.use]]
            self.strategy = strat(module)
        elif self.platform == 'Linux' and ServiceMgrFactCollector.is_systemd_managed(module):
            self.strategy = SystemdStrategy(module)
        else:
            self.strategy = self.strategy_class(module)

    def update_current_and_permanent_hostname(self):
        return self.strategy.update_current_and_permanent_hostname()

    def get_current_hostname(self):
        return self.strategy.get_current_hostname()

    def set_current_hostname(self, name):
        self.strategy.set_current_hostname(name)

    def get_permanent_hostname(self):
        return self.strategy.get_permanent_hostname()

    def set_permanent_hostname(self, name):
        self.strategy.set_permanent_hostname(name)


class BaseStrategy(object):
    def __init__(self, module):
        self.module = module
        self.changed = False

    def update_current_and_permanent_hostname(self):
        self.update_current_hostname()
        self.update_permanent_hostname()
        return self.changed

    def update_current_hostname(self):
        name = self.module.params['name']
        current_name = self.get_current_hostname()
        if current_name != name:
            if not self.module.check_mode:
                self.set_current_hostname(name)
            self.changed = True

    def update_permanent_hostname(self):
        name = self.module.params['name']
        permanent_name = self.get_permanent_hostname()
        if permanent_name != name:
            if not self.module.check_mode:
                self.set_permanent_hostname(name)
            self.changed = True

    def get_current_hostname(self):
        return self.get_permanent_hostname()

    def set_current_hostname(self, name):
        pass

    def get_permanent_hostname(self):
        raise NotImplementedError

    def set_permanent_hostname(self, name):
        raise NotImplementedError


class CommandStrategy(BaseStrategy):
    COMMAND = 'hostname'

    def __init__(self, module):
        super(CommandStrategy, self).__init__(module)
        self.hostname_cmd = self.module.get_bin_path(self.COMMAND, True)

    def get_current_hostname(self):
        cmd = [self.hostname_cmd]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native(out).strip()

    def set_current_hostname(self, name):
        cmd = [self.hostname_cmd, name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))

    def get_permanent_hostname(self):
        return 'UNKNOWN'

    def set_permanent_hostname(self, name):
        pass


class FileStrategy(BaseStrategy):
    FILE = '/etc/hostname'

    def get_permanent_hostname(self):
        if not os.path.isfile(self.FILE):
            return ''

        try:
            return get_file_lines(self.FILE)
        except Exception as e:
            self.module.fail_json(
                msg="failed to read hostname: %s" % to_native(e),
                exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            with open(self.FILE, 'w+') as f:
                f.write("%s\n" % name)
        except Exception as e:
            self.module.fail_json(
                msg="failed to update hostname: %s" % to_native(e),
                exception=traceback.format_exc())


class SLESStrategy(FileStrategy):
    """
    This is a SLES Hostname strategy class - it edits the
    /etc/HOSTNAME file.
    """
    FILE = '/etc/HOSTNAME'


class RedHatStrategy(BaseStrategy):
    """
    This is a Redhat Hostname strategy class - it edits the
    /etc/sysconfig/network file.
    """
    NETWORK_FILE = '/etc/sysconfig/network'

    def get_permanent_hostname(self):
        try:
            for line in get_file_lines(self.NETWORK_FILE):
                if line.startswith('HOSTNAME'):
                    k, v = line.split('=')
                    return v.strip()
        except Exception as e:
            self.module.fail_json(
                msg="failed to read hostname: %s" % to_native(e),
                exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            lines = []
            found = False
            for line in get_file_lines(self.NETWORK_FILE):
                if line.startswith('HOSTNAME'):
                    lines.append("HOSTNAME=%s\n" % name)
                    found = True
                else:
                    lines.append(line)
            if not found:
                lines.append("HOSTNAME=%s\n" % name)
            with open(self.NETWORK_FILE, 'w+') as f:
                f.writelines(lines)
        except Exception as e:
            self.module.fail_json(
                msg="failed to update hostname: %s" % to_native(e),
                exception=traceback.format_exc())


class AlpineStrategy(FileStrategy):
    """
    This is a Alpine Linux Hostname manipulation strategy class - it edits
    the /etc/hostname file then run hostname -F /etc/hostname.
    """

    FILE = '/etc/hostname'
    COMMAND = 'hostname'

    def set_current_hostname(self, name):
        super(AlpineStrategy, self).set_current_hostname(name)
        hostname_cmd = self.module.get_bin_path(self.COMMAND, True)

        cmd = [hostname_cmd, '-F', self.FILE]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))


class SystemdStrategy(BaseStrategy):
    """
    This is a Systemd hostname manipulation strategy class - it uses
    the hostnamectl command.
    """

    COMMAND = "hostnamectl"

    def __init__(self, module):
        super(SystemdStrategy, self).__init__(module)
        self.hostnamectl_cmd = self.module.get_bin_path(self.COMMAND, True)

    def get_current_hostname(self):
        cmd = [self.hostnamectl_cmd, '--transient', 'status']
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native(out).strip()

    def set_current_hostname(self, name):
        if len(name) > 64:
            self.module.fail_json(msg="name cannot be longer than 64 characters on systemd servers, try a shorter name")
        cmd = [self.hostnamectl_cmd, '--transient', 'set-hostname', name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))

    def get_permanent_hostname(self):
        cmd = [self.hostnamectl_cmd, '--static', 'status']
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native(out).strip()

    def set_permanent_hostname(self, name):
        if len(name) > 64:
            self.module.fail_json(msg="name cannot be longer than 64 characters on systemd servers, try a shorter name")
        cmd = [self.hostnamectl_cmd, '--pretty', 'set-hostname', name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        cmd = [self.hostnamectl_cmd, '--static', 'set-hostname', name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))


class OpenRCStrategy(BaseStrategy):
    """
    This is a Gentoo (OpenRC) Hostname manipulation strategy class - it edits
    the /etc/conf.d/hostname file.
    """

    FILE = '/etc/conf.d/hostname'

    def get_permanent_hostname(self):
        if not os.path.isfile(self.FILE):
            return ''

        try:
            for line in get_file_lines(self.FILE):
                line = line.strip()
                if line.startswith('hostname='):
                    return line[10:].strip('"')
        except Exception as e:
            self.module.fail_json(
                msg="failed to read hostname: %s" % to_native(e),
                exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            lines = [x.strip() for x in get_file_lines(self.FILE)]

            for i, line in enumerate(lines):
                if line.startswith('hostname='):
                    lines[i] = 'hostname="%s"' % name
                    break

            with open(self.FILE, 'w') as f:
                f.write('\n'.join(lines) + '\n')
        except Exception as e:
            self.module.fail_json(
                msg="failed to update hostname: %s" % to_native(e),
                exception=traceback.format_exc())


class OpenBSDStrategy(FileStrategy):
    """
    This is a OpenBSD family Hostname manipulation strategy class - it edits
    the /etc/myname file.
    """

    FILE = '/etc/myname'


class SolarisStrategy(BaseStrategy):
    """
    This is a Solaris11 or later Hostname manipulation strategy class - it
    execute hostname command.
    """

    COMMAND = "hostname"

    def __init__(self, module):
        super(SolarisStrategy, self).__init__(module)
        self.hostname_cmd = self.module.get_bin_path(self.COMMAND, True)

    def set_current_hostname(self, name):
        cmd_option = '-t'
        cmd = [self.hostname_cmd, cmd_option, name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))

    def get_permanent_hostname(self):
        fmri = 'svc:/system/identity:node'
        pattern = 'config/nodename'
        cmd = '/usr/sbin/svccfg -s %s listprop -o value %s' % (fmri, pattern)
        rc, out, err = self.module.run_command(cmd, use_unsafe_shell=True)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native(out).strip()

    def set_permanent_hostname(self, name):
        cmd = [self.hostname_cmd, name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))


class FreeBSDStrategy(BaseStrategy):
    """
    This is a FreeBSD hostname manipulation strategy class - it edits
    the /etc/rc.conf.d/hostname file.
    """

    FILE = '/etc/rc.conf.d/hostname'
    COMMAND = "hostname"

    def __init__(self, module):
        super(FreeBSDStrategy, self).__init__(module)
        self.hostname_cmd = self.module.get_bin_path(self.COMMAND, True)

    def get_current_hostname(self):
        cmd = [self.hostname_cmd]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native(out).strip()

    def set_current_hostname(self, name):
        cmd = [self.hostname_cmd, name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))

    def get_permanent_hostname(self):
        if not os.path.isfile(self.FILE):
            return ''

        try:
            for line in get_file_lines(self.FILE):
                line = line.strip()
                if line.startswith('hostname='):
                    return line[10:].strip('"')
        except Exception as e:
            self.module.fail_json(
                msg="failed to read hostname: %s" % to_native(e),
                exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            if os.path.isfile(self.FILE):
                lines = [x.strip() for x in get_file_lines(self.FILE)]

                for i, line in enumerate(lines):
                    if line.startswith('hostname='):
                        lines[i] = 'hostname="%s"' % name
                        break
            else:
                lines = ['hostname="%s"' % name]

            with open(self.FILE, 'w') as f:
                f.write('\n'.join(lines) + '\n')
        except Exception as e:
            self.module.fail_json(
                msg="failed to update hostname: %s" % to_native(e),
                exception=traceback.format_exc())


class DarwinStrategy(BaseStrategy):
    """
    This is a macOS hostname manipulation strategy class. It uses
    /usr/sbin/scutil to set ComputerName, HostName, and LocalHostName.

    HostName corresponds to what most platforms consider to be hostname.
    It controls the name used on the command line and SSH.

    However, macOS also has LocalHostName and ComputerName settings.
    LocalHostName controls the Bonjour/ZeroConf name, used by services
    like AirDrop. This class implements a method, _scrub_hostname(), that mimics
    the transformations macOS makes on hostnames when enterened in the Sharing
    preference pane. It replaces spaces with dashes and removes all special
    characters.

    ComputerName is the name used for user-facing GUI services, like the
    System Preferences/Sharing pane and when users connect to the Mac over the network.
    """

    def __init__(self, module):
        super(DarwinStrategy, self).__init__(module)

        self.scutil = self.module.get_bin_path('scutil', True)
        self.name_types = ('HostName', 'ComputerName', 'LocalHostName')
        self.scrubbed_name = self._scrub_hostname(self.module.params['name'])

    def _make_translation(self, replace_chars, replacement_chars, delete_chars):
        if PY3:
            return str.maketrans(replace_chars, replacement_chars, delete_chars)

        if not isinstance(replace_chars, text_type) or not isinstance(replacement_chars, text_type):
            raise ValueError('replace_chars and replacement_chars must both be strings')
        if len(replace_chars) != len(replacement_chars):
            raise ValueError('replacement_chars must be the same length as replace_chars')

        table = dict(zip((ord(c) for c in replace_chars), replacement_chars))
        for char in delete_chars:
            table[ord(char)] = None

        return table

    def _scrub_hostname(self, name):
        """
        LocalHostName only accepts valid DNS characters while HostName and ComputerName
        accept a much wider range of characters. This function aims to mimic how macOS
        translates a friendly name to the LocalHostName.
        """

        # Replace all these characters with a single dash
        name = to_text(name)
        replace_chars = u'\'"~`!@#$%^&*(){}[]/=?+\\|-_ '
        delete_chars = u".'"
        table = self._make_translation(replace_chars, u'-' * len(replace_chars), delete_chars)
        name = name.translate(table)

        # Replace multiple dashes with a single dash
        while '-' * 2 in name:
            name = name.replace('-' * 2, '')

        name = name.rstrip('-')
        return name

    def get_current_hostname(self):
        cmd = [self.scutil, '--get', 'HostName']
        rc, out, err = self.module.run_command(cmd)
        if rc != 0 and 'HostName: not set' not in err:
            self.module.fail_json(msg="Failed to get current hostname rc=%d, out=%s, err=%s" % (rc, out, err))

        return to_native(out).strip()

    def get_permanent_hostname(self):
        cmd = [self.scutil, '--get', 'ComputerName']
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Failed to get permanent hostname rc=%d, out=%s, err=%s" % (rc, out, err))

        return to_native(out).strip()

    def set_permanent_hostname(self, name):
        for hostname_type in self.name_types:
            cmd = [self.scutil, '--set', hostname_type]
            if hostname_type == 'LocalHostName':
                cmd.append(to_native(self.scrubbed_name))
            else:
                cmd.append(to_native(name))
            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg="Failed to set {3} to '{2}': {0} {1}".format(to_native(out), to_native(err), to_native(name), hostname_type))

    def set_current_hostname(self, name):
        pass

    def update_current_hostname(self):
        pass

    def update_permanent_hostname(self):
        name = self.module.params['name']

        # Get all the current host name values in the order of self.name_types
        all_names = tuple(self.module.run_command([self.scutil, '--get', name_type])[1].strip() for name_type in self.name_types)

        # Get the expected host name values based on the order in self.name_types
        expected_names = tuple(self.scrubbed_name if n == 'LocalHostName' else name for n in self.name_types)

        # Ensure all three names are updated
        if all_names != expected_names:
            if not self.module.check_mode:
                self.set_permanent_hostname(name)
            self.changed = True


class FedoraHostname(Hostname):
    platform = 'Linux'
    distribution = 'Fedora'
    strategy_class = SystemdStrategy


class SLESHostname(Hostname):
    platform = 'Linux'
    distribution = 'Sles'
    try:
        distribution_version = get_distribution_version()
        # cast to float may raise ValueError on non SLES, we use float for a little more safety over int
        if distribution_version and 10 <= float(distribution_version) <= 12:
            strategy_class = SLESStrategy
        else:
            raise ValueError()
    except ValueError:
        strategy_class = UnimplementedStrategy


class OpenSUSEHostname(Hostname):
    platform = 'Linux'
    distribution = 'Opensuse'
    strategy_class = SystemdStrategy


class OpenSUSELeapHostname(Hostname):
    platform = 'Linux'
    distribution = 'Opensuse-leap'
    strategy_class = SystemdStrategy


class OpenSUSETumbleweedHostname(Hostname):
    platform = 'Linux'
    distribution = 'Opensuse-tumbleweed'
    strategy_class = SystemdStrategy


class AsteraHostname(Hostname):
    platform = 'Linux'
    distribution = '"astralinuxce"'
    strategy_class = SystemdStrategy


class ArchHostname(Hostname):
    platform = 'Linux'
    distribution = 'Arch'
    strategy_class = SystemdStrategy


class ArchARMHostname(Hostname):
    platform = 'Linux'
    distribution = 'Archarm'
    strategy_class = SystemdStrategy


class AlmaLinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Almalinux'
    strategy_class = SystemdStrategy


class ManjaroHostname(Hostname):
    platform = 'Linux'
    distribution = 'Manjaro'
    strategy_class = SystemdStrategy


class ManjaroARMHostname(Hostname):
    platform = 'Linux'
    distribution = 'Manjaro-arm'
    strategy_class = SystemdStrategy


class RHELHostname(Hostname):
    platform = 'Linux'
    distribution = 'Redhat'
    strategy_class = RedHatStrategy


class CentOSHostname(Hostname):
    platform = 'Linux'
    distribution = 'Centos'
    strategy_class = RedHatStrategy


class AnolisOSHostname(Hostname):
    platform = 'Linux'
    distribution = 'Anolis'
    strategy_class = RedHatStrategy


class ClearLinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Clear-linux-os'
    strategy_class = SystemdStrategy


class CloudlinuxserverHostname(Hostname):
    platform = 'Linux'
    distribution = 'Cloudlinuxserver'
    strategy_class = RedHatStrategy


class CloudlinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Cloudlinux'
    strategy_class = RedHatStrategy


class AlinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Alinux'
    strategy_class = RedHatStrategy


class CoreosHostname(Hostname):
    platform = 'Linux'
    distribution = 'Coreos'
    strategy_class = SystemdStrategy


class FlatcarHostname(Hostname):
    platform = 'Linux'
    distribution = 'Flatcar'
    strategy_class = SystemdStrategy


class ScientificHostname(Hostname):
    platform = 'Linux'
    distribution = 'Scientific'
    strategy_class = RedHatStrategy


class OracleLinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Oracle'
    strategy_class = RedHatStrategy


class VirtuozzoLinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Virtuozzo'
    strategy_class = RedHatStrategy


class AmazonLinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Amazon'
    strategy_class = RedHatStrategy


class DebianHostname(Hostname):
    platform = 'Linux'
    distribution = 'Debian'
    strategy_class = FileStrategy


class KylinHostname(Hostname):
    platform = 'Linux'
    distribution = 'Kylin'
    strategy_class = FileStrategy


class CumulusHostname(Hostname):
    platform = 'Linux'
    distribution = 'Cumulus-linux'
    strategy_class = FileStrategy


class KaliHostname(Hostname):
    platform = 'Linux'
    distribution = 'Kali'
    strategy_class = FileStrategy


class ParrotHostname(Hostname):
    platform = 'Linux'
    distribution = 'Parrot'
    strategy_class = FileStrategy


class UbuntuHostname(Hostname):
    platform = 'Linux'
    distribution = 'Ubuntu'
    strategy_class = FileStrategy


class LinuxmintHostname(Hostname):
    platform = 'Linux'
    distribution = 'Linuxmint'
    strategy_class = FileStrategy


class LinaroHostname(Hostname):
    platform = 'Linux'
    distribution = 'Linaro'
    strategy_class = FileStrategy


class DevuanHostname(Hostname):
    platform = 'Linux'
    distribution = 'Devuan'
    strategy_class = FileStrategy


class RaspbianHostname(Hostname):
    platform = 'Linux'
    distribution = 'Raspbian'
    strategy_class = FileStrategy


class GentooHostname(Hostname):
    platform = 'Linux'
    distribution = 'Gentoo'
    strategy_class = OpenRCStrategy


class ALTLinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Altlinux'
    strategy_class = RedHatStrategy


class AlpineLinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Alpine'
    strategy_class = AlpineStrategy


class OpenBSDHostname(Hostname):
    platform = 'OpenBSD'
    distribution = None
    strategy_class = OpenBSDStrategy


class SolarisHostname(Hostname):
    platform = 'SunOS'
    distribution = None
    strategy_class = SolarisStrategy


class FreeBSDHostname(Hostname):
    platform = 'FreeBSD'
    distribution = None
    strategy_class = FreeBSDStrategy


class NetBSDHostname(Hostname):
    platform = 'NetBSD'
    distribution = None
    strategy_class = FreeBSDStrategy


class NeonHostname(Hostname):
    platform = 'Linux'
    distribution = 'Neon'
    strategy_class = FileStrategy


class DarwinHostname(Hostname):
    platform = 'Darwin'
    distribution = None
    strategy_class = DarwinStrategy


class OsmcHostname(Hostname):
    platform = 'Linux'
    distribution = 'Osmc'
    strategy_class = SystemdStrategy


class PardusHostname(Hostname):
    platform = 'Linux'
    distribution = 'Pardus'
    strategy_class = SystemdStrategy


class VoidLinuxHostname(Hostname):
    platform = 'Linux'
    distribution = 'Void'
    strategy_class = FileStrategy


class PopHostname(Hostname):
    platform = 'Linux'
    distribution = 'Pop'
    strategy_class = FileStrategy


class RockyHostname(Hostname):
    platform = 'Linux'
    distribution = 'Rocky'
    strategy_class = SystemdStrategy


class RedosHostname(Hostname):
    platform = 'Linux'
    distribution = 'Redos'
    strategy_class = SystemdStrategy


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            use=dict(type='str', choices=STRATS.keys())
        ),
        supports_check_mode=True,
    )

    hostname = Hostname(module)
    name = module.params['name']

    current_hostname = hostname.get_current_hostname()
    permanent_hostname = hostname.get_permanent_hostname()

    changed = hostname.update_current_and_permanent_hostname()

    if name != current_hostname:
        name_before = current_hostname
    elif name != permanent_hostname:
        name_before = permanent_hostname
    else:
        name_before = permanent_hostname

    # NOTE: socket.getfqdn() calls gethostbyaddr(socket.gethostname()), which can be
    # slow to return if the name does not resolve correctly.
    kw = dict(changed=changed, name=name,
              ansible_facts=dict(ansible_hostname=name.split('.')[0],
                                 ansible_nodename=name,
                                 ansible_fqdn=socket.getfqdn(),
                                 ansible_domain='.'.join(socket.getfqdn().split('.')[1:])))

    if changed:
        kw['diff'] = {'after': 'hostname = ' + name + '\n',
                      'before': 'hostname = ' + name_before + '\n'}

    module.exit_json(**kw)


if __name__ == '__main__':
    main()
