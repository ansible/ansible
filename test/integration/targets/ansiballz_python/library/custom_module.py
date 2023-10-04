#!/usr/bin/python

from __future__ import annotations

from ..module_utils.basic import AnsibleModule  # pylint: disable=relative-beyond-top-level
from ..module_utils.custom_util import forty_two  # pylint: disable=relative-beyond-top-level


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    module.exit_json(answer=forty_two())


if __name__ == '__main__':
    main()
