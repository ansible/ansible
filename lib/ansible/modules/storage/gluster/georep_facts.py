#!/usr/bin/python
# -*- coding: utf-8 -*-


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: georep_facts

short_description: module to get status of a geo-replication session.

version_added: "2.4"

description:
    - "module helps to get status and volume name of geo-replication session in gluster enabled hosts"

options:
    status:
        description:to get the status of geo replication sessions in the hosts. With the status options we get information such as the
                    master node, slave user name and the names of the master and slave volumes etc.
        required: true
author:
    - Ashmitha Ambastha (@ashmitha7)
'''
EXAMPLES = '''
# To get status
 - name: get status of a geo-rep session
   geo_rep: action=status

#the module will get information such as volume names, nodes and slave user name from action=status task and then run the tasks to
#start and stop geo-rep sessions.


'''
RETURN = '''
MASTER VOL- <master_volume name>
SLAVE-<for example, ssh://10.11.77.12::volume1>
STATUS- <for example, active/passive,stopped>
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
        if self.action == 'status':
            rc, output, err = self.call_gluster_cmd('volume ','geo-replication ', self.action)
            self._get_output(rc, output, err)
        if self.action == 'get_vol_data':
            return self.gluster_status_vol()

    def gluster_status_vol(self):
        cmd_str="gluster volume geo-replication status --xml"
        try:
            cmd = Popen(
                shlex.split(cmd_str),
                stdin=open(os.devnull, "r"),
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                close_fds=True
            )
            op, err = cmd.communicate()
            info = ElementTree.fromstring(op)
            it = info.iter("volume")
            georep_dict = {}
            try:
                while True:
                    volume = it.next()
                    # georep_dict[volume.find("name").text] = []
                    vol_sessions = volume.iter("sessions")
                    try:
                        while True:
                            vol_session = vol_sessions.next()
                            session_it = vol_session.iter("session")
                            try:
                                while True:
                                    session = session_it.next()
                                    session_slave_val = session.find("session_slave").text
                                    georep_dict[volume.find("name").text] = session_slave_val
                            except StopIteration:
                                pass
                    except StopIteration:
                        pass
            except StopIteration:
                pass
            # print georep_dict
            for k,v in georep_dict.iteritems():
                s_value = v.split("//")[1].split(":")
                slave_vol = '::'.join([s_value[0],s_value[2]])
                # print slave_vol
                dict_georep={}
                dict_georep[k]=slave_vol
                self.module.exit_json(rc=0,msg=dict_georep)
        except (subprocess.CalledProcessError, ValueError):
            print "Error....."

    def call_gluster_cmd(self, *args):
        params = ' '.join(opt for opt in args)
        return self._run_command('gluster', ' ' + params )

    def _get_output(self, rc, output, err):
        carryon = False
        changed = 0 if (carryon and rc) else 1
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
        action=dict(required=True, choices=['status','get_vol_data']),
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

