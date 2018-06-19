#!/usr/bin/python
# (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# originally copied from AWX's scan_services module to bring this functionality
# into Core

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: service_facts
short_description: Return service state information as fact data
description:
     - Return service state information as fact data for various service management utilities
version_added: "2.5"
requirements: ["Any of the following supported init systems: systemd, sysv, upstart"]

notes:
  - When accessing the C(ansible_facts.services) facts collected by this module,
    it is recommended to not use "dot notation" because services can have a C(-)
    character in their name which would result in invalid "dot notation", such as
    C(ansible_facts.services.zuul-gateway). It is instead recommended to
    using the string value of the service name as the key in order to obtain
    the fact data value like C(ansible_facts.services['zuul-gateway'])


author:
  - Matthew Jones
  - Adam Miller (@maxamillion)
'''

EXAMPLES = '''
- name: populate service facts
  service_facts:

- debug:
    var: ansible_facts.services

'''

RETURN = '''
ansible_facts:
  description: facts to add to ansible_facts about the services on the system
  returned: always
  type: complex
  contains:
    "services": {
      "network": {
        "source": "sysv",
        "state": "running",
        "name": "network"
      },
      arp-ethers.service: {
        "source": "systemd",
        "state": "stopped",
        "name": "arp-ethers.service"
      }
    }
'''


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
                    if m.group('rl3') == 'on':
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
                    service_data = {"name": service_name, "state": service_state, "source": "sysv"}
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
            services[service_name] = {"name": service_name, "state": state_val, "source": "systemd"}
        return services


def main():
    module = AnsibleModule(argument_spec=dict(), supports_check_mode=True)
    service_modules = (ServiceScanService, SystemctlScanService)
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
