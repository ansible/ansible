#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cl_license
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Install licenses fo Cumulus Linux
deprecated: Deprecated in 2.3.
description:
    - Installs a Cumulus Linux license. The module reports no change of status
      when a license is installed.
      For more details go the Cumulus Linux License Documentation at
      U(http://docs.cumulusnetwork.com) and the Licensing KB Site at
      U(https://support.cumulusnetworks.com/hc/en-us/sections/200507688)
notes:
    - To activate a license for the FIRST time, the switchd service must be
      restarted. This action is disruptive. The license renewal process occurs
      via the Cumulus Networks Customer Portal -
      U(http://customers.cumulusnetworks.com).
    - A non-EULA license is REQUIRED for automation. Manually install the
      license on a test switch, using the command "cl-license -i <license_file>"
      to confirm the license is a Non-EULA license.
      See EXAMPLES, for the proper way to issue this notify action.
options:
    src:
        description:
            - The full path to the license. Can be local path or HTTP URL.
        required: true
    force:
        description:
            - Force installation of a license. Typically not needed.
              It is recommended to manually run this command via the ansible
              command. A reload of switchd is not required. Running the force
              option in a playbook will break the idempotent state machine of
              the module and cause the switchd notification to kick in all the
              time, causing a disruption.
        choices:
            - yes
            - no

'''
EXAMPLES = '''
# Example playbook using the cl_license module to manage licenses on Cumulus Linux

- hosts: all
  tasks:
    - name: install license using http url
      cl_license:
        src: http://10.1.1.1/license.txt
      notify: restart switchd

    - name: Triggers switchd to be restarted right away, before play, or role
            is over. This is desired behaviour
      meta: flush_handlers

    - name: Configure interfaces
      template:
        src: interfaces.j2
        dest: /etc/network/interfaces
      notify: restart networking

  handlers:
   - name: restart switchd
     service:
      name: switchd
      state: restarted
   - name: restart networking
     service:
      name: networking
      state: reloaded

# Force all switches to accept a new license. Typically not needed
# ansible -m cl_license -a "src='http://10.1.1.1/new_lic' force=yes" -u root all
'''

RETURN = '''
changed:
    description: whether the interface was changed
    returned: changed
    type: bool
    sample: True
msg:
    description: human-readable report of success or failure
    returned: always
    type: string
    sample: "interface bond0 config updated"
'''

from ansible.module_utils.basic import AnsibleModule


CL_LICENSE_PATH = '/usr/cumulus/bin/cl-license'


def install_license(module):
    # license is not installed, install it
    _url = module.params.get('src')
    (_rc, out, _err) = module.run_command("%s -i %s" % (CL_LICENSE_PATH, _url))
    if _rc > 0:
        module.fail_json(msg=_err)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(required=True, type='str'),
            force=dict(type='bool', default=False)
        ),
    )

    # check if license is installed
    # if force is enabled then set return code to nonzero
    if module.params.get('force') is True:
        _rc = 10
    else:
        (_rc, out, _err) = module.run_command(CL_LICENSE_PATH)
    if _rc == 0:
        module.msg = "No change. License already installed"
        module.changed = False
    else:
        install_license(module)
        module.msg = "License installation completed"
        module.changed = True
    module.exit_json(changed=module.changed, msg=module.msg)


if __name__ == '__main__':
    main()
