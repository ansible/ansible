#!/usr/bin/python

from __future__ import annotations

ANSIBLE_EMBED = (('ansible_collections.ansible_test.ansiballz_python.plugins.module_utils', 'embed_test.py'),)

from importlib.resources import files
from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    ac = files('ansible_collections.ansible_test.ansiballz_python.plugins.module_utils')
    embed_test = ac.joinpath('embed_test.py')

    if embed_test.is_file():
        module.exit_json(exists=True)

    module.fail_json(msg='missing embed file')


if __name__ == '__main__':
    main()
