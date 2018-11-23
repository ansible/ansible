#!/usr/bin/python
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}


DOCUMENTATION = '''
---
author: "Bob ter Hark (@krahb)"
module: 'aix_update_all'
short_description: Update all
description:
    - Updates all
options:
  nfs_server:
    description:
    - name of the nfs server
    default: { NIM_MASTER }
  nfs_share:
    description:
    - name of the remote directory, if not given, it will be "/export/nim/aix<OSVER>/lpp_new"
      where OSVER is  OSVERSION + TL + -SP
      fi. /export/nim/aix7104-03/lpp_new

notes:
  - the changes are persistent
  - you need root rights to install updates
  - tested on aix 6.1 and aix 7.1
requirements: [ 'os', 're', 'tempfile', 'shutil', 'glob' ]
'''


EXAMPLES = '''
# Synchronize ALL rpms from the NIM_MASTER in the standard share
- name: Install All rpms
  aix_update_all:

# Install latest bash rpm from the nfs_server: rn100pgpl.itc.testlab.intranet from the share: /export/nim/aix7104-03/lpp_new
- name: Install rpm bash
  aix_update_all:
    nfs_server: rn100pgpl.itc.testlab.intranet
    nfs_share: /export/nim/aix7104-03/lpp_new
'''


RETURN = '''
'''

# Import necessary libraries
import re
import os
import tempfile
import shutil
import glob
from ansible.module_utils.basic import AnsibleModule

# end import modules


def nim_master(module):
    file = '/etc/niminfo'

    try:
        if os.path.exists(file):
            niminfo = dict(
                (k.strip(), v.strip(' "\n')) for k, v in (
                    line.split(
                        ' ', 1)[1].split(
                        '=', 1) for line in (
                        (l for l in open(
                            file, 'r') if l.startswith('export')))))
    except IOError as e:
        module.fail_json(msg="could not determine NIM_MASTER", rc=rc, err=e)
    return niminfo['NIM_MASTER_HOSTNAME']


def nfs_mount(module):
    dirpath = tempfile.mkdtemp()
    nfsserver = module.params['nfs_server']
    nfsshare = module.params['nfs_share']
    nfs_string = nfsserver + ":" + nfsshare
    mount = module.get_bin_path('mount')
    (rc, err, out) = module.run_command("%s %s %s %s" %
                                        (mount, '-o soft', nfs_string, dirpath))
    if rc != 0:
        msg = "ERROR: could not mount: " + nfs_string
        module.fail_json(
            msg=msg,
            err=err,
            rc=rc)
    return dirpath

def nfs_umount(module, path):
    umount = module.get_bin_path('umount')
    (rc, err, out) = module.run_command("%s %s" % (umount, path))
    if rc != 0:
        err = "ERROR: could not unmount" + path + err
        module.fail_json(
            err=err, rc=rc)
    shutil.rmtree(path)

def install_all_updates(module, path):
    nfsshare = module.params['nfs_share']
    changed = False
    msg = []
    cmd = module.get_bin_path('install_all_updates')
    rc = 0
    if module.check_mode:
        params = "-prYd " + path
    else:
        params = "-rYd " + path
    (rc, out, err) = module.run_command("%s %s" % (cmd, params))
    if rc != 0:
        nfs_umount(module, path)
        msg = ["ERROR: errors during installation: " + err + "Command used:" + "%s %s" % (cmd, params)]
        module.fail_json(msg=msg, err=err, rc=rc)
    else:
        # check for changes
        # dirty code to check output and decide when not changed
        no_lpps = "No filesets on the media could be used to update"
        no_rpms = "No updatable rpm packages found"
        no_both = "ATTENTION, no installp images were found on media"
        skipped = False
        changed = True
        if no_both in out:
            changed = False
            skipped = True
        if "rpm" not in out:
            if no_lpps in out:
                changed = False
                skipped = True
        else:
            if no_lpps in out and no_rpms in out:
                changed = False
                skipped = True
        if changed:
            msg = ['INFO: updates installed']
        else:
            msg = ['INFO: no updates available']
    return changed, msg, skipped


def main():
    # initalize
    module = AnsibleModule(
        argument_spec=dict(
            nfs_server=dict(default='NIM_MASTER', type='str'),
            nfs_share=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    module.warnings = []
    result = {
        'name': 'aix_update_all',
        'changed': False,
        'msg': [],
        'skipped': False,
        'warnings': module.warnings
    }

    # if the nfs_server is NIM_MASTER (default) then retrieve it
    if module.params['nfs_server'].upper() == 'NIM_MASTER':
        module.params['nfs_server'] = nim_master(module)
    # if the nfs_share is not given, then set the default value
    # /export/nim/aix<OSLEVEL><TL>-<SP>/lpp_new
    if module.params['nfs_share'] is None:
        # get oslevel -s and parse the output to get oslevel, TL and SP
        oslevel = module.get_bin_path('oslevel')
        (rc, out, err) = module.run_command("%s %s" % (oslevel, '-s'))
        if rc != 0:
            module.fail_json(
                msg='ERROR: Could not determine the oslevel',
                err=err,
                rc=rc)
        osver = out[:2]
        ostl = out[5:7]
        ossp = out[7:10]
        module.params['nfs_share'] = '/export/nim/aix' + \
            osver + ostl + ossp + '/lpp_new'

    # Mount the remote filesystem and get the mountpath
    mountpath = nfs_mount(module)

    if os.listdir(mountpath):
        # Evaluates to true if not empty.
        (result['changed'], result['msg'], result['skipped']) = install_all_updates(module, mountpath)
        # finished installing, unmount the share
        nfs_umount(module, mountpath)
    else:
        result['msg'] = ['INFO: empty share, no updates available. ']
        result['changed'] = False
        result['skipped'] = True
        result['warnings'] = ['Warning: No updates found on share. ']
        # finished installing, unmount the share
        nfs_umount(module, mountpath)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
