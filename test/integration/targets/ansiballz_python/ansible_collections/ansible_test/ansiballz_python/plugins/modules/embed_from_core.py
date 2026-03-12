#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.embed import EmbedManager

embed_test = EmbedManager.embed('ansible.module_utils._embed', 'dnf.py')

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    with embed_test.path_context_manager as path:
        assert path.is_file(), "resource was missing"

    assert embed_test.python_module_ref == "ansible.module_utils._embed.dnf", "python_module_ref mismatched"

    module.exit_json(passed=True)


if __name__ == '__main__':
    main()
