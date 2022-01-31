# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# originally copied from @maxmillion's service_facts module

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: timer_facts
short_description: Return timer state information as fact data
description:
     - Return timer state information as fact data for various timer management utilities.
version_added: "2.12.1"
requirements: ["systemd"]
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
  - When accessing the C(ansible_facts.timers) facts collected by this module,
    it is recommended to not use "dot notation" because timers can have a C(-)
    character in their name which would result in invalid "dot notation", such as
    C(ansible_facts.timers.zuul-gateway). It is instead recommended to
    using the string value of the timer name as the key in order to obtain
    the fact data value like C(ansible_facts.timers['zuul-gateway'])
  - AIX SRC was added in version 2.11.
author:
  - @aconitumnapellus
'''

EXAMPLES = r'''
- name: Populate timer facts
  ansible.builtin.timer_facts:

- name: Print timer facts
  ansible.builtin.debug:
    var: ansible_facts.timers
'''

RETURN = r'''
ansible_facts:
  description: Facts to add to ansible_facts about the timers on the system
  returned: always
  type: complex
  contains:
    timers:
      description: States of the timers with timer name as key.
      returned: always
      type: complex
      contains:
        source:
          description:
          - Init system of the timer.
          - C(systemd)
          returned: always
          type: str
          sample: sysv
        state:
          description:
          - State of the timer.
          - 'This commonly includes (but is not limited to) the following: C(failed), C(running), C(stopped) or C(unknown).'
          - Depending on the used init system additional states might be returned.
          returned: always
          type: str
          sample: running
        status:
          description:
          - State of the timer.
          - Either C(enabled), C(disabled), C(static), C(indirect) or C(unknown).
          returned: systemd systems
          type: str
          sample: enabled
        name:
          description: Name of the timer.
          returned: always
          type: str
          sample: arp-ethers.timer
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.locale import get_best_parsable_locale


class BaseService(object):

    def __init__(self, module):
        self.module = module
        self.incomplete_warning = False


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

    def gather_timers(self):
        BAD_STATES = frozenset(['not-found', 'masked', 'failed'])
        timers = {}
        if not self.systemd_enabled():
            return None
        systemctl_path = self.module.get_bin_path("systemctl", opt_dirs=["/usr/bin", "/usr/local/bin"])
        if systemctl_path is None:
            return None

        # list units as systemd sees them
        rc, stdout, stderr = self.module.run_command("%s list-units --no-pager --type timer --all" % systemctl_path, use_unsafe_shell=True)
        for line in [tmr_line for tmr_line in stdout.split('\n') if '.timer' in tmr_line]:
            state_val = "stopped"
            status_val = "unknown"
            fields = line.split()
            for bad in BAD_STATES:
                if bad in fields:  # dot is 0
                    status_val = bad
                    fields = fields[1:]
                    break
            else:
                # active/inactive
                status_val = fields[2]

            # array is normalize so predictable now
            timer_name = fields[0]
            if fields[3] == "running":
                state_val = "running"

            timers[timer_name] = {"name": timer_name, "state": state_val, "status": status_val, "source": "systemd"}
            

        # now try unit files for complete picture and final 'status'
        rc, stdout, stderr = self.module.run_command("%s list-unit-files --no-pager --type timer --all" % systemctl_path, use_unsafe_shell=True)
        for line in [tmr_line for tmr_line in stdout.split('\n') if '.timer' in tmr_line]:
            # there is one more column (VENDOR PRESET) from `systemctl list-unit-files` for systemd >= 245
            try:
                timer_name, status_val = line.split()[:2]
            except IndexError:
                self.module.fail_json(msg="Malformed output discovered from systemd list-unit-files: {0}".format(line))
            if timer_name not in timers:
                rc, stdout, stderr = self.module.run_command("%s show %s --property=ActiveState" % (systemctl_path, timer_name), use_unsafe_shell=True)
                state = 'unknown'
                if not rc and stdout != '':
                    state = stdout.replace('ActiveState=', '').rstrip()
                timers[timer_name] = {"name": timer_name, "state": state, "status": status_val, "source": "systemd"}
            elif timers[timer_name]["status"] not in BAD_STATES:
                timers[timer_name]["status"] = status_val

        return timers


def main():
    module = AnsibleModule(argument_spec=dict(), supports_check_mode=True)
    locale = get_best_parsable_locale(module)
    module.run_command_environ_update = dict(LANG=locale, LC_ALL=locale)
    all_timers = {}
    incomplete_warning = False
    tmrmod = SystemctlScanService(module)
    tmr = tmrmod.gather_timers()
    if tmr is not None:
        all_timers.update(tmr)
        if tmrmod.incomplete_warning:
            incomplete_warning = True
    if len(all_timers) == 0:
        results = dict(skipped=True, msg="Failed to find any timers. Sometimes this is due to insufficient privileges.")
    else:
        results = dict(ansible_facts=dict(timers=all_timers))
        if incomplete_warning:
            results['msg'] = "WARNING: Could not find status for all timers. Sometimes this is due to insufficient privileges."
    module.exit_json(**results)


if __name__ == '__main__':
    main()
