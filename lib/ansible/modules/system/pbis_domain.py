#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
---
module: pbis_domain
short_description: Join or leave AD with PBIS (open)
description:
  - This module allows to join or leave an Active Directory domain with PBIS (open).
  - The module attempts to catch and fix a couple of common error scenario's when joining.
version_added: "2.8"
author:
  - Luc Stroobant (@stroobl)
requirements:
  - PBIS (open) should be installed on the system.
options:
  name:
    description:
      - Domain name to join or leave.
      - Not required to leave a domain.
    type: str
    aliases: [domain]
  state:
    description:
      - Join or leave the domain?
    type: str
    default: present
    choices: [absent, join, leave, present]
  disabled_modules:
    description:
      - List of PBIS configuration modules to disable during the join command.
      - Refer to the pbis documentation for more information.
    default: ['hostname']
    choices: ['bash', 'firewall', 'gdm', 'hostname', 'krb5', 'lam-auth', 'pam', 'pam-mode', 'nsswitch', 'ssh']
  timesync:
    description: sync the system time with the domain?
    type: bool
    default: false
  ou:
    description:
      - AD Organizational Unit for the computer account.
      - Only used for join.
    type: str
  user:
    description:
      - Active Directory user with permission to join or leave the domain.
    type: str
    required: true
  password:
    description:
      - Password for user.
    type: str
    required: true
notes:
  - "The default join options are set to be minimaly intrusive on your system. The hostname
    and time won't be touched, hostname and time are supposed to be configured before
    the join. If you want PBIS to handle this, set timesync: yes and disable_mdoules: []"
"""

EXAMPLES = """
- name: join domain.com
  pbis_domain:
    name: ad.local
    state: present
    user: administrator@ad.local
    password: password

- name: leave domain.com
  pbis_domain:
    state: absent
    user: administrator@ad.local
    password: password
"""

RETURN = """
msg:
  description: The result of the join or leave action.
  returned: success
  type: str
  sample: Joined domain
fixed:
  description: Modules fixed when system is already joined, but not fully configured.
  returned: success
  type: list
  sample: ["nsswitch", "pam"]
errors:
  description: Errors when trying to join or leave the domain.
  returned: failure
  type: str
  sample: "Error: Undocumented exception [code 0x00009efc]"
pbis_open_reboot_required:
  description: Should the system be rebooted after the action?
  returned: success
  type: bool
  sample: true
