#!/usr/bin/python
# https://github.com/ansible/ansible/issues/64664
# https://github.com/ansible/ansible/issues/64479

from __future__ import annotations

import sys

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule({})

    this_module = sys.modules[__name__]
    module.exit_json(
        failed=not getattr(this_module, 'AnsibleModule', False)
    )


if __name__ == '__main__':
    main()
