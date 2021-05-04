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
    - Supports C(check_mode).
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
'''

EXAMPLES = '''
- name: Set a hostname
  ansible.builtin.hostname:
    name: web01

- name: Set a hostname specifying strategy
  ansible.builtin.hostname:
    name: web01
    strategy: systemd
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


class GenericStrategy(object):
    """
    This is a generic Hostname manipulation strategy class.

    A subclass may wish to override some or all of these methods.
      - get_current_hostname()
      - get_permanent_hostname()
      - set_current_hostname(name)
      - set_permanent_hostname(name)
    """

    def __init__(self, module):
        self.module = module
        self.changed = False
        self.hostname_cmd = self.module.get_bin_path('hostname', True)

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


class DebianStrategy(GenericStrategy):
    """
    This is a Debian family Hostname manipulation strategy class - it edits
    the /etc/hostname file.
    """

    HOSTNAME_FILE = '/etc/hostname'

    def get_permanent_hostname(self):
        if not os.path.isfile(self.HOSTNAME_FILE):
            try:
                open(self.HOSTNAME_FILE, "a").write("")
            except IOError as e:
                self.module.fail_json(msg="failed to write file: %s" %
                                          to_native(e), exception=traceback.format_exc())
        try:
            f = open(self.HOSTNAME_FILE)
            try:
                return f.read().strip()
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to read hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            f = open(self.HOSTNAME_FILE, 'w+')
            try:
                f.write("%s\n" % name)
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to update hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())


class SLESStrategy(GenericStrategy):
    """
    This is a SLES Hostname strategy class - it edits the
    /etc/HOSTNAME file.
    """
    HOSTNAME_FILE = '/etc/HOSTNAME'

    def get_permanent_hostname(self):
        if not os.path.isfile(self.HOSTNAME_FILE):
            try:
                open(self.HOSTNAME_FILE, "a").write("")
            except IOError as e:
                self.module.fail_json(msg="failed to write file: %s" %
                                          to_native(e), exception=traceback.format_exc())
        try:
            f = open(self.HOSTNAME_FILE)
            try:
                return f.read().strip()
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to read hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            f = open(self.HOSTNAME_FILE, 'w+')
            try:
                f.write("%s\n" % name)
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to update hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())


class RedHatStrategy(GenericStrategy):
    """
    This is a Redhat Hostname strategy class - it edits the
    /etc/sysconfig/network file.
    """
    NETWORK_FILE = '/etc/sysconfig/network'

    def get_permanent_hostname(self):
        try:
            f = open(self.NETWORK_FILE, 'rb')
            try:
                for line in f.readlines():
                    if line.startswith('HOSTNAME'):
                        k, v = line.split('=')
                        return v.strip()
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to read hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            lines = []
            found = False
            f = open(self.NETWORK_FILE, 'rb')
            try:
                for line in f.readlines():
                    if line.startswith('HOSTNAME'):
                        lines.append("HOSTNAME=%s\n" % name)
                        found = True
                    else:
                        lines.append(line)
            finally:
                f.close()
            if not found:
                lines.append("HOSTNAME=%s\n" % name)
            f = open(self.NETWORK_FILE, 'w+')
            try:
                f.writelines(lines)
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to update hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())


class AlpineStrategy(GenericStrategy):
    """
    This is a Alpine Linux Hostname manipulation strategy class - it edits
    the /etc/hostname file then run hostname -F /etc/hostname.
    """

    HOSTNAME_FILE = '/etc/hostname'

    def update_current_and_permanent_hostname(self):
        self.update_permanent_hostname()
        self.update_current_hostname()
        return self.changed

    def get_permanent_hostname(self):
        if not os.path.isfile(self.HOSTNAME_FILE):
            try:
                open(self.HOSTNAME_FILE, "a").write("")
            except IOError as e:
                self.module.fail_json(msg="failed to write file: %s" %
                                          to_native(e), exception=traceback.format_exc())
        try:
            f = open(self.HOSTNAME_FILE)
            try:
                return f.read().strip()
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to read hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            f = open(self.HOSTNAME_FILE, 'w+')
            try:
                f.write("%s\n" % name)
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to update hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())

    def set_current_hostname(self, name):
        cmd = [self.hostname_cmd, '-F', self.HOSTNAME_FILE]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))


class SystemdStrategy(GenericStrategy):
    """
    This is a Systemd hostname manipulation strategy class - it uses
    the hostnamectl command.
    """

    def __init__(self, module):
        super(SystemdStrategy, self).__init__(module)
        self.hostname_cmd = self.module.get_bin_path('hostnamectl', True)

    def get_current_hostname(self):
        cmd = [self.hostname_cmd, '--transient', 'status']
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native(out).strip()

    def set_current_hostname(self, name):
        if len(name) > 64:
            self.module.fail_json(msg="name cannot be longer than 64 characters on systemd servers, try a shorter name")
        cmd = [self.hostname_cmd, '--transient', 'set-hostname', name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))

    def get_permanent_hostname(self):
        cmd = [self.hostname_cmd, '--static', 'status']
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native(out).strip()

    def set_permanent_hostname(self, name):
        if len(name) > 64:
            self.module.fail_json(msg="name cannot be longer than 64 characters on systemd servers, try a shorter name")
        cmd = [self.hostname_cmd, '--pretty', 'set-hostname', name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        cmd = [self.hostname_cmd, '--static', 'set-hostname', name]
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))


