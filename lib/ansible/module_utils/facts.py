# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import os
import sys
import stat
import time
import shlex
import errno
import fnmatch
import glob
import platform
import re
import signal
import socket
import struct
import datetime
import getpass
import pwd

from ansible.module_utils.basic import get_all_subclasses
from ansible.module_utils.six import PY3, iteritems
from ansible.module_utils.six.moves import configparser, StringIO, reduce
from ansible.module_utils._text import to_native, to_text

try:
    import selinux
    HAVE_SELINUX=True
except ImportError:
    HAVE_SELINUX=False

try:
    # Check if we have SSLContext support
    from ssl import create_default_context, SSLContext
    del create_default_context
    del SSLContext
    HAS_SSLCONTEXT = True
except ImportError:
    HAS_SSLCONTEXT = False

try:
    import json
    # Detect python-json which is incompatible and fallback to simplejson in
    # that case
    try:
        json.loads
        json.dumps
    except AttributeError:
        raise ImportError
except ImportError:
    import simplejson as json

# The distutils module is not shipped with SUNWPython on Solaris.
# It's in the SUNWPython-devel package which also contains development files
# that don't belong on production boxes.  Since our Solaris code doesn't
# depend on LooseVersion, do not import it on Solaris.
if platform.system() != 'SunOS':
    from distutils.version import LooseVersion


# --------------------------------------------------------------
# timeout function to make sure some fact gathering
# steps do not exceed a time limit

GATHER_TIMEOUT=None
DEFAULT_GATHER_TIMEOUT = 10

class TimeoutError(Exception):
    pass

