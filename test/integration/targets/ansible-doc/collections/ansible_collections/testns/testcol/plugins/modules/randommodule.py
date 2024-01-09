#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = r'''
---
module: randommodule
short_description: A random module
description:
    - A random module.
    - See O(foo.bar.baz#role:main:foo=bar) for how this is used in the P(foo.bar.baz#role)'s C(main) entrypoint.
    - See L(the docsite,https://docs.ansible.com/ansible-core/devel/) for more information on ansible-core.
    - This module is not related to the M(ansible.builtin.copy) module. HORIZONTALLINE You might also be interested
      in R(ansible_python_interpreter, ansible_python_interpreter).
    - Sometimes you have M(broken markup) that will result in error messages.
author:
    - Ansible Core Team
version_added: 1.0.0
deprecated:
    alternative: Use some other module
    why: Test deprecation
    removed_in: '3.0.0'
options:
    test:
        description: Some text. Consider not using O(ignore:foo=bar).
        type: str
        version_added: 1.2.0
    sub:
        description: Suboptions. Contains O(sub.subtest), which can be set to V(123). You can use E(TEST_ENV) to set this.
        type: dict
        suboptions:
            subtest:
                description: A suboption. Not compatible to O(ansible.builtin.copy#module:path=c:\\foo\(1\).txt).
                type: int
                version_added: 1.1.0
        # The following is the wrong syntax, and should not get processed
        # by add_collection_to_versions_and_dates()
        options:
            subtest2:
                description: Another suboption. Useful when P(ansible.builtin.shuffle#filter) is used with value V([a,b,\),d\\]).
                type: float
                version_added: 1.1.0
        # The following is not supported in modules, and should not get processed
        # by add_collection_to_versions_and_dates()
        env:
            - name: TEST_ENV
              version_added: 1.0.0
              deprecated:
                alternative: none
                why: Test deprecation
                removed_in: '2.0.0'
                version: '2.0.0'
extends_documentation_fragment:
    - testns.testcol2.module
seealso:
    - module: ansible.builtin.ping
    - module: ansible.builtin.uri
      description: Use this to fetch an URI
    - module: testns.testcol.test
    - module: testns.testcol.fakemodule
      description: A fake module
    - link: https://docs.ansible.com
      name: Ansible docsite
      description: See also the Ansible docsite.
    - ref: foo_bar
      description: Some foo bar.
notes:
    - This is a note.
    - |-
      This is a multi-paragraph note.

      This is its second paragraph.
      This is just another line in the second paragraph.
      Eventually this will break into a new line,
      depending with which line width this is rendered.
'''

EXAMPLES = '''
'''

RETURN = r'''
z_last:
    description: A last result.
    type: str
    returned: success
    version_added: 1.3.0

m_middle:
    description:
        - This should be in the middle.
        - Has some more data.
        - Check out RV(m_middle.suboption) and compare it to RV(a_first=foo) and RV(community.general.foo#lookup:value).
    type: dict
    returned: success and 1st of month
    contains:
        suboption:
            description: A suboption.
            type: str
            choices: [ARF, BARN, c_without_capital_first_letter]
            version_added: 1.4.0

a_first:
    description: A first result. Use RV(a_first=foo\(bar\\baz\)bam).
    type: str
    returned: success
'''


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
