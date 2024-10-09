# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Brian Coca <briancoca+ansible@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: debconf
short_description: Configure a .deb package
description:
     - Configure a .deb package using debconf-set-selections.
     - Or just query existing selections.
version_added: "1.6"
extends_documentation_fragment:
- action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    platform:
        support: full
        platforms: debian
notes:
    - This module requires the command line debconf tools.
    - Several questions have to be answered (depending on the package).
      Use 'debconf-show <package>' on any Debian or derivative with the package
      installed to see questions/settings available.
    - Some distros will always record tasks involving the setting of passwords as changed. This is due to C(debconf-get-selections) masking passwords.
    - It is highly recommended to add C(no_log=True) to the task while handling sensitive information using this module.
    - The M(ansible.builtin.debconf) module does not reconfigure packages, it just updates the debconf database.
      An additional step is needed (typically with C(notify) if debconf makes a change)
      to reconfigure the package and apply the changes.
      C(debconf) is extensively used for pre-seeding configuration prior to installation
      rather than modifying configurations.
      So, while C(dpkg-reconfigure) does use debconf data, it is not always authoritative
      and you may need to check how your package is handled.
    - Also note C(dpkg-reconfigure) is a 3-phase process. It invokes the
      control scripts from the C(/var/lib/dpkg/info) directory with the
      C(<package>.prerm  reconfigure <version>),
      C(<package>.config reconfigure <version>) and C(<package>.postinst control <version>) arguments.
    - The main issue is that the C(<package>.config reconfigure) step for many packages
      will first reset the debconf database (overriding changes made by this module) by
      checking the on-disk configuration. If this is the case for your package then
      C(dpkg-reconfigure) will effectively ignore changes made by debconf.
    - However as C(dpkg-reconfigure) only executes the C(<package>.config) step if the file
      exists, it is possible to rename it to C(/var/lib/dpkg/info/<package>.config.ignore)
      before executing C(dpkg-reconfigure -f noninteractive <package>) and then restore it.
      This seems to be compliant with Debian policy for the .config file.
requirements:
- debconf
- debconf-utils
options:
  name:
    description:
      - Name of package to configure.
    type: str
    required: true
    aliases: [ pkg ]
  question:
    description:
      - A debconf configuration setting.
    type: str
    aliases: [ selection, setting ]
  vtype:
    description:
      - The type of the value supplied.
      - It is highly recommended to add C(no_log=True) to task while specifying O(vtype=password).
      - V(seen) was added in Ansible 2.2.
      - After Ansible 2.17, user can specify C(value) as a list, if C(vtype) is set as V(multiselect).
    type: str
    choices: [ boolean, error, multiselect, note, password, seen, select, string, text, title ]
  value:
    description:
      - Value to set the configuration to.
      - After Ansible 2.17, C(value) is of type C(raw).
    type: raw
    aliases: [ answer ]
  unseen:
    description:
      - Do not set C(seen) flag when pre-seeding.
    type: bool
    default: false
author:
- Brian Coca (@bcoca)
"""

EXAMPLES = r"""
- name: Set default locale to fr_FR.UTF-8
  ansible.builtin.debconf:
    name: locales
    question: locales/default_environment_locale
    value: fr_FR.UTF-8
    vtype: select

- name: Set to generate locales
  ansible.builtin.debconf:
    name: locales
    question: locales/locales_to_be_generated
    value: en_US.UTF-8 UTF-8, fr_FR.UTF-8 UTF-8
    vtype: multiselect

- name: Accept oracle license
  ansible.builtin.debconf:
    name: oracle-java7-installer
    question: shared/accepted-oracle-license-v1-1
    value: 'true'
    vtype: select

- name: Specifying package you can register/return the list of questions and current values
  ansible.builtin.debconf:
    name: tzdata

- name: Pre-configure tripwire site passphrase
  ansible.builtin.debconf:
    name: tripwire
    question: tripwire/site-passphrase
    value: "{{ site_passphrase }}"
    vtype: password
  no_log: True
