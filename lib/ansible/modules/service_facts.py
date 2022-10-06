# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# originally copied from AWX's scan_services module to bring this functionality
# into Core

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: service_facts
short_description: Return service state information as fact data
description:
     - Return service state information as fact data for various service management utilities.
version_added: "2.5"
requirements: ["Any of the following supported init systems: systemd, sysv, upstart, openrc, AIX SRC"]
extends_documentation_fragment:
  -  action_common_attributes
  -  action_common_attributes.facts
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    facts:
        support: full
    platform:
        platforms: posix
notes:
  - When accessing the C(ansible_facts.services) facts collected by this module,
    it is recommended to not use "dot notation" because services can have a C(-)
    character in their name which would result in invalid "dot notation", such as
    C(ansible_facts.services.zuul-gateway). It is instead recommended to
    using the string value of the service name as the key in order to obtain
    the fact data value like C(ansible_facts.services['zuul-gateway'])
  - AIX SRC was added in version 2.11.
author:
  - Adam Miller (@maxamillion)
'''

EXAMPLES = r'''
- name: Populate service facts
  ansible.builtin.service_facts:

- name: Print service facts
  ansible.builtin.debug:
    var: ansible_facts.services
'''

RETURN = r'''
ansible_facts:
  description: Facts to add to ansible_facts about the services on the system
  returned: always
  type: complex
  contains:
    services:
      description: States of the services with service name as key.
      returned: always
      type: complex
      contains:
        source:
          description:
          - Init system of the service.
          - One of C(rcctl), C(systemd), C(sysv), C(upstart), C(src).
          returned: always
          type: str
          sample: sysv
        state:
          description:
          - State of the service.
          - 'This commonly includes (but is not limited to) the following: C(failed), C(running), C(stopped) or C(unknown).'
          - Depending on the used init system additional states might be returned.
          returned: always
          type: str
          sample: running
        status:
          description:
          - State of the service.
          - Either C(enabled), C(disabled), C(static), C(indirect) or C(unknown).
          returned: systemd systems or RedHat/SUSE flavored sysvinit/upstart or OpenBSD
          type: str
          sample: enabled
        name:
          description: Name of the service.
          returned: always
          type: str
          sample: arp-ethers.service
