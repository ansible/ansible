from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.warn("This is a warning from a module")
    module.deprecate("This is a deprecation from a module", version="9.9")

    module.exit_json()


if __name__ == '__main__':
    main()
