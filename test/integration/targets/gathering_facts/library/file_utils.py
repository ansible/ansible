from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts.utils import (
    get_file_content,
    get_file_lines,
    get_mount_size,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            test=dict(type='str', default='strip'),
            touch_file=dict(type='str', default='/dev/null'),
            line_sep_file=dict(type='str', default='/dev/null'),
            line_sep_sep=dict(type='str', default='\n'),
        )
    )

    test = module.params['test']
    facts = {}

    if test == 'strip':
        etc_passwd = get_file_content('/etc/passwd')
        etc_passwd_unstripped = get_file_content('/etc/passwd', strip=False)
        facts['etc_passwd_newlines'] = etc_passwd.count('\n')
        facts['etc_passwd_newlines_unstripped'] = etc_passwd_unstripped.count('\n')

    elif test == 'default':
        path = module.params['touch_file']
        facts['touch_default'] = get_file_content(path, default='i am a default')

    elif test == 'line_sep':
        path = module.params['line_sep_file']
        sep = module.params['line_sep_sep']
        facts['line_sep'] = get_file_lines(path, line_sep=sep)

    elif test == 'invalid_mountpoint':
        facts['invalid_mountpoint'] = get_mount_size('/doesnotexist')

    result = {
        'changed': False,
        'ansible_facts': facts,
    }

    module.exit_json(**result)


main()
