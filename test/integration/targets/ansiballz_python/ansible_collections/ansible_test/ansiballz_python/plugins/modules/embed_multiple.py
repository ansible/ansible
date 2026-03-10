#!/usr/bin/python

from __future__ import annotations

ANSIBLE_EMBED = (
    ('ansible_collections.ansible_test.ansiballz_python.plugins.module_utils', 'embed_this.py'),
    ('ansible_collections.ansible_test.ansiballz_python.plugins.module_utils', 'embed_that.py'),
)

from importlib.resources import files
from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    ac = files('ansible_collections.ansible_test.ansiballz_python.plugins.module_utils')

    for embed in ('embed_this.py', 'embed_that.py'):
        if not ac.joinpath(embed).is_file():
            module.fail_json(msg='missing embed file')

    module.exit_json(exists=True)


if __name__ == '__main__':
    main()
