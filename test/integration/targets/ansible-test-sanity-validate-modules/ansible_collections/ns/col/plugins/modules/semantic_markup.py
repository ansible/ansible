#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r'''
module: semantic_markup
short_description: Test semantic markup
description:
  - Test semantic markup.
  - RV(does.not.exist=true).

author:
  - Ansible Core Team

options:
  foo:
    description:
      - Test.
    type: str

  a1:
    description:
      - O(foo)
      - O(foo=bar)
      - O(foo[1]=bar)
      - O(ignore:bar=baz)
      - O(ansible.builtin.copy#module:path=/)
      - V(foo)
      - V(bar(1\\2\)3)
      - V(C(foo\)).
      - E(env(var\))
      - RV(ansible.builtin.copy#module:backup)
      - RV(bar=baz)
      - RV(ignore:bam)
      - RV(ignore:bam.bar=baz)
      - RV(bar).
      - P(ansible.builtin.file#lookup)
    type: str

  a2:
    description: V(C\(foo\)).
    type: str

  a3:
    description: RV(bam).
    type: str

  a4:
    description: P(foo.bar#baz).
    type: str

  a5:
    description: P(foo.bar.baz).
    type: str

  a6:
    description: P(foo.bar.baz#woof).
    type: str

  a7:
    description: E(foo\(bar).
    type: str

  a8:
    description: O(bar).
    type: str

  a9:
    description: O(bar=bam).
    type: str

  a10:
    description: O(foo.bar=1).
    type: str

  a11:
    description: Something with suboptions.
    type: dict
    suboptions:
      b1:
        description:
          - V(C\(foo\)).
          - RV(bam).
          - P(foo.bar#baz).
          - P(foo.bar.baz).
          - P(foo.bar.baz#woof).
          - E(foo\(bar).
          - O(bar).
          - O(bar=bam).
          - O(foo.bar=1).
        type: str
'''

EXAMPLES = '''#'''

RETURN = r'''
bar:
  description: Bar.
  type: int
  returned: success
  sample: 5
'''

from ansible.module_utils.basic import AnsibleModule


if __name__ == '__main__':
    module = AnsibleModule(argument_spec=dict(
        foo=dict(),
        a1=dict(),
        a2=dict(),
        a3=dict(),
        a4=dict(),
        a5=dict(),
        a6=dict(),
        a7=dict(),
        a8=dict(),
        a9=dict(),
        a10=dict(),
        a11=dict(type='dict', options=dict(
            b1=dict(),
        ))
    ))
    module.exit_json()
