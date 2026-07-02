from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.shared_deprecation import get_deprecation_kwargs, get_deprecated_value


def main() -> None:
    m = AnsibleModule({})
    m.warn("This is a warning.")

    for deprecate_kw in get_deprecation_kwargs():
        m.deprecate(**deprecate_kw)  # pylint: disable=ansible-deprecated-no-version

    m.exit_json(deprecated_result=get_deprecated_value())


if __name__ == '__main__':
    main()