def timeout(seconds=None, error_message="Timer expired"):

    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            local_seconds = seconds  # Make local var as we modify this every time it's invoked
            if local_seconds is None:
                local_seconds = globals().get('GATHER_TIMEOUT') or DEFAULT_GATHER_TIMEOUT

            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(local_seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    # If we were called as @timeout, then the first parameter will be the
    # function we are to wrap instead of the number of seconds.  Detect this
    # and correct it by setting seconds to our sentinel value and return the
    # inner decorator function manually wrapped around the function
    if callable(seconds):
        func = seconds
        seconds = None
        return decorator(func)

    # If we were called as @timeout([...]) then python itself will take
    # care of wrapping the inner decorator around the function

    return decorator

# --------------------------------------------------------------

class Facts(object):
    """
    This class should only attempt to populate those facts that
    are mostly generic to all systems.  This includes platform facts,
    service facts (e.g. ssh keys or selinux), and distribution facts.
    Anything that requires extensive code or may have more than one
    possible implementation to establish facts for a given topic should
    subclass Facts.
    """

    # i86pc is a Solaris and derivatives-ism
    _I386RE = re.compile(r'i([3456]86|86pc)')
    # For the most part, we assume that platform.dist() will tell the truth.
    # This is the fallback to handle unknowns or exceptions
    SELINUX_MODE_DICT = { 1: 'enforcing', 0: 'permissive', -1: 'disabled' }

    # A list of dicts.  If there is a platform with more than one
    # package manager, put the preferred one last.  If there is an
    # ansible module, use that as the value for the 'name' key.
    PKG_MGRS = [ { 'path' : '/usr/bin/yum',         'name' : 'yum' },
                 { 'path' : '/usr/bin/dnf',         'name' : 'dnf' },
                 { 'path' : '/usr/bin/apt-get',     'name' : 'apt' },
                 { 'path' : '/usr/bin/zypper',      'name' : 'zypper' },
                 { 'path' : '/usr/sbin/urpmi',      'name' : 'urpmi' },
                 { 'path' : '/usr/bin/pacman',      'name' : 'pacman' },
                 { 'path' : '/bin/opkg',            'name' : 'opkg' },
                 { 'path' : '/usr/pkg/bin/pkgin',   'name' : 'pkgin' },
                 { 'path' : '/opt/local/bin/pkgin', 'name' : 'pkgin' },
                 { 'path' : '/opt/tools/bin/pkgin', 'name' : 'pkgin' },
                 { 'path' : '/opt/local/bin/port',  'name' : 'macports' },
                 { 'path' : '/usr/local/bin/brew',  'name' : 'homebrew' },
                 { 'path' : '/sbin/apk',            'name' : 'apk' },
                 { 'path' : '/usr/sbin/pkg',        'name' : 'pkgng' },
                 { 'path' : '/usr/sbin/swlist',     'name' : 'SD-UX' },
                 { 'path' : '/usr/bin/emerge',      'name' : 'portage' },
                 { 'path' : '/usr/sbin/pkgadd',     'name' : 'svr4pkg' },
                 { 'path' : '/usr/bin/pkg',         'name' : 'pkg5' },
                 { 'path' : '/usr/bin/xbps-install','name' : 'xbps' },
                 { 'path' : '/usr/local/sbin/pkg',  'name' : 'pkgng' },
                 { 'path' : '/usr/bin/swupd',       'name' : 'swupd' },
                 { 'path' : '/usr/sbin/sorcery',    'name' : 'sorcery' },
                ]

    def __init__(self, module, load_on_init=True, cached_facts=None):

        self.module = module
        if not cached_facts:
            self.facts = {}
        else:
            self.facts = cached_facts
        ### TODO: Eventually, these should all get moved to populate().  But
        # some of the values are currently being used by other subclasses (for
        # instance, os_family and distribution).  Have to sort out what to do
        # about those first.
        if load_on_init:
            self.get_platform_facts()
            self.facts.update(Distribution(module).populate())
            self.get_cmdline()
            self.get_public_ssh_host_keys()
            self.get_selinux_facts()
            self.get_apparmor_facts()
            self.get_caps_facts()
            self.get_fips_facts()
            self.get_pkg_mgr_facts()
            self.get_service_mgr_facts()
            self.get_lsb_facts()
            self.get_date_time_facts()
            self.get_user_facts()
            self.get_local_facts()
            self.get_env_facts()
            self.get_dns_facts()
            self.get_python_facts()


    def populate(self):
        return self.facts

    # Platform
    # platform.system() can be Linux, Darwin, Java, or Windows
    def get_platform_facts(self):
        self.facts['system'] = platform.system()
        self.facts['kernel'] = platform.release()
        self.facts['machine'] = platform.machine()
        self.facts['python_version'] = platform.python_version()
        self.facts['fqdn'] = socket.getfqdn()
        self.facts['hostname'] = platform.node().split('.')[0]
        self.facts['nodename'] = platform.node()
        self.facts['domain'] = '.'.join(self.facts['fqdn'].split('.')[1:])
        arch_bits = platform.architecture()[0]
        self.facts['userspace_bits'] = arch_bits.replace('bit', '')
        if self.facts['machine'] == 'x86_64':
            self.facts['architecture'] = self.facts['machine']
            if self.facts['userspace_bits'] == '64':
                self.facts['userspace_architecture'] = 'x86_64'
            elif self.facts['userspace_bits'] == '32':
                self.facts['userspace_architecture'] = 'i386'
        elif Facts._I386RE.search(self.facts['machine']):
            self.facts['architecture'] = 'i386'
            if self.facts['userspace_bits'] == '64':
                self.facts['userspace_architecture'] = 'x86_64'
            elif self.facts['userspace_bits'] == '32':
                self.facts['userspace_architecture'] = 'i386'
        else:
            self.facts['architecture'] = self.facts['machine']
        if self.facts['system'] == 'AIX':
            # Attempt to use getconf to figure out architecture
            # fall back to bootinfo if needed
            getconf_bin = self.module.get_bin_path('getconf')
            if getconf_bin:
                rc, out, err = self.module.run_command([getconf_bin, 'MACHINE_ARCHITECTURE'])
                data = out.splitlines()
                self.facts['architecture'] = data[0]
            else:
                bootinfo_bin = self.module.get_bin_path('bootinfo')
                rc, out, err = self.module.run_command([bootinfo_bin, '-p'])
                data = out.splitlines()
                self.facts['architecture'] = data[0]
        elif self.facts['system'] == 'OpenBSD':
            self.facts['architecture'] = platform.uname()[5]
        machine_id = get_file_content("/var/lib/dbus/machine-id") or get_file_content("/etc/machine-id")
        if machine_id:
            machine_id = machine_id.splitlines()[0]
            self.facts["machine_id"] = machine_id

    def get_local_facts(self):

        fact_path = self.module.params.get('fact_path', None)
        if not fact_path or not os.path.exists(fact_path):
            return

        local = {}
        for fn in sorted(glob.glob(fact_path + '/*.fact')):
            # where it will sit under local facts
            fact_base = os.path.basename(fn).replace('.fact','')
            if stat.S_IXUSR & os.stat(fn)[stat.ST_MODE]:
                # run it
                # try to read it as json first
                # if that fails read it with ConfigParser
                # if that fails, skip it
                try:
                    rc, out, err = self.module.run_command(fn)
                except UnicodeError:
                    fact = 'error loading fact - output of running %s was not utf-8' % fn
                    local[fact_base] = fact
                    self.facts['local'] = local
                    return
            else:
                out = get_file_content(fn, default='')

            # load raw json
            fact = 'loading %s' % fact_base
            try:
                fact = json.loads(out)
            except ValueError:
                # load raw ini
                cp = configparser.ConfigParser()
                try:
                    cp.readfp(StringIO(out))
                except configparser.Error:
                    fact = "error loading fact - please check content"
                else:
                    fact = {}
                    for sect in cp.sections():
                        if sect not in fact:
                            fact[sect] = {}
                        for opt in cp.options(sect):
                            val = cp.get(sect, opt)
                            fact[sect][opt]=val

            local[fact_base] = fact
        if not local:
            return
        self.facts['local'] = local

    def get_cmdline(self):
        data = get_file_content('/proc/cmdline')
        if data:
            self.facts['cmdline'] = {}
            try:
                for piece in shlex.split(data):
                    item = piece.split('=', 1)
                    if len(item) == 1:
                        self.facts['cmdline'][item[0]] = True
                    else:
                        self.facts['cmdline'][item[0]] = item[1]
            except ValueError:
                pass

    def get_public_ssh_host_keys(self):
        keytypes = ('dsa', 'rsa', 'ecdsa', 'ed25519')

        # list of directories to check for ssh keys
        # used in the order listed here, the first one with keys is used
        keydirs = ['/etc/ssh', '/etc/openssh', '/etc']

        for keydir in keydirs:
            for type_ in keytypes:
                factname = 'ssh_host_key_%s_public' % type_
                if factname in self.facts:
                    # a previous keydir was already successful, stop looking
                    # for keys
                    return
                key_filename = '%s/ssh_host_%s_key.pub' % (keydir, type_)
                keydata = get_file_content(key_filename)
                if keydata is not None:
                    self.facts[factname] = keydata.split()[1]

    def get_pkg_mgr_facts(self):
        if self.facts['system'] == 'OpenBSD':
            self.facts['pkg_mgr'] = 'openbsd_pkg'
        else:
            self.facts['pkg_mgr'] = 'unknown'
            for pkg in Facts.PKG_MGRS:
                if os.path.isfile(pkg['path']):
                    self.facts['pkg_mgr'] = pkg['name']

    def get_service_mgr_facts(self):
        #TODO: detect more custom init setups like bootscripts, dmd, s6, Epoch, etc
        # also other OSs other than linux might need to check across several possible candidates

        # Mapping of proc_1 values to more useful names
        proc_1_map = {
            'procd': 'openwrt_init',
            'runit-init': 'runit',
            'svscan': 'svc',
            'openrc-init': 'openrc',
        }

        # try various forms of querying pid 1
        proc_1 = get_file_content('/proc/1/comm')
        if proc_1 is None:
            rc, proc_1, err = self.module.run_command("ps -p 1 -o comm|tail -n 1", use_unsafe_shell=True)
            # If the output of the command starts with what looks like a PID, then the 'ps' command
            # probably didn't work the way we wanted, probably because it's busybox
            if re.match(r' *[0-9]+ ', proc_1):
                proc_1 = None

        # The ps command above may return "COMMAND" if the user cannot read /proc, e.g. with grsecurity
        if proc_1 == "COMMAND\n":
            proc_1 = None

        if proc_1 is not None:
            proc_1 = os.path.basename(proc_1)
            proc_1 = to_native(proc_1)
            proc_1 = proc_1.strip()

        if proc_1 is not None and (proc_1 == 'init' or proc_1.endswith('sh')):
            # many systems return init, so this cannot be trusted, if it ends in 'sh' it probalby is a shell in a container
            proc_1 = None

        # if not init/None it should be an identifiable or custom init, so we are done!
        if proc_1 is not None:
            # Lookup proc_1 value in map and use proc_1 value itself if no match
            self.facts['service_mgr'] = proc_1_map.get(proc_1, proc_1)

        # start with the easy ones
        elif self.facts['distribution'] == 'MacOSX':
            #FIXME: find way to query executable, version matching is not ideal
            if LooseVersion(platform.mac_ver()[0]) >= LooseVersion('10.4'):
                self.facts['service_mgr'] = 'launchd'
            else:
                self.facts['service_mgr'] = 'systemstarter'
        elif 'BSD' in self.facts['system'] or self.facts['system'] in ['Bitrig', 'DragonFly']:
            #FIXME: we might want to break out to individual BSDs or 'rc'
            self.facts['service_mgr'] = 'bsdinit'
        elif self.facts['system'] == 'AIX':
            self.facts['service_mgr'] = 'src'
        elif self.facts['system'] == 'SunOS':
            self.facts['service_mgr'] = 'smf'
        elif self.facts['distribution'] == 'OpenWrt':
            self.facts['service_mgr'] = 'openwrt_init'
        elif self.facts['system'] == 'Linux':
            if self.is_systemd_managed():
                self.facts['service_mgr'] = 'systemd'
            elif self.module.get_bin_path('initctl') and os.path.exists("/etc/init/"):
                self.facts['service_mgr'] = 'upstart'
            elif os.path.exists('/sbin/openrc'):
                self.facts['service_mgr'] = 'openrc'
            elif os.path.exists('/etc/init.d/'):
                self.facts['service_mgr'] = 'sysvinit'

        if not self.facts.get('service_mgr', False):
            # if we cannot detect, fallback to generic 'service'
            self.facts['service_mgr'] = 'service'

    def get_lsb_facts(self):
        lsb_path = self.module.get_bin_path('lsb_release')
        if lsb_path:
            rc, out, err = self.module.run_command([lsb_path, "-a"], errors='surrogate_then_replace')
            if rc == 0:
                self.facts['lsb'] = {}
                for line in out.splitlines():
                    if len(line) < 1 or ':' not in line:
                        continue
                    value = line.split(':', 1)[1].strip()
                    if 'LSB Version:' in line:
                        self.facts['lsb']['release'] = value
                    elif 'Distributor ID:' in line:
                        self.facts['lsb']['id'] = value
                    elif 'Description:' in line:
                        self.facts['lsb']['description'] = value
                    elif 'Release:' in line:
                        self.facts['lsb']['release'] = value
                    elif 'Codename:' in line:
                        self.facts['lsb']['codename'] = value
        elif lsb_path is None and os.path.exists('/etc/lsb-release'):
            self.facts['lsb'] = {}
            for line in get_file_lines('/etc/lsb-release'):
                value = line.split('=',1)[1].strip()
                if 'DISTRIB_ID' in line:
                    self.facts['lsb']['id'] = value
                elif 'DISTRIB_RELEASE' in line:
                    self.facts['lsb']['release'] = value
                elif 'DISTRIB_DESCRIPTION' in line:
                    self.facts['lsb']['description'] = value
                elif 'DISTRIB_CODENAME' in line:
                    self.facts['lsb']['codename'] = value

        if 'lsb' in self.facts and 'release' in self.facts['lsb']:
            self.facts['lsb']['major_release'] = self.facts['lsb']['release'].split('.')[0]

    def get_selinux_facts(self):
        if not HAVE_SELINUX:
            self.facts['selinux'] = False
            return
        self.facts['selinux'] = {}
        if not selinux.is_selinux_enabled():
            self.facts['selinux']['status'] = 'disabled'
        else:
            self.facts['selinux']['status'] = 'enabled'
            try:
                self.facts['selinux']['policyvers'] = selinux.security_policyvers()
            except (AttributeError,OSError):
                self.facts['selinux']['policyvers'] = 'unknown'
            try:
                (rc, configmode) = selinux.selinux_getenforcemode()
                if rc == 0:
                    self.facts['selinux']['config_mode'] = Facts.SELINUX_MODE_DICT.get(configmode, 'unknown')
                else:
                    self.facts['selinux']['config_mode'] = 'unknown'
            except (AttributeError,OSError):
                self.facts['selinux']['config_mode'] = 'unknown'
            try:
                mode = selinux.security_getenforce()
                self.facts['selinux']['mode'] = Facts.SELINUX_MODE_DICT.get(mode, 'unknown')
            except (AttributeError,OSError):
                self.facts['selinux']['mode'] = 'unknown'
            try:
                (rc, policytype) = selinux.selinux_getpolicytype()
                if rc == 0:
                    self.facts['selinux']['type'] = policytype
                else:
                    self.facts['selinux']['type'] = 'unknown'
            except (AttributeError,OSError):
                self.facts['selinux']['type'] = 'unknown'

    def get_apparmor_facts(self):
        self.facts['apparmor'] = {}
        if os.path.exists('/sys/kernel/security/apparmor'):
            self.facts['apparmor']['status'] = 'enabled'
        else:
            self.facts['apparmor']['status'] = 'disabled'

    def get_caps_facts(self):
        capsh_path = self.module.get_bin_path('capsh')
        if capsh_path:
            rc, out, err = self.module.run_command([capsh_path, "--print"], errors='surrogate_then_replace')
            enforced_caps = []
            enforced = 'NA'
            for line in out.splitlines():
                if len(line) < 1:
                    continue
                if line.startswith('Current:'):
                    if line.split(':')[1].strip() == '=ep':
                        enforced = 'False'
                    else:
                        enforced = 'True'
                        enforced_caps = [i.strip() for i in line.split('=')[1].split(',')]

            self.facts['system_capabilities_enforced'] = enforced
            self.facts['system_capabilities'] = enforced_caps


    def get_fips_facts(self):
        self.facts['fips'] = False
        data = get_file_content('/proc/sys/crypto/fips_enabled')
        if data and data == '1':
            self.facts['fips'] = True


    def get_date_time_facts(self):
        self.facts['date_time'] = {}

        now = datetime.datetime.now()
        self.facts['date_time']['year'] = now.strftime('%Y')
        self.facts['date_time']['month'] = now.strftime('%m')
        self.facts['date_time']['weekday'] = now.strftime('%A')
        self.facts['date_time']['weekday_number'] = now.strftime('%w')
        self.facts['date_time']['weeknumber'] = now.strftime('%W')
        self.facts['date_time']['day'] = now.strftime('%d')
        self.facts['date_time']['hour'] = now.strftime('%H')
        self.facts['date_time']['minute'] = now.strftime('%M')
        self.facts['date_time']['second'] = now.strftime('%S')
        self.facts['date_time']['epoch'] = now.strftime('%s')
        if self.facts['date_time']['epoch'] == '' or self.facts['date_time']['epoch'][0] == '%':
            self.facts['date_time']['epoch'] = str(int(time.time()))
        self.facts['date_time']['date'] = now.strftime('%Y-%m-%d')
        self.facts['date_time']['time'] = now.strftime('%H:%M:%S')
        self.facts['date_time']['iso8601_micro'] = now.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.facts['date_time']['iso8601'] = now.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.facts['date_time']['iso8601_basic'] = now.strftime("%Y%m%dT%H%M%S%f")
        self.facts['date_time']['iso8601_basic_short'] = now.strftime("%Y%m%dT%H%M%S")
        self.facts['date_time']['tz'] = time.strftime("%Z")
        self.facts['date_time']['tz_offset'] = time.strftime("%z")

    def is_systemd_managed(self):
        # tools must be installed
        if self.module.get_bin_path('systemctl'):

            # this should show if systemd is the boot init system, if checking init faild to mark as systemd
            # these mirror systemd's own sd_boot test http://www.freedesktop.org/software/systemd/man/sd_booted.html
            for canary in ["/run/systemd/system/", "/dev/.run/systemd/", "/dev/.systemd/"]:
                if os.path.exists(canary):
                    return True
        return False

    # User
    def get_user_facts(self):
        self.facts['user_id'] = getpass.getuser()
        pwent = pwd.getpwnam(getpass.getuser())
        self.facts['user_uid'] = pwent.pw_uid
        self.facts['user_gid'] = pwent.pw_gid
        self.facts['user_gecos'] = pwent.pw_gecos
        self.facts['user_dir'] = pwent.pw_dir
        self.facts['user_shell'] = pwent.pw_shell
        self.facts['real_user_id'] = os.getuid()
        self.facts['effective_user_id'] = os.geteuid()
        self.facts['real_group_id'] = os.getgid()
        self.facts['effective_group_id'] = os.getgid()

    def get_env_facts(self):
        self.facts['env'] = {}
        for k,v in iteritems(os.environ):
            self.facts['env'][k] = v

    def get_dns_facts(self):
        self.facts['dns'] = {}
        for line in get_file_content('/etc/resolv.conf', '').splitlines():
            if line.startswith('#') or line.startswith(';') or line.strip() == '':
                continue
            tokens = line.split()
            if len(tokens) == 0:
                continue
            if tokens[0] == 'nameserver':
                if not 'nameservers' in self.facts['dns']:
                    self.facts['dns']['nameservers'] = []
                for nameserver in tokens[1:]:
                    self.facts['dns']['nameservers'].append(nameserver)
            elif tokens[0] == 'domain':
                if len(tokens) > 1:
                    self.facts['dns']['domain'] = tokens[1]
            elif tokens[0] == 'search':
                self.facts['dns']['search'] = []
                for suffix in tokens[1:]:
                    self.facts['dns']['search'].append(suffix)
            elif tokens[0] == 'sortlist':
                self.facts['dns']['sortlist'] = []
                for address in tokens[1:]:
                    self.facts['dns']['sortlist'].append(address)
            elif tokens[0] == 'options':
                self.facts['dns']['options'] = {}
                if len(tokens) > 1:
                    for option in tokens[1:]:
                        option_tokens = option.split(':', 1)
                        if len(option_tokens) == 0:
                            continue
                        val = len(option_tokens) == 2 and option_tokens[1] or True
                        self.facts['dns']['options'][option_tokens[0]] = val

    def _get_mount_size_facts(self, mountpoint):
        size_total = None
        size_available = None
        try:
            statvfs_result = os.statvfs(mountpoint)
            size_total = statvfs_result.f_frsize * statvfs_result.f_blocks
            size_available = statvfs_result.f_frsize * (statvfs_result.f_bavail)
        except OSError:
            pass
        return size_total, size_available

    def get_python_facts(self):
        self.facts['python'] = {
            'version': {
                'major': sys.version_info[0],
                'minor': sys.version_info[1],
                'micro': sys.version_info[2],
                'releaselevel': sys.version_info[3],
                'serial': sys.version_info[4]
            },
            'version_info': list(sys.version_info),
            'executable': sys.executable,
            'has_sslcontext': HAS_SSLCONTEXT
        }
        try:
            self.facts['python']['type'] = sys.subversion[0]
        except AttributeError:
            try:
                self.facts['python']['type'] = sys.implementation.name
            except AttributeError:
                self.facts['python']['type'] = None


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
        {'path': '/etc/os-release', 'name': 'SuSE'},
        {'path': '/etc/SuSE-release', 'name': 'SuSE'},
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
        'ClearLinux': 'Clear Linux',
        'SMGL': 'Source Mage GNU/Linux',
    }

    # A list with OS Family members
    OS_FAMILY = dict(
        RedHat = 'RedHat', Fedora = 'RedHat', CentOS = 'RedHat', Scientific = 'RedHat',
        SLC = 'RedHat', Ascendos = 'RedHat', CloudLinux = 'RedHat', PSBM = 'RedHat',
        OracleLinux = 'RedHat', OVS = 'RedHat', OEL = 'RedHat', Amazon = 'RedHat', Virtuozzo = 'RedHat',
        XenServer = 'RedHat', Ubuntu = 'Debian', Debian = 'Debian', Raspbian = 'Debian', Slackware = 'Slackware', SLES = 'Suse',
        SLED = 'Suse', openSUSE = 'Suse', openSUSE_Tumbleweed = 'Suse', SuSE = 'Suse', SLES_SAP = 'Suse', SUSE_LINUX = 'Suse', Gentoo = 'Gentoo', Funtoo = 'Gentoo',
        Archlinux = 'Archlinux', Manjaro = 'Archlinux', Mandriva = 'Mandrake', Mandrake = 'Mandrake', Altlinux = 'Altlinux', SMGL = 'SMGL',
        Solaris = 'Solaris', Nexenta = 'Solaris', OmniOS = 'Solaris', OpenIndiana = 'Solaris',
        SmartOS = 'Solaris', AIX = 'AIX', Alpine = 'Alpine', MacOSX = 'Darwin',
        FreeBSD = 'FreeBSD', HPUX = 'HP-UX', openSUSE_Leap = 'Suse', Neon = 'Debian'
    )

    def __init__(self, module):
        self.system = platform.system()
        self.facts = {}
        self.module = module

    def populate(self):
        self.get_distribution_facts()
        return self.facts

    def get_distribution_facts(self):
        # The platform module provides information about the running
        # system/distribution. Use this as a baseline and fix buggy systems
        # afterwards
        self.facts['distribution'] = self.system
        self.facts['distribution_release'] = platform.release()
        self.facts['distribution_version'] = platform.version()
        systems_implemented = ('AIX', 'HP-UX', 'Darwin', 'FreeBSD', 'OpenBSD', 'SunOS', 'DragonFly', 'NetBSD')

        self.facts['distribution'] = self.system

        if self.system in systems_implemented:
            cleanedname = self.system.replace('-','')
            distfunc = getattr(self, 'get_distribution_'+cleanedname)
            distfunc()
        elif self.system == 'Linux':
            # try to find out which linux distribution this is
            dist = platform.dist()
            self.facts['distribution'] = dist[0].capitalize() or 'NA'
            self.facts['distribution_version'] = dist[1] or 'NA'
            self.facts['distribution_major_version'] = dist[1].split('.')[0] or 'NA'
            self.facts['distribution_release'] = dist[2] or 'NA'
            # Try to handle the exceptions now ...
            # self.facts['distribution_debug'] = []
            for ddict in self.OSDIST_LIST:
                name = ddict['name']
                path = ddict['path']

                if not os.path.exists(path):
                    continue
                # if allowempty is set, we only check for file existance but not content
                if 'allowempty' in ddict and ddict['allowempty']:
                    self.facts['distribution'] = name
                    break
                if os.path.getsize(path) == 0:
                    continue

                data = get_file_content(path)
                if name in self.SEARCH_STRING:
                    # look for the distribution string in the data and replace according to RELEASE_NAME_MAP
                    # only the distribution name is set, the version is assumed to be correct from platform.dist()
                    if self.SEARCH_STRING[name] in data:
                        # this sets distribution=RedHat if 'Red Hat' shows up in data
                        self.facts['distribution'] = name
                    else:
                        # this sets distribution to what's in the data, e.g. CentOS, Scientific, ...
                        self.facts['distribution'] = data.split()[0]
                    break
                else:
                    # call a dedicated function for parsing the file content
                    try:
                        distfunc = getattr(self, 'get_distribution_' + name)
                        parsed = distfunc(name, data, path)
                        if parsed is None or parsed:
                            # distfunc return False if parsing failed
                            # break only if parsing was succesful
                            # otherwise continue with other distributions
                            break
                    except AttributeError:
                        # this should never happen, but if it does fail quitely and not with a traceback
                        pass



                    # to debug multiple matching release files, one can use:
                    # self.facts['distribution_debug'].append({path + ' ' + name:
                    #         (parsed,
                    #          self.facts['distribution'],
                    #          self.facts['distribution_version'],
                    #          self.facts['distribution_release'],
                    #          )})

        self.facts['os_family'] = self.facts['distribution']
        distro = self.facts['distribution'].replace(' ', '_')
        if distro in self.OS_FAMILY:
            self.facts['os_family'] = self.OS_FAMILY[distro]

    def get_distribution_AIX(self):
        rc, out, err = self.module.run_command("/usr/bin/oslevel")
        data = out.split('.')
        self.facts['distribution_version'] = data[0]
        self.facts['distribution_release'] = data[1]

    def get_distribution_HPUX(self):
        rc, out, err = self.module.run_command("/usr/sbin/swlist |egrep 'HPUX.*OE.*[AB].[0-9]+\.[0-9]+'", use_unsafe_shell=True)
        data = re.search('HPUX.*OE.*([AB].[0-9]+\.[0-9]+)\.([0-9]+).*', out)
        if data:
            self.facts['distribution_version'] = data.groups()[0]
            self.facts['distribution_release'] = data.groups()[1]

    def get_distribution_Darwin(self):
        self.facts['distribution'] = 'MacOSX'
        rc, out, err = self.module.run_command("/usr/bin/sw_vers -productVersion")
        data = out.split()[-1]
        self.facts['distribution_version'] = data

    def get_distribution_FreeBSD(self):
        self.facts['distribution_release'] = platform.release()
        data = re.search('(\d+)\.(\d+)-RELEASE.*', self.facts['distribution_release'])
        if data:
            self.facts['distribution_major_version'] = data.group(1)
            self.facts['distribution_version'] = '%s.%s' % (data.group(1), data.group(2))

    def get_distribution_OpenBSD(self):
        self.facts['distribution_version'] = platform.release()
        rc, out, err = self.module.run_command("/sbin/sysctl -n kern.version")
        match = re.match('OpenBSD\s[0-9]+.[0-9]+-(\S+)\s.*', out)
        if match:
            self.facts['distribution_release'] = match.groups()[0]
        else:
            self.facts['distribution_release'] = 'release'

    def get_distribution_DragonFly(self):
        pass

    def get_distribution_NetBSD(self):
        self.facts['distribution_major_version'] = self.facts['distribution_release'].split('.')[0]

    def get_distribution_Slackware(self, name, data, path):
        if 'Slackware' not in data:
            return False  # TODO: remove
        self.facts['distribution'] = name
        version = re.findall('\w+[.]\w+', data)
        if version:
            self.facts['distribution_version'] = version[0]

    def get_distribution_Amazon(self, name, data, path):
        if 'Amazon' not in data:
            return False  # TODO: remove
        self.facts['distribution'] = 'Amazon'
        self.facts['distribution_version'] = data.split()[-1]

    def get_distribution_OpenWrt(self, name, data, path):
        if 'OpenWrt' not in data:
            return False  # TODO: remove
        self.facts['distribution'] = name
        version = re.search('DISTRIB_RELEASE="(.*)"', data)
        if version:
            self.facts['distribution_version'] = version.groups()[0]
        release = re.search('DISTRIB_CODENAME="(.*)"', data)
        if release:
            self.facts['distribution_release'] = release.groups()[0]

    def get_distribution_Alpine(self, name, data, path):
        self.facts['distribution'] = 'Alpine'
        self.facts['distribution_version'] = data

    def get_distribution_SMGL(self):
        self.facts['distribution'] = 'Source Mage GNU/Linux'

    def get_distribution_SunOS(self):
        data = get_file_content('/etc/release').splitlines()[0]
        if 'Solaris' in data:
            ora_prefix = ''
            if 'Oracle Solaris' in data:
                data = data.replace('Oracle ','')
                ora_prefix = 'Oracle '
            self.facts['distribution'] = data.split()[0]
            self.facts['distribution_version'] = data.split()[1]
            self.facts['distribution_release'] = ora_prefix + data
            return

        uname_v = get_uname_version(self.module)
        distribution_version = None
        if 'SmartOS' in data:
            self.facts['distribution'] = 'SmartOS'
            if os.path.exists('/etc/product'):
                product_data = dict([l.split(': ', 1) for l in get_file_content('/etc/product').splitlines() if ': ' in l])
                if 'Image' in product_data:
                    distribution_version = product_data.get('Image').split()[-1]
        elif 'OpenIndiana' in data:
            self.facts['distribution'] = 'OpenIndiana'
        elif 'OmniOS' in data:
            self.facts['distribution'] = 'OmniOS'
            distribution_version = data.split()[-1]
        elif uname_v is not None and 'NexentaOS_' in uname_v:
            self.facts['distribution'] = 'Nexenta'
            distribution_version = data.split()[-1].lstrip('v')

        if self.facts['distribution'] in ('SmartOS', 'OpenIndiana', 'OmniOS', 'Nexenta'):
            self.facts['distribution_release'] = data.strip()
            if distribution_version is not None:
                self.facts['distribution_version'] = distribution_version
            elif uname_v is not None:
                self.facts['distribution_version'] = uname_v.splitlines()[0].strip()
            return

        return False  # TODO: remove if tested without this

    def get_distribution_SuSE(self, name, data, path):
        if 'suse' not in data.lower():
            return False  # TODO: remove if tested without this
        if path == '/etc/os-release':
            for line in data.splitlines():
                distribution = re.search("^NAME=(.*)", line)
                if distribution:
                    self.facts['distribution'] = distribution.group(1).strip('"')
                # example pattern are 13.04 13.0 13
                distribution_version = re.search('^VERSION_ID="?([0-9]+\.?[0-9]*)"?', line)
                if distribution_version:
                    self.facts['distribution_version'] = distribution_version.group(1)
                if 'open' in data.lower():
                    release = re.search('^VERSION_ID="?[0-9]+\.?([0-9]*)"?', line)
                    if release:
                        self.facts['distribution_release'] = release.groups()[0]
                elif 'enterprise' in data.lower() and 'VERSION_ID' in line:
                    # SLES doesn't got funny release names
                    release = re.search('^VERSION_ID="?[0-9]+\.?([0-9]*)"?', line)
                    if release.group(1):
                        release = release.group(1)
                    else:
                        release = "0"  # no minor number, so it is the first release
                    self.facts['distribution_release'] = release
        elif path == '/etc/SuSE-release':
            if 'open' in data.lower():
                data = data.splitlines()
                distdata = get_file_content(path).splitlines()[0]
                self.facts['distribution'] = distdata.split()[0]
                for line in data:
                    release = re.search('CODENAME *= *([^\n]+)', line)
                    if release:
                        self.facts['distribution_release'] = release.groups()[0].strip()
            elif 'enterprise' in data.lower():
                lines = data.splitlines()
                distribution = lines[0].split()[0]
                if "Server" in data:
                    self.facts['distribution'] = "SLES"
                elif "Desktop" in data:
                    self.facts['distribution'] = "SLED"
                for line in lines:
                    release = re.search('PATCHLEVEL = ([0-9]+)', line) # SLES doesn't got funny release names
                    if release:
                        self.facts['distribution_release'] = release.group(1)
                        self.facts['distribution_version'] = self.facts['distribution_version'] + '.' + release.group(1)

    def get_distribution_Debian(self, name, data, path):
        if 'Debian' in data or 'Raspbian' in data:
            self.facts['distribution'] = 'Debian'
            release = re.search("PRETTY_NAME=[^(]+ \(?([^)]+?)\)", data)
            if release:
                self.facts['distribution_release'] = release.groups()[0]

            # Last resort: try to find release from tzdata as either lsb is missing or this is very old debian
            if self.facts['distribution_release'] == 'NA' and 'Debian' in data:
                dpkg_cmd = self.module.get_bin_path('dpkg')
                if dpkg_cmd:
                    cmd = "%s --status tzdata|grep Provides|cut -f2 -d'-'" % dpkg_cmd
                    rc, out, err = self.module.run_command(cmd)
                    if rc == 0:
                        self.facts['distribution_release'] = out.strip()
        elif 'Ubuntu' in data:
            self.facts['distribution'] = 'Ubuntu'
            # nothing else to do, Ubuntu gets correct info from python functions
        else:
            return False

    def get_distribution_Mandriva(self, name, data, path):
        if 'Mandriva' in data:
            self.facts['distribution'] = 'Mandriva'
            version = re.search('DISTRIB_RELEASE="(.*)"', data)
            if version:
                self.facts['distribution_version'] = version.groups()[0]
            release = re.search('DISTRIB_CODENAME="(.*)"', data)
            if release:
                self.facts['distribution_release'] = release.groups()[0]
            self.facts['distribution'] = name
        else:
            return False

    def get_distribution_NA(self, name, data, path):
        for line in data.splitlines():
            distribution = re.search("^NAME=(.*)", line)
            if distribution and self.facts['distribution'] == 'NA':
                self.facts['distribution'] = distribution.group(1).strip('"')
            version = re.search("^VERSION=(.*)", line)
            if version and self.facts['distribution_version'] == 'NA':
                self.facts['distribution_version'] = version.group(1).strip('"')

    def get_distribution_Coreos(self, name, data, path):
        if self.facts['distribution'].lower() == 'coreos':
            if not data:
                # include fix from #15230, #15228
                return
            release = re.search("^GROUP=(.*)", data)
            if release:
                self.facts['distribution_release'] = release.group(1).strip('"')
        else:
            return False  # TODO: remove if tested without this


