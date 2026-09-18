from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

import time


def main() -> None:
    module = AnsibleModule({'gather_timeout': {'type': int}})
    timeout = module.params['gather_timeout'] or 5
    time.sleep(timeout - 2)
    module.exit_json()


if __name__ == '__main__':
    main()
