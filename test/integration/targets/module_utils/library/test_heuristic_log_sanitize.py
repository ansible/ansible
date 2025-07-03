#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils import basic
from ansible.module_utils.basic import AnsibleModule

heuristic_log_sanitize = basic.heuristic_log_sanitize


def heuristic_log_sanitize_spy(*args, **kwargs):
    heuristic_log_sanitize_spy.return_value = heuristic_log_sanitize(*args, **kwargs)
    return heuristic_log_sanitize_spy.return_value


basic.heuristic_log_sanitize = heuristic_log_sanitize_spy


def main():

    module = AnsibleModule(
        argument_spec={
            'data': {
                'type': 'str',
                'required': True,
            }
        },
    )

    # This test module is testing that the data that will be used for logging
    # to syslog is properly sanitized when it includes URLs that contain a password.
    #
    # As such, we build an expected sanitized string from the input, to
    # compare it with the output from heuristic_log_sanitize.
    #
    # To test this in the same way that modules ultimately operate this test
    # monkeypatches ansible.module_utils.basic to store the sanitized data
    # for later inspection.
    data = module.params['data']
    left = data.rindex(':') + 1
    right = data.rindex('@')
    expected = data[:left] + '********' + data[right:]

    sanitized = heuristic_log_sanitize_spy.return_value
    if sanitized != expected:
        module.fail_json(msg='Invalid match', expected=expected, sanitized=sanitized)
    module.exit_json(match=True)


if __name__ == '__main__':
    main()