class Hardware(Facts):
    """
    This is a generic Hardware subclass of Facts.  This should be further
    subclassed to implement per platform.  If you subclass this, it
    should define:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count

    All subclasses MUST define platform.
    """
    platform = 'Generic'

    def __new__(cls, *arguments, **keyword):
        # When Hardware is created, it chooses a subclass to create instead.
        # This check prevents the subclass from then trying to find a subclass
        # and create that.
        if cls is not Hardware:
            return super(Hardware, cls).__new__(cls)

        subclass = cls
        for sc in get_all_subclasses(Hardware):
            if sc.platform == platform.system():
                subclass = sc
        if PY3:
            return super(cls, subclass).__new__(subclass)
        else:
            return super(cls, subclass).__new__(subclass, *arguments, **keyword)

    def populate(self):
        return self.facts

    def get_sysctl(self, prefixes):
        sysctl_cmd = self.module.get_bin_path('sysctl')
        cmd = [sysctl_cmd]
        cmd.extend(prefixes)
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            return dict()
        sysctl = dict()
        for line in out.splitlines():
            if not line:
                continue
            (key, value) = re.split('\s?=\s?|: ', line, maxsplit=1)
            sysctl[key] = value.strip()
        return sysctl



class LinuxHardware(Hardware):
    """
    Linux-specific subclass of Hardware.  Defines memory and CPU facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count

    In addition, it also defines number of DMI facts and device facts.
    """

    platform = 'Linux'

    # Originally only had these four as toplevelfacts
    ORIGINAL_MEMORY_FACTS = frozenset(('MemTotal', 'SwapTotal', 'MemFree', 'SwapFree'))
    # Now we have all of these in a dict structure
    MEMORY_FACTS = ORIGINAL_MEMORY_FACTS.union(('Buffers', 'Cached', 'SwapCached'))

    # regex used against findmnt output to detect bind mounts
    BIND_MOUNT_RE = re.compile(r'.*\]')

    # regex used against mtab content to find entries that are bind mounts
    MTAB_BIND_MOUNT_RE = re.compile(r'.*bind.*"')

    def populate(self):
        self.get_cpu_facts()
        self.get_memory_facts()
        self.get_dmi_facts()
        self.get_device_facts()
        self.get_uptime_facts()
        self.get_lvm_facts()
        try:
            self.get_mount_facts()
        except TimeoutError:
            pass
        return self.facts

    def get_memory_facts(self):
        if not os.access("/proc/meminfo", os.R_OK):
            return

        memstats = {}
        for line in get_file_lines("/proc/meminfo"):
            data = line.split(":", 1)
            key = data[0]
            if key in self.ORIGINAL_MEMORY_FACTS:
                val = data[1].strip().split(' ')[0]
                self.facts["%s_mb" % key.lower()] = int(val) // 1024

            if key in self.MEMORY_FACTS:
                val = data[1].strip().split(' ')[0]
                memstats[key.lower()] = int(val) // 1024

        if None not in (memstats.get('memtotal'), memstats.get('memfree')):
            memstats['real:used'] = memstats['memtotal'] - memstats['memfree']
        if None not in (memstats.get('cached'), memstats.get('memfree'), memstats.get('buffers')):
            memstats['nocache:free'] = memstats['cached'] + memstats['memfree'] + memstats['buffers']
        if None not in (memstats.get('memtotal'), memstats.get('nocache:free')):
            memstats['nocache:used'] = memstats['memtotal'] - memstats['nocache:free']
        if None not in (memstats.get('swaptotal'), memstats.get('swapfree')):
            memstats['swap:used'] = memstats['swaptotal'] - memstats['swapfree']

        self.facts['memory_mb'] = {
            'real' : {
                'total': memstats.get('memtotal'),
                'used': memstats.get('real:used'),
                'free': memstats.get('memfree'),
                },
            'nocache' : {
                'free': memstats.get('nocache:free'),
                'used': memstats.get('nocache:used'),
                },
            'swap' : {
                'total': memstats.get('swaptotal'),
                'free': memstats.get('swapfree'),
                'used': memstats.get('swap:used'),
                'cached': memstats.get('swapcached'),
                },
            }

    def get_cpu_facts(self):
        i = 0
        vendor_id_occurrence = 0
        model_name_occurrence = 0
        physid = 0
        coreid = 0
        sockets = {}
        cores = {}

        xen = False
        xen_paravirt = False
        try:
            if os.path.exists('/proc/xen'):
                xen = True
            else:
                for line in get_file_lines('/sys/hypervisor/type'):
                    if line.strip() == 'xen':
                        xen = True
                    # Only interested in the first line
                    break
        except IOError:
            pass

        if not os.access("/proc/cpuinfo", os.R_OK):
            return
        self.facts['processor'] = []
        for line in get_file_lines('/proc/cpuinfo'):
            data = line.split(":", 1)
            key = data[0].strip()

            if xen:
                if key == 'flags':
                    # Check for vme cpu flag, Xen paravirt does not expose this.
                    #   Need to detect Xen paravirt because it exposes cpuinfo
                    #   differently than Xen HVM or KVM and causes reporting of
                    #   only a single cpu core.
                    if 'vme' not in data:
                        xen_paravirt = True

            # model name is for Intel arch, Processor (mind the uppercase P)
            # works for some ARM devices, like the Sheevaplug.
            if key in ['model name', 'Processor', 'vendor_id', 'cpu', 'Vendor']:
                if 'processor' not in self.facts:
                    self.facts['processor'] = []
                self.facts['processor'].append(data[1].strip())
                if key == 'vendor_id':
                    vendor_id_occurrence += 1
                if key == 'model name':
                    model_name_occurrence += 1
                i += 1
            elif key == 'physical id':
                physid = data[1].strip()
                if physid not in sockets:
                    sockets[physid] = 1
            elif key == 'core id':
                coreid = data[1].strip()
                if coreid not in sockets:
                    cores[coreid] = 1
            elif key == 'cpu cores':
                sockets[physid] = int(data[1].strip())
            elif key == 'siblings':
                cores[coreid] = int(data[1].strip())
            elif key == '# processors':
                self.facts['processor_cores'] = int(data[1].strip())

        # Skip for platforms without vendor_id/model_name in cpuinfo (e.g ppc64le)
        if vendor_id_occurrence > 0:
            if vendor_id_occurrence == model_name_occurrence:
                i = vendor_id_occurrence

        if self.facts['architecture'] != 's390x':
            if xen_paravirt:
                self.facts['processor_count'] = i
                self.facts['processor_cores'] = i
                self.facts['processor_threads_per_core'] = 1
                self.facts['processor_vcpus'] = i
            else:
                if sockets:
                    self.facts['processor_count'] = len(sockets)
                else:
                    self.facts['processor_count'] = i

                socket_values = list(sockets.values())
                if socket_values:
                    self.facts['processor_cores'] = socket_values[0]
                else:
                    self.facts['processor_cores'] = 1

                core_values = list(cores.values())
                if core_values:
                    self.facts['processor_threads_per_core'] = core_values[0] // self.facts['processor_cores']
                else:
                    self.facts['processor_threads_per_core'] = 1 // self.facts['processor_cores']

                self.facts['processor_vcpus'] = (self.facts['processor_threads_per_core'] *
                    self.facts['processor_count'] * self.facts['processor_cores'])

    def get_dmi_facts(self):
        ''' learn dmi facts from system

        Try /sys first for dmi related facts.
        If that is not available, fall back to dmidecode executable '''

        if os.path.exists('/sys/devices/virtual/dmi/id/product_name'):
            # Use kernel DMI info, if available

            # DMI SPEC -- http://www.dmtf.org/sites/default/files/standards/documents/DSP0134_2.7.0.pdf
            FORM_FACTOR = [ "Unknown", "Other", "Unknown", "Desktop",
                            "Low Profile Desktop", "Pizza Box", "Mini Tower", "Tower",
                            "Portable", "Laptop", "Notebook", "Hand Held", "Docking Station",
                            "All In One", "Sub Notebook", "Space-saving", "Lunch Box",
                            "Main Server Chassis", "Expansion Chassis", "Sub Chassis",
                            "Bus Expansion Chassis", "Peripheral Chassis", "RAID Chassis",
                            "Rack Mount Chassis", "Sealed-case PC", "Multi-system",
                            "CompactPCI", "AdvancedTCA", "Blade" ]

            DMI_DICT = {
                'bios_date': '/sys/devices/virtual/dmi/id/bios_date',
                'bios_version': '/sys/devices/virtual/dmi/id/bios_version',
                'form_factor': '/sys/devices/virtual/dmi/id/chassis_type',
                'product_name': '/sys/devices/virtual/dmi/id/product_name',
                'product_serial': '/sys/devices/virtual/dmi/id/product_serial',
                'product_uuid': '/sys/devices/virtual/dmi/id/product_uuid',
                'product_version': '/sys/devices/virtual/dmi/id/product_version',
                'system_vendor': '/sys/devices/virtual/dmi/id/sys_vendor'
                }

            for (key,path) in DMI_DICT.items():
                data = get_file_content(path)
                if data is not None:
                    if key == 'form_factor':
                        try:
                            self.facts['form_factor'] = FORM_FACTOR[int(data)]
                        except IndexError:
                            self.facts['form_factor'] = 'unknown (%s)' % data
                    else:
                        self.facts[key] = data
                else:
                    self.facts[key] = 'NA'

        else:
            # Fall back to using dmidecode, if available
            dmi_bin = self.module.get_bin_path('dmidecode')
            DMI_DICT = {
                'bios_date': 'bios-release-date',
                'bios_version': 'bios-version',
                'form_factor': 'chassis-type',
                'product_name': 'system-product-name',
                'product_serial': 'system-serial-number',
                'product_uuid': 'system-uuid',
                'product_version': 'system-version',
                'system_vendor': 'system-manufacturer'
                }
            for (k, v) in DMI_DICT.items():
                if dmi_bin is not None:
                    (rc, out, err) = self.module.run_command('%s -s %s' % (dmi_bin, v))
                    if rc == 0:
                        # Strip out commented lines (specific dmidecode output)
                        thisvalue = ''.join([ line for line in out.splitlines() if not line.startswith('#') ])
                        try:
                            json.dumps(thisvalue)
                        except UnicodeDecodeError:
                            thisvalue = "NA"

                        self.facts[k] = thisvalue
                    else:
                        self.facts[k] = 'NA'
                else:
                    self.facts[k] = 'NA'

    def _run_lsblk(self, lsblk_path):
        # call lsblk and collect all uuids
        # --exclude 2 makes lsblk ignore floppy disks, which are slower to answer than typical timeouts
        # this uses the linux major device number
        # for details see https://www.kernel.org/doc/Documentation/devices.txt
        args = ['--list', '--noheadings', '--paths',  '--output', 'NAME,UUID', '--exclude', '2']
        cmd = [lsblk_path] + args
        rc, out, err = self.module.run_command(cmd)
        return rc, out, err

    def _lsblk_uuid(self):
        uuids = {}
        lsblk_path = self.module.get_bin_path("lsblk")
        if not lsblk_path:
            return uuids

        rc, out, err = self._run_lsblk(lsblk_path)
        if rc != 0:
            return uuids

        # each line will be in format:
        # <devicename><some whitespace><uuid>
        # /dev/sda1  32caaec3-ef40-4691-a3b6-438c3f9bc1c0
        for lsblk_line in out.splitlines():
            if not lsblk_line:
                continue

            line = lsblk_line.strip()
            fields = line.rsplit(None, 1)

            if len(fields) < 2:
                continue

            device_name, uuid = fields[0].strip(), fields[1].strip()
            if device_name in uuids:
                continue
            uuids[device_name] = uuid

        return uuids

    def _run_findmnt(self, findmnt_path):
        args = ['--list', '--noheadings', '--notruncate']
        cmd = [findmnt_path] + args
        rc, out, err = self.module.run_command(cmd, errors='surrogate_then_replace')
        return rc, out, err

    def _find_bind_mounts(self):
        bind_mounts = set()
        findmnt_path = self.module.get_bin_path("findmnt")
        if not findmnt_path:
            return bind_mounts

        rc, out, err = self._run_findmnt(findmnt_path)
        if rc != 0:
            return bind_mounts

        # find bind mounts, in case /etc/mtab is a symlink to /proc/mounts
        for line in out.splitlines():
            fields = line.split()
            # fields[0] is the TARGET, fields[1] is the SOURCE
            if len(fields) < 2:
                continue

            # bind mounts will have a [/directory_name] in the SOURCE column
            if self.BIND_MOUNT_RE.match(fields[1]):
                bind_mounts.add(fields[0])

        return bind_mounts

    def _mtab_entries(self):
        mtab_file = '/etc/mtab'
        if not os.path.exists(mtab_file):
            mtab_file = '/proc/mounts'

        mtab = get_file_content(mtab_file, '')
        mtab_entries = []
        for line in mtab.splitlines():
            fields = line.split()
            if len(fields) < 4:
                continue
            mtab_entries.append(fields)
        return mtab_entries

    @timeout()
    def get_mount_facts(self):
        self.facts['mounts'] = []

        bind_mounts = self._find_bind_mounts()
        uuids = self._lsblk_uuid()
        mtab_entries = self._mtab_entries()

        mounts = []
        for fields in mtab_entries:
            device, mount, fstype, options = fields[0], fields[1], fields[2], fields[3]

            if not device.startswith('/') and ':/' not in device:
                continue

            if fstype == 'none':
                continue

            size_total, size_available = self._get_mount_size_facts(mount)

            if mount in bind_mounts:
                # only add if not already there, we might have a plain /etc/mtab
                if not self.MTAB_BIND_MOUNT_RE.match(options):
                    options += ",bind"

            mount_info = {'mount': mount,
                          'device': device,
                          'fstype': fstype,
                          'options': options,
                          # statvfs data
                          'size_total': size_total,
                          'size_available': size_available,
                          'uuid': uuids.get(device, 'N/A')}

            mounts.append(mount_info)

        self.facts['mounts'] = mounts

    def get_holders(self, block_dev_dict, sysdir):
        block_dev_dict['holders'] = []
        if os.path.isdir(sysdir + "/holders"):
            for folder in os.listdir(sysdir + "/holders"):
                if not folder.startswith("dm-"):
                    continue
                name = get_file_content(sysdir + "/holders/" + folder + "/dm/name")
                if name:
                    block_dev_dict['holders'].append(name)
                else:
                    block_dev_dict['holders'].append(folder)

    def get_device_facts(self):
        self.facts['devices'] = {}
        lspci = self.module.get_bin_path('lspci')
        if lspci:
            rc, pcidata, err = self.module.run_command([lspci, '-D'], errors='surrogate_then_replace')
        else:
            pcidata = None

        try:
            block_devs = os.listdir("/sys/block")
        except OSError:
            return

        for block in block_devs:
            virtual = 1
            sysfs_no_links = 0
            try:
                path = os.readlink(os.path.join("/sys/block/", block))
            except OSError:
                e = sys.exc_info()[1]
                if e.errno == errno.EINVAL:
                    path = block
                    sysfs_no_links = 1
                else:
                    continue
            if "virtual" in path:
                continue
            sysdir = os.path.join("/sys/block", path)
            if sysfs_no_links == 1:
                for folder in os.listdir(sysdir):
                    if "device" in folder:
                        virtual = 0
                        break
                if virtual:
                    continue
            d = {}
            diskname = os.path.basename(sysdir)
            for key in ['vendor', 'model', 'sas_address', 'sas_device_handle']:
                d[key] = get_file_content(sysdir + "/device/" + key)

            for key,test in [ ('removable','/removable'), \
                              ('support_discard','/queue/discard_granularity'),
                              ]:
                d[key] = get_file_content(sysdir + test)

            d['partitions'] = {}
            for folder in os.listdir(sysdir):
                m = re.search("(" + diskname + "\d+)", folder)
                if m:
                    part = {}
                    partname = m.group(1)
                    part_sysdir = sysdir + "/" + partname

                    part['start'] = get_file_content(part_sysdir + "/start",0)
                    part['sectors'] = get_file_content(part_sysdir + "/size",0)
                    part['sectorsize'] = get_file_content(part_sysdir + "/queue/logical_block_size")
                    if not part['sectorsize']:
                        part['sectorsize'] = get_file_content(part_sysdir + "/queue/hw_sector_size",512)
                    part['size'] = self.module.pretty_bytes((float(part['sectors']) * float(part['sectorsize'])))
                    part['uuid'] = get_partition_uuid(partname)
                    self.get_holders(part, part_sysdir)

                    d['partitions'][partname] = part

            d['rotational'] = get_file_content(sysdir + "/queue/rotational")
            d['scheduler_mode'] = ""
            scheduler = get_file_content(sysdir + "/queue/scheduler")
            if scheduler is not None:
                m = re.match(".*?(\[(.*)\])", scheduler)
                if m:
                    d['scheduler_mode'] = m.group(2)

            d['sectors'] = get_file_content(sysdir + "/size")
            if not d['sectors']:
                d['sectors'] = 0
            d['sectorsize'] = get_file_content(sysdir + "/queue/logical_block_size")
            if not d['sectorsize']:
                d['sectorsize'] = get_file_content(sysdir + "/queue/hw_sector_size",512)
            d['size'] = self.module.pretty_bytes(float(d['sectors']) * float(d['sectorsize']))

            d['host'] = ""

            # domains are numbered (0 to ffff), bus (0 to ff), slot (0 to 1f), and function (0 to 7).
            m = re.match(".+/([a-f0-9]{4}:[a-f0-9]{2}:[0|1][a-f0-9]\.[0-7])/", sysdir)
            if m and pcidata:
                pciid = m.group(1)
                did = re.escape(pciid)
                m = re.search("^" + did + "\s(.*)$", pcidata, re.MULTILINE)
                if m:
                    d['host'] = m.group(1)

            self.get_holders(d, sysdir)

            self.facts['devices'][diskname] = d

    def get_uptime_facts(self):
        uptime_file_content = get_file_content('/proc/uptime')
        if uptime_file_content:
            uptime_seconds_string = uptime_file_content.split(' ')[0]
            self.facts['uptime_seconds'] = int(float(uptime_seconds_string))

    def get_lvm_facts(self):
        """ Get LVM Facts if running as root and lvm utils are available """

        if os.getuid() == 0 and self.module.get_bin_path('vgs'):
            lvm_util_options = '--noheadings --nosuffix --units g'

            vgs_path = self.module.get_bin_path('vgs')
            #vgs fields: VG #PV #LV #SN Attr VSize VFree
            vgs={}
            if vgs_path:
                rc, vg_lines, err = self.module.run_command( '%s %s' % (vgs_path, lvm_util_options))
                for vg_line in vg_lines.splitlines():
                    items = vg_line.split()
                    vgs[items[0]] = {'size_g':items[-2],
                                     'free_g':items[-1],
                                     'num_lvs': items[2],
                                     'num_pvs': items[1]}

            lvs_path = self.module.get_bin_path('lvs')
            #lvs fields:
            #LV VG Attr LSize Pool Origin Data% Move Log Copy% Convert
            lvs = {}
            if lvs_path:
                rc, lv_lines, err = self.module.run_command( '%s %s' % (lvs_path, lvm_util_options))
                for lv_line in lv_lines.splitlines():
                    items = lv_line.split()
                    lvs[items[0]] = {'size_g': items[3], 'vg': items[1]}

            self.facts['lvm'] = {'lvs': lvs, 'vgs': vgs}


