from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    m = AnsibleModule({})
    m.warn("Hello\r\nNew\rAnsible\nWorld")
    m.exit_json()


if __name__ == '__main__':
    main()
