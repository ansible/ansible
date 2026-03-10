#!/usr/bin/python

from __future__ import annotations

ANSIBLE_EMBED = (('ansible.module_utils._embed', '__init__.py'),)

from importlib.resources import files
from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    ac = files('ansible.module_utils._embed')
    embed_test = ac.joinpath('__init__.py')

    if embed_test.is_file():
        module.exit_json(exists=True)

    module.fail_json(msg='missing embed file')


if __name__ == '__main__':
    main()
