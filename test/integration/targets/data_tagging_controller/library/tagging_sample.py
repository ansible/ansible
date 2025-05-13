from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.datatag import deprecate_value

METADATA = """
schema_version: 1
serialization_profile: modern
"""


def main():
    mod = AnsibleModule(argument_spec={
        'sensitive_module_arg': dict(default='THIS VALUE WAS NO_LOG IN A MODULE AND SHOULD NOT BE SEEN', type='str', no_log=True),
    })

    something_old_value = 'an old thing'
    # Deprecated needs args; tag the value and store it
    something_old_value = deprecate_value(something_old_value, "`something_old` is deprecated, don't use it!", version='9.9999')

    result = {
        'something_old': something_old_value,
        # send the module param back to core
        'sensitive_module_arg': mod.params['sensitive_module_arg'],
        # rendering templates from modules is a no-no, core does not trust anything by default
        'untrusted_template': '{{ ["me", "see", "not", "should"] | sort(reverse=true) | join(" ") }}',
        'changed': False
    }

    mod.exit_json(**result)


if __name__ == '__main__':
    main()