class SunOSHardware(Hardware):
    """
    In addition to the generic memory and cpu facts, this also sets
    swap_reserved_mb and swap_allocated_mb that is available from *swap -s*.
    """
    platform = 'SunOS'

    def populate(self):
        self.module.run_command_environ_update = {'LANG': 'C', 'LC_ALL': 'C', 'LC_NUMERIC': 'C'}
        self.get_cpu_facts()
        self.get_memory_facts()
        self.get_dmi_facts()
        self.get_device_facts()
        self.get_uptime_facts()
        try:
            self.get_mount_facts()
        except TimeoutError:
            pass
        return self.facts

    def get_cpu_facts(self):
        physid = 0
        sockets = {}
        rc, out, err = self.module.run_command("/usr/bin/kstat cpu_info")
        self.facts['processor'] = []
        for line in out.splitlines():
            if len(line) < 1:
                continue
            data = line.split(None, 1)
            key = data[0].strip()
            # "brand" works on Solaris 10 & 11. "implementation" for Solaris 9.
            if key == 'module:':
                brand = ''
            elif key == 'brand':
                brand = data[1].strip()
            elif key == 'clock_MHz':
                clock_mhz = data[1].strip()
            elif key == 'implementation':
                processor = brand or data[1].strip()
                # Add clock speed to description for SPARC CPU
                if self.facts['machine'] != 'i86pc':
                    processor += " @ " + clock_mhz + "MHz"
                if 'processor' not in self.facts:
                    self.facts['processor'] = []
                self.facts['processor'].append(processor)
            elif key == 'chip_id':
                physid = data[1].strip()
                if physid not in sockets:
                    sockets[physid] = 1
                else:
                    sockets[physid] += 1
        # Counting cores on Solaris can be complicated.
        # https://blogs.oracle.com/mandalika/entry/solaris_show_me_the_cpu
        # Treat 'processor_count' as physical sockets and 'processor_cores' as
        # virtual CPUs visisble to Solaris. Not a true count of cores for modern SPARC as
        # these processors have: sockets -> cores -> threads/virtual CPU.
        if len(sockets) > 0:
            self.facts['processor_count'] = len(sockets)
            self.facts['processor_cores'] = reduce(lambda x, y: x + y, sockets.values())
        else:
            self.facts['processor_cores'] = 'NA'
            self.facts['processor_count'] = len(self.facts['processor'])

    def get_memory_facts(self):
        rc, out, err = self.module.run_command(["/usr/sbin/prtconf"])
        for line in out.splitlines():
            if 'Memory size' in line:
                self.facts['memtotal_mb'] = int(line.split()[2])
        rc, out, err = self.module.run_command("/usr/sbin/swap -s")
        allocated = int(out.split()[1][:-1])
        reserved = int(out.split()[5][:-1])
        used = int(out.split()[8][:-1])
        free = int(out.split()[10][:-1])
        self.facts['swapfree_mb'] = free // 1024
        self.facts['swaptotal_mb'] = (free + used) // 1024
        self.facts['swap_allocated_mb'] = allocated // 1024
        self.facts['swap_reserved_mb'] = reserved // 1024

    @timeout()
    def get_mount_facts(self):
        self.facts['mounts'] = []
        # For a detailed format description see mnttab(4)
        #   special mount_point fstype options time
        fstab = get_file_content('/etc/mnttab')
        if fstab:
            for line in fstab.splitlines():
                fields = line.split('\t')
                size_total, size_available = self._get_mount_size_facts(fields[1])
                self.facts['mounts'].append({'mount': fields[1], 'device': fields[0], 'fstype' : fields[2], 'options': fields[3], 'time': fields[4], 'size_total': size_total, 'size_available': size_available})

    def get_dmi_facts(self):
        uname_path = self.module.get_bin_path("prtdiag")
        rc, out, err = self.module.run_command(uname_path)
        """
        rc returns 1
        """
        if out:
            system_conf = out.split('\n')[0]
            found = re.search(r'(\w+\sEnterprise\s\w+)',system_conf)
            if found:
                self.facts['product_name'] = found.group(1)

    def get_device_facts(self):
        # Device facts are derived for sdderr kstats. This code does not use the
        # full output, but rather queries for specific stats.
        # Example output:
        # sderr:0:sd0,err:Hard Errors     0
        # sderr:0:sd0,err:Illegal Request 6
        # sderr:0:sd0,err:Media Error     0
        # sderr:0:sd0,err:Predictive Failure Analysis     0
        # sderr:0:sd0,err:Product VBOX HARDDISK   9
        # sderr:0:sd0,err:Revision        1.0
        # sderr:0:sd0,err:Serial No       VB0ad2ec4d-074a
        # sderr:0:sd0,err:Size    53687091200
        # sderr:0:sd0,err:Soft Errors     0
        # sderr:0:sd0,err:Transport Errors        0
        # sderr:0:sd0,err:Vendor  ATA

        self.facts['devices'] = {}

        disk_stats = {
            'Product': 'product',
            'Revision': 'revision',
            'Serial No': 'serial',
            'Size': 'size',
            'Vendor': 'vendor',
            'Hard Errors': 'hard_errors',
            'Soft Errors': 'soft_errors',
            'Transport Errors': 'transport_errors',
            'Media Error': 'media_errors',
            'Predictive Failure Analysis': 'predictive_failure_analysis',
            'Illegal Request': 'illegal_request',
        }

        cmd = ['/usr/bin/kstat', '-p']

        for ds in disk_stats:
            cmd.append('sderr:::%s' % ds)

        d = {}
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            return dict()

        sd_instances = frozenset(line.split(':')[1] for line in out.split('\n') if line.startswith('sderr'))
        for instance in sd_instances:
            lines = (line for line in out.split('\n') if ':' in line and line.split(':')[1] == instance)
            for line in lines:
                text, value = line.split('\t')
                stat = text.split(':')[3]

                if stat == 'Size':
                    d[disk_stats.get(stat)] = self.module.pretty_bytes(float(value))
                else:
                    d[disk_stats.get(stat)] = value.rstrip()

            diskname = 'sd' + instance
            self.facts['devices'][diskname] = d
            d = {}

    def get_uptime_facts(self):
        # On Solaris, unix:0:system_misc:snaptime is created shortly after machine boots up
        # and displays tiem in seconds. This is much easier than using uptime as we would
        # need to have a parsing procedure for translating from human-readable to machine-readable
        # format.
        # Example output:
        # unix:0:system_misc:snaptime     1175.410463590
        rc, out, err = self.module.run_command('/usr/bin/kstat -p unix:0:system_misc:snaptime')

        if rc != 0:
            return

        self.facts['uptime_seconds'] = int(float(out.split('\t')[1]))


class OpenBSDHardware(Hardware):
    """
    OpenBSD-specific subclass of Hardware. Defines memory, CPU and device facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count
    - processor_speed

    In addition, it also defines number of DMI facts and device facts.
    """
    platform = 'OpenBSD'

    def populate(self):
        self.sysctl = self.get_sysctl(['hw'])
        self.get_memory_facts()
        self.get_processor_facts()
        self.get_device_facts()
        try:
            self.get_mount_facts()
        except TimeoutError:
            pass
        self.get_dmi_facts()
        return self.facts

    @timeout()
    def get_mount_facts(self):
        self.facts['mounts'] = []
        fstab = get_file_content('/etc/fstab')
        if fstab:
            for line in fstab.splitlines():
                if line.startswith('#') or line.strip() == '':
                    continue
                fields = re.sub(r'\s+',' ', line).split()
                if fields[1] == 'none' or fields[3] == 'xx':
                    continue
                size_total, size_available = self._get_mount_size_facts(fields[1])
                self.facts['mounts'].append({'mount': fields[1], 'device': fields[0], 'fstype' : fields[2], 'options': fields[3], 'size_total': size_total, 'size_available': size_available})


    def get_memory_facts(self):
        # Get free memory. vmstat output looks like:
        #  procs    memory       page                    disks    traps          cpu
        #  r b w    avm     fre  flt  re  pi  po  fr  sr wd0 fd0  int   sys   cs us sy id
        #  0 0 0  47512   28160   51   0   0   0   0   0   1   0  116    89   17  0  1 99
        rc, out, err = self.module.run_command("/usr/bin/vmstat")
        if rc == 0:
            self.facts['memfree_mb'] = int(out.splitlines()[-1].split()[4]) // 1024
            self.facts['memtotal_mb'] = int(self.sysctl['hw.usermem']) // 1024 // 1024

        # Get swapctl info. swapctl output looks like:
        # total: 69268 1K-blocks allocated, 0 used, 69268 available
        # And for older OpenBSD:
        # total: 69268k bytes allocated = 0k used, 69268k available
        rc, out, err = self.module.run_command("/sbin/swapctl -sk")
        if rc == 0:
            swaptrans = { ord(u'k'): None, ord(u'm'): None, ord(u'g'): None}
            data = to_text(out, errors='surrogate_or_strict').split()
            self.facts['swapfree_mb'] = int(data[-2].translate(swaptrans)) // 1024
            self.facts['swaptotal_mb'] = int(data[1].translate(swaptrans)) // 1024

    def get_processor_facts(self):
        processor = []
        for i in range(int(self.sysctl['hw.ncpu'])):
            processor.append(self.sysctl['hw.model'])

        self.facts['processor'] = processor
        # The following is partly a lie because there is no reliable way to
        # determine the number of physical CPUs in the system. We can only
        # query the number of logical CPUs, which hides the number of cores.
        # On amd64/i386 we could try to inspect the smt/core/package lines in
        # dmesg, however even those have proven to be unreliable.
        # So take a shortcut and report the logical number of processors in
        # 'processor_count' and 'processor_cores' and leave it at that.
        self.facts['processor_count'] = self.sysctl['hw.ncpu']
        self.facts['processor_cores'] = self.sysctl['hw.ncpu']

    def get_device_facts(self):
        devices = []
        devices.extend(self.sysctl['hw.disknames'].split(','))
        self.facts['devices'] = devices

    def get_dmi_facts(self):
        # We don't use dmidecode(1) here because:
        # - it would add dependency on an external package
        # - dmidecode(1) can only be ran as root
        # So instead we rely on sysctl(8) to provide us the information on a
        # best-effort basis. As a bonus we also get facts on non-amd64/i386
        # platforms this way.
        sysctl_to_dmi = {
            'hw.product':  'product_name',
            'hw.version':  'product_version',
            'hw.uuid':     'product_uuid',
            'hw.serialno': 'product_serial',
            'hw.vendor':   'system_vendor',
        }

        for mib in sysctl_to_dmi:
            if mib in self.sysctl:
                self.facts[sysctl_to_dmi[mib]] = self.sysctl[mib]

class FreeBSDHardware(Hardware):
    """
    FreeBSD-specific subclass of Hardware.  Defines memory and CPU facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count
    - devices
    """
    platform = 'FreeBSD'
    DMESG_BOOT = '/var/run/dmesg.boot'

    def populate(self):
        self.get_cpu_facts()
        self.get_memory_facts()
        self.get_dmi_facts()
        self.get_device_facts()
        try:
            self.get_mount_facts()
        except TimeoutError:
            pass
        return self.facts

    def get_cpu_facts(self):
        self.facts['processor'] = []
        rc, out, err = self.module.run_command("/sbin/sysctl -n hw.ncpu")
        self.facts['processor_count'] = out.strip()

        dmesg_boot = get_file_content(FreeBSDHardware.DMESG_BOOT)
        if not dmesg_boot:
            rc, dmesg_boot, err = self.module.run_command("/sbin/dmesg")
        for line in dmesg_boot.splitlines():
            if 'CPU:' in line:
                cpu = re.sub(r'CPU:\s+', r"", line)
                self.facts['processor'].append(cpu.strip())
            if 'Logical CPUs per core' in line:
                self.facts['processor_cores'] = line.split()[4]


    def get_memory_facts(self):
        rc, out, err = self.module.run_command("/sbin/sysctl vm.stats")
        for line in out.splitlines():
            data = line.split()
            if 'vm.stats.vm.v_page_size' in line:
                pagesize = int(data[1])
            if 'vm.stats.vm.v_page_count' in line:
                pagecount = int(data[1])
            if 'vm.stats.vm.v_free_count' in line:
                freecount = int(data[1])
        self.facts['memtotal_mb'] = pagesize * pagecount // 1024 // 1024
        self.facts['memfree_mb'] = pagesize * freecount // 1024 // 1024
        # Get swapinfo.  swapinfo output looks like:
        # Device          1M-blocks     Used    Avail Capacity
        # /dev/ada0p3        314368        0   314368     0%
        #
        rc, out, err = self.module.run_command("/usr/sbin/swapinfo -k")
        lines = out.splitlines()
        if len(lines[-1]) == 0:
            lines.pop()
        data = lines[-1].split()
        if data[0] != 'Device':
            self.facts['swaptotal_mb'] = int(data[1]) // 1024
            self.facts['swapfree_mb'] = int(data[3]) // 1024

    @timeout()
    def get_mount_facts(self):
        self.facts['mounts'] = []
        fstab = get_file_content('/etc/fstab')
        if fstab:
            for line in fstab.splitlines():
                if line.startswith('#') or line.strip() == '':
                    continue
                fields = re.sub(r'\s+',' ',line).split()
                size_total, size_available = self._get_mount_size_facts(fields[1])
                self.facts['mounts'].append({'mount': fields[1], 'device': fields[0], 'fstype' : fields[2], 'options': fields[3], 'size_total': size_total, 'size_available': size_available})

    def get_device_facts(self):
        sysdir = '/dev'
        self.facts['devices'] = {}
        drives = re.compile('(ada?\d+|da\d+|a?cd\d+)') #TODO: rc, disks, err = self.module.run_command("/sbin/sysctl kern.disks")
        slices = re.compile('(ada?\d+s\d+\w*|da\d+s\d+\w*)')
        if os.path.isdir(sysdir):
            dirlist = sorted(os.listdir(sysdir))
            for device in dirlist:
                d = drives.match(device)
                if d:
                    self.facts['devices'][d.group(1)] = []
                s = slices.match(device)
                if s:
                    self.facts['devices'][d.group(1)].append(s.group(1))

    def get_dmi_facts(self):
        ''' learn dmi facts from system

        Use dmidecode executable if available'''

        # Fall back to using dmidecode, if available
        dmi_bin = self.module.get_bin_path('dmidecode')
        DMI_DICT = dict(
            bios_date='bios-release-date',
            bios_version='bios-version',
            form_factor='chassis-type',
            product_name='system-product-name',
            product_serial='system-serial-number',
            product_uuid='system-uuid',
            product_version='system-version',
            system_vendor='system-manufacturer'
        )
        for (k, v) in DMI_DICT.items():
            if dmi_bin is not None:
                (rc, out, err) = self.module.run_command('%s -s %s' % (dmi_bin, v))
                if rc == 0:
                    # Strip out commented lines (specific dmidecode output)
                    self.facts[k] = ''.join([line for line in out.splitlines() if not line.startswith('#') ])
                    try:
                        json.dumps(self.facts[k])
                    except UnicodeDecodeError:
                        self.facts[k] = 'NA'
                else:
                    self.facts[k] = 'NA'
            else:
                self.facts[k] = 'NA'


class DragonFlyHardware(FreeBSDHardware):
    platform = 'DragonFly'


