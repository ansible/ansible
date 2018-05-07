#!/usr/bin/python

import os
from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', choices=['normal', 'exception', 'fail_json'], default='normal')
        )
    )

    if module._tmpdir_created:
        module.fail_json(msg="tmpdir should not have been created before calling it first")

    pre_tmpdir = module._tmpdir
    first_tmpdir = module.tmpdir
    second_tmpdir = module.tmpdir

    results = {
        "_tmpdir": pre_tmpdir,
        "tmpdir": first_tmpdir
    }

    if not module._tmpdir_created:
        module.fail_json(msg="_tmpdir_created should be True after calling tmpdir once")

    if not os.path.exists(first_tmpdir):
        module.fail_json(msg="tmpdir '%s' should exist" % first_tmpdir)

    if first_tmpdir != second_tmpdir:
        module.fail_json(msg="tmpdir should stay the same when getting the attribute, "
                             "first: '%s' != second: '%s'" % (first_tmpdir, second_tmpdir))

    action = module.params['action']
    if action == 'normal':
        module.exit_json(**results)
    elif action == 'exception':
        raise Exception(first_tmpdir)
    elif action == 'fail_json':
        module.fail_json(msg="fail_json was called", **results)


if __name__ == '__main__':
    main()