"""

RETURN = r"""#"""

from ansible.module_utils.common.text.converters import to_text, to_native
from ansible.module_utils.basic import AnsibleModule


def get_password_value(module, pkg, question, vtype):
    getsel = module.get_bin_path('debconf-get-selections', True)
    cmd = [getsel]
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg=f"Failed to get the value '{question}' from '{pkg}': {err}")

    for line in out.split("\n"):
        if not line.startswith(pkg):
            continue

        # line is a collection of tab separated values
        fields = line.split('\t')
        if len(fields) <= 3:
            # No password found, return a blank password
            return ''
        try:
            if fields[1] == question and fields[2] == vtype:
                # If correct question and question type found, return password value
                return fields[3]
        except IndexError:
            # Fail safe
            return ''


def get_selections(module, pkg):
    cmd = [module.get_bin_path('debconf-show', True), pkg]
    rc, out, err = module.run_command(' '.join(cmd))

    if rc != 0:
        module.fail_json(msg=err)

    selections = {}

    for line in out.splitlines():
        (key, value) = line.split(':', 1)
        selections[key.strip('*').strip()] = value.strip()

    return selections


def set_selection(module, pkg, question, vtype, value, unseen):
    setsel = module.get_bin_path('debconf-set-selections', True)
    cmd = [setsel]
    if unseen:
        cmd.append('-u')

    data = ' '.join([pkg, question, vtype, value])

    return module.run_command(cmd, data=data)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, aliases=['pkg']),
            question=dict(type='str', aliases=['selection', 'setting']),
            vtype=dict(type='str', choices=['boolean', 'error', 'multiselect', 'note', 'password', 'seen', 'select', 'string', 'text', 'title']),
            value=dict(type='raw', aliases=['answer']),
            unseen=dict(type='bool', default=False),
        ),
        required_together=(['question', 'vtype', 'value'],),
        supports_check_mode=True,
    )

    # TODO: enable passing array of options and/or debconf file from get-selections dump
    pkg = module.params["name"]
    question = module.params["question"]
    vtype = module.params["vtype"]
    value = module.params["value"]
    unseen = module.params["unseen"]

    prev = get_selections(module, pkg)

    changed = False
    msg = ""

    if question is not None:
        if vtype is None or value is None:
            module.fail_json(msg="when supplying a question you must supply a valid vtype and value")

        # ensure we compare booleans supplied to the way debconf sees them (true/false strings)
        if vtype == 'boolean':
            value = to_text(value).lower()

        # if question doesn't exist, value cannot match
        if question not in prev:
            changed = True
        else:
            existing = prev[question]

            if vtype == 'boolean':
                existing = to_text(prev[question]).lower()
            elif vtype == 'password':
                existing = get_password_value(module, pkg, question, vtype)
            elif vtype == 'multiselect' and isinstance(value, list):
                try:
                    value = sorted(value)
                except TypeError as exc:
                    module.fail_json(msg="Invalid value provided for 'multiselect': %s" % to_native(exc))
                existing = sorted([i.strip() for i in existing.split(",")])

            if value != existing:
                changed = True

    if changed:
        if not module.check_mode:
            if vtype == 'multiselect' and isinstance(value, list):
                try:
                    value = ", ".join(value)
                except TypeError as exc:
                    module.fail_json(msg="Invalid value provided for 'multiselect': %s" % to_native(exc))
            rc, msg, e = set_selection(module, pkg, question, vtype, value, unseen)
            if rc:
                module.fail_json(msg=e)

        curr = {question: value}
        if question in prev:
            prev = {question: prev[question]}
        else:
            prev[question] = ''

        diff_dict = {}
        if module._diff:
            after = prev.copy()
            after.update(curr)
            diff_dict = {'before': prev, 'after': after}

        module.exit_json(changed=changed, msg=msg, current=curr, previous=prev, diff=diff_dict)

    module.exit_json(changed=changed, msg=msg, current=prev)


if __name__ == '__main__':
    main()