class NetBSDHardware(Hardware):
    """
    NetBSD-specific subclass of Hardware.  Defines memory and CPU facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count
    - devices
    """
    platform = 'NetBSD'
    MEMORY_FACTS = ['MemTotal', 'SwapTotal', 'MemFree', 'SwapFree']

    def populate(self):
        self.sysctl = self.get_sysctl(['machdep'])
        self.get_cpu_facts()
        self.get_memory_facts()
        try:
            self.get_mount_facts()
        except TimeoutError:
            pass
        self.get_dmi_facts()
        return self.facts

    def get_cpu_facts(self):

        i = 0
        physid = 0
        sockets = {}
        if not os.access("/proc/cpuinfo", os.R_OK):
            return
        self.facts['processor'] = []
        for line in get_file_lines("/proc/cpuinfo"):
            data = line.split(":", 1)
            key = data[0].strip()
            # model name is for Intel arch, Processor (mind the uppercase P)
            # works for some ARM devices, like the Sheevaplug.
            if key == 'model name' or key == 'Processor':
                if 'processor' not in self.facts:
                    self.facts['processor'] = []
                self.facts['processor'].append(data[1].strip())
                i += 1
            elif key == 'physical id':
                physid = data[1].strip()
                if physid not in sockets:
                    sockets[physid] = 1
            elif key == 'cpu cores':
                sockets[physid] = int(data[1].strip())
        if len(sockets) > 0:
            self.facts['processor_count'] = len(sockets)
            self.facts['processor_cores'] = reduce(lambda x, y: x + y, sockets.values())
        else:
            self.facts['processor_count'] = i
            self.facts['processor_cores'] = 'NA'

    def get_memory_facts(self):
        if not os.access("/proc/meminfo", os.R_OK):
            return
        for line in get_file_lines("/proc/meminfo"):
            data = line.split(":", 1)
            key = data[0]
            if key in NetBSDHardware.MEMORY_FACTS:
                val = data[1].strip().split(' ')[0]
                self.facts["%s_mb" % key.lower()] = int(val) // 1024

    @timeout()
    def get_mount_facts(self):
        self.facts['mounts'] = []
        fstab = get_file_content('/etc/fstab')
        if fstab:
            for line in fstab.splitlines():
                if line.startswith('#') or line.strip() == '':
                    continue
                fields = re.sub(r'\s+',' ',line).split()
                size_total, size_available = self._get_mount_size_facts(fields[1])
                self.facts['mounts'].append({'mount': fields[1], 'device': fields[0], 'fstype' : fields[2], 'options': fields[3], 'size_total': size_total, 'size_available': size_available})

    def get_dmi_facts(self):
        # We don't use dmidecode(1) here because:
        # - it would add dependency on an external package
        # - dmidecode(1) can only be ran as root
        # So instead we rely on sysctl(8) to provide us the information on a
        # best-effort basis. As a bonus we also get facts on non-amd64/i386
        # platforms this way.
        sysctl_to_dmi = {
            'machdep.dmi.system-product':  'product_name',
            'machdep.dmi.system-version':  'product_version',
            'machdep.dmi.system-uuid':     'product_uuid',
            'machdep.dmi.system-serial':   'product_serial',
            'machdep.dmi.system-vendor':   'system_vendor',
        }

        for mib in sysctl_to_dmi:
            if mib in self.sysctl:
                self.facts[sysctl_to_dmi[mib]] = self.sysctl[mib]

class AIX(Hardware):
    """
    AIX-specific subclass of Hardware.  Defines memory and CPU facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count
    """
    platform = 'AIX'

    def populate(self):
        self.get_cpu_facts()
        self.get_memory_facts()
        self.get_dmi_facts()
        self.get_vgs_facts()
        self.get_mount_facts()
        return self.facts

    def get_cpu_facts(self):
        self.facts['processor'] = []


        rc, out, err = self.module.run_command("/usr/sbin/lsdev -Cc processor")
        if out:
            i = 0
            for line in out.splitlines():

                if 'Available' in line:
                    if i == 0:
                        data = line.split(' ')
                        cpudev = data[0]

                    i += 1
            self.facts['processor_count'] = int(i)

            rc, out, err = self.module.run_command("/usr/sbin/lsattr -El " + cpudev + " -a type")

            data = out.split(' ')
            self.facts['processor'] = data[1]

            rc, out, err = self.module.run_command("/usr/sbin/lsattr -El " + cpudev + " -a smt_threads")

            data = out.split(' ')
            self.facts['processor_cores'] = int(data[1])

    def get_memory_facts(self):
        pagesize = 4096
        rc, out, err = self.module.run_command("/usr/bin/vmstat -v")
        for line in out.splitlines():
            data = line.split()
            if 'memory pages' in line:
                pagecount = int(data[0])
            if 'free pages' in line:
                freecount = int(data[0])
        self.facts['memtotal_mb'] = pagesize * pagecount // 1024 // 1024
        self.facts['memfree_mb'] = pagesize * freecount // 1024 // 1024
        # Get swapinfo.  swapinfo output looks like:
        # Device          1M-blocks     Used    Avail Capacity
        # /dev/ada0p3        314368        0   314368     0%
        #
        rc, out, err = self.module.run_command("/usr/sbin/lsps -s")
        if out:
            lines = out.splitlines()
            data = lines[1].split()
            swaptotal_mb = int(data[0].rstrip('MB'))
            percused = int(data[1].rstrip('%'))
            self.facts['swaptotal_mb'] = swaptotal_mb
            self.facts['swapfree_mb'] = int(swaptotal_mb * ( 100 - percused ) / 100)

    def get_dmi_facts(self):
        rc, out, err = self.module.run_command("/usr/sbin/lsattr -El sys0 -a fwversion")
        data = out.split()
        self.facts['firmware_version'] = data[1].strip('IBM,')
        lsconf_path = self.module.get_bin_path("lsconf")
        if lsconf_path:
            rc, out, err = self.module.run_command(lsconf_path)
            if rc == 0 and out:
                for line in out.splitlines():
                    data = line.split(':')
                    if 'Machine Serial Number' in line:
                        self.facts['product_serial'] = data[1].strip()
                    if 'LPAR Info' in line:
                        self.facts['lpar_info'] = data[1].strip()
                    if 'System Model' in line:
                        self.facts['product_name'] = data[1].strip()
    def get_vgs_facts(self):
        """
        Get vg and pv Facts
        rootvg:
        PV_NAME           PV STATE          TOTAL PPs   FREE PPs    FREE DISTRIBUTION
        hdisk0            active            546         0           00..00..00..00..00
        hdisk1            active            546         113         00..00..00..21..92
        realsyncvg:
        PV_NAME           PV STATE          TOTAL PPs   FREE PPs    FREE DISTRIBUTION
        hdisk74           active            1999        6           00..00..00..00..06
        testvg:
        PV_NAME           PV STATE          TOTAL PPs   FREE PPs    FREE DISTRIBUTION
        hdisk105          active            999         838         200..39..199..200..200
        hdisk106          active            999         599         200..00..00..199..200
        """

        lsvg_path = self.module.get_bin_path("lsvg")
        xargs_path = self.module.get_bin_path("xargs")
        cmd = "%s | %s %s -p" % (lsvg_path ,xargs_path,lsvg_path)
        if lsvg_path and xargs_path:
            rc, out, err = self.module.run_command(cmd,use_unsafe_shell=True)
            if rc == 0 and out:
                self.facts['vgs']= {}
                for m in re.finditer(r'(\S+):\n.*FREE DISTRIBUTION(\n(\S+)\s+(\w+)\s+(\d+)\s+(\d+).*)+', out):
                    self.facts['vgs'][m.group(1)] = []
                    pp_size = 0
                    cmd = "%s %s" % (lsvg_path,m.group(1))
                    rc, out, err = self.module.run_command(cmd)
                    if rc == 0 and out:
                        pp_size = re.search(r'PP SIZE:\s+(\d+\s+\S+)',out).group(1)
                        for n in re.finditer(r'(\S+)\s+(\w+)\s+(\d+)\s+(\d+).*',m.group(0)):
                            pv_info = { 'pv_name': n.group(1),
                                        'pv_state': n.group(2),
                                        'total_pps': n.group(3),
                                        'free_pps': n.group(4),
                                        'pp_size': pp_size
                                      }
                            self.facts['vgs'][m.group(1)].append(pv_info)


    def get_mount_facts(self):
        self.facts['mounts'] = []
        # AIX does not have mtab but mount command is only source of info (or to use
        # api calls to get same info)
        mount_path = self.module.get_bin_path('mount')
        rc, mount_out, err = self.module.run_command(mount_path)
        if mount_out:
            for line in mount_out.split('\n'):
                fields = line.split()
                if len(fields) != 0 and fields[0] != 'node' and fields[0][0] != '-' and re.match('^/.*|^[a-zA-Z].*|^[0-9].*', fields[0]):
                    if re.match('^/', fields[0]):
                        # normal mount
                        self.facts['mounts'].append({'mount': fields[1],
                                                 'device': fields[0],
                                                 'fstype' : fields[2],
                                                 'options': fields[6],
                                                 'time': '%s %s %s' % ( fields[3], fields[4], fields[5])})
                    else:
                        # nfs or cifs based mount
                        # in case of nfs if no mount options are provided on command line
                        # add into fields empty string...
                        if len(fields) < 8:
                            fields.append("")
                        self.facts['mounts'].append({'mount': fields[2],
                                                 'device': '%s:%s' % (fields[0], fields[1]),
                                                 'fstype' : fields[3],
                                                 'options': fields[7],
                                                 'time': '%s %s %s' % ( fields[4], fields[5], fields[6])})

class HPUX(Hardware):
    """
    HP-UX-specific subclass of Hardware. Defines memory and CPU facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor
    - processor_cores
    - processor_count
    - model
    - firmware
    """

    platform = 'HP-UX'

    def populate(self):
        self.get_cpu_facts()
        self.get_memory_facts()
        self.get_hw_facts()
        return self.facts

    def get_cpu_facts(self):
        if self.facts['architecture'] == '9000/800':
            rc, out, err = self.module.run_command("ioscan -FkCprocessor | wc -l", use_unsafe_shell=True)
            self.facts['processor_count'] = int(out.strip())
        #Working with machinfo mess
        elif self.facts['architecture'] == 'ia64':
            if self.facts['distribution_version'] == "B.11.23":
                rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep 'Number of CPUs'", use_unsafe_shell=True)
                self.facts['processor_count'] = int(out.strip().split('=')[1])
                rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep 'processor family'", use_unsafe_shell=True)
                self.facts['processor'] = re.search('.*(Intel.*)', out).groups()[0].strip()
                rc, out, err = self.module.run_command("ioscan -FkCprocessor | wc -l", use_unsafe_shell=True)
                self.facts['processor_cores'] = int(out.strip())
            if self.facts['distribution_version'] == "B.11.31":
                #if machinfo return cores strings release B.11.31 > 1204
                rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep core | wc -l", use_unsafe_shell=True)
                if out.strip()== '0':
                    rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep Intel", use_unsafe_shell=True)
                    self.facts['processor_count'] = int(out.strip().split(" ")[0])
                    #If hyperthreading is active divide cores by 2
                    rc, out, err = self.module.run_command("/usr/sbin/psrset | grep LCPU", use_unsafe_shell=True)
                    data = re.sub(' +',' ',out).strip().split(' ')
                    if len(data) == 1:
                        hyperthreading = 'OFF'
                    else:
                        hyperthreading = data[1]
                    rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep logical", use_unsafe_shell=True)
                    data = out.strip().split(" ")
                    if hyperthreading == 'ON':
                        self.facts['processor_cores'] = int(data[0])/2
                    else:
                        if len(data) == 1:
                            self.facts['processor_cores'] = self.facts['processor_count']
                        else:
                            self.facts['processor_cores'] = int(data[0])
                    rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep Intel |cut -d' ' -f4-", use_unsafe_shell=True)
                    self.facts['processor'] = out.strip()
                else:
                    rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | egrep 'socket[s]?$' | tail -1", use_unsafe_shell=True)
                    self.facts['processor_count'] = int(out.strip().split(" ")[0])
                    rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep -e '[0-9] core' | tail -1", use_unsafe_shell=True)
                    self.facts['processor_cores'] = int(out.strip().split(" ")[0])
                    rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep Intel", use_unsafe_shell=True)
                    self.facts['processor'] = out.strip()

    def get_memory_facts(self):
        pagesize = 4096
        rc, out, err = self.module.run_command("/usr/bin/vmstat | tail -1", use_unsafe_shell=True)
        data = int(re.sub(' +',' ',out).split(' ')[5].strip())
        self.facts['memfree_mb'] = pagesize * data // 1024 // 1024
        if self.facts['architecture'] == '9000/800':
            try:
                rc, out, err = self.module.run_command("grep Physical /var/adm/syslog/syslog.log")
                data = re.search('.*Physical: ([0-9]*) Kbytes.*',out).groups()[0].strip()
                self.facts['memtotal_mb'] = int(data) // 1024
            except AttributeError:
                #For systems where memory details aren't sent to syslog or the log has rotated, use parsed
                #adb output. Unfortunately /dev/kmem doesn't have world-read, so this only works as root.
                if os.access("/dev/kmem", os.R_OK):
                    rc, out, err = self.module.run_command("echo 'phys_mem_pages/D' | adb -k /stand/vmunix /dev/kmem | tail -1 | awk '{print $2}'", use_unsafe_shell=True)
                    if not err:
                        data = out
                        self.facts['memtotal_mb'] = int(data) / 256
        else:
            rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo | grep Memory", use_unsafe_shell=True)
            data = re.search('Memory[\ :=]*([0-9]*).*MB.*',out).groups()[0].strip()
            self.facts['memtotal_mb'] = int(data)
        rc, out, err = self.module.run_command("/usr/sbin/swapinfo -m -d -f -q")
        self.facts['swaptotal_mb'] = int(out.strip())
        rc, out, err = self.module.run_command("/usr/sbin/swapinfo -m -d -f | egrep '^dev|^fs'", use_unsafe_shell=True)
        swap = 0
        for line in out.strip().splitlines():
            swap += int(re.sub(' +',' ',line).split(' ')[3].strip())
        self.facts['swapfree_mb'] = swap

    def get_hw_facts(self):
        rc, out, err = self.module.run_command("model")
        self.facts['model'] = out.strip()
        if self.facts['architecture'] == 'ia64':
            separator = ':'
            if self.facts['distribution_version'] == "B.11.23":
                separator = '='
            rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo |grep -i 'Firmware revision' | grep -v BMC", use_unsafe_shell=True)
            self.facts['firmware_version'] = out.split(separator)[1].strip()
            rc, out, err = self.module.run_command("/usr/contrib/bin/machinfo |grep -i 'Machine serial number' ",use_unsafe_shell=True)
            if rc == 0 and out:
                self.facts['product_serial'] = out.split(separator)[1].strip()

class Darwin(Hardware):
    """
    Darwin-specific subclass of Hardware.  Defines memory and CPU facts:
    - processor
    - processor_cores
    - memtotal_mb
    - memfree_mb
    - model
    - osversion
    - osrevision
    """
    platform = 'Darwin'

    def populate(self):
        self.sysctl = self.get_sysctl(['hw','machdep','kern'])
        self.get_mac_facts()
        self.get_cpu_facts()
        self.get_memory_facts()
        return self.facts

    def get_system_profile(self):
        rc, out, err = self.module.run_command(["/usr/sbin/system_profiler", "SPHardwareDataType"])
        if rc != 0:
            return dict()
        system_profile = dict()
        for line in out.splitlines():
            if ': ' in line:
                (key, value) = line.split(': ', 1)
                system_profile[key.strip()] = ' '.join(value.strip().split())
        return system_profile

    def get_mac_facts(self):
        rc, out, err = self.module.run_command("sysctl hw.model")
        if rc == 0:
            self.facts['model'] = out.splitlines()[-1].split()[1]
        self.facts['osversion'] = self.sysctl['kern.osversion']
        self.facts['osrevision'] = self.sysctl['kern.osrevision']

    def get_cpu_facts(self):
        if 'machdep.cpu.brand_string' in self.sysctl: # Intel
            self.facts['processor'] = self.sysctl['machdep.cpu.brand_string']
            self.facts['processor_cores'] = self.sysctl['machdep.cpu.core_count']
        else: # PowerPC
            system_profile = self.get_system_profile()
            self.facts['processor'] = '%s @ %s' % (system_profile['Processor Name'], system_profile['Processor Speed'])
            self.facts['processor_cores'] = self.sysctl['hw.physicalcpu']

    def get_memory_facts(self):
        self.facts['memtotal_mb'] = int(self.sysctl['hw.memsize']) // 1024 // 1024

        rc, out, err = self.module.run_command("sysctl hw.usermem")
        if rc == 0:
            self.facts['memfree_mb'] = int(out.splitlines()[-1].split()[1]) // 1024 // 1024

class HurdHardware(LinuxHardware):
    """
    GNU Hurd specific subclass of Hardware. Define memory and mount facts
    based on procfs compatibility translator mimicking the interface of
    the Linux kernel.
    """

    platform = 'GNU'

    def populate(self):
        self.get_uptime_facts()
        self.get_memory_facts()
        try:
            self.get_mount_facts()
        except TimeoutError:
            pass
        return self.facts

class Network(Facts):
    """
    This is a generic Network subclass of Facts.  This should be further
    subclassed to implement per platform.  If you subclass this,
    you must define:
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.

    All subclasses MUST define platform.
    """
    platform = 'Generic'

    IPV6_SCOPE = { '0' : 'global',
                   '10' : 'host',
                   '20' : 'link',
                   '40' : 'admin',
                   '50' : 'site',
                   '80' : 'organization' }

    def __new__(cls, *arguments, **keyword):
        # When Network is created, it chooses a subclass to create instead.
        # This check prevents the subclass from then trying to find a subclass
        # and create that.
        if cls is not Network:
            return super(Network, cls).__new__(cls)

        subclass = cls
        for sc in get_all_subclasses(Network):
            if sc.platform == platform.system():
                subclass = sc
        if PY3:
            return super(cls, subclass).__new__(subclass)
        else:
            return super(cls, subclass).__new__(subclass, *arguments, **keyword)

    def populate(self):
        return self.facts