class OpenRCStrategy(GenericStrategy):
    """
    This is a Gentoo (OpenRC) Hostname manipulation strategy class - it edits
    the /etc/conf.d/hostname file.
    """

    HOSTNAME_FILE = '/etc/conf.d/hostname'

    def get_permanent_hostname(self):
        name = 'UNKNOWN'
        try:
            try:
                f = open(self.HOSTNAME_FILE, 'r')
                for line in f:
                    line = line.strip()
                    if line.startswith('hostname='):
                        name = line[10:].strip('"')
                        break
            except Exception as e:
                self.module.fail_json(msg="failed to read hostname: %s" %
                                          to_native(e), exception=traceback.format_exc())
        finally:
            f.close()

        return name

    def set_permanent_hostname(self, name):
        try:
            try:
                f = open(self.HOSTNAME_FILE, 'r')
                lines = [x.strip() for x in f]

                for i, line in enumerate(lines):
                    if line.startswith('hostname='):
                        lines[i] = 'hostname="%s"' % name
                        break
                f.close()

                f = open(self.HOSTNAME_FILE, 'w')
                f.write('\n'.join(lines) + '\n')
            except Exception as e:
                self.module.fail_json(msg="failed to update hostname: %s" %
                                          to_native(e), exception=traceback.format_exc())
        finally:
            f.close()


class OpenBSDStrategy(GenericStrategy):
    """
    This is a OpenBSD family Hostname manipulation strategy class - it edits
    the /etc/myname file.
    """

    HOSTNAME_FILE = '/etc/myname'

    def get_permanent_hostname(self):
        if not os.path.isfile(self.HOSTNAME_FILE):
            try:
                open(self.HOSTNAME_FILE, "a").write("")
            except IOError as e:
                self.module.fail_json(msg="failed to write file: %s" %
                                          to_native(e), exception=traceback.format_exc())
        try:
            f = open(self.HOSTNAME_FILE)
            try:
                return f.read().strip()
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to read hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())

    def set_permanent_hostname(self, name):
        try:
            f = open(self.HOSTNAME_FILE, 'w+')
            try:
                f.write("%s\n" % name)
            finally:
                f.close()
        except Exception as e:
            self.module.fail_json(msg="failed to update hostname: %s" %
                                      to_native(e), exception=traceback.format_exc())


class SolarisStrategy(GenericStrategy):
    """
    This is a Solaris11 or later Hostname manipulation strategy class - it
    execute hostname command.
    """

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


class FreeBSDStrategy(GenericStrategy):
    """
    This is a FreeBSD hostname manipulation strategy class - it edits
    the /etc/rc.conf.d/hostname file.
    """

    HOSTNAME_FILE = '/etc/rc.conf.d/hostname'

    def get_permanent_hostname(self):

        name = 'UNKNOWN'
        if not os.path.isfile(self.HOSTNAME_FILE):
            try:
                open(self.HOSTNAME_FILE, "a").write("hostname=temporarystub\n")
            except IOError as e:
                self.module.fail_json(msg="failed to write file: %s" %
                                          to_native(e), exception=traceback.format_exc())
        try:
            try:
                f = open(self.HOSTNAME_FILE, 'r')
                for line in f:
                    line = line.strip()
                    if line.startswith('hostname='):
                        name = line[10:].strip('"')
                        break
            except Exception as e:
                self.module.fail_json(msg="failed to read hostname: %s" %
                                          to_native(e), exception=traceback.format_exc())
        finally:
            f.close()

        return name

    def set_permanent_hostname(self, name):
        try:
            try:
                f = open(self.HOSTNAME_FILE, 'r')
                lines = [x.strip() for x in f]

                for i, line in enumerate(lines):
                    if line.startswith('hostname='):
                        lines[i] = 'hostname="%s"' % name
                        break
                f.close()

                f = open(self.HOSTNAME_FILE, 'w')
                f.write('\n'.join(lines) + '\n')
            except Exception as e:
                self.module.fail_json(msg="failed to update hostname: %s" %
                                          to_native(e), exception=traceback.format_exc())
        finally:
            f.close()


class DarwinStrategy(GenericStrategy):
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
    strategy_class = DebianStrategy


class KylinHostname(Hostname):
    platform = 'Linux'
    distribution = 'Kylin'
    strategy_class = DebianStrategy


class CumulusHostname(Hostname):
    platform = 'Linux'
    distribution = 'Cumulus-linux'
    strategy_class = DebianStrategy


class KaliHostname(Hostname):
    platform = 'Linux'
    distribution = 'Kali'
    strategy_class = DebianStrategy


class ParrotHostname(Hostname):
    platform = 'Linux'
    distribution = 'Parrot'
    strategy_class = DebianStrategy


class UbuntuHostname(Hostname):
    platform = 'Linux'
    distribution = 'Ubuntu'
    strategy_class = DebianStrategy


class LinuxmintHostname(Hostname):
    platform = 'Linux'
    distribution = 'Linuxmint'
    strategy_class = DebianStrategy


class LinaroHostname(Hostname):
    platform = 'Linux'
    distribution = 'Linaro'
    strategy_class = DebianStrategy


class DevuanHostname(Hostname):
    platform = 'Linux'
    distribution = 'Devuan'
    strategy_class = DebianStrategy


class RaspbianHostname(Hostname):
    platform = 'Linux'
    distribution = 'Raspbian'
    strategy_class = DebianStrategy


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
    strategy_class = DebianStrategy


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
    strategy_class = DebianStrategy


class PopHostname(Hostname):
    platform = 'Linux'
    distribution = 'Pop'
    strategy_class = DebianStrategy


class RockyHostname(Hostname):
    platform = 'Linux'
    distribution = 'Rocky'
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
