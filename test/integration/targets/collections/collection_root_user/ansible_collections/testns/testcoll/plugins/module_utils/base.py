from __future__ import annotations

from ansible_collections.testns.testcoll.plugins.module_utils import secondary
import ansible_collections.testns.testcoll.plugins.module_utils.secondary


def thingtocall():
    if secondary != ansible_collections.testns.testcoll.plugins.module_utils.secondary:
        raise Exception()

    return "thingtocall in base called " + ansible_collections.testns.testcoll.plugins.module_utils.secondary.thingtocall()
