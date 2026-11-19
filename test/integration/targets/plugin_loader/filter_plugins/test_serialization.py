from __future__ import annotations

import copy


def deepcopy(data):
    return copy.deepcopy(data)


class FilterModule(object):
    def filters(self):
        return {
            'deepcopy': deepcopy,
        }