"""


import os

from ansible.module_utils.basic import AnsibleModule


def join(disabled_modules, timesync, ou, domain, user, password, module):
    """Join the domain"""

    changed, reboot_required = False, False
    result, errors = None, None

    if os.path.isfile("/opt/pbis/bin/domainjoin-cli"):
        # Test if system is already joined:
        rc, result, errors = module.run_command(
            "/opt/pbis/bin/domainjoin-cli query", check_rc=False
        )

        # (Re)join if required
        if rc == 1 or not domain.lower() in result.lower():
            cmd = ["/opt/pbis/bin/domainjoin-cli", "join"]
            if module.check_mode:
                cmd.extend(["--preview"])
            if not timesync:
                cmd.extend(["--notimesync"])
            if disabled_modules:
                for mdl in disabled_modules:
                    cmd.extend(["--disable", mdl])
            if ou:
                cmd.extend(["--ou", ou])
            cmd.extend([domain, user, password])

            rc, result, errors = None, None, None
            rc, result, errors = module.run_command(cmd, check_rc=False)
            if rc == 0:
                changed = True
                reboot_required = True
            else:
                # Catch a special case while rejoining and "computer failed to update the dnsHostName
                # and/or servicePrincipalName(SPN) attribute in its Active Directory computer account"
                chkrc, chkresult, chkerrors = None, None, None
                chkrc, chkresult, chkerrors = module.run_command(
                    "/opt/pbis/bin/domainjoin-cli query", check_rc=False
                )
                if chkrc == 0 and domain.lower() in chkresult.lower():
                    changed = True
                    reboot_required = True
                else:
                    module.fail_json(msg=result)

        # Check configuration status to catch unconfigured modules causing failure
        status_dict = check_config(domain, module)
        # Fix configuration if required
        fixed_mdls = list()
        for mdl in ["keytab", "nsswitch", "krb5", "pam", "ssh"]:
            if status_dict[mdl]["configured"] == "N":
                fixed_mdls.append(mdl)
                if not module.check_mode:
                    fix_config(mdl, domain, module)
        module.exit_json(
            changed=bool(fixed_mdls),
            fixed=fixed_mdls,
            ansible_facts=dict(pbis_open_reboot_required=reboot_required),
        )
    else:
        module.fail_json(
            msg="/opt/pbis/bin/domainjoin-cli not found, is PBIS installed?"
        )

    return changed, result, errors, reboot_required


def check_config(domain, module):
    """Test if all required configuration is active"""

    rc, result, errors = module.run_command(
        "/opt/pbis/bin/domainjoin-cli join --advanced --preview {0}".format(domain),
        check_rc=True,
    )

    status_block = result.split("\n\n")[1].splitlines()
    status_dict = {}
    for line in status_block:
        enabled = line[1] == "X"
        configured = line[5]
        flag = line[8: line.find("-")].strip()
        status_dict[flag] = dict(enabled=enabled, configured=configured)

    return status_dict


def fix_config(mdl, domain, module):
    """Apply the required fixes"""

    opts = dict(krb5=["--long", domain, "--short", domain.split(".")[0]])
    cmd = ["/opt/pbis/bin/domainjoin-cli", "configure"]
    cmd.extend(opts.get(mdl, []))
    cmd.extend(["--enable", mdl])

    rc, result, errors = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg=result)


def leave(domain, user, password, module):
    """Leave the domain"""

    changed = False
    result, errors = None, None
    if os.path.isfile("/opt/pbis/bin/domainjoin-cli"):
        # Test if system is already joined:
        rc, result, errors = module.run_command(
            "/opt/pbis/bin/domainjoin-cli query", check_rc=False
        )
        # Second test for half joined systems
        rc2, result2, errors2 = module.run_command(
            "/opt/pbis/bin/get-status", check_rc=False
        )

        # Leave if joined
        if domain.lower() in result.lower() or domain.lower() in result2.lower():
            cmd = ["/opt/pbis/bin/domainjoin-cli", "leave", "--deleteAccount"]
            if module.check_mode:
                cmd.append("--preview")
            cmd.extend([user, password])

            rc, result, errors = module.run_command(cmd)
            if rc == 0:
                changed = True
                reboot_required = True
            else:
                module.fail_json(msg=result)
    else:
        module.fail_json(
            msg="/opt/pbis/bin/domainjoin-cli not found, is PBIS installed?"
        )

    return changed, result, errors, reboot_required


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, aliases=["domain"]),
            state=dict(
                type='str', default="present", choices=["absent", "join", "leave", "present"]
            ),
            disabled_modules=dict(
                type='list', default=["hostname"],
                choices=["bash", "firewall", "gdm", "hostname", "krb5", "lam-auth", "pam", "pam-mode", "nsswitch", "ssh"]
            ),
            timesync=dict(type='bool', default=False),
            ou=dict(type='str'),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
        ),
        supports_check_mode=True,
    )

    domain = module.params["name"]
    state = module.params["state"]
    disabled_modules = module.params["disabled_modules"]
    timesync = module.params["timesync"]
    ou = module.params["ou"]
    user = module.params["user"]
    password = module.params["password"]

    errors, result = None, None
    changed, reboot_required = False, False
    if state in ["join", "present"]:
        changed, result, errors, reboot_required = join(
            disabled_modules, timesync, ou, domain, user, password, module
        )
    else:
        changed, result, errors, reboot_required = leave(domain, user, password, module)

    module.exit_json(
        changed=changed,
        msg=result,
        errors=errors,
        ansible_facts=dict(pbis_open_reboot_required=reboot_required),
    )


if __name__ == "__main__":
    main()
