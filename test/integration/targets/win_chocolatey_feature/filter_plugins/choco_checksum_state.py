from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def choco_checksum_state(value):
    return [i for i in value if i.startswith("checksumFiles|")][0].split("|")[1] == "Enabled"


class FilterModule(object):

    def filters(self):
        return {
            'choco_checksum_state': choco_checksum_state
        }
