from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.datatag.tags import Deprecated


def main():
    mod = AnsibleModule(argument_spec={
        'sensitive_module_arg': dict(default='NO DISPLAY, sensitive arg to module', type='str', no_log=True),
    })

    result = {
        'good_key': 'good value',
        'deprecated_key': Deprecated(msg="`deprecated_key` is deprecated, don't use it!", removal_version='1.2.3').tag('deprecated value'),
        'sensitive_module_arg': mod.params['sensitive_module_arg'],
        'unmarked_template': '{{ ["me", "see", "not", "should"] | sort(reverse=true) | join(" ") }}',
        'changed': False
    }

    mod.exit_json(**result)


if __name__ == '__main__':
    main()
