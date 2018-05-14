#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2016, Loic Blot <loic.blot@unix-experience.fr>
# Copyright (c) 2018, Ansible Project
# Sponsored by Infopro Digital. http://www.infopro-digital.com/
# Sponsored by E.T.A.I. http://www.etai.fr/
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: icinga2_feature

short_description: Manage Icinga2 feature
description:
    - This module can be used to enable or disable an Icinga2 feature.
version_added: "2.3"
author: "Loic Blot (@nerzhul)"
options:
    name:
      description:
      - This is the feature name to enable or disable.
      required: True
    state:
      description:
      - If set to C(present) and feature is disabled, then feature is enabled.
      - If set to C(present) and feature is already enabled, then nothing is changed.
      - If set to C(absent) and feature is enabled, then feature is disabled.
      - If set to C(absent) and feature is already disabled, then nothing is changed.
      choices: [ "present", "absent" ]
      default: present
'''

EXAMPLES = '''
- name: Enable ido-pgsql feature
  icinga2_feature:
    name: ido-pgsql
    state: present

- name: Disable api feature
  icinga2_feature:
    name: api
    state: absent
'''

RETURN = '''
#
'''

import re
from ansible.module_utils.basic import AnsibleModule


class Icinga2FeatureHelper:
    def __init__(self, module):
        self.module = module
        self._icinga2 = module.get_bin_path('icinga2', True)
        self.feature_name = self.module.params['name']
        self.state = self.module.params['state']

    def _exec(self, args):
        cmd = [self._icinga2, 'feature']
        rc, out, err = self.module.run_command(cmd + args, check_rc=True)
        return rc, out

    def manage(self):
        rc, out = self._exec(["list"])
        if rc != 0:
            self.module.fail_json(msg="Unable to list icinga2 features. "
                                      "Ensure icinga2 is installed and present in binary path.")

        # If feature is already in good state, just exit
        if (re.search("Disabled features:.* %s[ \n]" % self.feature_name, out) and self.state == "absent") or \
                (re.search("Enabled features:.* %s[ \n]" % self.feature_name, out) and self.state == "present"):
            self.module.exit_json(changed=False)

        if self.module.check_mode:
            self.module.exit_json(changed=True)

        feature_enable_str = "enable" if self.state == "present" else "disable"

        rc, out = self._exec([feature_enable_str, self.feature_name])

        change_applied = False
        if self.state == "present":
            if rc != 0:
                self.module.fail_json(msg="Failed to %s feature %s."
                                          " icinga2 command returned %s" % (feature_enable_str,
                                                                            self.feature_name,
                                                                            out))

            if re.search("already enabled", out) is None:
                change_applied = True
        else:
            if rc == 0:
                change_applied = True
            # RC is not 0 for this already disabled feature, handle it as no change applied
            elif re.search("Cannot disable feature '%s'. Target file .* does not exist" % self.feature_name, out):
                change_applied = False
            else:
                self.module.fail_json(msg="Failed to disable feature. Command returns %s" % out)

        self.module.exit_json(changed=change_applied)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', choices=["present", "absent"], default="present")
        ),
        supports_check_mode=True
    )

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')
    Icinga2FeatureHelper(module).manage()


if __name__ == '__main__':
    main()
