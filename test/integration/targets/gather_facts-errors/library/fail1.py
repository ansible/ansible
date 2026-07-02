from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    module = AnsibleModule({})
    module.fail_json("the fail1 module went bang")


if __name__ == '__main__':
    main()
