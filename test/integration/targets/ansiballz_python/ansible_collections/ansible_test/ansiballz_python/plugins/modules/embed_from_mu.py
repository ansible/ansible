#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.mu_with_embed import e1, e2  # pylint: disable=relative-beyond-top-level


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    with e1.path_context_manager as path:
        assert "embedded content for embed_this.py" in path.read_text(), "e1 resource content mismatch"

    with e2.path_context_manager as path:
        assert "embedded content for embed_that.py" in path.read_text(), "e2 resource content mismatch"

    module.exit_json(passed=True)


if __name__ == '__main__':
    main()
