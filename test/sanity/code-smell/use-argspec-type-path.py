#!/usr/bin/env python

import re
import sys


def main():
    skip = set([
        # add legitimate uses of expanduser to the following list
        'lib/ansible/modules/cloud/lxc/lxc_container.py',
        'lib/ansible/modules/cloud/rackspace/rax_files_objects.py',
        'lib/ansible/modules/database/mongodb/mongodb_parameter.py',
        'lib/ansible/modules/database/mongodb/mongodb_user.py',
        'lib/ansible/modules/database/postgresql/postgresql_db.py',
        'lib/ansible/modules/files/synchronize.py',
        'lib/ansible/modules/source_control/git.py',
        'lib/ansible/modules/system/puppet.py',
        'lib/ansible/modules/utilities/logic/async_status.py',
        'lib/ansible/modules/utilities/logic/async_wrapper.py',
        'lib/ansible/modules/web_infrastructure/ansible_tower/tower_host.py',
        'lib/ansible/modules/web_infrastructure/ansible_tower/tower_group.py',
        'lib/ansible/modules/web_infrastructure/jenkins_plugin.py',
        'lib/ansible/modules/cloud/vmware/vmware_deploy_ovf.py',
        # fix uses of expanduser in the following modules and remove them from the following list
        'lib/ansible/modules/cloud/rackspace/rax.py',
        'lib/ansible/modules/cloud/rackspace/rax_scaling_group.py',
        'lib/ansible/modules/files/archive.py',
        'lib/ansible/modules/files/find.py',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        with open(path, 'r') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'(expanduser)', text)

                if match:
                    print('%s:%d:%d: use argspec type="path" instead of type="str" to avoid use of `expanduser`' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
