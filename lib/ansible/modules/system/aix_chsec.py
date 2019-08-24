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
version_added: '2.9'
description:
- Modify stanza attributes to AIX config files using the C(chsec) command.
options:
  file:
    description:
      - File path to the stanza file.
    type: path
    required: true
    aliases: [ path, dest ]
  stanza:
    description:
    - Name of stanza.
    type: str
    required: true
  attrs:
    description:
    - A list of key/value pairs
    type: raw
    aliases: [ options ]
  state:
    description:
    - If set to C(present) all given attrs values will be set.
    - If set to C(absent) all attrs provided will be un-set, regardless of value provided.
    - NB, this does not remove the entire stanza, only the provided attrs will be removed.
    - To remove a single attribute from the stanza set to C(present) and set key to an empty value (key=).
    - All rules, allowed file-stanza combos, and allowed files for the AIX C(chsec) command apply here.
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
    file: /etc/security/user
    stanza: ldapuser
    attrs:
      SYSTEM: LDAP
      registry: LDAP
    state: present
- name: Change login times for user
  aix_chsec:
    file: /etc/security/user
    stanza: ldapuser
    attrs:
      logintimes: :0800-1700
    state: present
- name: Remove registry attribute from stanza
  aix_chsec:
    file: /etc/security/user
    stanza: ldapuser
    attrs:
      SYSTEM: LDAP
      registry: null
    state: present
'''

RETURN = r''' # '''

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
    if isinstance(attrs, str):
        # Assume we have this:
        #   "SYSTEM=LDAP,registry=LDAP"
        # Split it into a list of strings, like this:
        #   [ "SYSTEM=LDAP", "registry=LDAP" ]
        attrs = [x.strip() for x in attrs.split(',')]
    if isinstance(attrs, list):
        # Assume it's a list of key=values, so
        #   [ "SYSTEM=LDAP", "registry=LDAP" ]
        # Take each attr and split it into a key:value dict and update return_dict
        #   { "SYSTEM": "LDAP", "registry":"LDAP" }
        for element in attrs:
            k, v = element.split('=')
            return_dict.update({k: v})
    if isinstance(attrs, dict):
        return_dict.update(attrs)
    return return_dict


def set_attr_value(module, filename, stanza, attr, value):
    '''Sets the selected file/stanza/attr=value.  Only returns True '''
    chsec_command = module.get_bin_path('chsec', required=True)
    cmd = [chsec_command, '-f', filename, '-s', stanza, '-a', '='.join(map(str, [attr, value]))]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run chsec command: ' + ' '.join(cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    return True


def get_current_attr_value(module, filename, stanza, attr):
    ''' Given single filename/stanza/attr, returns str(attr_value)'''
    lssec_command = module.get_bin_path('lssec', required=True)
    cmd = [lssec_command, '-c', '-f', filename, '-s', stanza, '-a', attr]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run lssec command: ' + ' '.join(cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    # Strip off whitespace and double-quotation marks that are sometimes added
    lssec_out = stdout.splitlines()[1].split(':')[1].strip('\\\"\n ')
    return lssec_out


def do_stanza(module, filename, stanza, attrs, state):
    ''' Returns (bool(changed), dict(msg)) '''
    attrs = attrs2dict(attrs)
    return_msg = {}
    changed = 0

    for attr, tgt_value in attrs.items():
        if state == 'absent':
            # 'absent' sets all of the given attrs to None, regardless of given value
            tgt_value = ''
        # Start our msg dict for this key+value
        msg = {
            'desired_value': tgt_value,
            'status': 'unchanged',
        }
        curr_value = get_current_attr_value(module, filename, stanza, attr)
        msg.update({
            'existing_value': curr_value,
        })
        if curr_value != tgt_value:
            # Change the value of the attr
            if module.check_mode:
                msg.update({"check_mode": True})
            else:
                set_attr_value(module, filename, stanza, attr, tgt_value)
            msg.update({
                # 'outgoing_value': tgt_value,
                'status': 'changed',
            })
            changed += 1
        return_msg[attr] = msg
    return (bool(changed), return_msg)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            file=dict(type='path', required=True, aliases=['dest', 'path']),
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

    file = module.params['file']
    stanza = module.params['stanza']
    attrs = module.params['attrs']
    state = module.params['state']

    result['changed'], result['msg'] = do_stanza(module, file, stanza, attrs, state)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
