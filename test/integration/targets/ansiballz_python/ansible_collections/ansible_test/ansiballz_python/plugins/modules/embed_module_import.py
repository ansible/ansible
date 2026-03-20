#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

# import the embed module (no alias)
from ansible.module_utils import embed

e1 = embed.EmbedManager.embed('..module_utils', 'embed_this.py')


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    with e1.path_context_manager as path:
        assert "embedded content for embed_this.py" in path.read_text(), "content mismatch"

    module.exit_json(passed=True)


if __name__ == '__main__':
    main()
