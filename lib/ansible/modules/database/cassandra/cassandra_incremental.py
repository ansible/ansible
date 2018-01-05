#!/usr/bin/python
# -*- coding: utf-8 -*-

# 2017 Rhys Campbell <rhys.james.campbell@googlemail.com>
# Based on the group module by  Stephen Fromm <sfromm@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cassandra_backup
author: "Rhys Campbell (rhys.james.campbell@googlemail.com)"
version_added: "2.3.2.0"
short_description: Enable and disable the incremental backup feature
requirements: [ nodetool ]
description:
    - Enable and disable incremental backup feature via playbook
options:
    host:
        description:
          - Hostname / ip address of Cassandra node instance
        required: false
        default: localhost
    port:
      description:
        - Remote jmx agent port number
      required: False
      default: 7199
   password:
     description:
       - Remote jmx agent password
     required: false
     default: null
   passwordFile:
     description:
       - Path to the JMX password file
     required: false
     default: null
   username:
     description:
       - Remote jmx agent username
     required: false
     default: null
   incremental:
     description:
       - Enables and disables the incremental backup feature
     required: true
     choices [ true, false ]
   nodetool_path:
     description:
       - The path to nodetool
     required: false
     default: null
'''

LOCAL_TESTING = '''
1. Basic test
#############
cat << EOF > /tmp/args.json
{
    "ANSIBLE_MODULE_ARGS": {
	    "nodetool_path": "/Users/rhys1/dse/bin",
	    "incremental": false
    }
}
EOF

python ./lib/ansible/modules/database/cassandra/cassandra_incremental.py /tmp/args.json

cat << EOF > /tmp/args.json
{
    "ANSIBLE_MODULE_ARGS": {
	    "nodetool_path": "/Users/rhys1/dse/bin",
	    "incremental": true
    }
}
EOF

python ./lib/ansible/modules/database/cassandra/cassandra_incremental.py /tmp/args.json

'''

EXAMPLES = '''
# Enable the incremental backup feature
- cassandra_snapshot:
    username: admin
    password: secret
    incremental: true
# Disable the incremental backup feature
- cassandra_snapshot:
    username: admin
    password: secret
    incremental: false
'''

from ansible.module_utils.basic import AnsibleModule, load_platform_subclass


class NodeToolCmd(object):
    """
    This is a generic NodeToolCmd class for building nodetool commands
    """

    def __init__(self, module):
        self.module                 = module
        self.host                   = module.params['host']
        self.port                   = module.params['port']
        self.password               = module.params['password']
        self.passwordFile           = module.params['passwordFile']
        self.username               = module.params['username']
        self.nodetool_path          = module.params['nodetool_path']
        self.debug                  = module.params['debug']

    def execute_command(self, cmd):
        return self.module.run_command(cmd)

    def nodetool_cmd(self, sub_command):
        if self.nodetool_path is not None and not self.nodetool_path.endswith('/'):
            self.nodetool_path += '/'
        cmd = "{0}nodetool --host {1} --port {2}".format(self.nodetool_path,
                                                         self.host,
                                                         self.port)
        if self.username is not None:
            cmd += " --username {0}".format(self.username)
            if self.passwordFile is not None:
                cmd += " --passwordFile {0}".format(self.passwordFile)
            else:
                cmd += " --password '{0}'".format(self.password)
        # The thing we want nodetool to execute
        cmd += " {0}".format(sub_command)
        if self.debug:
            print(cmd)
        return self.execute_command(cmd)

class NodeToolIncrementalBackup(NodeToolCmd):

    """
    Inherits from the NodeToolCmd class. Adds the following methods;

        - check_incremental_enabled
        - enable_incremental
        - disable_incremental
    """

    def check_incremental_enabled(self):
        return self.nodetool_cmd("statusbackup")

    def enable_incremental(self):
        return self.nodetool_cmd("enablebackup")

    def disable_incremental(self):
        return self.nodetool_cmd("disablebackup")

def main():
    module = AnsibleModule(
        argument_spec = dict(
            host=dict(type='str', default='localhost'),
            port=dict(type='int', default=7199),
            password=dict(type='str', no_log=True),
            passwordFile=dict(type='str', no_log=True),
            username=dict(type='str'),
            incremental=dict(choices=[True, False], type='bool', required=True),
            nodetool_path=dict(type='str', default=None, required=False),
            debug=dict(type='bool', default=False, required=False),
        ),
        supports_check_mode=True
    )

    n = NodeToolIncrementalBackup(module)

    rc = None
    out = ''
    err = ''
    result = {}
    changed = False

    (rc, out, err) = n.check_incremental_enabled()

    if module.params['incremental'] == False:

        if rc != 0:
            module.fail_json(name="statusbackup", msg=err)
        if module.check_mode:
            if out == "running":
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)
        if out.strip() == "running":
            (rc, out, err) = n.disable_incremental()
            changed = True
        if rc != 0:
            module.fail_json(name="disablebackup", msg=err)

    elif module.params['incremental'] == True:

        if rc != 0:
            module.fail_json(name="statsbackup", msg=err)
        if module.check_mode:
            if out == "not running":
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)
        if out.strip() == "not running":
            (rc, out, err) = n.enable_incremental()
            changed = True
        if rc is not None and rc != 0:
            module.fail_json(name="enablebackup", msg=err)

    result['changed'] = changed
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err
    module.exit_json(**result)


if __name__ == '__main__':
    main()