class LinuxNetwork(Network):
    """
    This is a Linux-specific subclass of Network.  It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    - ipv4_address and ipv6_address: the first non-local address for each family.
    """
    platform = 'Linux'
    INTERFACE_TYPE = {
        '1': 'ether',
        '512': 'ppp',
        '772': 'loopback',
        '65534': 'tunnel',
    }

    def populate(self):
        ip_path = self.module.get_bin_path('ip')
        if ip_path is None:
            return self.facts
        default_ipv4, default_ipv6 = self.get_default_interfaces(ip_path)
        interfaces, ips = self.get_interfaces_info(ip_path, default_ipv4, default_ipv6)
        self.facts['interfaces'] = interfaces.keys()
        for iface in interfaces:
            self.facts[iface] = interfaces[iface]
        self.facts['default_ipv4'] = default_ipv4
        self.facts['default_ipv6'] = default_ipv6
        self.facts['all_ipv4_addresses'] = ips['all_ipv4_addresses']
        self.facts['all_ipv6_addresses'] = ips['all_ipv6_addresses']
        return self.facts

    def get_default_interfaces(self, ip_path):
        # Use the commands:
        #     ip -4 route get 8.8.8.8                     -> Google public DNS
        #     ip -6 route get 2404:6800:400a:800::1012    -> ipv6.google.com
        # to find out the default outgoing interface, address, and gateway
        command = dict(
            v4 = [ip_path, '-4', 'route', 'get', '8.8.8.8'],
            v6 = [ip_path, '-6', 'route', 'get', '2404:6800:400a:800::1012']
        )
        interface = dict(v4 = {}, v6 = {})
        for v in 'v4', 'v6':
            if v == 'v6' and self.facts['os_family'] == 'RedHat' \
                and self.facts['distribution_version'].startswith('4.'):
                continue
            if v == 'v6' and not socket.has_ipv6:
                continue
            rc, out, err = self.module.run_command(command[v], errors='surrogate_then_replace')
            if not out:
                # v6 routing may result in
                #   RTNETLINK answers: Invalid argument
                continue
            words = out.splitlines()[0].split()
            # A valid output starts with the queried address on the first line
            if len(words) > 0 and words[0] == command[v][-1]:
                for i in range(len(words) - 1):
                    if words[i] == 'dev':
                        interface[v]['interface'] = words[i+1]
                    elif words[i] == 'src':
                        interface[v]['address'] = words[i+1]
                    elif words[i] == 'via' and words[i+1] != command[v][-1]:
                        interface[v]['gateway'] = words[i+1]
        return interface['v4'], interface['v6']

    def get_interfaces_info(self, ip_path, default_ipv4, default_ipv6):
        interfaces = {}
        ips = dict(
            all_ipv4_addresses = [],
            all_ipv6_addresses = [],
        )

        for path in glob.glob('/sys/class/net/*'):
            if not os.path.isdir(path):
                continue
            device = os.path.basename(path)
            interfaces[device] = { 'device': device }
            if os.path.exists(os.path.join(path, 'address')):
                macaddress = get_file_content(os.path.join(path, 'address'), default='')
                if macaddress and macaddress != '00:00:00:00:00:00':
                    interfaces[device]['macaddress'] = macaddress
            if os.path.exists(os.path.join(path, 'mtu')):
                interfaces[device]['mtu'] = int(get_file_content(os.path.join(path, 'mtu')))
            if os.path.exists(os.path.join(path, 'operstate')):
                interfaces[device]['active'] = get_file_content(os.path.join(path, 'operstate')) != 'down'
            if os.path.exists(os.path.join(path, 'device','driver', 'module')):
                interfaces[device]['module'] = os.path.basename(os.path.realpath(os.path.join(path, 'device', 'driver', 'module')))
            if os.path.exists(os.path.join(path, 'type')):
                _type = get_file_content(os.path.join(path, 'type'))
                interfaces[device]['type'] = self.INTERFACE_TYPE.get(_type, 'unknown')
            if os.path.exists(os.path.join(path, 'bridge')):
                interfaces[device]['type'] = 'bridge'
                interfaces[device]['interfaces'] = [ os.path.basename(b) for b in glob.glob(os.path.join(path, 'brif', '*')) ]
                if os.path.exists(os.path.join(path, 'bridge', 'bridge_id')):
                    interfaces[device]['id'] = get_file_content(os.path.join(path, 'bridge', 'bridge_id'), default='')
                if os.path.exists(os.path.join(path, 'bridge', 'stp_state')):
                    interfaces[device]['stp'] = get_file_content(os.path.join(path, 'bridge', 'stp_state')) == '1'
            if os.path.exists(os.path.join(path, 'bonding')):
                interfaces[device]['type'] = 'bonding'
                interfaces[device]['slaves'] = get_file_content(os.path.join(path, 'bonding', 'slaves'), default='').split()
                interfaces[device]['mode'] = get_file_content(os.path.join(path, 'bonding', 'mode'), default='').split()[0]
                interfaces[device]['miimon'] = get_file_content(os.path.join(path, 'bonding', 'miimon'), default='').split()[0]
                interfaces[device]['lacp_rate'] = get_file_content(os.path.join(path, 'bonding', 'lacp_rate'), default='').split()[0]
                primary = get_file_content(os.path.join(path, 'bonding', 'primary'))
                if primary:
                    interfaces[device]['primary'] = primary
                    path = os.path.join(path, 'bonding', 'all_slaves_active')
                    if os.path.exists(path):
                        interfaces[device]['all_slaves_active'] = get_file_content(path) == '1'
            if os.path.exists(os.path.join(path,'device')):
                interfaces[device]['pciid'] = os.path.basename(os.readlink(os.path.join(path,'device')))
            if os.path.exists(os.path.join(path, 'speed')):
                speed = get_file_content(os.path.join(path, 'speed'))
                if speed is not None:
                    interfaces[device]['speed'] = int(speed)

            # Check whether an interface is in promiscuous mode
            if os.path.exists(os.path.join(path,'flags')):
                promisc_mode = False
                # The second byte indicates whether the interface is in promiscuous mode.
                # 1 = promisc
                # 0 = no promisc
                data = int(get_file_content(os.path.join(path, 'flags')),16)
                promisc_mode = (data & 0x0100 > 0)
                interfaces[device]['promisc'] = promisc_mode

            def parse_ip_output(output, secondary=False):
                for line in output.splitlines():
                    if not line:
                        continue
                    words = line.split()
                    broadcast = ''
                    if words[0] == 'inet':
                        if '/' in words[1]:
                            address, netmask_length = words[1].split('/')
                            if len(words) > 3:
                                broadcast = words[3]
                        else:
                            # pointopoint interfaces do not have a prefix
                            address = words[1]
                            netmask_length = "32"
                        address_bin = struct.unpack('!L', socket.inet_aton(address))[0]
                        netmask_bin = (1<<32) - (1<<32>>int(netmask_length))
                        netmask = socket.inet_ntoa(struct.pack('!L', netmask_bin))
                        network = socket.inet_ntoa(struct.pack('!L', address_bin & netmask_bin))
                        iface = words[-1]
                        if iface != device:
                            interfaces[iface] = {}
                        if not secondary and "ipv4" not in interfaces[iface]:
                            interfaces[iface]['ipv4'] = {'address': address,
                                                         'broadcast': broadcast,
                                                         'netmask': netmask,
                                                         'network': network}
                        else:
                            if "ipv4_secondaries" not in interfaces[iface]:
                                interfaces[iface]["ipv4_secondaries"] = []
                            interfaces[iface]["ipv4_secondaries"].append({
                                'address': address,
                                'broadcast': broadcast,
                                'netmask': netmask,
                                'network': network,
                            })

                        # add this secondary IP to the main device
                        if secondary:
                            if "ipv4_secondaries" not in interfaces[device]:
                                interfaces[device]["ipv4_secondaries"] = []
                            interfaces[device]["ipv4_secondaries"].append({
                                'address': address,
                                'broadcast': broadcast,
                                'netmask': netmask,
                                'network': network,
                            })

                        # If this is the default address, update default_ipv4
                        if 'address' in default_ipv4 and default_ipv4['address'] == address:
                            default_ipv4['broadcast'] = broadcast
                            default_ipv4['netmask'] = netmask
                            default_ipv4['network'] = network
                            default_ipv4['macaddress'] = macaddress
                            default_ipv4['mtu'] = interfaces[device]['mtu']
                            default_ipv4['type'] = interfaces[device].get("type", "unknown")
                            default_ipv4['alias'] = words[-1]
                        if not address.startswith('127.'):
                            ips['all_ipv4_addresses'].append(address)
                    elif words[0] == 'inet6':
                        if 'peer' == words[2]:
                            address = words[1]
                            _, prefix = words[3].split('/')
                            scope = words[5]
                        else:
                            address, prefix = words[1].split('/')
                            scope = words[3]
                        if 'ipv6' not in interfaces[device]:
                            interfaces[device]['ipv6'] = []
                        interfaces[device]['ipv6'].append({
                            'address' : address,
                            'prefix'  : prefix,
                            'scope'   : scope
                        })
                        # If this is the default address, update default_ipv6
                        if 'address' in default_ipv6 and default_ipv6['address'] == address:
                            default_ipv6['prefix']     = prefix
                            default_ipv6['scope']      = scope
                            default_ipv6['macaddress'] = macaddress
                            default_ipv6['mtu']        = interfaces[device]['mtu']
                            default_ipv6['type']       = interfaces[device].get("type", "unknown")
                        if not address == '::1':
                            ips['all_ipv6_addresses'].append(address)

            ip_path = self.module.get_bin_path("ip")

            args = [ip_path, 'addr', 'show', 'primary', device]
            rc, primary_data, stderr = self.module.run_command(args, errors='surrogate_then_replace')

            args = [ip_path, 'addr', 'show', 'secondary', device]
            rc, secondary_data, stderr = self.module.run_command(args, errors='surrogate_then_replace')

            parse_ip_output(primary_data)
            parse_ip_output(secondary_data, secondary=True)

            interfaces[device]['features'] = self.get_ethtool_data(device)

        # replace : by _ in interface name since they are hard to use in template
        new_interfaces = {}
        for i in interfaces:
            if ':' in i:
                new_interfaces[i.replace(':','_')] = interfaces[i]
            else:
                new_interfaces[i] = interfaces[i]
        return new_interfaces, ips

    def get_ethtool_data(self, device):

        features = {}
        ethtool_path = self.module.get_bin_path("ethtool")
        if ethtool_path:
            args = [ethtool_path, '-k', device]
            rc, stdout, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                for line in stdout.strip().splitlines():
                    if not line or line.endswith(":"):
                        continue
                    key,value = line.split(": ")
                    if not value:
                        continue
                    features[key.strip().replace('-','_')] = value.strip()
        return features


class GenericBsdIfconfigNetwork(Network):
    """
    This is a generic BSD subclass of Network using the ifconfig command.
    It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    """
    platform = 'Generic_BSD_Ifconfig'

    def populate(self):

        ifconfig_path = self.module.get_bin_path('ifconfig')

        if ifconfig_path is None:
            return self.facts
        route_path = self.module.get_bin_path('route')

        if route_path is None:
            return self.facts

        default_ipv4, default_ipv6 = self.get_default_interfaces(route_path)
        interfaces, ips = self.get_interfaces_info(ifconfig_path)
        self.detect_type_media(interfaces)
        self.merge_default_interface(default_ipv4, interfaces, 'ipv4')
        self.merge_default_interface(default_ipv6, interfaces, 'ipv6')
        self.facts['interfaces'] = interfaces.keys()

        for iface in interfaces:
            self.facts[iface] = interfaces[iface]

        self.facts['default_ipv4'] = default_ipv4
        self.facts['default_ipv6'] = default_ipv6
        self.facts['all_ipv4_addresses'] = ips['all_ipv4_addresses']
        self.facts['all_ipv6_addresses'] = ips['all_ipv6_addresses']

        return self.facts

    def detect_type_media(self, interfaces):
        for iface in interfaces:
            if 'media' in interfaces[iface]:
                if 'ether' in interfaces[iface]['media'].lower():
                    interfaces[iface]['type'] = 'ether'

    def get_default_interfaces(self, route_path):

        # Use the commands:
        #     route -n get 8.8.8.8                            -> Google public DNS
        #     route -n get -inet6 2404:6800:400a:800::1012    -> ipv6.google.com
        # to find out the default outgoing interface, address, and gateway

        command = dict(
            v4 = [route_path, '-n', 'get', '8.8.8.8'],
            v6 = [route_path, '-n', 'get', '-inet6', '2404:6800:400a:800::1012']
        )

        interface = dict(v4 = {}, v6 = {})

        for v in 'v4', 'v6':

            if v == 'v6' and not socket.has_ipv6:
                continue
            rc, out, err = self.module.run_command(command[v])
            if not out:
                # v6 routing may result in
                #   RTNETLINK answers: Invalid argument
                continue
            for line in out.splitlines():
                words = line.split()
                # Collect output from route command
                if len(words) > 1:
                    if words[0] == 'interface:':
                        interface[v]['interface'] = words[1]
                    if words[0] == 'gateway:':
                        interface[v]['gateway'] = words[1]

        return interface['v4'], interface['v6']

    def get_interfaces_info(self, ifconfig_path, ifconfig_options='-a'):
        interfaces = {}
        current_if = {}
        ips = dict(
            all_ipv4_addresses = [],
            all_ipv6_addresses = [],
        )
        # FreeBSD, DragonflyBSD, NetBSD, OpenBSD and OS X all implicitly add '-a'
        # when running the command 'ifconfig'.
        # Solaris must explicitly run the command 'ifconfig -a'.
        rc, out, err = self.module.run_command([ifconfig_path, ifconfig_options])

        for line in out.splitlines():

            if line:
                words = line.split()

                if words[0] == 'pass':
                    continue
                elif re.match('^\S', line) and len(words) > 3:
                    current_if = self.parse_interface_line(words)
                    interfaces[ current_if['device'] ] = current_if
                elif words[0].startswith('options='):
                    self.parse_options_line(words, current_if, ips)
                elif words[0] == 'nd6':
                    self.parse_nd6_line(words, current_if, ips)
                elif words[0] == 'ether':
                    self.parse_ether_line(words, current_if, ips)
                elif words[0] == 'media:':
                    self.parse_media_line(words, current_if, ips)
                elif words[0] == 'status:':
                    self.parse_status_line(words, current_if, ips)
                elif words[0] == 'lladdr':
                    self.parse_lladdr_line(words, current_if, ips)
                elif words[0] == 'inet':
                    self.parse_inet_line(words, current_if, ips)
                elif words[0] == 'inet6':
                    self.parse_inet6_line(words, current_if, ips)
                elif words[0] == 'tunnel':
                    self.parse_tunnel_line(words, current_if, ips)
                else:
                    self.parse_unknown_line(words, current_if, ips)

        return interfaces, ips

    def parse_interface_line(self, words):
        device = words[0][0:-1]
        current_if = {'device': device, 'ipv4': [], 'ipv6': [], 'type': 'unknown'}
        current_if['flags']  = self.get_options(words[1])
        if 'LOOPBACK' in current_if['flags']:
            current_if['type'] = 'loopback'
        current_if['macaddress'] = 'unknown'    # will be overwritten later

        if len(words) >= 5 :  # Newer FreeBSD versions
            current_if['metric'] = words[3]
            current_if['mtu'] = words[5]
        else:
            current_if['mtu'] = words[3]

        return current_if

    def parse_options_line(self, words, current_if, ips):
        # Mac has options like this...
        current_if['options'] = self.get_options(words[0])

    def parse_nd6_line(self, words, current_if, ips):
        # FreeBSD has options like this...
        current_if['options'] = self.get_options(words[1])

    def parse_ether_line(self, words, current_if, ips):
        current_if['macaddress'] = words[1]
        current_if['type'] = 'ether'

    def parse_media_line(self, words, current_if, ips):
        # not sure if this is useful - we also drop information
        current_if['media'] = words[1]
        if len(words) > 2:
            current_if['media_select'] = words[2]
        if len(words) > 3:
            current_if['media_type'] = words[3][1:]
        if len(words) > 4:
            current_if['media_options'] = self.get_options(words[4])

    def parse_status_line(self, words, current_if, ips):
        current_if['status'] = words[1]

    def parse_lladdr_line(self, words, current_if, ips):
        current_if['lladdr'] = words[1]

    def parse_inet_line(self, words, current_if, ips):
        # netbsd show aliases like this
        #  lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 33184
        #         inet 127.0.0.1 netmask 0xff000000
        #         inet alias 127.1.1.1 netmask 0xff000000
        if words[1] == 'alias':
            del words[1]
        address = {'address': words[1]}
        # deal with hex netmask
        if re.match('([0-9a-f]){8}', words[3]) and len(words[3]) == 8:
            words[3] = '0x' + words[3]
        if words[3].startswith('0x'):
            address['netmask'] = socket.inet_ntoa(struct.pack('!L', int(words[3], base=16)))
        else:
            # otherwise assume this is a dotted quad
            address['netmask'] = words[3]
        # calculate the network
        address_bin = struct.unpack('!L', socket.inet_aton(address['address']))[0]
        netmask_bin = struct.unpack('!L', socket.inet_aton(address['netmask']))[0]
        address['network'] = socket.inet_ntoa(struct.pack('!L', address_bin & netmask_bin))
        # broadcast may be given or we need to calculate
        if len(words) > 5:
            address['broadcast'] = words[5]
        else:
            address['broadcast'] = socket.inet_ntoa(struct.pack('!L', address_bin | (~netmask_bin & 0xffffffff)))
        # add to our list of addresses
        if not words[1].startswith('127.'):
            ips['all_ipv4_addresses'].append(address['address'])
        current_if['ipv4'].append(address)

    def parse_inet6_line(self, words, current_if, ips):
        address = {'address': words[1]}
        if (len(words) >= 4) and (words[2] == 'prefixlen'):
            address['prefix'] = words[3]
        if (len(words) >= 6) and (words[4] == 'scopeid'):
            address['scope'] = words[5]
        localhost6 = ['::1', '::1/128', 'fe80::1%lo0']
        if address['address'] not in localhost6:
            ips['all_ipv6_addresses'].append(address['address'])
        current_if['ipv6'].append(address)

    def parse_tunnel_line(self, words, current_if, ips):
        current_if['type'] = 'tunnel'

    def parse_unknown_line(self, words, current_if, ips):
        # we are going to ignore unknown lines here - this may be
        # a bad idea - but you can override it in your subclass
        pass

    def get_options(self, option_string):
        start = option_string.find('<') + 1
        end = option_string.rfind('>')
        if (start > 0) and (end > 0) and (end > start + 1):
            option_csv = option_string[start:end]
            return option_csv.split(',')
        else:
            return []

    def merge_default_interface(self, defaults, interfaces, ip_type):
        if 'interface' not in defaults:
            return
        if not defaults['interface'] in interfaces:
            return
        ifinfo = interfaces[defaults['interface']]
        # copy all the interface values across except addresses
        for item in ifinfo:
            if item != 'ipv4' and item != 'ipv6':
                defaults[item] = ifinfo[item]
        if len(ifinfo[ip_type]) > 0:
            for item in ifinfo[ip_type][0]:
                defaults[item] = ifinfo[ip_type][0][item]


