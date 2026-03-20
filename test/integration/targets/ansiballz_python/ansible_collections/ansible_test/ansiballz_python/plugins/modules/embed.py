#!/usr/bin/python

from __future__ import annotations

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.embed import EmbedManager

# multiple assignments are okay
foo = bar = baz = other = EmbedManager.embed("..module_utils", "embed_this.py")

# reassignment is okay
baz = EmbedManager.embed("..module_utils", "embed_this.py")

# even reassignment to a different embed
other = EmbedManager.embed("..module_utils", "embed_that.py")


# an unrelated function we should ignore calls to
def embed() -> int:
    return 42


# an unrelated class we should ignore calls to
class NotEmbedManager:
    def embed(self) -> int:
        return 42


# a bunch of other assignment forms that should be ignored (code coverage)
a1 = 123
a2 = type(123)
a3 = os.path.abspath('/')
a4 = EmbedManager.mro()
a5 = EmbedManager.mro
a6 = embed()
a7 = NotEmbedManager().embed()


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    assert foo is bar, "multiple assignments did not have reference equality"
    assert foo == bar == baz, "reaasigment was not equivalent"

    with foo.path_context_manager as path:
        assert "embedded content for embed_this.py" in path.read_text(), "embedded content mismatch"

    with other.path_context_manager as path:
        assert "embedded content for embed_that.py" in path.read_text(), "reassigned embedded content mismatch"

    module.exit_json(passed=True)


def non_top_level():
    EmbedManager.embed()  # bogus call, but shouldn't trip since it's not top-level


if __name__ == '__main__':
    main()
