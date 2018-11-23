#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aix_chsec

short_description: modify aix stanza files

version_added: "0.1"

description:
    - "adds stanzas to aix config files using the chsec command. see "man chsec" for additional infos"

options:
    path:
        description:
            - Path to the stanza file
        required: true
    stanza:
        description:
            - name of stanza
        required: true
    options:
         description:
             - comman separated key/value pairs eg. key=val,key=val
    state:
         description:
            - If set to C(absent) the whole stanza incl. all given options will be removed.
            - If set to C(present) stanza incl.options will be added.
            - To remove an option from the stanza set to C(present) and set key to an empty value (key=).
            - All rules/allowed file-stanza combos/allowed files for the chsec command also applies here, so once again, read "man chsec"!
         choices: [ absent, present ]
         default: present

extends_documentation_fragment:
    - files

author:
    - Christian Tremel (@flynn1973)
'''

EXAMPLES = '''
- name: add ldap user stanza
  aix_chsec:
    path: /etc/security/user
    stanza: ldapuser
    options: SYSTEM=LDAP,registry=LDAP
    state: present
    mode: 0644

- name: change login times for user
  aix_chsec:
    path: /etc/security/user
    stanza: ldapuser
    options: logintimes=:0800-1700
    state: present

- name: remove registry option from stanza 
  aix_chsec:
    path: /etc/security/user
    stanza: ldapuser
    options: SYSTEM=LDAP,registry=
    state: present
'''


from ansible.module_utils.basic import *



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
        rc, package_result, err = module.run_command(command)
        if rc != 0:
            module.fail_json(msg='Failed to run chsec command (present).', rc=rc, err=err)
        else:
            msg='stanza added'
            changed=True
    elif state == 'absent':
        # remove values from keys to enable chsec delete mode 
        command += [s[:1+s.find('=')] or s for s in options]
        rc, package_result, err = module.run_command(command)
        if rc != 0:
             module.fail_json(msg='Failed to run chsec command (absent).', rc=rc, err=err)
        else:
             msg='stanza removed'
             changed=True

    return (changed, msg)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest']),
            stanza=dict(type='str', required=True),
            options=dict(type='list', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present'])
        ),
        supports_check_mode=False,
    )

    path = module.params['path']
    stanza = module.params['stanza']
    options = module.params['options']
    state = module.params['state']

    (changed, msg) = do_stanza(module, path, stanza, options, state)


    results = dict(
        changed=changed,
        msg=msg,
        path=path
    )

    # Mission complete
    module.exit_json(**results)

if __name__ == '__main__':
    main()