class HPUXNetwork(Network):
    """
    HP-UX-specifig subclass of Network. Defines networking facts:
    - default_interface
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4 address information.
    """
    platform = 'HP-UX'

    def populate(self):
        netstat_path = self.module.get_bin_path('netstat')
        if netstat_path is None:
            return self.facts
        self.get_default_interfaces()
        interfaces = self.get_interfaces_info()
        self.facts['interfaces'] = interfaces.keys()
        for iface in interfaces:
            self.facts[iface] = interfaces[iface]
        return self.facts

    def get_default_interfaces(self):
        rc, out, err = self.module.run_command("/usr/bin/netstat -nr")
        lines = out.splitlines()
        for line in lines:
            words = line.split()
            if len(words) > 1:
                if words[0] == 'default':
                    self.facts['default_interface'] = words[4]
                    self.facts['default_gateway'] = words[1]

    def get_interfaces_info(self):
        interfaces = {}
        rc, out, err = self.module.run_command("/usr/bin/netstat -ni")
        lines = out.splitlines()
        for line in lines:
            words = line.split()
            for i in range(len(words) - 1):
                if words[i][:3] == 'lan':
                    device = words[i]
                    interfaces[device] = { 'device': device }
                    address = words[i+3]
                    interfaces[device]['ipv4'] = { 'address': address }
                    network = words[i+2]
                    interfaces[device]['ipv4'] = { 'network': network,
                                                   'interface': device,
                                                   'address': address }
        return interfaces

class DarwinNetwork(GenericBsdIfconfigNetwork):
    """
    This is the Mac OS X/Darwin Network Class.
    It uses the GenericBsdIfconfigNetwork unchanged
    """
    platform = 'Darwin'

    # media line is different to the default FreeBSD one
    def parse_media_line(self, words, current_if, ips):
        # not sure if this is useful - we also drop information
        current_if['media'] = 'Unknown' # Mac does not give us this
        current_if['media_select'] = words[1]
        if len(words) > 2:
            # MacOSX sets the media to '<unknown type>' for bridge interface
            # and parsing splits this into two words; this if/else helps
            if words[1] == '<unknown' and words[2] == 'type>':
                current_if['media_select'] = 'Unknown'
                current_if['media_type'] = 'unknown type'
            else:
                current_if['media_type'] = words[2][1:-1]
        if len(words) > 3:
            current_if['media_options'] = self.get_options(words[3])


class FreeBSDNetwork(GenericBsdIfconfigNetwork):
    """
    This is the FreeBSD Network Class.
    It uses the GenericBsdIfconfigNetwork unchanged.
    """
    platform = 'FreeBSD'


class DragonFlyNetwork(GenericBsdIfconfigNetwork):
    """
    This is the DragonFly Network Class.
    It uses the GenericBsdIfconfigNetwork unchanged.
    """
    platform = 'DragonFly'


class AIXNetwork(GenericBsdIfconfigNetwork):
    """
    This is the AIX Network Class.
    It uses the GenericBsdIfconfigNetwork unchanged.
    """
    platform = 'AIX'

    def get_default_interfaces(self, route_path):
        netstat_path = self.module.get_bin_path('netstat')

        rc, out, err = self.module.run_command([netstat_path, '-nr'])

        interface = dict(v4 = {}, v6 = {})

        lines = out.splitlines()
        for line in lines:
            words = line.split()
            if len(words) > 1 and words[0] == 'default':
                if '.' in words[1]:
                    interface['v4']['gateway'] = words[1]
                    interface['v4']['interface'] = words[5]
                elif ':' in words[1]:
                    interface['v6']['gateway'] = words[1]
                    interface['v6']['interface'] = words[5]

        return interface['v4'], interface['v6']

    # AIX 'ifconfig -a' does not have three words in the interface line
    def get_interfaces_info(self, ifconfig_path, ifconfig_options='-a'):
        interfaces = {}
        current_if = {}
        ips = dict(
            all_ipv4_addresses = [],
            all_ipv6_addresses = [],
        )

        uname_rc = None
        uname_out = None
        uname_err = None
        uname_path = self.module.get_bin_path('uname')
        if uname_path:
            uname_rc, uname_out, uname_err = self.module.run_command([uname_path, '-W'])

        rc, out, err = self.module.run_command([ifconfig_path, ifconfig_options])

        for line in out.splitlines():

            if line:
                words = line.split()

                # only this condition differs from GenericBsdIfconfigNetwork
                if re.match('^\w*\d*:', line):
                    current_if = self.parse_interface_line(words)
                    interfaces[ current_if['device'] ] = current_if
                elif words[0].startswith('options='):
                    self.parse_options_line(words, current_if, ips)
                elif words[0] == 'nd6':
                    self.parse_nd6_line(words, current_if, ips)
                elif words[0] == 'ether':
                    self.parse_ether_line(words, current_if, ips)
                elif words[0] == 'media:':
                    self.parse_media_line(words, current_if, ips)
                elif words[0] == 'status:':
                    self.parse_status_line(words, current_if, ips)
                elif words[0] == 'lladdr':
                    self.parse_lladdr_line(words, current_if, ips)
                elif words[0] == 'inet':
                    self.parse_inet_line(words, current_if, ips)
                elif words[0] == 'inet6':
                    self.parse_inet6_line(words, current_if, ips)
                else:
                    self.parse_unknown_line(words, current_if, ips)

            # don't bother with wpars it does not work
            # zero means not in wpar
            if not uname_rc and uname_out.split()[0] == '0':

                if current_if['macaddress'] == 'unknown' and re.match('^en', current_if['device']):
                    entstat_path = self.module.get_bin_path('entstat')
                    if entstat_path:
                        rc, out, err = self.module.run_command([entstat_path, current_if['device'] ])
                        if rc != 0:
                            break
                        for line in out.splitlines():
                            if not line:
                                pass
                            buff = re.match('^Hardware Address: (.*)', line)
                            if buff:
                                current_if['macaddress'] = buff.group(1)

                            buff = re.match('^Device Type:', line)
                            if buff and re.match('.*Ethernet', line):
                                current_if['type'] = 'ether'

                # device must have mtu attribute in ODM
                if 'mtu' not in current_if:
                    lsattr_path = self.module.get_bin_path('lsattr')
                    if lsattr_path:
                        rc, out, err = self.module.run_command([lsattr_path,'-El', current_if['device'] ])
                        if rc != 0:
                            break
                        for line in out.splitlines():
                            if line:
                                words = line.split()
                                if words[0] == 'mtu':
                                    current_if['mtu'] = words[1]
        return interfaces, ips

    # AIX 'ifconfig -a' does not inform about MTU, so remove current_if['mtu'] here
    def parse_interface_line(self, words):
        device = words[0][0:-1]
        current_if = {'device': device, 'ipv4': [], 'ipv6': [], 'type': 'unknown'}
        current_if['flags'] = self.get_options(words[1])
        current_if['macaddress'] = 'unknown'    # will be overwritten later
        return current_if

class OpenBSDNetwork(GenericBsdIfconfigNetwork):
    """
    This is the OpenBSD Network Class.
    It uses the GenericBsdIfconfigNetwork.
    """
    platform = 'OpenBSD'

    # OpenBSD 'ifconfig -a' does not have information about aliases
    def get_interfaces_info(self, ifconfig_path, ifconfig_options='-aA'):
        return super(OpenBSDNetwork, self).get_interfaces_info(ifconfig_path, ifconfig_options)

    # Return macaddress instead of lladdr
    def parse_lladdr_line(self, words, current_if, ips):
        current_if['macaddress'] = words[1]
        current_if['type'] = 'ether'

class NetBSDNetwork(GenericBsdIfconfigNetwork):
    """
    This is the NetBSD Network Class.
    It uses the GenericBsdIfconfigNetwork
    """
    platform = 'NetBSD'

    def parse_media_line(self, words, current_if, ips):
        # example of line:
        # $ ifconfig
        # ne0: flags=8863<UP,BROADCAST,NOTRAILERS,RUNNING,SIMPLEX,MULTICAST> mtu 1500
        #    ec_capabilities=1<VLAN_MTU>
        #    ec_enabled=0
        #    address: 00:20:91:45:00:78
        #    media: Ethernet 10baseT full-duplex
        #    inet 192.168.156.29 netmask 0xffffff00 broadcast 192.168.156.255
        current_if['media'] = words[1]
        if len(words) > 2:
            current_if['media_type'] = words[2]
        if len(words) > 3:
            current_if['media_options'] = words[3].split(',')


class SunOSNetwork(GenericBsdIfconfigNetwork):
    """
    This is the SunOS Network Class.
    It uses the GenericBsdIfconfigNetwork.

    Solaris can have different FLAGS and MTU for IPv4 and IPv6 on the same interface
    so these facts have been moved inside the 'ipv4' and 'ipv6' lists.
    """
    platform = 'SunOS'

    # Solaris 'ifconfig -a' will print interfaces twice, once for IPv4 and again for IPv6.
    # MTU and FLAGS also may differ between IPv4 and IPv6 on the same interface.
    # 'parse_interface_line()' checks for previously seen interfaces before defining
    # 'current_if' so that IPv6 facts don't clobber IPv4 facts (or vice versa).
    def get_interfaces_info(self, ifconfig_path):
        interfaces = {}
        current_if = {}
        ips = dict(
            all_ipv4_addresses = [],
            all_ipv6_addresses = [],
        )
        rc, out, err = self.module.run_command([ifconfig_path, '-a'])

        for line in out.splitlines():

            if line:
                words = line.split()

                if re.match('^\S', line) and len(words) > 3:
                    current_if = self.parse_interface_line(words, current_if, interfaces)
                    interfaces[ current_if['device'] ] = current_if
                elif words[0].startswith('options='):
                    self.parse_options_line(words, current_if, ips)
                elif words[0] == 'nd6':
                    self.parse_nd6_line(words, current_if, ips)
                elif words[0] == 'ether':
                    self.parse_ether_line(words, current_if, ips)
                elif words[0] == 'media:':
                    self.parse_media_line(words, current_if, ips)
                elif words[0] == 'status:':
                    self.parse_status_line(words, current_if, ips)
                elif words[0] == 'lladdr':
                    self.parse_lladdr_line(words, current_if, ips)
                elif words[0] == 'inet':
                    self.parse_inet_line(words, current_if, ips)
                elif words[0] == 'inet6':
                    self.parse_inet6_line(words, current_if, ips)
                else:
                    self.parse_unknown_line(words, current_if, ips)

        # 'parse_interface_line' and 'parse_inet*_line' leave two dicts in the
        # ipv4/ipv6 lists which is ugly and hard to read.
        # This quick hack merges the dictionaries. Purely cosmetic.
        for iface in interfaces:
            for v in 'ipv4', 'ipv6':
                combined_facts = {}
                for facts in interfaces[iface][v]:
                    combined_facts.update(facts)
                if len(combined_facts.keys()) > 0:
                    interfaces[iface][v] = [combined_facts]

        return interfaces, ips

    def parse_interface_line(self, words, current_if, interfaces):
        device = words[0][0:-1]
        if device not in interfaces:
            current_if = {'device': device, 'ipv4': [], 'ipv6': [], 'type': 'unknown'}
        else:
            current_if = interfaces[device]
        flags = self.get_options(words[1])
        v = 'ipv4'
        if 'IPv6' in flags:
            v = 'ipv6'
        if 'LOOPBACK' in flags:
            current_if['type'] = 'loopback'
        current_if[v].append({'flags': flags, 'mtu': words[3]})
        current_if['macaddress'] = 'unknown'    # will be overwritten later
        return current_if

    # Solaris displays single digit octets in MAC addresses e.g. 0:1:2:d:e:f
    # Add leading zero to each octet where needed.
    def parse_ether_line(self, words, current_if, ips):
        macaddress = ''
        for octet in words[1].split(':'):
            octet = ('0' + octet)[-2:None]
            macaddress += (octet + ':')
        current_if['macaddress'] = macaddress[0:-1]

class HurdPfinetNetwork(Network):
    """
    This is a GNU Hurd specific subclass of Network. It use fsysopts to
    get the ip address and support only pfinet.
    """
    platform = 'GNU'
    _socket_dir = '/servers/socket/'

    def populate(self):
        fsysopts_path = self.module.get_bin_path('fsysopts')
        if fsysopts_path is None:
            return self.facts
        socket_path = None
        for l in ('inet', 'inet6'):
            link = os.path.join(self._socket_dir, l)
            if os.path.exists(link):
                socket_path = link
                break

        if socket_path:
            rc, out, err = self.module.run_command([fsysopts_path, '-L', socket_path])
            self.facts['interfaces'] = []
            for i in out.split():
                if '=' in i and i.startswith('--'):
                    k,v = i.split('=',1)
                    # remove '--'
                    k = k[2:]
                    if k == 'interface':
                        # remove /dev/ from /dev/eth0
                        v = v[5:]
                        self.facts['interfaces'].append(v)
                        self.facts[v] = {
                            'active': True,
                            'device': v,
                            'ipv4': {},
                            'ipv6': [],
                        }
                        current_if = v
                    elif k == 'address':
                        self.facts[current_if]['ipv4']['address'] = v
                    elif k == 'netmask':
                        self.facts[current_if]['ipv4']['netmask'] = v
                    elif k == 'address6':
                        address,prefix = v.split('/')
                        self.facts[current_if]['ipv6'].append({
                            'address': address,
                            'prefix': prefix,
                        })

        return self.facts


class Virtual(Facts):
    """
    This is a generic Virtual subclass of Facts.  This should be further
    subclassed to implement per platform.  If you subclass this,
    you should define:
    - virtualization_type
    - virtualization_role
    - container (e.g. solaris zones, freebsd jails, linux containers)

    All subclasses MUST define platform.
    """

    def __new__(cls, *arguments, **keyword):
        # When Virtual is created, it chooses a subclass to create instead.
        # This check prevents the subclass from then trying to find a subclass
        # and create that.
        if cls is not Virtual:
            return super(Virtual, cls).__new__(cls)

        subclass = cls
        for sc in get_all_subclasses(Virtual):
            if sc.platform == platform.system():
                subclass = sc

        if PY3:
            return super(cls, subclass).__new__(subclass)
        else:
            return super(cls, subclass).__new__(subclass, *arguments, **keyword)

    def populate(self):
        self.get_virtual_facts()
        return self.facts

    def get_virtual_facts(self):
        self.facts['virtualization_type'] = ''
        self.facts['virtualization_role'] = ''

