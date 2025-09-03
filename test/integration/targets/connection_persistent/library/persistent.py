from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection


def main():
    module = AnsibleModule({})

    connection = Connection(module._socket_path)
    capabilities = module.from_json(connection.get_capabilities())
    module.exit_json(**capabilities)


if __name__ == '__main__':
    main()