'''


import os
import platform
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.locale import get_best_parsable_locale


class BaseService(object):

    def __init__(self, module):
        self.module = module


class ServiceScanService(BaseService):

    def _list_sysvinit(self, services):
        rc, stdout, stderr = self.module.run_command("%s --status-all" % self.service_path)
        if rc == 4 and not os.path.exists('/etc/init.d'):
            # This function is not intended to run on Red Hat but it could happen
            # if `chkconfig` is not installed. `service` on RHEL9 returns rc 4
            # when /etc/init.d is missing, add the extra guard of checking /etc/init.d
            # instead of solely relying on rc == 4
            return
        if rc != 0:
            self.module.warn("Unable to query 'service' tool (%s): %s" % (rc, stderr))
        p = re.compile(r'^\s*\[ (?P<state>\+|\-) \]\s+(?P<name>.+)$', flags=re.M)
        for match in p.finditer(stdout):
            service_name = match.group('name')
            if match.group('state') == "+":
                service_state = "running"
            else:
                service_state = "stopped"
            services[service_name] = {"name": service_name, "state": service_state, "source": "sysv"}

    def _list_upstart(self, services):
        p = re.compile(r'^\s?(?P<name>.*)\s(?P<goal>\w+)\/(?P<state>\w+)(\,\sprocess\s(?P<pid>[0-9]+))?\s*$')
        rc, stdout, stderr = self.module.run_command("%s list" % self.initctl_path)
        if rc != 0:
            self.module.warn('Unable to query upstart for service data: %s' % stderr)
        else:
            real_stdout = stdout.replace("\r", "")
            for line in real_stdout.split("\n"):
                m = p.match(line)
                if not m:
                    continue
                service_name = m.group('name')
                service_goal = m.group('goal')
                service_state = m.group('state')
                if m.group('pid'):
                    pid = m.group('pid')
                else:
                    pid = None  # NOQA
                payload = {"name": service_name, "state": service_state, "goal": service_goal, "source": "upstart"}
                services[service_name] = payload

    def _list_rh(self, services):

        p = re.compile(
            r'(?P<service>.*?)\s+[0-9]:(?P<rl0>on|off)\s+[0-9]:(?P<rl1>on|off)\s+[0-9]:(?P<rl2>on|off)\s+'
            r'[0-9]:(?P<rl3>on|off)\s+[0-9]:(?P<rl4>on|off)\s+[0-9]:(?P<rl5>on|off)\s+[0-9]:(?P<rl6>on|off)')
        rc, stdout, stderr = self.module.run_command('%s' % self.chkconfig_path, use_unsafe_shell=True)
        # Check for special cases where stdout does not fit pattern
        match_any = False
        for line in stdout.split('\n'):
            if p.match(line):
                match_any = True
        if not match_any:
            p_simple = re.compile(r'(?P<service>.*?)\s+(?P<rl0>on|off)')
            match_any = False
            for line in stdout.split('\n'):
                if p_simple.match(line):
                    match_any = True
            if match_any:
                # Try extra flags " -l --allservices" needed for SLES11
                rc, stdout, stderr = self.module.run_command('%s -l --allservices' % self.chkconfig_path, use_unsafe_shell=True)
            elif '--list' in stderr:
                # Extra flag needed for RHEL5
                rc, stdout, stderr = self.module.run_command('%s --list' % self.chkconfig_path, use_unsafe_shell=True)

        for line in stdout.split('\n'):
            m = p.match(line)
            if m:
                service_name = m.group('service')
                service_state = 'stopped'
                service_status = "disabled"
                if m.group('rl3') == 'on':
                    service_status = "enabled"
                rc, stdout, stderr = self.module.run_command('%s %s status' % (self.service_path, service_name), use_unsafe_shell=True)
                service_state = rc
                if rc in (0,):
                    service_state = 'running'
                # elif rc in (1,3):
                else:
                    output = stderr.lower()
                    for x in ('root', 'permission', 'not in sudoers'):
                        if x in output:
                            self.module.warn('Insufficient permissions to query sysV service "%s" and their states' % service_name)
                            break
                    else:
                        service_state = 'stopped'

                service_data = {"name": service_name, "state": service_state, "status": service_status, "source": "sysv"}
                services[service_name] = service_data

    def _list_openrc(self, services):
        all_services_runlevels = {}
        rc, stdout, stderr = self.module.run_command("%s -a -s -m 2>&1 | grep '^ ' | tr -d '[]'" % self.rc_status_path, use_unsafe_shell=True)
        rc_u, stdout_u, stderr_u = self.module.run_command("%s show -v 2>&1 | grep '|'" % self.rc_update_path, use_unsafe_shell=True)
        for line in stdout_u.split('\n'):
            line_data = line.split('|')
            if len(line_data) < 2:
                continue
            service_name = line_data[0].strip()
            runlevels = line_data[1].strip()
            if not runlevels:
                all_services_runlevels[service_name] = None
            else:
                all_services_runlevels[service_name] = runlevels.split()
        for line in stdout.split('\n'):
            line_data = line.split()
            if len(line_data) < 2:
                continue
            service_name = line_data[0]
            service_state = line_data[1]
            service_runlevels = all_services_runlevels[service_name]
            service_data = {"name": service_name, "runlevels": service_runlevels, "state": service_state, "source": "openrc"}
            services[service_name] = service_data

    def gather_services(self):
        services = {}

        # find cli tools if available
        self.service_path = self.module.get_bin_path("service")
        self.chkconfig_path = self.module.get_bin_path("chkconfig")
        self.initctl_path = self.module.get_bin_path("initctl")
        self.rc_status_path = self.module.get_bin_path("rc-status")
        self.rc_update_path = self.module.get_bin_path("rc-update")

        # TODO: review conditionals ... they should not be this 'exclusive'
        if self.service_path and self.chkconfig_path is None and self.rc_status_path is None:
            self._list_sysvinit(services)
        if self.initctl_path and self.chkconfig_path is None:
            self._list_upstart(services)
        elif self.chkconfig_path:
            self._list_rh(services)
        elif self.rc_status_path is not None and self.rc_update_path is not None:
            self._list_openrc(services)
        return services


class SystemctlScanService(BaseService):

    BAD_STATES = frozenset(['not-found', 'masked', 'failed'])

    def systemd_enabled(self):
        # Check if init is the systemd command, using comm as cmdline could be symlink
        try:
            f = open('/proc/1/comm', 'r')
        except IOError:
            # If comm doesn't exist, old kernel, no systemd
            return False
        for line in f:
            if 'systemd' in line:
                return True
        return False

    def _list_from_units(self, systemctl_path, services):

        # list units as systemd sees them
        rc, stdout, stderr = self.module.run_command("%s list-units --no-pager --type service --all" % systemctl_path, use_unsafe_shell=True)
        if rc != 0:
            self.module.warn("Could not list units from systemd: %s" % stderr)
        else:
            for line in [svc_line for svc_line in stdout.split('\n') if '.service' in svc_line]:

                state_val = "stopped"
                status_val = "unknown"
                fields = line.split()
                for bad in self.BAD_STATES:
                    if bad in fields:  # dot is 0
                        status_val = bad
                        fields = fields[1:]
                        break
                else:
                    # active/inactive
                    status_val = fields[2]

                # array is normalize so predictable now
                service_name = fields[0]
                if fields[3] == "running":
                    state_val = "running"

                services[service_name] = {"name": service_name, "state": state_val, "status": status_val, "source": "systemd"}

    def _list_from_unit_files(self, systemctl_path, services):

        # now try unit files for complete picture and final 'status'
        rc, stdout, stderr = self.module.run_command("%s list-unit-files --no-pager --type service --all" % systemctl_path, use_unsafe_shell=True)
        if rc != 0:
            self.module.warn("Could not get unit files data from systemd: %s" % stderr)
        else:
            for line in [svc_line for svc_line in stdout.split('\n') if '.service' in svc_line]:
                # there is one more column (VENDOR PRESET) from `systemctl list-unit-files` for systemd >= 245
                try:
                    service_name, status_val = line.split()[:2]
                except IndexError:
                    self.module.fail_json(msg="Malformed output discovered from systemd list-unit-files: {0}".format(line))
                if service_name not in services:
                    rc, stdout, stderr = self.module.run_command("%s show %s --property=ActiveState" % (systemctl_path, service_name), use_unsafe_shell=True)
                    state = 'unknown'
                    if not rc and stdout != '':
                        state = stdout.replace('ActiveState=', '').rstrip()
                    services[service_name] = {"name": service_name, "state": state, "status": status_val, "source": "systemd"}
                elif services[service_name]["status"] not in self.BAD_STATES:
                    services[service_name]["status"] = status_val

    def gather_services(self):

        services = {}
        if self.systemd_enabled():
            systemctl_path = self.module.get_bin_path("systemctl", opt_dirs=["/usr/bin", "/usr/local/bin"])
            if systemctl_path:
                self._list_from_units(systemctl_path, services)
                self._list_from_unit_files(systemctl_path, services)

        return services


class AIXScanService(BaseService):

    def gather_services(self):

        services = {}
        if platform.system() == 'AIX':
            lssrc_path = self.module.get_bin_path("lssrc")
            if lssrc_path:
                rc, stdout, stderr = self.module.run_command("%s -a" % lssrc_path)
                if rc != 0:
                    self.module.warn("lssrc could not retrieve service data (%s): %s" % (rc, stderr))
                else:
                    for line in stdout.split('\n'):
                        line_data = line.split()
                        if len(line_data) < 2:
                            continue  # Skipping because we expected more data
                        if line_data[0] == "Subsystem":
                            continue  # Skip header
                        service_name = line_data[0]
                        if line_data[-1] == "active":
                            service_state = "running"
                        elif line_data[-1] == "inoperative":
                            service_state = "stopped"
                        else:
                            service_state = "unknown"
                        services[service_name] = {"name": service_name, "state": service_state, "source": "src"}
        return services


class OpenBSDScanService(BaseService):

    def query_rcctl(self, cmd):
        svcs = []
        rc, stdout, stderr = self.module.run_command("%s ls %s" % (self.rcctl_path, cmd))
        if 'needs root privileges' in stderr.lower():
            self.module.warn('rcctl requires root privileges')
        else:
            for svc in stdout.split('\n'):
                if svc == '':
                    continue
                else:
                    svcs.append(svc)
        return svcs

    def gather_services(self):

        services = {}
        self.rcctl_path = self.module.get_bin_path("rcctl")
        if self.rcctl_path:

            for svc in self.query_rcctl('all'):
                services[svc] = {'name': svc, 'source': 'rcctl'}

            for svc in self.query_rcctl('on'):
                services[svc].update({'status': 'enabled'})

            for svc in self.query_rcctl('started'):
                services[svc].update({'state': 'running'})

            # Based on the list of services that are enabled, determine which are disabled
            [services[svc].update({'status': 'disabled'}) for svc in services if services[svc].get('status') is None]

            # and do the same for those are aren't running
            [services[svc].update({'state': 'stopped'}) for svc in services if services[svc].get('state') is None]

            # Override the state for services which are marked as 'failed'
            for svc in self.query_rcctl('failed'):
                services[svc].update({'state': 'failed'})

        return services


def main():
    module = AnsibleModule(argument_spec=dict(), supports_check_mode=True)
    locale = get_best_parsable_locale(module)
    module.run_command_environ_update = dict(LANG=locale, LC_ALL=locale)
    service_modules = (ServiceScanService, SystemctlScanService, AIXScanService, OpenBSDScanService)
    all_services = {}
    for svc_module in service_modules:
        svcmod = svc_module(module)
        svc = svcmod.gather_services()
        if svc:
            all_services.update(svc)
    if len(all_services) == 0:
        results = dict(skipped=True, msg="Failed to find any services. This can be due to privileges or some other configuration issue.")
    else:
        results = dict(ansible_facts=dict(services=all_services))
    module.exit_json(**results)


if __name__ == '__main__':
    main()