class LinuxVirtual(Virtual):
    """
    This is a Linux-specific subclass of Virtual.  It defines
    - virtualization_type
    - virtualization_role
    """
    platform = 'Linux'

    # For more information, check: http://people.redhat.com/~rjones/virt-what/
    def get_virtual_facts(self):
        # lxc/docker
        if os.path.exists('/proc/1/cgroup'):
            for line in get_file_lines('/proc/1/cgroup'):
                if re.search(r'/docker(/|-[0-9a-f]+\.scope)', line):
                    self.facts['virtualization_type'] = 'docker'
                    self.facts['virtualization_role'] = 'guest'
                    return
                if re.search('/lxc/', line) or re.search('/machine.slice/machine-lxc', line):
                    self.facts['virtualization_type'] = 'lxc'
                    self.facts['virtualization_role'] = 'guest'
                    return

        # lxc does not always appear in cgroups anymore but sets 'container=lxc' environment var, requires root privs
        if os.path.exists('/proc/1/environ'):
            for line in get_file_lines('/proc/1/environ'):
                if re.search('container=lxc', line):
                    self.facts['virtualization_type'] = 'lxc'
                    self.facts['virtualization_role'] = 'guest'
                    return

        if os.path.exists('/proc/vz'):
            self.facts['virtualization_type'] = 'openvz'
            if os.path.exists('/proc/bc'):
                self.facts['virtualization_role'] = 'host'
            else:
                self.facts['virtualization_role'] = 'guest'
            return

        systemd_container = get_file_content('/run/systemd/container')
        if systemd_container:
            self.facts['virtualization_type'] = systemd_container
            self.facts['virtualization_role'] = 'guest'
            return

        if os.path.exists("/proc/xen"):
            self.facts['virtualization_type'] = 'xen'
            self.facts['virtualization_role'] = 'guest'
            try:
                for line in get_file_lines('/proc/xen/capabilities'):
                    if "control_d" in line:
                        self.facts['virtualization_role'] = 'host'
            except IOError:
                pass
            return

        product_name = get_file_content('/sys/devices/virtual/dmi/id/product_name')

        if product_name in ['KVM', 'Bochs']:
            self.facts['virtualization_type'] = 'kvm'
            self.facts['virtualization_role'] = 'guest'
            return

        if product_name == 'RHEV Hypervisor':
            self.facts['virtualization_type'] = 'RHEV'
            self.facts['virtualization_role'] = 'guest'
            return

        if product_name == 'VMware Virtual Platform':
            self.facts['virtualization_type'] = 'VMware'
            self.facts['virtualization_role'] = 'guest'
            return

        if product_name == 'OpenStack Nova':
            self.facts['virtualization_type'] = 'openstack'
            self.facts['virtualization_role'] = 'guest'
            return

        bios_vendor = get_file_content('/sys/devices/virtual/dmi/id/bios_vendor')

        if bios_vendor == 'Xen':
            self.facts['virtualization_type'] = 'xen'
            self.facts['virtualization_role'] = 'guest'
            return

        if bios_vendor == 'innotek GmbH':
            self.facts['virtualization_type'] = 'virtualbox'
            self.facts['virtualization_role'] = 'guest'
            return

        sys_vendor = get_file_content('/sys/devices/virtual/dmi/id/sys_vendor')

        # FIXME: This does also match hyperv
        if sys_vendor == 'Microsoft Corporation':
            self.facts['virtualization_type'] = 'VirtualPC'
            self.facts['virtualization_role'] = 'guest'
            return

        if sys_vendor == 'Parallels Software International Inc.':
            self.facts['virtualization_type'] = 'parallels'
            self.facts['virtualization_role'] = 'guest'
            return

        if sys_vendor == 'QEMU':
            self.facts['virtualization_type'] = 'kvm'
            self.facts['virtualization_role'] = 'guest'
            return

        if sys_vendor == 'oVirt':
            self.facts['virtualization_type'] = 'kvm'
            self.facts['virtualization_role'] = 'guest'
            return

        if sys_vendor == 'OpenStack Foundation':
            self.facts['virtualization_type'] = 'openstack'
            self.facts['virtualization_role'] = 'guest'
            return

        if os.path.exists('/proc/self/status'):
            for line in get_file_lines('/proc/self/status'):
                if re.match('^VxID: \d+', line):
                    self.facts['virtualization_type'] = 'linux_vserver'
                    if re.match('^VxID: 0', line):
                        self.facts['virtualization_role'] = 'host'
                    else:
                        self.facts['virtualization_role'] = 'guest'
                    return

        if os.path.exists('/proc/cpuinfo'):
            for line in get_file_lines('/proc/cpuinfo'):
                if re.match('^model name.*QEMU Virtual CPU', line):
                    self.facts['virtualization_type'] = 'kvm'
                elif re.match('^vendor_id.*User Mode Linux', line):
                    self.facts['virtualization_type'] = 'uml'
                elif re.match('^model name.*UML', line):
                    self.facts['virtualization_type'] = 'uml'
                elif re.match('^vendor_id.*PowerVM Lx86', line):
                    self.facts['virtualization_type'] = 'powervm_lx86'
                elif re.match('^vendor_id.*IBM/S390', line):
                    self.facts['virtualization_type'] = 'PR/SM'
                    lscpu = self.module.get_bin_path('lscpu')
                    if lscpu:
                        rc, out, err = self.module.run_command(["lscpu"])
                        if rc == 0:
                            for line in out.splitlines():
                                data = line.split(":", 1)
                                key = data[0].strip()
                                if key == 'Hypervisor':
                                    self.facts['virtualization_type'] = data[1].strip()
                    else:
                        self.facts['virtualization_type'] = 'ibm_systemz'
                else:
                    continue
                if self.facts['virtualization_type'] == 'PR/SM':
                    self.facts['virtualization_role'] = 'LPAR'
                else:
                    self.facts['virtualization_role'] = 'guest'
                return

        # Beware that we can have both kvm and virtualbox running on a single system
        if os.path.exists("/proc/modules") and os.access('/proc/modules', os.R_OK):
            modules = []
            for line in get_file_lines("/proc/modules"):
                data = line.split(" ", 1)
                modules.append(data[0])

            if 'kvm' in modules:

                if os.path.isdir('/rhev/'):

                    # Check whether this is a RHEV hypervisor (is vdsm running ?)
                    for f in glob.glob('/proc/[0-9]*/comm'):
                        try:
                            if open(f).read().rstrip() == 'vdsm':
                                self.facts['virtualization_type'] = 'RHEV'
                                break
                        except:
                            pass
                    else:
                        self.facts['virtualization_type'] = 'kvm'

                else:
                    self.facts['virtualization_type'] = 'kvm'
                self.facts['virtualization_role'] = 'host'
                return

            if 'vboxdrv' in modules:
                self.facts['virtualization_type'] = 'virtualbox'
                self.facts['virtualization_role'] = 'host'
                return

        # If none of the above matches, return 'NA' for virtualization_type
        # and virtualization_role. This allows for proper grouping.
        self.facts['virtualization_type'] = 'NA'
        self.facts['virtualization_role'] = 'NA'
        return

class VirtualSysctlDetectionMixin(object):
    def detect_sysctl(self):
        self.sysctl_path = self.module.get_bin_path('sysctl')

    def detect_virt_product(self, key):
        self.detect_sysctl()
        if self.sysctl_path:
            rc, out, err = self.module.run_command("%s -n %s" % (self.sysctl_path, key))
            if rc == 0:
                if re.match('(KVM|Bochs|SmartDC).*', out):
                    self.facts['virtualization_type'] = 'kvm'
                    self.facts['virtualization_role'] = 'guest'
                elif re.match('.*VMware.*', out):
                    self.facts['virtualization_type'] = 'VMware'
                    self.facts['virtualization_role'] = 'guest'
                elif out.rstrip() == 'VirtualBox':
                    self.facts['virtualization_type'] = 'virtualbox'
                    self.facts['virtualization_role'] = 'guest'
                elif out.rstrip() == 'HVM domU':
                    self.facts['virtualization_type'] = 'xen'
                    self.facts['virtualization_role'] = 'guest'
                elif out.rstrip() == 'Parallels':
                    self.facts['virtualization_type'] = 'parallels'
                    self.facts['virtualization_role'] = 'guest'
                elif out.rstrip() == 'RHEV Hypervisor':
                    self.facts['virtualization_type'] = 'RHEV'
                    self.facts['virtualization_role'] = 'guest'

    def detect_virt_vendor(self, key):
        self.detect_sysctl()
        if self.sysctl_path:
            rc, out, err = self.module.run_command("%s -n %s" % (self.sysctl_path, key))
            if rc == 0:
                if out.rstrip() == 'QEMU':
                    self.facts['virtualization_type'] = 'kvm'
                    self.facts['virtualization_role'] = 'guest'
                if out.rstrip() == 'OpenBSD':
                    self.facts['virtualization_type'] = 'vmm'
                    self.facts['virtualization_role'] = 'guest'


class FreeBSDVirtual(Virtual):
    """
    This is a FreeBSD-specific subclass of Virtual.  It defines
    - virtualization_type
    - virtualization_role
    """
    platform = 'FreeBSD'

    def get_virtual_facts(self):

        # Set empty values as default
        self.facts['virtualization_type'] = ''
        self.facts['virtualization_role'] = ''

        if os.path.exists('/dev/xen/xenstore'):
            self.facts['virtualization_type'] = 'xen'
            self.facts['virtualization_role'] = 'guest'

class DragonFlyVirtual(FreeBSDVirtual):
    platform = 'DragonFly'

class OpenBSDVirtual(Virtual, VirtualSysctlDetectionMixin):
    """
    This is a OpenBSD-specific subclass of Virtual.  It defines
    - virtualization_type
    - virtualization_role
    """
    platform = 'OpenBSD'
    DMESG_BOOT = '/var/run/dmesg.boot'

    def get_virtual_facts(self):

        # Set empty values as default
        self.facts['virtualization_type'] = ''
        self.facts['virtualization_role'] = ''

        self.detect_virt_product('hw.product')
        if self.facts['virtualization_type'] == '':
            self.detect_virt_vendor('hw.vendor')

        # Check the dmesg if vmm(4) attached, indicating the host is
        # capable of virtualization.
        dmesg_boot = get_file_content(OpenBSDVirtual.DMESG_BOOT)
        for line in dmesg_boot.splitlines():
            match = re.match('^vmm0 at mainbus0: (SVM/RVI|VMX/EPT)$', line)
            if match:
                self.facts['virtualization_type'] = 'vmm'
                self.facts['virtualization_role'] = 'host'

class NetBSDVirtual(Virtual, VirtualSysctlDetectionMixin):
    platform = 'NetBSD'

    def get_virtual_facts(self):
        # Set empty values as default
        self.facts['virtualization_type'] = ''
        self.facts['virtualization_role'] = ''

        self.detect_virt_product('machdep.dmi.system-product')
        if self.facts['virtualization_type'] == '':
            self.detect_virt_vendor('machdep.dmi.system-vendor')

        if os.path.exists('/dev/xencons'):
            self.facts['virtualization_type'] = 'xen'
            self.facts['virtualization_role'] = 'guest'


class HPUXVirtual(Virtual):
    """
    This is a HP-UX specific subclass of Virtual. It defines
    - virtualization_type
    - virtualization_role
    """
    platform = 'HP-UX'

    def get_virtual_facts(self):
        if os.path.exists('/usr/sbin/vecheck'):
            rc, out, err = self.module.run_command("/usr/sbin/vecheck")
            if rc == 0:
                self.facts['virtualization_type'] = 'guest'
                self.facts['virtualization_role'] = 'HP vPar'
        if os.path.exists('/opt/hpvm/bin/hpvminfo'):
            rc, out, err = self.module.run_command("/opt/hpvm/bin/hpvminfo")
            if rc == 0 and re.match('.*Running.*HPVM vPar.*', out):
                self.facts['virtualization_type'] = 'guest'
                self.facts['virtualization_role'] = 'HPVM vPar'
            elif rc == 0 and re.match('.*Running.*HPVM guest.*', out):
                self.facts['virtualization_type'] = 'guest'
                self.facts['virtualization_role'] = 'HPVM IVM'
            elif rc == 0 and re.match('.*Running.*HPVM host.*', out):
                self.facts['virtualization_type'] = 'host'
                self.facts['virtualization_role'] = 'HPVM'
        if os.path.exists('/usr/sbin/parstatus'):
            rc, out, err = self.module.run_command("/usr/sbin/parstatus")
            if rc == 0:
                self.facts['virtualization_type'] = 'guest'
                self.facts['virtualization_role'] = 'HP nPar'


class SunOSVirtual(Virtual):
    """
    This is a SunOS-specific subclass of Virtual.  It defines
    - virtualization_type
    - virtualization_role
    - container
    """
    platform = 'SunOS'

    def get_virtual_facts(self):

        # Check if it's a zone

        zonename = self.module.get_bin_path('zonename')
        if zonename:
            rc, out, err = self.module.run_command(zonename)
            if rc == 0 and out.rstrip() != "global":
                self.facts['container'] = 'zone'
        # Check if it's a branded zone (i.e. Solaris 8/9 zone)
        if os.path.isdir('/.SUNWnative'):
            self.facts['container'] = 'zone'
        # If it's a zone check if we can detect if our global zone is itself virtualized.
        # Relies on the "guest tools" (e.g. vmware tools) to be installed
        if 'container' in self.facts and self.facts['container'] == 'zone':
            modinfo = self.module.get_bin_path('modinfo')
            if modinfo:
                rc, out, err = self.module.run_command(modinfo)
                if rc == 0:
                    for line in out.splitlines():
                        if 'VMware' in line:
                            self.facts['virtualization_type'] = 'vmware'
                            self.facts['virtualization_role'] = 'guest'
                        if 'VirtualBox' in line:
                            self.facts['virtualization_type'] = 'virtualbox'
                            self.facts['virtualization_role'] = 'guest'

        if os.path.exists('/proc/vz'):
            self.facts['virtualization_type'] = 'virtuozzo'
            self.facts['virtualization_role'] = 'guest'

        # Detect domaining on Sparc hardware
        virtinfo = self.module.get_bin_path('virtinfo')
        if virtinfo:
            # The output of virtinfo is different whether we are on a machine with logical
            # domains ('LDoms') on a T-series or domains ('Domains') on a M-series. Try LDoms first.
            rc, out, err = self.module.run_command("/usr/sbin/virtinfo -p")
            # The output contains multiple lines with different keys like this:
            #   DOMAINROLE|impl=LDoms|control=false|io=false|service=false|root=false
            # The output may also be not formatted and the returncode is set to 0 regardless of the error condition:
            #   virtinfo can only be run from the global zone
            if rc == 0:
                try:
                    for line in out.splitlines():
                        fields = line.split('|')
                        if( fields[0] == 'DOMAINROLE' and fields[1] == 'impl=LDoms' ):
                            self.facts['virtualization_type'] = 'ldom'
                            self.facts['virtualization_role'] = 'guest'
                            hostfeatures = []
                            for field in fields[2:]:
                                arg = field.split('=')
                                if( arg[1] == 'true' ):
                                    hostfeatures.append(arg[0])
                            if( len(hostfeatures) > 0 ):
                                self.facts['virtualization_role'] = 'host (' + ','.join(hostfeatures) + ')'
                except ValueError:
                    pass

        else:
            smbios = self.module.get_bin_path('smbios')
            if not smbios:
                return
            rc, out, err = self.module.run_command(smbios)
            if rc == 0:
                for line in out.splitlines():
                    if 'VMware' in line:
                        self.facts['virtualization_type'] = 'vmware'
                        self.facts['virtualization_role'] = 'guest'
                    elif 'Parallels' in line:
                        self.facts['virtualization_type'] = 'parallels'
                        self.facts['virtualization_role'] = 'guest'
                    elif 'VirtualBox' in line:
                        self.facts['virtualization_type'] = 'virtualbox'
                        self.facts['virtualization_role'] = 'guest'
                    elif 'HVM domU' in line:
                        self.facts['virtualization_type'] = 'xen'
                        self.facts['virtualization_role'] = 'guest'
                    elif 'KVM' in line:
                        self.facts['virtualization_type'] = 'kvm'
                        self.facts['virtualization_role'] = 'guest'

class Ohai(Facts):
    """
    This is a subclass of Facts for including information gathered from Ohai.
    """

    def populate(self):
        self.run_ohai()
        return self.facts

    def run_ohai(self):
        ohai_path = self.module.get_bin_path('ohai')
        if ohai_path is None:
            return
        rc, out, err = self.module.run_command(ohai_path)
        try:
            self.facts.update(json.loads(out))
        except:
            pass

class Facter(Facts):
    """
    This is a subclass of Facts for including information gathered from Facter.
    """
    def populate(self):
        self.run_facter()
        return self.facts

    def run_facter(self):
        facter_path = self.module.get_bin_path('facter', opt_dirs=['/opt/puppetlabs/bin'])
        cfacter_path = self.module.get_bin_path('cfacter', opt_dirs=['/opt/puppetlabs/bin'])
        # Prefer to use cfacter if available
        if cfacter_path is not None:
            facter_path = cfacter_path

        if facter_path is None:
            return

        # if facter is installed, and we can use --json because
        # ruby-json is ALSO installed, include facter data in the JSON
        rc, out, err = self.module.run_command(facter_path + " --puppet --json")
        try:
            self.facts = json.loads(out)
        except:
            pass


def get_file_content(path, default=None, strip=True):
    data = default
    if os.path.exists(path) and os.access(path, os.R_OK):
        try:
            try:
                datafile = open(path)
                data = datafile.read()
                if strip:
                    data = data.strip()
                if len(data) == 0:
                    data = default
            finally:
                datafile.close()
        except:
            # ignore errors as some jails/containers might have readable permissions but not allow reads to proc
            # done in 2 blocks for 2.4 compat
            pass
    return data

def get_uname_version(module):
    rc, out, err = module.run_command(['uname', '-v'])
    if rc == 0:
        return out
    return None

def get_partition_uuid(partname):
    try:
        uuids = os.listdir("/dev/disk/by-uuid")
    except OSError:
        return

    for uuid in uuids:
        dev = os.path.realpath("/dev/disk/by-uuid/" + uuid)
        if dev == ("/dev/" + partname):
            return uuid

    return None

def get_file_lines(path):
    '''get list of lines from file'''
    data = get_file_content(path)
    if data:
        ret = data.splitlines()
    else:
        ret = []
    return ret

def ansible_facts(module, gather_subset):
    facts = {}
    facts['gather_subset'] = list(gather_subset)
    facts.update(Facts(module).populate())
    for subset in gather_subset:
        facts.update(FACT_SUBSETS[subset](module,
                                         load_on_init=False,
                                         cached_facts=facts).populate())
    return facts

def get_all_facts(module):

    setup_options = dict(module_setup=True)

    # Retrieve module parameters
    gather_subset = module.params['gather_subset']

    global GATHER_TIMEOUT
    GATHER_TIMEOUT = module.params['gather_timeout']

    # Retrieve all facts elements
    additional_subsets = set()
    exclude_subsets = set()
    for subset in gather_subset:
        if subset == 'all':
            additional_subsets.update(VALID_SUBSETS)
            continue
        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            raise TypeError("Bad subset '%s' given to Ansible. gather_subset options allowed: all, %s" % (subset, ", ".join(FACT_SUBSETS.keys())))

        if exclude:
            exclude_subsets.add(subset)
        else:
            additional_subsets.add(subset)

    if not additional_subsets:
        additional_subsets.update(VALID_SUBSETS)

    additional_subsets.difference_update(exclude_subsets)

    # facter and ohai are given a different prefix than other subsets
    if 'facter' in additional_subsets:
        additional_subsets.difference_update(('facter',))
        facter_ds = FACT_SUBSETS['facter'](module, load_on_init=False).populate()
        if facter_ds:
            for (k, v) in facter_ds.items():
                setup_options['facter_%s' % k.replace('-', '_')] = v

    if 'ohai' in additional_subsets:
        additional_subsets.difference_update(('ohai',))
        ohai_ds = FACT_SUBSETS['ohai'](module, load_on_init=False).populate()
        if ohai_ds:
            for (k, v) in ohai_ds.items():
                setup_options['ohai_%s' % k.replace('-', '_')] = v

    facts = ansible_facts(module, additional_subsets)

    for (k, v) in facts.items():
        setup_options["ansible_%s" % k.replace('-', '_')] = v

    setup_result = { 'ansible_facts': {} }

    for (k,v) in setup_options.items():
        if module.params['filter'] == '*' or fnmatch.fnmatch(k, module.params['filter']):
            setup_result['ansible_facts'][k] = v

    return setup_result

# Allowed fact subset for gather_subset options and what classes they use
# Note: have to define this at the bottom as it references classes defined earlier in this file
FACT_SUBSETS = dict(
    hardware=Hardware,
    network=Network,
    virtual=Virtual,
    ohai=Ohai,
    facter=Facter,
)
VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())
