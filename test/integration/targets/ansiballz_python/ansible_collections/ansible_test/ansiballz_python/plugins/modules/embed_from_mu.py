#!/usr/bin/python

from __future__ import annotations

from importlib.resources import files
from ansible.module_utils.basic import AnsibleModule
from ..module_utils.mu_with_embed import some_value  #pylint: disable=relative-beyond-top-level


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    assert some_value == 42

    ac = files('ansible_collections.ansible_test.ansiballz_python.plugins.module_utils')
    embed_test = ac.joinpath('embed_this.py')

    if embed_test.is_file():
        module.exit_json(exists=True)

    module.fail_json(msg='missing embed file')


if __name__ == '__main__':
    main()
