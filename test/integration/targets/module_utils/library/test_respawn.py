#!/usr/bin/python

from __future__ import annotations


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module

HAS_SAMPLEPROJECTPY2 = True

try:
    import sample  # pylint: disable=unused-import
except ImportError:
    HAS_SAMPLEPROJECTPY2 = False


def main():
    module = AnsibleModule(
        argument_spec={
            'test_multiple_modules': {
                'type': 'bool',
                'default': False,
            },
        }
    )
    system_interpreters = ['/usr/bin/python3', '/usr/bin/python', '/usr/local/bin/python3.12', '/usr/local/bin/python3.11']
    test_multiple_modules = module.params['test_multiple_modules']

    if not HAS_SAMPLEPROJECTPY2:
        interpreter = probe_interpreters_for_module(system_interpreters, 'sample')
        if not interpreter or has_respawned():
            module.fail_json(f'unable to find sample; tried {system_interpreters}')
        respawn_module(interpreter)

    if test_multiple_modules:
        # Check that multiple module names are supported by probe_interpreters_for_module
        interpreter = probe_interpreters_for_module(system_interpreters, 'os', 're')
        if not interpreter:
            module.fail_json(f'unable to find yaml or json; tried {system_interpreters}')

    module.exit_json(changed=True)


if __name__ == "__main__":
    main()
