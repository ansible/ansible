#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

# alias the EmbedManager type
from ansible.module_utils.embed import EmbedManager as _EmbedManager

e1 = _EmbedManager.embed('..module_utils', 'embed_this.py')


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    with e1.path_context_manager as path:
        assert "embedded content for embed_this.py" in path.read_text(), "content mismatch"

    module.exit_json(passed=True)


if __name__ == '__main__':
    main()
