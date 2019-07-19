# FIXME: this style (full module import via from) doesn't work yet from collections
# from ansible_collections.testns.testcoll.plugins.module_utils import secondary
import ansible_collections.testns.testcoll.plugins.module_utils.secondary


def thingtocall():
    return "thingtocall in base called " + ansible_collections.testns.testcoll.plugins.module_utils.secondary.thingtocall()
