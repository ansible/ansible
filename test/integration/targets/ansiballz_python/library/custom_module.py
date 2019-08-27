#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ..module_utils.basic import AnsibleModule
from ..module_utils.custom_util import forty_two


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    module.exit_json(answer=forty_two())


if __name__ == '__main__':
    main()
