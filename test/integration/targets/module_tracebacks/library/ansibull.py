from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


class Die(BaseException):
    """Raise an exception that is unlikely to be caught (and will thus catastrophically exit the process)."""


def main():
    module = AnsibleModule(
        argument_spec=dict(
            errors=dict(type='list', elements='str', default=[]),
            trigger_unhandled_exception=dict(type='str', default=''),
            return_from_main=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        mutually_exclusive=[['errors', 'trigger_unhandled_exception', 'return_from_main']],
    )

    if module.params['return_from_main']:
        return

    if trigger_unhandled_exception := module.params['trigger_unhandled_exception']:
        raise Die(trigger_unhandled_exception)

    if errors := module.params['errors']:
        raise_exceptions(errors)

    result = dict()

    module.exit_json(**result)


def raise_exceptions(exceptions: list[str]) -> None:
    if len(exceptions) > 1:
        try:
            raise_exceptions(exceptions[1:])
        except Exception as ex:
            raise Exception(exceptions[0]) from ex

    raise Exception(exceptions[0])


if __name__ == '__main__':
    main()
