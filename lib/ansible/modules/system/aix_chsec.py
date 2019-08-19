#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Christian Tremel (@flynn1973)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# AIX 7.1: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_71/c_commands/chsec.html
# AIX 7.2: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/c_commands/chsec.html
# AIX 6.1 PDF: https://public.dhe.ibm.com/systems/power/docs/aix/61/aixcmds1_pdf.pdf

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: aix_chsec
short_description: Modify AIX stanza files
version_added: '2.8'
description:
- Modify stanzas to AIX config files using the C(chsec) command.
options:
  path:
    description:
    - Path to the stanza file.
    type: path
    required: true
    aliases: [ dest ]
  stanza:
    description:
    - Name of stanza.
    type: str
    required: true
  options:
     description:
     - A list of key/value pairs, e.g. C(key=val,key=val).
     type: list
  state:
     description:
     - If set to C(absent) the whole stanza incl. all given options will be removed.
     - If set to C(present) stanza incl.options will be added.
     - To remove an option from the stanza set to C(present) and set key to an empty value (key=).
     - All rules, allowed file-stanza combos or allowed files for the C(chsec) command also applies here.
     type: str
     choices: [ absent, present ]
     default: present
seealso:
- name: The chsec manual page from the IBM Knowledge Center
  description: Changes the attributes in the security stanza files.
  link: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/com.ibm.aix.cmds1/chsec.htm
author:
- Christian Tremel (@flynn1973)
'''

EXAMPLES = r'''
- name: Add an LDAP user stanza
  aix_chsec:
    path: /etc/security/user
    stanza: ldapuser
    attrs:
      SYSTEM: LDAP
      registry: LDAP
    state: present
    mode: '0644'

- name: Change login times for user
  aix_chsec:
    path: /etc/security/user
    stanza: ldapuser
    attrs: 
      logintimes: 0800-1700
    state: present

- name: Remove registry attribute from stanza
  aix_chsec:
    path: /etc/security/user
    stanza: ldapuser
    attrs:
      SYSTEM: LDAP
      registry: null
    state: present
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule


def do_stanza(module, filename, stanza, options, state='present'):

    chsec_command = module.get_bin_path('chsec', True)

    def arguments_generator(options):
        for element in options:
            yield '-a'
            yield element

    command = [chsec_command, '-f', filename, '-s', '%s' % stanza]
    options = list(arguments_generator(options))

    if state == 'present':
        command += options
        rc, stdout, stderr = module.run_command(command)
        if rc != 0:
            module.fail_json(msg='Failed to run chsec command (present).', rc=rc, stdout=stdout, stderr=stderr)
        else:
            msg = 'stanza added'
            changed = True
    elif state == 'absent':
        # remove values from keys to enable chsec delete mode
        command += [s[:1 + s.find('=')] or s for s in options]
        rc, stdout, stderr = module.run_command(command)
        if rc != 0:
            module.fail_json(msg='Failed to run chsec command (absent).', rc=rc, stdout=stdout, stderr=stderr)
        else:
            msg = 'stanza removed'
            changed = True

    return changed, msg


def main():

    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest']),
            stanza=dict(type='str', required=True),
            options=dict(type='list', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=False,
    )

    path = module.params['path']
    stanza = module.params['stanza']
    options = module.params['options']
    state = module.params['state']

    result = dict(
        changed=False,
    )

    result['changed'], result['msg'] = do_stanza(module, path, stanza, options, state)

    # Mission complete
    module.exit_json(**result)


if __name__ == '__main__':
    main()
