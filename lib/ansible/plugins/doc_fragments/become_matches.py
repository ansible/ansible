:# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
        become_fail_match:
            version_added: '2.9'
            description: Strings to match to detect a privilege escalation failure
            required: False
            type: list
            ini:
              - section: become
                key: fail_match
            env:
              - name: ANSIBLE_BECOME_FAIL_MATCH
            vars:
              - name: ansible_fail_match
        become_missing_password_match:
            version_added: '2.9'
            description: Strings to match to detect a missing, but required,  password
            required: False
            type: list
            ini:
              - section: become
                key: missing_password_match
            env:
              - name: ANSIBLE_BECOME_MISSING_PASSWORD_MATCH
            vars:
              - name: ansible_missing_passowrd_match
    '''
