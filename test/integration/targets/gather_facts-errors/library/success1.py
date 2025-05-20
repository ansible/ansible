from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    module = AnsibleModule({})
    module.exit_json()


if __name__ == '__main__':
    main()
