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
- Modify stanza attributes to AIX config files using the C(chsec) command.
attrs:
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
  attrs:
     description:
     - A list of key/value pairs, e.g. C(key: val,key: val).
     type: list
     aliases: [ options ]
  state:
     description:
     - If set to C(present) all given attrs values will be set.
     - If set to C(absent) all attrs provided will be un-set, regardless of value provided.
       - NB: This does not remove the entire stanza, only the provided attrs will be removed.
     - To remove an attribute from the stanza set to C(present) and set key to an empty value (key=).
     - All rules, allowed file-stanza combos or allowed files for the C(chsec) command also applies here.
     type: str
     choices: [ absent, present ]
     default: present
seealso:
- name: The chsec manual page from the IBM Knowledge Center
  description: Changes the attributes in the security stanza files.
  link: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/c_commands/chsec.html
- name: The lssec manual page from the IBM Knowledge Center
  description: Lists attributes in the security stanza files.
  link: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/l_commands/lssec.html
author:
- Christian Tremel (@flynn1973)
- David Little (@d-little)
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

- name: Change login times for user
  aix_chsec:
    path: /etc/security/user
    stanza: ldapuser
    attrs:
      logintimes: :0800-1700
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
tbd:
    fill: this
    out: please.
'''

from ansible.module_utils.basic import AnsibleModule


def attrs2dict(attrs):
    """ Given any of the possible module 'attr' formats, return them as a dict. """
    """
    eg: Can take data as either a dict, a list, or a string.
        - Dict:     { "SYSTEM": "LDAP", "registry": "LDAP" }
        - List:     [ "SYSTEM=LDAP", "registry=LDAP" ]
        - String:   "SYSTEM=LDAP,registry=LDAP"
    All of these will return the dict (nothing changes for dicts):
        { 'SYSTEM': 'LDAP', 'registry': 'LDAP' }
    """
    return_dict = {}
    if type(attrs) == str:
        # Assume we have this:
        #   "SYSTEM=LDAP,registry=LDAP"
        # Split it into a list of strings, like this:
        #   [ "SYSTEM=LDAP", "registry=LDAP" ]
        attrs = [x.strip() for x in attrs.split(',')]
    if type(attrs) == list:
        # Assume it's a list of key=values, so
        #   [ "SYSTEM=LDAP", "registry=LDAP" ]
        # Take each attr and split it into a key:value dict and update return_dict
        #   { "SYSTEM": "LDAP", "registry":"LDAP" }
        for element in attrs:
            k, v = element.split('=')
            return_dict.update({k: v})
    if type(attrs) == dict:
        return_dict.update(attrs)
    return return_dict


def do_stanza(module, filename, stanza, attrs, state='present'):
    lssec_command = module.get_bin_path('lssec', required=True)
    chsec_command = module.get_bin_path('chsec', required=True)

    return_msg = {}
    changed = 0

    if state == 'absent':
        # We need to rip out the entire stanza.
        # Not sure how to do this, or if it's even possible
        pass

    elif state == 'present':
        attrs = attrs2dict(attrs)
        for k, v in attrs.items():
            # Start our msg dict for this key+value
            msg = {
                'target_value': v,
                'status': 'unchanged',
            }
            # Check current values
            cmd = [lssec_command, '-c', '-f', filename, '-s', stanza, '-a', k]
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                msg = 'Failed to run lssec command: ' + ' '.join(cmd)
                module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
            lssec_out = stdout.splitlines()[1].split(':')[1].strip('\\\"\n ')
            msg.update({
                'incoming_value': lssec_out,
            })
            if lssec_out != v:
                # Change the value of the attr
                cmd = [chsec_command, '-f', filename, '-s', stanza, '-a', '='.join([k, v])]
                if module.check_mode:
                    msg.update({"check_mode": True})
                else:
                    rc, stdout, stderr = module.run_command(cmd)
                    if rc != 0:
                        msg = 'Failed to run chsec command: ' + ' '.join(cmd)
                        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
                msg.update({
                    'outgoing_value': v,
                    'status': 'changed',
                })
                changed += 1
            return_msg[k] = msg

    return bool(changed), msg


def main():

    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest']),
            stanza=dict(type='str', required=True),
            attrs=dict(type='raw', required=True, aliases=['options']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True,
    )

    result = dict(
        changed=False,
        msg={},
    )

    path = module.params['path']
    stanza = module.params['stanza']
    attrs = module.params['attrs']
    state = module.params['state']

    result['changed'], result['msg'] = do_stanza(module, path, stanza, attrs, state)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
