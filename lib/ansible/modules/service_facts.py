#!/usr/bin/python
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
requirements: ["Any of the following supported init systems: systemd, sysv, upstart, AIX SRC"]

notes:
  - When accessing the C(ansible_facts.services) facts collected by this module,
    it is recommended to not use "dot notation" because services can have a C(-)
    character in their name which would result in invalid "dot notation", such as
    C(ansible_facts.services.zuul-gateway). It is instead recommended to
    using the string value of the service name as the key in order to obtain
    the fact data value like C(ansible_facts.services['zuul-gateway'])
  - AIX SRC was added in version 2.11.
  - Supports C(check_mode).

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
          - Either C(failed), C(running), C(stopped), or C(unknown).
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


import platform
import re
from ansible.module_utils.basic import AnsibleModule


class BaseService(object):

    def __init__(self, module):
        self.module = module
        self.incomplete_warning = False


class ServiceScanService(BaseService):

    def gather_services(self):
        services = {}
        service_path = self.module.get_bin_path("service")
        if service_path is None:
            return None
        initctl_path = self.module.get_bin_path("initctl")
        chkconfig_path = self.module.get_bin_path("chkconfig")

        # sysvinit
        if service_path is not None and chkconfig_path is None:
            rc, stdout, stderr = self.module.run_command("%s --status-all 2>&1 | grep -E \"\\[ (\\+|\\-) \\]\"" % service_path, use_unsafe_shell=True)
            for line in stdout.split("\n"):
                line_data = line.split()
                if len(line_data) < 4:
                    continue  # Skipping because we expected more data
                service_name = " ".join(line_data[3:])
                if line_data[1] == "+":
                    service_state = "running"
                else:
                    service_state = "stopped"
                services[service_name] = {"name": service_name, "state": service_state, "source": "sysv"}

        # Upstart
        if initctl_path is not None and chkconfig_path is None:
            p = re.compile(r'^\s?(?P<name>.*)\s(?P<goal>\w+)\/(?P<state>\w+)(\,\sprocess\s(?P<pid>[0-9]+))?\s*$')
            rc, stdout, stderr = self.module.run_command("%s list" % initctl_path)
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

        # RH sysvinit
        elif chkconfig_path is not None:
            # print '%s --status-all | grep -E "is (running|stopped)"' % service_path
            p = re.compile(
                r'(?P<service>.*?)\s+[0-9]:(?P<rl0>on|off)\s+[0-9]:(?P<rl1>on|off)\s+[0-9]:(?P<rl2>on|off)\s+'
                r'[0-9]:(?P<rl3>on|off)\s+[0-9]:(?P<rl4>on|off)\s+[0-9]:(?P<rl5>on|off)\s+[0-9]:(?P<rl6>on|off)')
            rc, stdout, stderr = self.module.run_command('%s' % chkconfig_path, use_unsafe_shell=True)
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
                    rc, stdout, stderr = self.module.run_command('%s -l --allservices' % chkconfig_path, use_unsafe_shell=True)
                elif '--list' in stderr:
                    # Extra flag needed for RHEL5
                    rc, stdout, stderr = self.module.run_command('%s --list' % chkconfig_path, use_unsafe_shell=True)
            for line in stdout.split('\n'):
                m = p.match(line)
                if m:
                    service_name = m.group('service')
                    service_state = 'stopped'
                    service_status = "disabled"
                    if m.group('rl3') == 'on':
                        service_status = "enabled"
                    rc, stdout, stderr = self.module.run_command('%s %s status' % (service_path, service_name), use_unsafe_shell=True)
                    service_state = rc
                    if rc in (0,):
                        service_state = 'running'
                    # elif rc in (1,3):
                    else:
                        if 'root' in stderr or 'permission' in stderr.lower() or 'not in sudoers' in stderr.lower():
                            self.incomplete_warning = True
                            continue
                        else:
                            service_state = 'stopped'
                    service_data = {"name": service_name, "state": service_state, "status": service_status, "source": "sysv"}
                    services[service_name] = service_data
        return services


class SystemctlScanService(BaseService):

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

    def gather_services(self):
        services = {}
        if not self.systemd_enabled():
            return None
        systemctl_path = self.module.get_bin_path("systemctl", opt_dirs=["/usr/bin", "/usr/local/bin"])
        if systemctl_path is None:
            return None
        rc, stdout, stderr = self.module.run_command("%s list-units --no-pager --type service --all" % systemctl_path, use_unsafe_shell=True)
        for line in [svc_line for svc_line in stdout.split('\n') if '.service' in svc_line and 'not-found' not in svc_line]:
            service_name = line.split()[0]
            if "running" in line:
                state_val = "running"
            else:
                if 'failed' in line:
                    service_name = line.split()[1]
                state_val = "stopped"
            services[service_name] = {"name": service_name, "state": state_val, "status": "unknown", "source": "systemd"}
        rc, stdout, stderr = self.module.run_command("%s list-unit-files --no-pager --type service --all" % systemctl_path, use_unsafe_shell=True)
        for line in [svc_line for svc_line in stdout.split('\n') if '.service' in svc_line and 'not-found' not in svc_line]:
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
            else:
                services[service_name]["status"] = status_val
        return services


class AIXScanService(BaseService):

    def gather_services(self):
        services = {}
        if platform.system() != 'AIX':
            return None
        lssrc_path = self.module.get_bin_path("lssrc")
        if lssrc_path is None:
            return None
        rc, stdout, stderr = self.module.run_command("%s -a" % lssrc_path)
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
            self.incomplete_warning = True
            return []

        for svc in stdout.split('\n'):
            if svc == '':
                continue
            else:
                svcs.append(svc)

        return svcs

    def gather_services(self):
        services = {}
        self.rcctl_path = self.module.get_bin_path("rcctl")
        if self.rcctl_path is None:
            return None

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
    module.run_command_environ_update = dict(LANG="C", LC_ALL="C")
    service_modules = (ServiceScanService, SystemctlScanService, AIXScanService, OpenBSDScanService)
    all_services = {}
    incomplete_warning = False
    for svc_module in service_modules:
        svcmod = svc_module(module)
        svc = svcmod.gather_services()
        if svc is not None:
            all_services.update(svc)
            if svcmod.incomplete_warning:
                incomplete_warning = True
    if len(all_services) == 0:
        results = dict(skipped=True, msg="Failed to find any services. Sometimes this is due to insufficient privileges.")
    else:
        results = dict(ansible_facts=dict(services=all_services))
        if incomplete_warning:
            results['msg'] = "WARNING: Could not find status for all services. Sometimes this is due to insufficient privileges."
    module.exit_json(**results)


if __name__ == '__main__':
    main()
