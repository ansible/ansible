#!/usr/bin/python
# -*- coding: utf-8 -*-


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: geo_rep (actions module for geo-replication)

short_description: module to start and stop of geo-replication session in gluster enabled hosts

version_added: "2.4"

description:
    - "module helps to start and stop a geo-rep session in gluster enabled hosts"

options:
    start:
        description: starts a geo-rep session with the credentials gained from the status action in the georep_facts module in the gluster enabled hosts.
    stop:
        description: stops a geo-rep session with the credentials gained from the status action in the georep_facts module in the gluster enabled hosts.
author:
    - Ashmitha Ambastha (@ashmitha7)
'''
EXAMPLES = '''
#the module will get information such as volume names, nodes and slave user name from georep_facts module and then run the tasks to
#start and stop geo-rep sessions.

# If the module is used to ONLY start a geo-rep session
# then the playbook will have a task like below,
 - name: starting geo-rep status
    geo_rep: action=start
             mastervol=master_volume
             slavevol=10.11.77.12:slave_volume
             georepuser=root
             force=yes

# If the module is used to ONLY stop a geo-rep session
# then the playbook will have a task like below,
- name: stopping geo-rep session
    geo_rep: action=stop
             mastervol=master_volume
             slavevol=10.11.77.12:slave_volume
             georepuser=root
             force=yes
'''
RETURN = '''
MASTER NODE- <master volume IP>
MASTER VOL- <master_volume name>
MASTER BRICK- <for example, /gluster-bricks/b1/b1>
SLAVE USER- <for example,root>
SLAVE-<for example, ssh://10.11.77.12::volume1>
'''

import sys
import re
import shlex
from subprocess import Popen
import subprocess
import os


from collections import OrderedDict
from ansible.module_utils.basic import *
from ast import literal_eval

class GeoRep(object):
    def __init__(self, module):
        self.module = module
        self.action = self._validated_params('action')
        self.gluster_georep_ops()

    def get_playbook_params(self, opt):
        return self.module.params[opt]

    def _validated_params(self, opt):
        value = self.get_playbook_params(opt)
        if value is None:
            msg = "Please provide %s option in the playbook!" % opt
            self.module.fail_json(msg=msg)
        return value

    def gluster_georep_ops(self):

        mastervol = self._validated_params('mastervol')
        slavevol = self._validated_params('slavevol')
        slavevol = self.check_pool_exclusiveness(mastervol, slavevol)

        if self.action in ['start','stop']:
            force = self._validated_params('force')
            force = 'force' if force == 'yes' else ' '

        if self.action == 'start':
            rc, output, err = self.call_gluster_cmd(' volume', ' geo-replication ',
                    mastervol, slavevol,self.action,force)
            self._get_output(rc, output, err)

        if self.action == 'stop' and self.user == 'root':
            rc,output,err = self.call_gluster_cmd(' volume',' geo-replication ',
                mastervol,slavevol,
                self.action,force)
            self._get_output(rc,output,err)

    def call_gluster_cmd(self, *args, **kwargs):
        params = ' '.join(opt for opt in args)
        key_value_pair = ' '.join(' %s %s ' % (key, value)
                for key, value in kwargs)
        return self._run_command('gluster', ' ' + params + ' ' + key_value_pair )

    def _get_output(self, rc, output, err):
        carryon = True if self.action in  ['stop'] else False
        changed = 0 if (carryon and rc) else 1
        if self.action in ['stop'] and (
                self.user == 'root' and changed == 0):
            return
        if not rc or carryon:
            self.module.exit_json(stdout=output, changed=changed)
        else:
            self.module.fail_json(msg=err)

    def _run_command(self, op, opts):
        cmd = self.module.get_bin_path(op, True) + opts
        return self.module.run_command(cmd)

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
        action=dict(required=True, choices=['start',
            'stop']),
        mastervol=dict(),
        slavevol=dict(),
        georepuser=dict(),
        force=dict(),
        ),
    )
    GeoRep(module)

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

def main():
    run_module()

if __name__ == '__main__':
    main()

