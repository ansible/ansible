#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

# alias the embed module
from ansible.module_utils import embed as _aliasedembed

e1 = _aliasedembed.EmbedManager.embed('..module_utils', 'embed_this.py')


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    with e1.path_context_manager as path:
        assert "embedded content for embed_this.py" in path.read_text(), "content mismatch"

    module.exit_json(passed=True)


if __name__ == '__main__':
    main()
